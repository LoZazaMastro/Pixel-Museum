// Pixel Museum - local, persistent museum achievements.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace museum {
enum class TrophyRank { Bronze, Silver, Gold, Platinum };
enum class TrophyTrigger { VisitCount, AllCatalogSnapshot, AllOtherTrophies, SecretCard, FirstMusic,
    FirstVideo, MaximumZoom, FirstCulture, FirstToday, ExperienceStat };
struct TrophyDefinition {
    std::string id,title,description,hint,badge;
    TrophyRank rank=TrophyRank::Bronze;
    TrophyTrigger trigger=TrophyTrigger::VisitCount;
    bool secret=false;
    std::uint64_t target=1;
    std::string owner_id; // Canonical ID, required for SecretCard.
    int card_index=-1;
    std::string stat_key; // Exact real experience statistic; no guessed thresholds.
};
struct TrophyView {
    std::string id,title,description,hint,badge;
    TrophyRank rank=TrophyRank::Bronze;
    bool secret=false,unlocked=false;
    std::uint64_t current=0,target=0,unlocked_at=0;
};
struct TrophyUnlock {
    std::string id,title,description,badge;
    TrophyRank rank=TrophyRank::Bronze;
    std::uint64_t unlocked_at=0;
};
class Trophies {
public:
    explicit Trophies(std::string state_path);
    bool reset(); // Atomically clear progress while retaining the eligible catalogue snapshot.
    bool load(); // Missing file is a valid first run. Corrupt data is never overwritten.
    void setDefinitions(std::vector<TrophyDefinition> definitions);
    bool setEligibleCatalogSnapshot(const std::vector<std::string>& canonical_ids);
    bool visit(const std::string& canonical_owner);
    bool card(const std::string& canonical_owner,int card_index);
    bool musicProgress(const std::string& session_id,double played_seconds,bool ended=false);
    bool videoProgress(const std::string& session_id,double played_seconds,bool ended=false);
    bool zoomMaximum();
    bool cultureVisit(const std::string& canonical_owner);
    bool todayVisit(const std::string& canonical_owner); // Only after a real matched jump succeeds.
    bool experienceResult(const std::string& experience_id,
                          const std::map<std::string,std::uint64_t>& real_statistics);
    std::vector<TrophyView> views(bool reveal_secrets=false) const;
    std::vector<TrophyUnlock> drainUnlocks(); // One delivery per newly persisted unlock.
    const std::vector<TrophyDefinition>& definitions() const { return definitions_; }
    const std::string& lastError() const { return error_; }
    std::size_t visitedCount() const;
    bool writable() const { return writable_; }
    static std::vector<std::uint64_t> visitMilestones();
private:
    struct State {
        std::map<std::string,std::uint64_t> unlocked;
        std::vector<std::string> visited,snapshot,seen_cards,culture;
        std::map<std::string,std::uint64_t> stats;
        bool first_music=false,first_video=false,max_zoom=false,first_today=false;
    } state_;
    std::string path_,error_;
    bool writable_=true;
    std::vector<TrophyDefinition> definitions_;
    std::vector<TrophyUnlock> pending_;
    bool commit(State next);
    std::uint64_t progress(const TrophyDefinition&,const State&) const;
    static std::string encode(const State&);
    static bool decode(const std::string&,State&);
};
} // namespace museum
