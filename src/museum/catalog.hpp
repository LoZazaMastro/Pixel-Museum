// Pixel Museum — curated records and date-aware collection navigation.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string>
#include <vector>
#include <cstdint>
#include <cstddef>
#include <map>
namespace museum {
inline constexpr std::size_t kCatalogByteLimit=64u<<20;
inline constexpr std::size_t kSoundtrackTrackLimit=2048;
inline constexpr std::size_t kEntryAliasLimit=4096,kEntryAliasIdBytes=192,kEntryAliasHops=32;
struct Image { std::string url,source_page,title,creator,license,credit;int story_paragraph=-1;std::string caption;std::string dark_url{}; };
struct VideoRecord { std::string youtube_id,url,title,caption,creator,source_page;std::string poster_url{};double start_seconds=0,end_seconds=0;int story_paragraph=-1; };
struct Soundtrack { std::string title,composer,curator_note;std::vector<VideoRecord> tracks; };
struct Source { std::string title,url,publisher,license,attribution; };
struct Model { std::string url,asset_file,source_page,title,creator,license,credit;std::vector<std::string> include_groups;float initial_tilt=.13f,initial_angle=0.f,initial_zoom=1.f;bool source_z_up=false;std::string display_caption; };
struct EditorialFeature {
    std::string id,title,summary,editorial_credit;
    std::vector<std::string> body,story_headings;
    std::vector<int> image_indices; // The parent gallery owns actual image records.
    std::vector<Source> sources;
};
struct Entry {
    std::string id,kind,title,subtitle,summary,era_id,layout,culture_category;
    int year=0,month=0,day=0;
    std::string precision,region;
    std::string event_semantics,editorial_credit,factual_note,linked_exhibit_id,story_entry_id;
    bool featured=false,calendar_only=false,explicit_story_media_only=false;
    bool preserve_unillustrated_opening=false;
    int calendar_month=0,calendar_day=0;
    int preferred_image=0; // Base gallery index; feature illustrations never replace the exhibit cover.
    std::vector<std::string> body,tags,related_ids,story_headings;
    std::vector<Image> images;
    std::vector<VideoRecord> videos;
    Soundtrack soundtrack;
    std::vector<Soundtrack> soundtrack_rooms;
    std::vector<Model> models;
    std::vector<Source> sources;
    std::vector<EditorialFeature> editorial_features;
};
std::string date_label(const Entry&,bool include_year=true);
// Internal navigation anchor only; unknown months/days stay unknown in the UI.
int chronology_day(const Entry&);
struct Era { std::string id,title,summary; int start_year=0,end_year=0; std::uint32_t colour=0xcb5a37; };
class Catalog {
public:
    std::vector<Entry> entries;
    std::vector<Era> eras;
    std::string title,subtitle,remote_url,initial_id,error;
    bool load(const std::string& path);
    bool parse(const std::string& bytes);
    // Retired wrapper IDs resolve to existing entries without adding timeline
    // stops. Real entries take precedence; cycles/dangling chains resolve empty.
    std::string resolve_entry_id(const std::string& id) const;
    const Entry* find_entry(const std::string& id) const;
    // Changes text only; dates, media, sources and paragraph positions stay intact.
    bool set_locale(const std::string& app_root,const std::string& locale);
    const std::string& locale() const { return locale_; }
    const std::string& locale_error() const { return locale_error_; }
    const Era* era(const Entry&) const;
    std::vector<int> on_this_day(int month,int day) const;
private:
    struct EnglishText {
        std::string id,title,subtitle,summary,editorial_credit;
        std::vector<std::string> body,story_headings;
        struct FeatureText {
            std::string id,title,summary,editorial_credit;
            std::vector<std::string> body,story_headings;
        };
        std::vector<FeatureText> features;
    };
    std::vector<EnglishText> english_;
    std::map<std::string,std::string,std::less<>> entry_aliases_;
    std::string locale_="en",locale_error_;
    void capture_english();
};
}
