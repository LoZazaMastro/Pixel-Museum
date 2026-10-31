// Pixel Museum - optional native trophy-style local notifications.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/trophies.hpp"
#include <condition_variable>
#include <cstdint>
#include <atomic>
#include <deque>
#include <mutex>
#include <pthread.h>
#include <set>
#include <string>
#include <vector>
namespace hui::ps5 {
struct TrophyNotificationFallback { museum::TrophyUnlock unlock;std::string icon_path,reason; };
class TrophyNotifications {
public:
    ~TrophyNotifications();
    bool start(std::string user_data_directory); // Persistent /data or title /download0 directory on PS5.
    bool submit(const museum::TrophyUnlock&,const std::string& local_png_path);
    std::vector<TrophyNotificationFallback> pollFallback(); // Consume on UI thread.
    void stop();
    void clearPending(); // Reset unsent events/dedupe; cannot retract an OS toast already accepted.
    static std::string payload(const museum::TrophyUnlock&,const std::string& local_png_path,
                               const std::string& timestamp,const std::string& notification_id);
#ifdef MUSEUM_TROPHY_HOST_TEST
    static std::vector<std::uint8_t> testRelayAddress();
    static bool testRelayPayload(const std::string&,std::vector<std::uint8_t>&);
    using TestSender=int(*)(int,bool,const char*);
    void setTestSender(TestSender sender) { test_sender_=sender; }
#endif
private:
    struct Item {museum::TrophyUnlock unlock;std::string icon;};
    std::mutex mutex_;std::condition_variable wake_;
    std::deque<Item> queue_;std::vector<TrophyNotificationFallback> fallback_;
    std::set<std::string> seen_;std::string root_;
    pthread_t thread_{};bool running_=false,stopping_=false;
    std::atomic<unsigned long long> generation_{0};
    static void* entry(void*);void run();bool validIcon(const std::string&,std::string* reason=nullptr)const;
#ifdef MUSEUM_TROPHY_HOST_TEST
    TestSender test_sender_=nullptr;
#endif
};
} // namespace hui::ps5
