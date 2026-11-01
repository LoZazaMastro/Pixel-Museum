// Pixel Museum - transactional, resumable first-run collection installation.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <cstddef>
#include <memory>
#include <string>
namespace museum {
class CollectionInstaller {
public:
    enum class Phase {unconfigured,idle,downloading,verifying,extracting,paused,ready,failed,cancelled};
    struct Status {
        Phase phase=Phase::unconfigured;
        std::uint64_t downloaded_bytes=0,total_bytes=0;
        std::uint64_t installed_bytes=0,total_expanded_bytes=0,installed_files=0,total_files=0;
        std::size_t pack_index=0,pack_count=0;
        double bytes_per_second=0;
        std::string error,stage;
        int filesystem_errno=0;
        std::string diagnostic; // Operation/path/errno for native troubleshooting.
    };
    CollectionInstaller();
    ~CollectionInstaller();
    CollectionInstaller(const CollectionInstaller&)=delete;
    CollectionInstaller& operator=(const CollectionInstaller&)=delete;
    // Small bundled manifest only; filesystem/network work starts on the worker.
    // HTTP is disabled in production. The explicit last argument is for local tests.
    bool configure(const std::string& manifest_path,const std::string& data_directory,
                   const std::string& bundled_root={},bool allow_http_for_tests=false,
                   const std::string& legacy_data_directory={});
    bool start();
    bool retry();
    void pause();
    void cancel(); // Stops work, retaining private partial downloads for retry.
    void shutdown(); // Joins the worker; never deletes an active collection.
    Status snapshot() const;
    bool is_ready() const;
    // Empty when a verified complete bundled collection is being used.
    std::string cache_root() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
