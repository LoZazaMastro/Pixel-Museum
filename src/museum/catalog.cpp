// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/catalog.hpp"
#include "museum/localization.hpp"
#include "core/save_file.hpp"
#include "platform/playback_window.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstdio>
#include <tuple>
#include <array>
#include <string_view>
namespace museum {
using Json=nlohmann::json;
namespace {
std::string str(const Json& j,const char* k){auto i=j.find(k);return i!=j.end()&&i->is_string()?i->get<std::string>():"";}
int number(const Json& j,const char* k){auto i=j.find(k);return i!=j.end()&&i->is_number_integer()?i->get<int>():0;}
float decimal(const Json& j,const char* k,float fallback){auto i=j.find(k);if(i==j.end()||!i->is_number())return fallback;const float value=i->get<float>();return std::isfinite(value)?value:fallback;}
std::vector<std::string> strings(const Json& j,const char* k){std::vector<std::string> v;auto i=j.find(k);if(i!=j.end()&&i->is_array())for(const auto& s:*i)if(s.is_string())v.push_back(s.get<std::string>());return v;}
bool https(const std::string& s){return s.rfind("https://",0)==0;}
bool identified_cover(const Json& image){
    for(const char*key:{"cover_art","cover_role"})
        if(image.contains(key)&&image[key].is_boolean()&&image[key].get<bool>())return true;
    return str(image,"kind")=="cover"||str(image,"role")=="cover"||str(image,"cover_role")=="cover";
}
void label_award_editions(std::vector<Entry>& entries){
    for(auto& entry:entries)
        if(entry.id=="the-game-awards-"+std::to_string(entry.year))
            entry.title="The Game Awards "+std::to_string(entry.year);
}
}
std::string date_label(const Entry&e,bool include_year){
    static constexpr const char*months[]={"January","February","March","April","May","June","July","August","September","October","November","December"};
    static constexpr int days[]={31,28,31,30,31,30,31,31,30,31,30,31};
    const bool month=e.month>=1&&e.month<=12;
    const int limit=month?days[e.month-1]+(e.month==2&&e.year%4==0&&(e.year%100!=0||e.year%400==0)?1:0):0;
    std::string label;
    if(e.precision=="day"&&month&&e.day>=1&&e.day<=limit){char date[128];const std::string pattern(i18n::tr("%d %s")),name(i18n::tr(months[e.month-1]));std::snprintf(date,sizeof(date),pattern.c_str(),e.day,name.c_str());label=date;}
    else if(e.precision=="month"&&month)label=i18n::tr(months[e.month-1]);
    if(include_year){if(label.empty())label=std::to_string(e.year);else{char dated[160];const std::string pattern(i18n::tr("%s %d"));std::snprintf(dated,sizeof(dated),pattern.c_str(),label.c_str(),e.year);label=dated;}}
    return label;
}
bool Catalog::load(const std::string& path){std::string b;if(!hui::save::read_file(path,&b,kCatalogByteLimit)){error="The collection catalogue could not be read or exceeds 64 MiB.";return false;}return parse(b);}
bool Catalog::parse(const std::string& bytes){
    if(bytes.size()>kCatalogByteLimit){error="The collection catalogue exceeds the 64 MiB limit.";return false;}
    auto j=Json::parse(bytes,nullptr,false);
    if(j.is_discarded()||!j.is_object()||!j.contains("entries")||!j["entries"].is_array()){error="The collection catalogue is invalid.";return false;}
    std::vector<Entry> next;
    for(const auto& row:j["entries"]){
        if(!row.is_object())continue;
        Entry e;e.id=str(row,"id");e.title=str(row,"title");e.year=number(row,"year");
        if(e.id.empty()||e.title.empty()||e.year<1800||e.year>2100)continue;
        e.kind=str(row,"kind");e.subtitle=str(row,"subtitle");e.summary=str(row,"summary");e.era_id=str(row,"era_id");e.layout=str(row,"layout");e.culture_category=str(row,"culture_category");
        e.event_semantics=str(row,"event_semantics");e.editorial_credit=str(row,"editorial_credit");e.factual_note=str(row,"factual_note");e.linked_exhibit_id=str(row,"linked_exhibit_id");e.story_entry_id=str(row,"story_entry_id");
        e.body=strings(row,"body");e.tags=strings(row,"tags");e.related_ids=strings(row,"related_ids");e.story_headings=strings(row,"story_headings");
        if(row.contains("featured")&&row["featured"].is_boolean())e.featured=row["featured"].get<bool>();
        if(row.contains("calendar_only")&&row["calendar_only"].is_boolean())e.calendar_only=row["calendar_only"].get<bool>();
        e.explicit_story_media_only=(row.contains("explicit_story_media_only")&&row["explicit_story_media_only"].is_boolean()&&row["explicit_story_media_only"].get<bool>())||(row.contains("canonical_narrative_enrichment")&&row["canonical_narrative_enrichment"].is_object());
        e.preserve_unillustrated_opening=row.contains("preserve_unillustrated_opening")&&row["preserve_unillustrated_opening"].is_boolean()&&row["preserve_unillustrated_opening"].get<bool>();
        if(row.contains("calendar")&&row["calendar"].is_object()){e.calendar_month=number(row["calendar"],"month");e.calendar_day=number(row["calendar"],"day");}
        if(row.contains("date")&&row["date"].is_object()){const auto& d=row["date"];e.month=number(d,"month");e.day=number(d,"day");e.precision=str(d,"precision");e.region=str(d,"region");}
        bool cover_selected=false;int first_game_cover=-1;std::vector<bool> image_cover_roles;
        if(row.contains("images")&&row["images"].is_array())for(const auto& a:row["images"]){Image i;i.url=str(a,"url");i.dark_url=str(a,"dark_url");if(!https(i.dark_url))i.dark_url.clear();i.source_page=str(a,"source_page");i.title=str(a,"title");i.caption=str(a,"caption");i.creator=str(a,"creator");i.license=str(a,"license");i.credit=str(a,"credit");if(a.contains("story_paragraph")&&a["story_paragraph"].is_number_integer())i.story_paragraph=std::clamp(number(a,"story_paragraph"),-1,1000);if(https(i.url)){
            const int width=number(a,"width"),height=number(a,"height");
            const bool game_cover=e.kind=="game"&&identified_cover(a);
            if(game_cover&&first_game_cover<0)first_game_cover=int(e.images.size());
            image_cover_roles.push_back(game_cover);
            if(!cover_selected&&std::max(width,height)>=1600&&std::min(width,height)>=800){e.preferred_image=int(e.images.size());cover_selected=true;}
            e.images.push_back(i);
        }}
        const bool explicit_preferred=row.contains("preferred_image")&&row["preferred_image"].is_number_integer();
        if(explicit_preferred&&!e.images.empty())e.preferred_image=std::clamp(number(row,"preferred_image"),0,int(e.images.size())-1);
        else if(first_game_cover>=0)e.preferred_image=first_game_cover;
        // A game cover explicitly bound to paragraph zero is the timeline hero.
        // Keep it in the gallery, while leaving the first story card to gameplay.
        if(e.kind=="game"&&!e.images.empty()&&image_cover_roles[size_t(e.preferred_image)]&&e.images[size_t(e.preferred_image)].story_paragraph==0)
            e.images[size_t(e.preferred_image)].story_paragraph=-1;
        if(row.contains("videos")&&row["videos"].is_array())for(const auto& a:row["videos"]){
            VideoRecord v;v.youtube_id=str(a,"youtube_id");v.url=str(a,"url");v.title=str(a,"title");v.caption=str(a,"caption");v.creator=str(a,"creator");v.source_page=str(a,"source_page");v.poster_url=str(a,"poster_url");
            if(!https(v.poster_url))v.poster_url.clear();
            if(a.contains("story_paragraph")&&a["story_paragraph"].is_number_integer()){
                const auto placement=a["story_paragraph"].get<long long>();
                if(placement>=0&&placement<static_cast<long long>(e.body.size()))v.story_paragraph=static_cast<int>(placement);
            }
            if(v.youtube_id.size()==11)e.videos.push_back(v);
        }
        const auto parse_soundtrack=[&](const Json& list){
            Soundtrack soundtrack;
            soundtrack.title=str(list,"title");soundtrack.composer=str(list,"composer");soundtrack.curator_note=str(list,"curator_note");
            if(list.contains("tracks")&&list["tracks"].is_array())for(const auto&a:list["tracks"]){
                VideoRecord v;v.youtube_id=str(a,"youtube_id");v.url=str(a,"url");v.title=str(a,"title");v.caption=str(a,"caption");v.creator=str(a,"creator");v.source_page=str(a,"source_page");
                if(a.contains("start_seconds")||a.contains("end_seconds")){
                    if(!a.contains("start_seconds")||!a.contains("end_seconds")||!a["start_seconds"].is_number()||!a["end_seconds"].is_number())continue;
                    v.start_seconds=a["start_seconds"].get<double>();v.end_seconds=a["end_seconds"].get<double>();
                    if(!media::PlaybackWindow::valid(v.start_seconds,v.end_seconds))continue;
                }
                if(v.youtube_id.size()==11&&v.youtube_id.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")==std::string::npos&&!v.title.empty()&&https(v.source_page))soundtrack.tracks.push_back(v);
                if(soundtrack.tracks.size()>=kSoundtrackTrackLimit)break;
            }
            return soundtrack;
        };
        if(row.contains("soundtrack")&&row["soundtrack"].is_object())e.soundtrack=parse_soundtrack(row["soundtrack"]);
        if(row.contains("soundtrack_rooms")&&row["soundtrack_rooms"].is_array())for(const auto&room:row["soundtrack_rooms"]){
            if(!room.is_object())continue;
            auto parsed=parse_soundtrack(room);
            if(!parsed.tracks.empty())e.soundtrack_rooms.push_back(std::move(parsed));
            if(e.soundtrack_rooms.size()>=16)break;
        }
        if(row.contains("models")&&row["models"].is_array())for(const auto& a:row["models"]){Model m;m.display_caption=str(a,"display_caption");m.url=str(a,"url");m.asset_file=str(a,"asset_file");if(m.asset_file.rfind("models/",0)!=0||m.asset_file.find("..")!=std::string::npos||m.asset_file.find_first_of("\\:")!=std::string::npos)m.asset_file.clear();m.source_page=str(a,"source_page");m.title=str(a,"title");m.creator=str(a,"creator");m.license=str(a,"license");m.credit=str(a,"credit");m.include_groups=strings(a,"include_groups");m.initial_tilt=std::clamp(decimal(a,"initial_tilt",.13f),-1.2f,1.2f);m.initial_angle=decimal(a,"initial_angle",0.f);m.initial_zoom=std::clamp(decimal(a,"initial_zoom",1.f),.5f,2.f);if(a.contains("source_z_up")&&a["source_z_up"].is_boolean())m.source_z_up=a["source_z_up"].get<bool>();if(https(m.url)||!m.asset_file.empty())e.models.push_back(m);}
        if(row.contains("sources")&&row["sources"].is_array())for(const auto& a:row["sources"]){Source s;s.title=str(a,"title");s.url=str(a,"url");s.publisher=str(a,"publisher");s.license=str(a,"license");s.attribution=str(a,"attribution");if(https(s.url))e.sources.push_back(s);}
        if(row.contains("editorial_features")&&row["editorial_features"].is_array())for(const auto& a:row["editorial_features"]){
            if(!a.is_object()||e.editorial_features.size()>=32)continue;
            EditorialFeature f;f.id=str(a,"id");f.title=str(a,"title");f.summary=str(a,"summary");f.editorial_credit=str(a,"editorial_credit");
            f.body=strings(a,"body");f.story_headings=strings(a,"story_headings");
            if(f.id.empty()||f.title.empty()||f.body.empty()||f.body.size()>1000||f.story_headings.size()!=f.body.size())continue;
            if(a.contains("images")&&a["images"].is_array())for(const auto& photo:a["images"]){
                Image i;i.url=str(photo,"url");i.dark_url=str(photo,"dark_url");if(!https(i.dark_url))i.dark_url.clear();i.source_page=str(photo,"source_page");i.title=str(photo,"title");i.caption=str(photo,"caption");i.creator=str(photo,"creator");i.license=str(photo,"license");i.credit=str(photo,"credit");
                if(photo.contains("story_paragraph")&&photo["story_paragraph"].is_number_integer())i.story_paragraph=std::clamp(number(photo,"story_paragraph"),-1,1000);
                if(https(i.url)){f.image_indices.push_back(int(e.images.size()));e.images.push_back(std::move(i));}
            }
            if(a.contains("sources")&&a["sources"].is_array())for(const auto& source:a["sources"]){Source s;s.title=str(source,"title");s.url=str(source,"url");s.publisher=str(source,"publisher");s.license=str(source,"license");s.attribution=str(source,"attribution");if(https(s.url))f.sources.push_back(std::move(s));}
            e.editorial_features.push_back(std::move(f));
        }
        next.push_back(std::move(e));
        if(next.size()>5000){error="The collection catalogue exceeds the 5,000-exhibit limit.";return false;}
    }
    if(next.empty()){error="The collection contains no valid exhibits.";return false;}
    std::stable_sort(next.begin(),next.end(),[](const Entry&a,const Entry&b){
        const auto order=[](const Entry&e){
            const bool dated=(e.precision=="month"||e.precision=="day")&&e.month>=1&&e.month<=12;
            // Unknown days stay unknown. Editorial calendar slots never sort
            // a historical event ahead of its actual date within the year.
            return std::make_tuple(e.year,dated?e.month:0,dated&&e.precision=="day"?e.day:0);
        };
        return order(a)<order(b);
    });
    decltype(entry_aliases_) next_aliases;
    if(j.contains("entry_aliases")&&j["entry_aliases"].is_object()&&j["entry_aliases"].size()<=kEntryAliasLimit){
        for(auto alias=j["entry_aliases"].begin();alias!=j["entry_aliases"].end();++alias){
            if(!alias.value().is_string())continue;
            const auto&key=alias.key();const auto&target=alias.value().get_ref<const std::string&>();
            if(key.empty()||target.empty()||key.size()>kEntryAliasIdBytes||target.size()>kEntryAliasIdBytes||key.find('\0')!=std::string::npos||target.find('\0')!=std::string::npos)continue;
            next_aliases.emplace(key,target);
        }
    }
    entries=std::move(next);entry_aliases_=std::move(next_aliases);eras.clear();
    if(j.contains("eras")&&j["eras"].is_array())for(const auto& r:j["eras"]){Era e;e.id=str(r,"id");e.title=str(r,"title");e.summary=str(r,"summary");e.start_year=number(r,"start_year");e.end_year=number(r,"end_year");std::string colour=str(r,"colour");if(colour.empty()&&r.contains("palette")&&r["palette"].is_array()&&r["palette"].size()>1&&r["palette"][1].is_string())colour=r["palette"][1].get<std::string>();if(!colour.empty()){if(colour[0]=='#')colour.erase(0,1);if(colour.size()==6)e.colour=std::strtoul(colour.c_str(),nullptr,16);}eras.push_back(e);}
    title=str(j,"title");subtitle=str(j,"subtitle");remote_url=str(j,"remote_catalog_url");initial_id=str(j,"initial_id");
    const auto canonical_initial=resolve_entry_id(initial_id);if(!canonical_initial.empty())initial_id=canonical_initial;
    label_award_editions(entries);
    error.clear();capture_english();return true;
}
std::string Catalog::resolve_entry_id(const std::string& id) const{
    if(id.empty())return {};
    std::string_view key=id;std::array<std::string_view,kEntryAliasHops>seen{};
    for(std::size_t hop=0;hop<=kEntryAliasHops;++hop){
        for(const auto&entry:entries)if(entry.id==key)return entry.id;
        if(hop==kEntryAliasHops||key.size()>kEntryAliasIdBytes)return {};
        for(std::size_t prior=0;prior<hop;++prior)if(seen[prior]==key)return {};
        seen[hop]=key;
        const auto found=entry_aliases_.find(key);if(found==entry_aliases_.end())return {};
        key=found->second;
    }
    return {};
}
const Entry* Catalog::find_entry(const std::string& id) const{
    const auto canonical=resolve_entry_id(id);if(canonical.empty())return nullptr;
    for(const auto&entry:entries)if(entry.id==canonical)return &entry;
    return nullptr;
}
void Catalog::capture_english(){
    english_.clear();english_.reserve(entries.size());
    for(const auto&e:entries){
        EnglishText baseline{e.id,e.title,e.subtitle,e.summary,e.editorial_credit,e.body,e.story_headings,{}};
        for(const auto&f:e.editorial_features)baseline.features.push_back({f.id,f.title,f.summary,f.editorial_credit,f.body,f.story_headings});
        english_.push_back(std::move(baseline));
    }
    locale_="en";locale_error_.clear();
}
bool Catalog::set_locale(const std::string& root,const std::string& locale){
    // A text-only baseline keeps heavy media/provenance vectors single-owned.
    if(english_.size()!=entries.size())capture_english();
    for(size_t n=0;n<entries.size();++n){auto&e=entries[n];const auto&b=english_[n];
        if(e.id!=b.id){locale_error_="Collection order changed after localization initialization.";return false;}
        e.title=b.title;e.subtitle=b.subtitle;e.summary=b.summary;e.editorial_credit=b.editorial_credit;e.body=b.body;e.story_headings=b.story_headings;
        if(e.editorial_features.size()!=b.features.size()){locale_error_="Collection features changed after localization initialization.";return false;}
        for(size_t k=0;k<b.features.size();++k){auto&f=e.editorial_features[k];const auto&original=b.features[k];
            if(f.id!=original.id){locale_error_="Collection feature order changed after localization initialization.";return false;}
            f.title=original.title;f.summary=original.summary;f.editorial_credit=original.editorial_credit;
            f.body=original.body;f.story_headings=original.story_headings;
        }
    }
    locale_="en";locale_error_.clear();
    if(locale!="en"&&locale!="it"&&locale!="es"&&locale!="fr"&&locale!="de"){
        locale_error_="This collection language is not supported.";return false;
    }
    std::string bytes;
    if(!hui::save::read_file(root+"/content/locales/"+locale+".json",&bytes,kCatalogByteLimit)){
        if(locale=="en")return true;
        locale_error_="Localized collection text is unavailable; English is retained.";return false;
    }
    auto doc=Json::parse(bytes,nullptr,false);
    if(doc.is_discarded()||!doc.is_object()||!doc.contains("entries")||!doc["entries"].is_object()||
       (doc.contains("locale")&&str(doc,"locale")!=locale)||doc["entries"].size()>5000){
        locale_error_="The localized collection text is invalid; English is retained.";return false;
    }
    size_t rejected=0;
    const auto text=[&](const Json&row,const char*key,std::string&out,size_t limit){
        const auto it=row.find(key);if(it==row.end())return;
        if(!it->is_string()){++rejected;return;}const auto v=it->get<std::string>();
        if(v.size()>limit||v.find('\0')!=std::string::npos){++rejected;return;}out=v;
    };
    const auto paragraphs=[&](const Json&row,const char*key,std::vector<std::string>&out){
        const auto it=row.find(key);if(it==row.end())return;
        // Images and story cards refer to these indices; never shift or truncate them.
        if(!it->is_array()||it->size()!=out.size()||it->size()>1000){++rejected;return;}
        std::vector<std::string> values;values.reserve(it->size());
        for(const auto&v:*it){if(!v.is_string()){++rejected;return;}auto value=v.get<std::string>();
            if(value.size()>65536||value.find('\0')!=std::string::npos){++rejected;return;}values.push_back(std::move(value));}
        out=std::move(values);
    };
    for(auto&e:entries){const auto it=doc["entries"].find(e.id);
        if(it!=doc["entries"].end()){
            if(!it->is_object())++rejected;
            else{
                text(*it,"title",e.title,4096);text(*it,"subtitle",e.subtitle,8192);text(*it,"summary",e.summary,16384);
                text(*it,"editorial_credit",e.editorial_credit,16384);
                paragraphs(*it,"body",e.body);paragraphs(*it,"story_headings",e.story_headings);
            }
        }
        // A feature is independently authored and translated. Its identity and
        // paragraph positions never depend on whether its parent has an overlay.
        for(auto&f:e.editorial_features){const auto found=doc["entries"].find(f.id);if(found==doc["entries"].end())continue;
            if(!found->is_object()){++rejected;continue;}
            text(*found,"title",f.title,4096);text(*found,"summary",f.summary,16384);
            text(*found,"editorial_credit",f.editorial_credit,16384);
            paragraphs(*found,"body",f.body);paragraphs(*found,"story_headings",f.story_headings);
        }
    }
    label_award_editions(entries);
    locale_=locale;if(rejected)locale_error_=std::to_string(rejected)+" invalid localized fields kept their English text.";
    return true;
}
int chronology_day(const Entry&e){
    const int year=std::max(1,e.year),previous=year-1;
    const int month=e.month>=1&&e.month<=12?e.month:7;
    const bool leap=year%4==0&&(year%100!=0||year%400==0);
    constexpr int before[]={0,31,59,90,120,151,181,212,243,273,304,334};
    const int day=e.day>=1&&e.day<=31?e.day:(e.month>=1&&e.month<=12?15:1);
    return previous*365+previous/4-previous/100+previous/400+before[month-1]+(leap&&month>2?1:0)+day;
}
const Era* Catalog::era(const Entry&e)const{for(const auto&r:eras)if(r.id==e.era_id)return &r;return nullptr;}
std::vector<int> Catalog::on_this_day(int month,int day)const{
    std::vector<int> out;
    // A known historical date takes precedence over an inherited editorial
    // slot. An edition filed on17March must not override a verified20March
    // regional launch; undated scheduled discoveries remain available.
    for(size_t i=0;i<entries.size();++i){const auto&e=entries[i];if(e.calendar_only&&e.calendar_month==month&&e.calendar_day==day&&(e.precision!="day"||(e.month==month&&e.day==day)))out.push_back(int(i));}
    const auto same_event=[](const Entry&a,const Entry&b){
        if(a.id==b.id)return true;
        if(a.year!=b.year)return false;
        return a.linked_exhibit_id==b.id||b.linked_exhibit_id==a.id||(!a.linked_exhibit_id.empty()&&a.linked_exhibit_id==b.linked_exhibit_id)||(a.title==b.title);
    };
    for(size_t i=0;i<entries.size();++i){
        const auto&e=entries[i];if(e.precision!="day"||e.month!=month||e.day!=day)continue;
        bool duplicate=false;for(int n:out)if(same_event(entries[size_t(n)],e)){duplicate=true;break;}
        if(!duplicate)out.push_back(int(i));
    }
    return out;
}
}
