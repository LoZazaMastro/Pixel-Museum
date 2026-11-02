// Windows application updates. Editorial database updates remain independent.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <map>
#include <memory>
#include <string>

namespace museum {
class ApplicationUpdater {
public:
#ifndef MUSEUM_APP_VERSION
#define MUSEUM_APP_VERSION "0.2.0-preview"
#endif
    static constexpr const char* bundled_version = MUSEUM_APP_VERSION;
    static constexpr const char* feed_url = "https://lozazamastro.github.io/Pixel-Museum/application-update.json";
    enum class Phase { idle, checking, current, available, downloading, ready, failed };
    struct Snapshot {
        Phase phase = Phase::idle;
        std::string current_version = bundled_version, version, error;
        std::uint64_t downloaded_bytes = 0, total_bytes = 0;
        std::map<std::string, std::string> notes;
    };
    ApplicationUpdater();
    ~ApplicationUpdater();
    ApplicationUpdater(const ApplicationUpdater&) = delete;
    ApplicationUpdater& operator=(const ApplicationUpdater&) = delete;
    bool configure(const std::string& application_root, const std::string& data_root,
                   const std::string& source = feed_url,
                   const std::string& current_version = bundled_version);
    bool check();
    bool install();
    Snapshot snapshot() const;
    // Starts a bounded, independent helper waiting for this process to exit.
    // Only after true may the caller quit; failure leaves the app running.
    bool begin_restart(const std::string& language = "en");
    void shutdown();
    static bool newer_version(const std::string& candidate, const std::string& current);
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
