// Host preview has no PS5 system shell. Deliver the actual UI fallback event.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/ps5/trophy_notification.hpp"
#include <cstdlib>
namespace hui::ps5 {
TrophyNotifications::~TrophyNotifications(){stop();}
bool TrophyNotifications::start(std::string directory){std::lock_guard<std::mutex> lock(mutex_);root_=std::move(directory);return false;}
bool TrophyNotifications::submit(const museum::TrophyUnlock& unlock,const std::string& icon){
    std::lock_guard<std::mutex> lock(mutex_);
    if(unlock.id.empty()||unlock.title.empty()||!seen_.insert(unlock.id).second)return false;
    if(std::getenv("MUSEUM_HOST_TROPHY_NATIVE_ACCEPT"))return true; // API accepted, no visible-shell/failure event.
    fallback_.push_back({unlock,icon,"Native OS notifications unavailable in host preview"});return true;
}
std::vector<TrophyNotificationFallback> TrophyNotifications::pollFallback(){std::lock_guard<std::mutex> lock(mutex_);std::vector<TrophyNotificationFallback> out;out.swap(fallback_);return out;}
void TrophyNotifications::clearPending(){std::lock_guard<std::mutex> lock(mutex_);generation_.fetch_add(1,std::memory_order_release);queue_.clear();fallback_.clear();seen_.clear();}
void TrophyNotifications::stop(){std::lock_guard<std::mutex> lock(mutex_);running_=false;stopping_=true;}
}
