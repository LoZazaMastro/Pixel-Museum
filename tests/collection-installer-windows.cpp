#if defined(_WIN32)

// Actual Windows installer worker, exercised by the local fixture runner.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_installer.hpp"
#include "third_party/nlohmann/json.hpp"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <string>
#include <thread>

namespace museum::media {
bool packaged_images_complete(const std::string&) { return false; }
}

int main(int argc,char**argv) {
    if(argc!=5)return 2;
    _fmode=_O_BINARY;
    museum::CollectionInstaller installer;
    const bool configured=installer.configure(argv[1],argv[2],argv[3],true);
    const std::string command=argv[4];
    bool started=false;
    if(configured)started=command=="remove"?installer.remove_downloaded():installer.start();
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(15);
    using Phase=museum::CollectionInstaller::Phase;
    if(started)for(;;) {
        const auto status=installer.snapshot();
        if(status.phase==Phase::ready||status.phase==Phase::removed||status.phase==Phase::failed||status.phase==Phase::cancelled)break;
        if(std::chrono::steady_clock::now()>deadline) {
            installer.shutdown();std::puts("Timed out waiting for native collection worker");return 3;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    installer.shutdown();
    const auto status=installer.snapshot();
    const nlohmann::json result={{"configured",configured},{"started",started},{"ready",status.phase==Phase::ready},
        {"removed",status.phase==Phase::removed},{"failed",status.phase==Phase::failed},{"error",status.error},
        {"diagnostic",status.diagnostic},{"errno",status.filesystem_errno},{"root",installer.cache_root()}};
    std::puts(result.dump().c_str());return 0;
}

#endif // _WIN32
