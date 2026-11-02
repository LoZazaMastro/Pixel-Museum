// Independently versioned editorial content; application binaries never update here.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <map>
#include <memory>
#include <string>

namespace museum {
class DatabaseUpdater {
public:
    static constexpr std::uint64_t bundled_revision = 1;
    static constexpr const char* feed_url = "https://lozazamastro.github.io/Pixel-Museum/database-update.json";
    enum class Phase { idle, checking, current, available, downloading, ready, failed };
    struct Snapshot {
        Phase phase = Phase::idle;
        std::uint64_t current_revision = bundled_revision, revision = bundled_revision;
        std::uint64_t downloaded_bytes = 0, total_bytes = 0;
        std::string version, error;
        std::map<std::string, std::string> notes;
    };
    DatabaseUpdater();
    ~DatabaseUpdater();
    DatabaseUpdater(const DatabaseUpdater&) = delete;
    DatabaseUpdater& operator=(const DatabaseUpdater&) = delete;
    // Mounts the previous verified snapshot before catalogue/locale loading.
    // New downloads remain inactive in this process until the next launch.
    bool configure(const std::string& application_root, const std::string& data_root,
                   const std::string& source = feed_url);
    bool check();
    bool install();
    Snapshot snapshot() const;
    void shutdown();
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
