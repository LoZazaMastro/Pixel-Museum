// Real installer removal worker: isolated filesystem and lifecycle regressions.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_installer.hpp"
#include "third_party/nlohmann/json.hpp"
#include <curl/curl.h>
#include <atomic>
#include <cassert>
#include <cerrno>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <sys/stat.h>
#include <unistd.h>

namespace fs = std::filesystem;
using Installer = museum::CollectionInstaller;
using Phase = Installer::Phase;
namespace {
std::atomic<unsigned> erase_calls{0}, network_calls{0}, lstat_calls{0};
std::atomic<bool> slow_erase{false}, deny_erase{false};
std::string complete_bundle;
void write(const fs::path& path, const std::string& bytes = "fixture") {
    fs::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary); file << bytes; file.close();
    assert(file);
}
struct Fixture {
    fs::path root, data, legacy, bundle, manifest;
    explicit Fixture(const fs::path& base, const std::string& name)
        : root(base / name), data(root / "data"), legacy(root / "legacy"),
          bundle(root / "bundle"), manifest(root / "collection-packs.json") {
        fs::create_directories(root);
        nlohmann::json value = {{"schema_version", 1}, {"collection_id", "removal-fixture"},
            {"packs", nlohmann::json::array({{{"id", "one"},
                {"url", "https://127.0.0.1:1/never-requested.tar"},
                {"bytes", 10240u}, {"sha256", std::string(64, '0')}, {"format", "tar"}}})}};
        write(manifest, value.dump());
        write(data / "preferences.json", "preferences-preserved");
        write(data / "trophies.json", "trophies-preserved");
        write(legacy / "preferences.json", "legacy-preferences-preserved");
        write(bundle / "assets/bundled-image.jpg", "bundle-preserved");
        write(root / "unrelated/save.bin", "unrelated-preserved");
    }
    void populate() const {
        write(data / "collection/ready-version/archives/pack.tar");
        write(data / "collection/ready-version/.complete.json");
        write(data / "collection/.stage-old/assets/images/partial.jpg");
        write(data / "collection/downloads/part.tar.part");
        write(data / "collection/media-cache/cache/photo.jpg");
        write(legacy / "collection/legacy-version/archives/legacy.tar");
        write(legacy / "collection/.stage-legacy/.pack-0.json");
        write(legacy / "collection/downloads/old.tar.part");
    }
    void configure(Installer& installer, bool ready = false) const {
        complete_bundle = ready ? bundle.string() : std::string();
        assert(installer.configure(manifest.string(), data.string(), bundle.string(), false, legacy.string()));
    }
    void protected_files() const {
        assert(fs::exists(data / "preferences.json"));
        assert(fs::exists(data / "trophies.json"));
        assert(fs::exists(legacy / "preferences.json"));
        assert(fs::exists(bundle / "assets/bundled-image.jpg"));
        assert(fs::exists(root / "unrelated/save.bin"));
    }
};
Installer::Status wait(Installer& installer, Phase wanted) {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
    for (;;) {
        const auto status = installer.snapshot();
        if (status.phase == wanted) return status;
        if (status.phase == Phase::failed && wanted != Phase::failed) {
            std::cerr << "Unexpected removal failure: " << status.error << " / " << status.diagnostic << '\n';
            assert(false);
        }
        assert(std::chrono::steady_clock::now() < deadline);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}
void removed(Installer& installer, const Fixture& fixture) {
    const auto status = wait(installer, Phase::removed);
    installer.shutdown();
    assert(!installer.is_ready() && installer.cache_root().empty());
    assert(!status.downloaded_bytes && !status.installed_bytes && !status.installed_files && status.bytes_per_second == 0);
    assert(!fs::exists(fixture.data / "collection"));
    assert(!fs::exists(fixture.legacy / "collection"));
    fixture.protected_files();
}
}
extern "C" int __real_unlinkat(int, const char*, int);
extern "C" int __wrap_unlinkat(int directory, const char* path, int flags) {
    ++erase_calls;
    if (slow_erase) std::this_thread::sleep_for(std::chrono::milliseconds(10));
    if (deny_erase && std::string(path) == "deny-delete") { errno = EACCES; return -1; }
    return __real_unlinkat(directory, path, flags);
}
extern "C" int __wrap_lstat(const char*, struct stat*) { ++lstat_calls; errno = ENOSYS; return -1; }
extern "C" CURLcode __wrap_curl_easy_perform(CURL*) { ++network_calls; return CURLE_FAILED_INIT; }
namespace museum::media {
bool packaged_images_complete(const std::string& root) { return root == complete_bundle; }
}
int main() {
    char pattern[] = "/tmp/pm-collection-removal-XXXXXX";
    char* temporary = mkdtemp(pattern); assert(temporary);
    const fs::path base(temporary);
    Installer unconfigured; assert(!unconfigured.remove_downloaded());
    {
        Fixture fixture(base, "ready-and-legacy"); fixture.populate(); Installer installer;
        fixture.configure(installer, true); assert(installer.start()); wait(installer, Phase::ready);
        assert(installer.is_ready()); assert(installer.remove_downloaded()); removed(installer, fixture);
        assert(network_calls == 0);
        assert(installer.remove_downloaded()); removed(installer, fixture); // Idempotent missing tree.
        complete_bundle.clear(); assert(installer.start()); wait(installer, Phase::failed); installer.shutdown();
        assert(network_calls > 0); // A fresh install, not a stale ready marker. No actual HTTP call occurs.
        network_calls = 0;
    }
    {
        Fixture fixture(base, "nested-link"); fixture.populate();
        write(fixture.root / "outside/keep.bin", "outside-preserved");
        fs::create_directory_symlink(fixture.root / "outside", fixture.data / "collection/link-outside");
        fs::create_symlink(fixture.root / "outside/keep.bin", fixture.data / "collection/file-link");
        Installer installer; fixture.configure(installer); assert(installer.remove_downloaded()); removed(installer, fixture);
        assert(fs::exists(fixture.root / "outside/keep.bin"));
    }
    {
        Fixture fixture(base, "failure-and-retry"); fixture.populate();
        write(fixture.data / "collection/deny-delete"); Installer installer; fixture.configure(installer);
        deny_erase = true; assert(installer.remove_downloaded()); const auto status = wait(installer, Phase::failed); installer.shutdown();
        assert(!installer.is_ready() && status.filesystem_errno == EACCES && !status.diagnostic.empty());
        assert(fs::exists(fixture.data / "collection/deny-delete")); fixture.protected_files();
        deny_erase = false; assert(installer.remove_downloaded()); removed(installer, fixture);
    }
    {
        Fixture fixture(base, "interrupt-and-retry"); fixture.populate();
        for (unsigned n = 0; n < 64; ++n) write(fixture.data / "collection/many" / std::to_string(n));
        Installer installer; fixture.configure(installer); erase_calls = 0; slow_erase = true;
        assert(installer.remove_downloaded());
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        while (!erase_calls) { assert(std::chrono::steady_clock::now() < deadline); std::this_thread::sleep_for(std::chrono::milliseconds(1)); }
        assert(!installer.remove_downloaded()); // Cannot launch a second deleting worker.
        installer.shutdown(); slow_erase = false;
        assert(installer.snapshot().phase != Phase::removed && fs::exists(fixture.data / "collection"));
        fixture.protected_files(); assert(installer.remove_downloaded()); removed(installer, fixture);
    }
    {
        Fixture fixture(base, "ancestor-link"); write(fixture.root / "outside/data/collection/keep.bin");
        fs::create_directory_symlink(fixture.root / "outside", fixture.root / "alias");
        Installer installer; assert(installer.configure(fixture.manifest.string(), (fixture.root / "alias/data").string(), fixture.bundle.string()));
        if (installer.remove_downloaded()) wait(installer, Phase::failed);
        installer.shutdown(); assert(fs::exists(fixture.root / "outside/data/collection/keep.bin")); fixture.protected_files();
    }
    {
        Fixture fixture(base, "root-link"); write(fixture.root / "outside/keep.bin");
        fs::create_directory_symlink(fixture.root / "outside", fixture.data / "collection");
        Installer installer; fixture.configure(installer);
        if (installer.remove_downloaded()) wait(installer, Phase::failed);
        installer.shutdown(); assert(fs::exists(fixture.root / "outside/keep.bin"));
        assert(fs::is_symlink(fixture.data / "collection")); fixture.protected_files();
    }
    {
        // A failure in the legacy location must never follow its redirected
        // parent or claim that all data has been removed. Partial cleanup of
        // the valid current location is retried through the same API.
        Fixture fixture(base, "legacy-parent-link"); fixture.populate();
        write(fixture.root / "outside/collection/keep.bin");
        fs::create_directory_symlink(fixture.root / "outside", fixture.root / "legacy-alias");
        Installer installer; assert(installer.configure(fixture.manifest.string(), fixture.data.string(),
            fixture.bundle.string(), false, (fixture.root / "legacy-alias").string()));
        if (installer.remove_downloaded()) wait(installer, Phase::failed);
        installer.shutdown(); assert(installer.snapshot().phase==Phase::failed);
        assert(fs::exists(fixture.root / "outside/collection/keep.bin")); fixture.protected_files();
    }
    {
        Fixture fixture(base, "missing-parent"); Installer installer;
        const auto missing=fixture.root / "not-yet-created/data";
        assert(installer.configure(fixture.manifest.string(), missing.string(), fixture.bundle.string()));
        assert(installer.remove_downloaded()); wait(installer, Phase::removed); installer.shutdown();
        assert(!fs::exists(missing)); fixture.protected_files();
    }
    {
        Fixture fixture(base, "invalid-traversal"); Installer installer;
        assert(!installer.configure(fixture.manifest.string(), (fixture.data / "../outside").string(), fixture.bundle.string()));
        assert(!installer.remove_downloaded()); fixture.protected_files();
    }
    assert(network_calls == 0 && lstat_calls == 0);
    fs::remove_all(base);
    std::cout << "PASS: isolated collection removal, legacy/partial/cache cleanup, protected data, no-follow symlinks, failure/retry, interrupted worker and fresh restart; no external network or lstat.\n";
}
