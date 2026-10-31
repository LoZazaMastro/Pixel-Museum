// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/general_credits.hpp"
#include "museum/feature_resources.hpp"
#include "museum/trophy_definitions.hpp"
#include "platform/playback_window.hpp"
#include "core/save_file.hpp"
#include "platform/ps5/system.hpp"
#include "yt/qr.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <cmath>
#include <ctime>
#include <cstdio>
#include <chrono>
#include <random>
#include <set>
#include <tuple>
#include <limits>
namespace museum {
using namespace hui;
using gfx::Color;using gfx::Rect;using gfx::Align;
namespace {
const Color paper=Color::rgb(0xf1efe7),ink=Color::rgb(0x202521),muted=Color::rgb(0x656a63),rule=Color::rgb(0x202521,.16f);
const Color orange=Color::rgb(0xb3492e);
bool matches(const Entry&e,int f){if(f==0)return true;if(f==1)return e.kind=="console"||e.kind=="hardware"||e.kind=="computer";if(f==2)return e.kind=="game";if(f==3)return e.kind=="person";return e.kind!="console"&&e.kind!="hardware"&&e.kind!="computer"&&e.kind!="game"&&e.kind!="person";}

}
Screen::~Screen(){shutdown();}
void Screen::apply_language(){
    story_credits_.clear();story_text_.clear();
    static constexpr const char*locales[]={"en","it","es","fr","de"};
    language_focus_=0;for(int n=0;n<5;++n)if(language_==locales[n])language_focus_=n;
    i18n::load(root_,language_);ui::text_resolver=&i18n::tr;ui::install_inline_controls();
    if(trophies_)trophies_->setDefinitions(make_trophy_definitions());
    video_.caption_language(language_);
    if(!catalog_.set_locale(root_,language_))sys::log("[Museum] locale %s: %s",language_.c_str(),catalog_.locale_error().c_str());
    if(!history_catalog_all_.entries.empty()&&!history_catalog_all_.set_locale(root_,language_))sys::log("[Museum] history locale %s: %s",language_.c_str(),history_catalog_all_.locale_error().c_str());
    rebuild_history_filter();
    if(ready_&&!history_focus_)prepare_story();
}
bool Screen::font(const std::string&p,gfx::Font&f,ui::FontRef&r){
    // The existing fallback can be 2048x4096 R8 plus bounded glyph/run
    // metadata. Keep this font-only allowance separate from save/JSON limits.
    std::string b;if(!save::read_file(p,&b,10u<<20)){sys::log("[Museum] font file unavailable or exceeds 10 MiB: %s",p.c_str());return false;}
    if(!f.load(b)){sys::log("[Museum] font rejected %s: %s",p.c_str(),f.error().c_str());return false;}
    r={&f,renderer_.batch().create_font_texture(f)};return true;
}
bool Screen::initialize_object_programs(){
    if(std::none_of(catalog_.entries.begin(),catalog_.entries.end(),[](const Entry& entry){return !entry.models.empty();})){
        prepared_programs_ready_=false;
        sys::log("[Museum] console photograph catalogue: object shaders not needed");
        return true;
    }
    prepared_programs_ready_=object_.init();
    if(!prepared_programs_ready_)sys::log("[Museum] active model programs unavailable: %s",object_.error().c_str());
    // Compile every scene's programs at startup, before navigation begins.
    // The original per-scene ownership/context lifetime remains unchanged.
    for(auto&prepared:prepared_objects_)if(!prepared.init()){
        sys::log("[Museum] neighbour model programs unavailable: %s; background model caching disabled",prepared.error().c_str());
        prepared_programs_ready_=false;
    }
    if(!prepared_programs_ready_){
        for(auto&prepared:prepared_objects_)prepared.release();
        prepared_paths_.fill({});
    }
    return prepared_programs_ready_;
}
bool Screen::init(const std::string&root,const std::string&data){
    auto checkpoint=std::chrono::steady_clock::now();
    const auto startup_phase=[&](const char*name){const auto now=std::chrono::steady_clock::now();sys::log("[Museum] interface init %s %.2fms",name,std::chrono::duration<double,std::milli>(now-checkpoint).count());checkpoint=now;};
    root_=root;data_=data;save::ensure_directory(data_);
    if(!renderer_.init())return false;
    startup_phase("renderer");
    const std::string f=root+"/assets/fonts/";
    if(!font(f+"inter-regular.huifont",regular_,fonts_.regular)||!font(f+"inter-semibold.huifont",bold_,fonts_.semibold)||!font(f+"montserrat-medium.huifont",display_,fonts_.display)||!font(f+"dejavu-sans-mono.huifont",mono_,fonts_.mono))return false;
    if(!font(f+"cjk-subset.huifont",cjk_,cjk_ref_))return false;
    if(!font(f+"unicode-fallback.huifont",unicode_,unicode_ref_))return false;
    for(auto*face:{&regular_,&bold_,&display_,&mono_}){face->clear_fallbacks();face->add_fallback(&unicode_,unicode_ref_.texture);face->add_fallback(&cjk_,cjk_ref_.texture);}
    fonts_.hand=fonts_.regular;fonts_.pixel=fonts_.mono;startup_phase("fonts");
    if(!catalog_.load(root+"/content/catalog.json")){sys::log("[Museum] %s",catalog_.error.c_str());return false;}
    startup_phase("catalogue");
    if(!history_catalog_.load(root+"/content/human-history.json"))sys::log("[Museum] history rail unavailable: %s",history_catalog_.error.c_str());
    history_catalog_all_=history_catalog_;
    if(culture_ambience_.load(root+"/content/culture-memories.json"))sys::log("[Museum] selective cultural recollections: %zu reviewed stops / streamed one-shot",culture_ambience_.cues().size());
    else sys::log("[Museum] cultural recollections unavailable: missing or invalid separate cue table");
    initial_exhibit_=catalog_.initial_id;
    refresh_today_date();
    load_settings();apply_language();language_selection_.snap(float(language_focus_));theme_selection_.snap(dark_theme_?0.f:1.f);theme_mix_.snap(dark_theme_?1.f:0.f);video_.volume(media_volume_);onboarding_fade_.snap(1);cache_.images_from_package(root);cache_.start(data+"/cache");video_.start(data,root);startup_phase("preferences and media workers");initialize_object_programs();startup_phase("object programs");
    auto theme=ui::default_theme();theme.page=paper;theme.text=ink;theme.text_muted=muted;theme.primary=ink;theme.focus=orange;theme.accent=orange;theme.surface=Color::rgb(0xe5e2d7);theme.surface_high=paper;
    viewer_.style.theme=theme;viewer_.style.radius=0;viewer_.style.frame=false;viewer_.style.focus_ring=false;viewer_.style.caption=false;viewer_.style.filmstrip=false;viewer_.style.counter=false;viewer_.style.readout=false;viewer_.style.arrows=false;viewer_.style.readout_size=22;viewer_.set_bounds({0,0,1920,1080});
    viewer_.picture=[this](ui::Canvas&canvas,const Rect&where,const ui::ViewerImage&,int index,float alpha){const auto*e=current();if(e&&index>=0&&index<int(e->images.size()))image(canvas.list,e->images[size_t(index)],where,true,alpha);};
    timeline_.snap(float(focus_));scroll_.snap(0);panel_.snap(0);focus_line_.snap(258);chapter_marker_.snap(0);
    history_focus_=false;detail_=false;rebuild();
    // A first visit begins at Nintendo's founding; later visits retain the
    // saved place. The culture route is entered only through navigation.
    const std::string arrival=onboarding_complete_?initial_exhibit_:"daily-09-23";
    for(size_t n=0;n<visible_.size();++n)if(catalog_.entries[size_t(visible_[n])].id==arrival){focus_=int(n);break;}
    timeline_.snap(float(focus_));
    changed();ready_=true;initialize_trophies();startup_phase("initial exhibit");sys::log("[Museum] composition GPU texture draws / display and entry snapshots / no framebuffer blit");return true;
}
void Screen::shutdown(){if(!ready_)return;trophy_notifications_.stop();if(trophy_pin_renderer_)trophy_pin_renderer_(TrophyView{},0,0,0,0,0,0);trophy_pin_open_=false;save_settings();video_.stop();cache_.stop();object_.release();for(auto&prepared:prepared_objects_)prepared.release();if(connection_qr_)glDeleteTextures(1,&connection_qr_);connection_qr_=0;video_.release_texture();cache_.release_textures();composed_.destroy();previous_entry_.destroy();wall_.destroy();renderer_.release();ready_=false;}
const Entry* Screen::current()const{if(history_focus_&&!history_catalog_.entries.empty())return &history_catalog_.entries[size_t(std::clamp(history_focus_index_,0,int(history_catalog_.entries.size())-1))];if(visible_.empty())return nullptr;return &catalog_.entries[size_t(visible_[size_t(std::clamp(focus_,0,int(visible_.size())-1))])];}
float Screen::selected_year()const{if(year_guide_&&!guide_experiences_&&!guide_trophies_&&year_focus_>=0&&year_focus_<int(years_.size()))return float(years_[size_t(year_focus_)]);if(chapters_&&chapter_focus_>=0&&chapter_focus_<int(catalog_.eras.size()))return float(catalog_.eras[size_t(chapter_focus_)].start_year);const auto*e=current();return e?float(e->year):1980;}
bool Screen::video_active()const{return media::suspend_ambient(playlist_active_,screening_,video_.state()==media::State::ready,video_.paused(),video_.ended());}
void Screen::load_settings(){reduced_=false;muted_=false;std::string b;if(!save::read_file(data_+"/preferences.json",&b))return;auto j=nlohmann::json::parse(b,nullptr,false);if(j.is_discarded()||!j.is_object())return;if(j.contains("language")&&j["language"].is_string()&&i18n::supported(j["language"].get<std::string>()))language_=j["language"].get<std::string>();if(j.contains("language_chosen")&&j["language_chosen"].is_boolean())language_chosen_=j["language_chosen"].get<bool>();language_choice_=!language_chosen_;if(j.contains("dark_theme")&&j["dark_theme"].is_boolean())dark_theme_=j["dark_theme"].get<bool>();if(j.contains("theme_chosen")&&j["theme_chosen"].is_boolean())theme_chosen_=j["theme_chosen"].get<bool>();theme_choice_=!theme_chosen_;if(j.contains("media_volume")&&j["media_volume"].is_number())media_volume_=std::clamp(j["media_volume"].get<float>(),0.f,1.f);if(j.contains("onboarding_complete")&&j["onboarding_complete"].is_boolean()){onboarding_complete_=j["onboarding_complete"].get<bool>();onboarding_=!onboarding_complete_||theme_choice_||language_choice_;}const auto levels=VolumePreferences::load(j);master_volume_=levels.master;sfx_volume_=levels.sfx;volume_=levels.music;culture_volume_=levels.culture;pad_volume_=levels.pad;culture_audio_on_pad_=levels.culture_on_pad;if(j.contains("exhibit")&&j["exhibit"].is_string()){const auto id=catalog_.resolve_entry_id(j["exhibit"].get<std::string>());if(!id.empty())initial_exhibit_=id;}}
void Screen::save_settings(){if(data_.empty())return;nlohmann::json j;j["onboarding_complete"]=onboarding_complete_;j["language"]=language_;j["language_chosen"]=language_chosen_;j["dark_theme"]=dark_theme_;j["theme_chosen"]=theme_chosen_;j["media_volume"]=media_volume_;VolumePreferences{master_volume_,sfx_volume_,volume_,culture_volume_,pad_volume_,culture_audio_on_pad_}.save(j);if(!visible_.empty())j["exhibit"]=catalog_.entries[size_t(visible_[size_t(focus_)])].id;const auto error=save::write_atomic(data_+"/preferences.json",j.dump());if(!error.empty())sys::log("[Museum] preferences: %s",error.c_str());dirty_=false;}
void Screen::rebuild(bool notify){
    visible_.clear();section_=0;anniversary_=false;
    for(size_t i=0;i<catalog_.entries.size();++i){
        const auto&e=catalog_.entries[i];
        // Calendar editions point at the same historical object in the main
        // collection. Only otherwise-unlinked stories need their own stop.
        if(e.calendar_only){bool linked=false;for(const auto&base:catalog_.entries)if(!base.calendar_only&&base.id==e.linked_exhibit_id&&base.year==e.year){linked=true;break;}if(linked)continue;}
        if(matches(e,filter_))visible_.push_back(int(i));
    }
    years_.clear();for(int n:visible_){const int year=catalog_.entries[size_t(n)].year;if(years_.empty()||years_.back()!=year)years_.push_back(year);}
    focus_=std::clamp(focus_,0,std::max(0,int(visible_.size())-1));timeline_.snap(float(focus_));if(ready_&&notify)changed();
}
void Screen::set_today_date(int year,int month,int day){
    if(year==date_year_&&month==date_month_&&day==date_day_)return;
    date_year_=year;date_month_=month;date_day_=day;today_cursor_.fill(-1);
}
void Screen::refresh_today_date(){
    const auto now=std::time(nullptr);
    if(const auto*date=std::localtime(&now))set_today_date(date->tm_year+1900,date->tm_mon+1,date->tm_mday);
}
std::string Screen::today_date_label()const{
    Entry date;date.year=date_year_;date.month=date_month_;date.day=date_day_;date.precision="day";
    auto label=date_label(date);
    static constexpr const char*months[]={"January","February","March","April","May","June","July","August","September","October","November","December"};
    if(date.month>=1&&date.month<=12){const std::string month(i18n::tr(months[date.month-1]));const auto position=label.find(month);if(position!=std::string::npos&&!month.empty()&&month[0]>='a'&&month[0]<='z')label[position]=char(month[0]-'a'+'A');}
    return label;
}
std::vector<int> Screen::today_entries(bool culture)const{
    const auto&catalog=culture?history_catalog_:catalog_;
    std::vector<int> result;
    for(int index:catalog.on_this_day(date_month_,date_day_)){
        const auto&entry=catalog.entries[size_t(index)];
        if(!entry.linked_exhibit_id.empty()){
            const auto id=catalog.resolve_entry_id(entry.linked_exhibit_id);
            for(size_t n=0;n<catalog.entries.size();++n){const auto&base=catalog.entries[n];
                if(!base.calendar_only&&base.id==id&&base.year==entry.year){index=int(n);break;}
            }
        }
        if(std::find(result.begin(),result.end(),index)==result.end())result.push_back(index);
    }
    return result;
}
void Screen::change_filter(int delta,ui::Feedback&f){
    const auto*entry=current();const std::string id=entry?entry->id:std::string{};
    const int day=entry?chronology_day(*entry):0;
    if(history_focus_){
        culture_filter_=(culture_filter_+delta%9+9)%9;rebuild_history_filter();
        scroll_.snap(0);scroll_max_=0;fade_=0;image_index_=current()?current()->preferred_image:0;warm_history();
        filter_notice_time_=1.35f;year_notice_time_=0;
        f.play(audio::Cue::tab,1,delta<0?-.45f:.45f);return;
    }
    filter_=(filter_+delta+5)%5;rebuild(false);
    int nearest=0;
    for(size_t n=0;n<visible_.size();++n){const auto&candidate=catalog_.entries[size_t(visible_[n])];
        if(candidate.id==id){nearest=int(n);break;}
        if(n==0||std::abs(chronology_day(candidate)-day)<std::abs(chronology_day(catalog_.entries[size_t(visible_[size_t(nearest)])])-day))nearest=int(n);
    }
    focus_=nearest;timeline_.snap(float(focus_));changed();
    filter_notice_time_=1.35f;year_notice_time_=0;
    f.play(audio::Cue::tab,1,delta<0?-.45f:.45f);
}
void Screen::jump_today(ui::Feedback&f){
    const auto candidates=today_entries(history_focus_);
    if(candidates.empty()){f.play(audio::Cue::error,1,0,.25f);return;}
    auto&cursor=today_cursor_[history_focus_?1:0];cursor=(cursor+1)%int(candidates.size());
    const int target=candidates[size_t(cursor)];
    if(history_focus_){
        ui::Feedback discarded;move_history(target-history_focus_index_,discarded);
    }else{
        detail_=gallery_=screening_=object_inspect_=false;filter_=0;rebuild(false);
        for(size_t n=0;n<visible_.size();++n)if(visible_[n]==target){focus_=int(n);break;}
        changed();
    }
    if(trophies_&&current())trophies_->todayVisit(current()->id);
    f.play(audio::Cue::tab);
}
void Screen::open_year_guide(){
    years_.clear();
    if(history_focus_){for(const auto&e:history_catalog_.entries)if(years_.empty()||years_.back()!=e.year)years_.push_back(e.year);}
    else{for(int id:visible_){const int year=catalog_.entries[size_t(id)].year;if(years_.empty()||years_.back()!=year)years_.push_back(year);}}
    year_guide_=true;year_focus_=0;guide_experiences_=guide_trophies_=false;trophy_focus_time_=0;trophy_expanded_=false;
    if(const auto*e=current())for(size_t n=0;n<years_.size();++n)if(years_[n]<=e->year)year_focus_=int(n);
    year_position_.snap(float(year_focus_));
}
void Screen::retain_object(){
    if(!prepared_programs_ready_){object_.release_render_target();return;}
    if(!object_.ready()||model_path_.empty())return;
    // Keep the active framebuffer when a large model cannot enter the
    // neighbour cache. cancel()/request() retire its artwork separately, so
    // the next selected console can reuse this same full-resolution target.
    const auto memory=object_.timings();
    const auto target=static_cast<std::size_t>(memory.render_width)*static_cast<std::size_t>(memory.render_height)*12;
    const auto model_bytes=memory.estimated_gpu_bytes>target?memory.estimated_gpu_bytes-target:0;
    if(model_bytes>(352u<<20))return;
    // Small cached neighbours retain geometry/artwork, never an unused FBO.
    object_.release_render_target();
    size_t slot=0;
    if(prepared_paths_[0].empty())slot=0;else if(prepared_paths_[1].empty())slot=1;else slot=prepared_use_[0]<=prepared_use_[1]?0:1;
    object_.swap(prepared_objects_[slot]);prepared_paths_[slot]=model_path_;prepared_use_[slot]=++prepared_clock_;
}
bool Screen::warm_objects(){
    if(!prepared_programs_ready_)return true;
    // Active and prepared models share one residency budget. Stop background
    // work first rather than making a new neighbour displace the exhibit.
    const auto resident=[&]{std::size_t bytes=object_.timings().estimated_gpu_bytes;for(const auto&model:prepared_objects_)bytes+=model.timings().estimated_gpu_bytes;return bytes;};
    constexpr std::size_t budget=512u<<20,reserve=160u<<20;
    const bool active_pending=object_.loading()||(!model_path_.empty()&&!object_.ready());
    const auto active=object_.timings();
    const auto active_reservation=active_pending?std::max(reserve,active.planned_gpu_bytes):active.estimated_gpu_bytes;
    const auto ceiling=active_reservation<budget?budget-active_reservation:0;
    const auto cached_resident=[&]{std::size_t bytes=0;for(const auto&model:prepared_objects_)bytes+=model.timings().estimated_gpu_bytes;return bytes;};
    auto projected=cached_resident();
    // A queued neighbour must never contend with a selected model for its
    // next atlas. Prefer keeping the most recently visited ready neighbour.
    std::array<size_t,2> oldest={0,1};
    if(prepared_use_[oldest[0]]>prepared_use_[oldest[1]])std::swap(oldest[0],oldest[1]);
    for(const auto n:oldest){
        if(prepared_paths_[n].empty())continue;
        if((active_pending&&prepared_objects_[n].loading())||projected>ceiling){
            const auto t=prepared_objects_[n].timings();
            const auto target=static_cast<std::size_t>(t.render_width)*static_cast<std::size_t>(t.render_height)*12;
            const auto released=t.estimated_gpu_bytes>target?t.estimated_gpu_bytes-target:0;
            projected=released>projected?0:projected-released;
            prepared_objects_[n].cancel();prepared_paths_[n].clear();
        }
    }
    for(size_t n=0;n<prepared_objects_.size();++n){
        // cancel() defers destruction to protect frame time. These scenes
        // still require maintenance while the active scene is loading.
        if(prepared_paths_[n].empty()||(!prepared_objects_[n].loading()&&prepared_objects_[n].timings().pending_gpu_deletes))prepared_objects_[n].upload_pending();
    }
    if(active_pending){
        if(cached_resident()>ceiling)for(const auto&prepared:prepared_objects_)if(prepared.timings().pending_gpu_deletes)return false;
        return true;
    }
    for(size_t n=0;n<prepared_objects_.size();++n){
        if(prepared_paths_[n].empty())continue;
        const bool uploading=prepared_objects_[n].loading();
        const auto planned=prepared_objects_[n].timings().planned_gpu_bytes;
        if(uploading&&planned>ceiling){
            if(std::find(large_model_paths_.begin(),large_model_paths_.end(),prepared_paths_[n])==large_model_paths_.end())large_model_paths_.push_back(prepared_paths_[n]);
            prepared_objects_[n].cancel();prepared_paths_[n].clear();continue;
        }
        prepared_objects_[n].upload_pending();
        if(uploading)return true; // one background transfer slice per display frame
    }
    if(model_wait_<.5f||gallery_||screening_||resident()+reserve>budget)return true;
    std::vector<const Entry*> neighbours;
    for(int distance=1;distance<=32&&neighbours.size()<2;++distance)for(int direction:{1,-1}){
        const int index=focus_+distance*direction;if(index<0||index>=int(visible_.size()))continue;
        const auto&e=catalog_.entries[size_t(visible_[size_t(index)])];if(e.models.empty()||e.models[0].asset_file.empty())continue;
        const auto path=root_+"/"+e.models[0].asset_file;if(path==model_path_||std::find(large_model_paths_.begin(),large_model_paths_.end(),path)!=large_model_paths_.end())continue;neighbours.push_back(&e);if(neighbours.size()==2)break;
    }
    for(const auto*e:neighbours){const auto path=root_+"/"+e->models[0].asset_file;
        if(std::find(prepared_paths_.begin(),prepared_paths_.end(),path)!=prepared_paths_.end())continue;
        size_t slot=prepared_paths_[0].empty()?0:prepared_paths_[1].empty()?1:prepared_use_[0]<=prepared_use_[1]?0:1;
        if(!prepared_paths_[slot].empty()){
            bool needed=false;for(const auto*other:neighbours)if(root_+"/"+other->models[0].asset_file==prepared_paths_[slot])needed=true;
            if(needed)return true;
        }
        prepared_objects_[slot].request(path,e->models[0].include_groups);prepared_paths_[slot]=path;prepared_use_[slot]=++prepared_clock_;return true;
    }
    return true;
}
void Screen::changed(bool timeline_navigation){
    if(!history_focus_&&current())gaming_year_selection_[current()->year]=current()->id;
    if(!history_focus_&&!history_catalog_.entries.empty()&&current()){
        const int day=chronology_day(*current());int nearest=0;
        for(size_t n=0;n<history_catalog_.entries.size();++n)if(std::abs(chronology_day(history_catalog_.entries[n])-day)<std::abs(chronology_day(history_catalog_.entries[size_t(nearest)])-day))nearest=int(n);
        history_focus_index_=nearest;warm_history();
    }
    history_transition_=false;playlist_closing_=false;retain_object();stop_playlist();if(!culture_ambience_.owns_player())video_.close();screening_=false;fullscreen_=false;if(model_requested_||object_.loading()||object_.ready())object_.cancel();if(!timeline_navigation)snapshot_current();else entry_snapshot_=false;fade_=timeline_navigation?1.f:0.f;story_actions_.clear();story_sources_=false;seek_sources_=false;sources_open_.snap(0);scroll_.snap(0);scroll_max_=0;tab_=0;image_index_=0;video_index_=0;dirty_=true;save_delay_=1.5f;model_url_.clear();model_path_.clear();model_requested_=false;model_wait_=0;object_render_clock_=0;object_frame_ms_=0;object_texture_=0;object_alpha_=0;object_angle_=0;object_tilt_offset_=0;object_zoom_=2;object_manual_=false;prepare_story();const auto*e=current();if(e){image_index_=e->preferred_image;sys::log("[Museum] exhibit %s (%d), layout %s",e->id.c_str(),e->year,e->layout.c_str());if(e->models.empty()&&!e->images.empty())cache_.request(image_url(e->images[e->preferred_image]));if(!e->models.empty()){object_angle_=e->models[0].initial_angle;object_zoom_=e->id=="xbox-series-x"?1.3f:(e->id=="playstation-5"||e->id=="game-boy")?1.6f:2.f;if(!e->models[0].asset_file.empty()){model_path_=root_+"/"+e->models[0].asset_file;
            for(size_t n=0;n<prepared_paths_.size();++n)if(prepared_paths_[n]==model_path_){object_.swap(prepared_objects_[n]);prepared_paths_[n].clear();model_requested_=true;prepared_use_[n]=++prepared_clock_;break;}
            /* New GLB requests are deferred until focus settles. */}else{model_url_=e->models[0].url;}}}
    std::vector<std::string> nearby;nearby_covers_.clear();
    const auto collect=[&](int index,bool cover){if(index<0||index>=int(visible_.size()))return;const auto&entry=catalog_.entries[size_t(visible_[size_t(index)])];if(cover){if(!entry.images.empty())nearby.push_back(entry.images[size_t(entry.preferred_image)].url);}else for(const auto&photo:entry.images)nearby.push_back(photo.url);};
    collect(focus_,true);for(int distance=1;distance<=4;++distance){const auto before=nearby.size();collect(focus_+distance,true);collect(focus_-distance,true);nearby_covers_.insert(nearby_covers_.end(),nearby.begin()+before,nearby.end());}
    collect(focus_,false);for(int distance=1;distance<=4;++distance){collect(focus_+distance,false);collect(focus_-distance,false);}cache_.prefetch_images(nearby);
}

void Screen::move(int delta,ui::Feedback&f){if(visible_.empty())return;const int next=std::clamp(focus_+delta,0,int(visible_.size())-1);if(next==focus_){f.play(audio::Cue::error,1,0,.2f);return;}focus_=next;changed(!detail_);f.timeline_step(delta);}
void Screen::chapter(int delta,ui::Feedback&f){const auto*e=current();if(!e)return;const int from=e->year,decade=from/10;int next=focus_;for(int i=focus_+delta;i>=0&&i<int(visible_.size());i+=delta){next=i;if(catalog_.entries[size_t(visible_[size_t(i)])].year/10!=decade)break;}move(next-focus_,f);if(current())show_year_notice(from,current()->year);}
void Screen::select(const std::string&id){history_focus_=false;section_=0;filter_=culture_filter_=0;rebuild_history_filter();rebuild();for(size_t i=0;i<visible_.size();++i)if(catalog_.entries[size_t(visible_[i])].id==id){focus_=int(i);timeline_.snap(float(i));changed();break;}}
void Screen::preview(int mode){
    chapters_=mode==6;detail_=mode==1||mode==3;gallery_=mode==2;screening_=mode==3;settings_=mode==4;credits_=mode==5;
    story_open_.snap(detail_?1.f:0.f);gallery_open_.snap(gallery_?1.f:0.f);screening_open_.snap(screening_?1.f:0.f);object_open_.snap(0);video_full_.snap(0);media_hints_.snap(1);
    panel_.snap(settings_||credits_?1.f:0.f);if(gallery_){prepare_gallery();viewer_.set_mode(ui::ZoomMode::fit,true);}
}
void Screen::prepare_gallery(bool reset){const auto*e=current();if(!e)return;std::vector<ui::ViewerImage> images;for(size_t n=0;n<e->images.size();++n){const auto&i=e->images[n];const auto a=int(n)==image_index_?cache_.request(image_url(i)):cache_.get(image_url(i));ui::ViewerImage v;v.title=i.title;v.caption.clear();v.texture=a.texture;v.aspect=a.width&&a.height?float(a.width)/a.height:1.f;v.pixel_width=float(a.width);images.push_back(v);}if(reset){viewer_.set_images(std::move(images));viewer_.set_index(image_index_);}else viewer_.refresh_images(std::move(images));}
void Screen::handle(const InputFrame&i,ui::Feedback&f){
    const bool rail_input=!onboarding_&&!settings_&&!credits_&&!year_guide_&&!chapters_&&!detail_&&!gallery_&&!screening_&&!object_inspect_&&!experience_active_&&!workshop_active_&&!image_dialog_&&!connection_panel_&&!(history_transition_&&fade_<1)&&!(i.pressed&~(action_bit(Action::left)|action_bit(Action::right)));
    auto&rail_position=history_focus_?history_position_:timeline_;
    timeline_motion_.input(i,dt_,history_focus_?history_focus_index_:focus_,rail_input,rail_position);
    std::array<bool,2> filter_press{};
    for(size_t n=0;n<2;++n){
        const auto action=n?Action::jump_next:Action::jump_prev;
        const float value=n?i.trigger_r:i.trigger_l;
        auto&down=filter_trigger_down_[n];
        culture_input_active_=!i.focus_lost&&i.connected;
    if(i.focus_lost||!i.connected){down=true;continue;}
        // Physical buttons and analogue travel share one hysteresis latch.
        const bool digital=i.is_pressed(action)&&value<=.001f;
        if(!down&&(value>=.55f||digital)){filter_press[n]=true;down=true;}
        else if(value<=.20f&&!i.is_held(action)&&!i.is_pressed(action))down=false;
    }
    const bool previous_history=history_focus_,previous_gallery=gallery_,previous_experience=experience_active_;
    const bool previous_onboarding=onboarding_;
    const int previous_story_focus=story_focus_;
    const auto previous_cues=f.cues.size();
    const auto photo_motion=viewer_.take_motion_feedback();
    const float previous_zoom=object_zoom_,previous_photo_zoom=viewer_.zoom(),previous_angle=object_angle_,previous_tilt=object_tilt_offset_;
    const float previous_scroll=scroll_.target,previous_credits=credits_scroll_.target,previous_description=experience_description_scroll_,previous_pan_x=viewer_.pan_x(),previous_pan_y=viewer_.pan_y(),previous_volume=media_volume_;
    // Every early return shares this feedback contract. Continuous gestures
    // produce spaced textures instead of frame-rate-dependent motor commands.
    const auto finish_feedback=[&]{
        if(i.focus_lost||!i.connected||experience_input_paused_)return;
        // Studies emit feedback only for accepted state changes, never raw buttons.
        if(previous_experience||experience_active_)return;
        // The pin viewer owns its accepted-motion pulses. A left-stick nav
        // repeat at its pan limit must not also trigger a menu-focus pulse.
        if(year_guide_&&guide_trophies_&&trophy_pin_open_)return;
        if(previous_onboarding&&f.cues.size()>previous_cues){
            const auto cue=f.cues.back().cue;
            const auto voice=cue==audio::Cue::focus?audio::SpeakerCue::ui_focus:
                cue==audio::Cue::back?audio::SpeakerCue::ui_back:audio::SpeakerCue::ui_confirm;
            f.speak(voice,1.f+float(std::max(0,onboarding_step_))*.035f,.085f);
        }
        using audio::Tactile;
        if(previous_history!=history_focus_){f.timeline_route(history_focus_);return;}
        // Moving to a new card resets the reading position. That reset is
        // not a scroll gesture and must not replace its directional detent.
        if(detail_&&previous_story_focus!=story_focus_)return;
        Tactile texture=Tactile::focus;float direction=0;bool gesture=false;
        if(previous_zoom!=object_zoom_||previous_photo_zoom!=viewer_.zoom()){
            const float delta=object_zoom_-previous_zoom+viewer_.zoom()-previous_photo_zoom;
            texture=delta>0?Tactile::zoom_in:Tactile::zoom_out;direction=delta>0?1.f:-1.f;gesture=true;
        }else if(previous_angle!=object_angle_||previous_tilt!=object_tilt_offset_){texture=Tactile::rotate;direction=i.stick2_x;gesture=true;}
        else if(previous_scroll!=scroll_.target||previous_credits!=credits_scroll_.target||previous_description!=experience_description_scroll_){texture=Tactile::scroll;direction=i.stick2_y;gesture=true;}
        else if(previous_pan_x!=viewer_.pan_x()||previous_pan_y!=viewer_.pan_y()){texture=Tactile::touch;direction=i.stick2_x;gesture=true;}
        else if(previous_volume!=media_volume_){texture=media_volume_>previous_volume?Tactile::zoom_in:Tactile::zoom_out;gesture=true;}
        else if(previous_gallery&&gallery_&&photo_motion.image==viewer_.index()){
            if(photo_motion.zoom!=0){texture=photo_motion.zoom>0?Tactile::zoom_in:Tactile::zoom_out;direction=photo_motion.zoom>0?1.f:-1.f;gesture=true;}
            else if(photo_motion.pan_x!=0||photo_motion.pan_y!=0){texture=Tactile::touch;direction=photo_motion.pan_x>0?1.f:photo_motion.pan_x<0?-1.f:0.f;gesture=true;}
        }
        if(gesture&&tactile_repeat_<=0){f.tactile.clear();f.feel(texture,.15f,.035f,direction);tactile_repeat_=.065f;}
        if(f.tactile.empty()){
            // Silent UI actions still have a tactile identity. Confirming a
            // media action, backing out and moving focus must not all feel like
            // the same faint navigation tick.
            if(i.is_pressed(Action::back))f.feel(Tactile::back,.22f,.065f);
            else if(i.is_pressed(Action::confirm)||i.is_pressed(Action::menu)||i.is_pressed(Action::west)||i.is_pressed(Action::north)||i.is_pressed(Action::touch)||i.is_pressed(Action::r3))f.feel(Tactile::confirm,.22f,.055f);
            else if(i.pressed||i.nav!=Direction::none){
                const float pan=i.nav==Direction::left?-.45f:i.nav==Direction::right?.45f:0.f;
                f.feel(Tactile::focus,.12f,.022f,pan);
            }
        }
    };
    struct FinishFeedback { const decltype(finish_feedback)&run;~FinishFeedback(){run();} } finish{finish_feedback};
    if(i.focus_lost||!i.connected){
        year_notice_tick_=false;
        trophy_pin_haptic_wait_=0;
        experience_input_paused_=true;experience_rearm_=experience_active_;
        experience_audio_.paused(true);motion_calibrated_=false;
        if(study_){auto blocked=i;blocked.focus_lost=true;blocked.pressed=blocked.released=blocked.held=0;blocked.nav=Direction::none;ui::Feedback discarded;study_->handle(blocked,discarded);study_->take_note();}
        return;
    }
    if(year_notice_tick_){
        year_notice_tick_=false;
        if(!reduced_&&!onboarding_&&!experience_active_)f.feel(audio::Tactile::focus,.52f,.034f,0.f);
    }
    if(experience_active_&&experience_rearm_){
        const auto at_rest=[](float value){return std::isfinite(value)&&std::abs(value)<.08f;};
        const bool neutral=!i.pressed&&!i.held&&i.nav==Direction::none&&at_rest(i.stick_x)&&at_rest(i.stick_y)&&at_rest(i.stick2_x)&&at_rest(i.stick2_y)&&at_rest(i.trigger_l)&&at_rest(i.trigger_r)&&(!i.touch.available||!i.touch.count);
        if(!neutral)return;
        experience_rearm_=false;experience_input_paused_=false;experience_audio_.paused(experience_paused_);
        // This sample only releases the focus latch. Drain any feedback from
        // the final pre-suspension physics tick instead of replaying it as a
        // new touch/impact on reconnect. No new user action exists here.
        if(study_){ui::Feedback discarded;study_->handle(i,discarded);study_->take_note();}
        return;
    }
    experience_rearm_=false;experience_input_paused_=false;experience_audio_.paused(experience_paused_);
    if(onboarding_){
        if(onboarding_leaving_)return;
        if(language_choice_){
            const int before=language_focus_;
            if(i.nav==Direction::down||i.nav==Direction::right)language_focus_=std::min(4,language_focus_+1);
            if(i.nav==Direction::up||i.nav==Direction::left)language_focus_=std::max(0,language_focus_-1);
            if(before!=language_focus_)f.play(audio::Cue::focus);
            if(i.is_pressed(Action::confirm)){
                static constexpr const char*locales[]={"en","it","es","fr","de"};
                language_=locales[language_focus_];language_chosen_=true;language_choice_=false;theme_choice_=true;theme_confirming_=false;theme_confirm_progress_=0;apply_language();dirty_=true;save_delay_=0;f.play(audio::Cue::select);
            }
            return;
        }
        if(theme_choice_){
            if(theme_confirming_)return;
            if(i.is_pressed(Action::back)){language_choice_=true;f.play(audio::Cue::back);return;}
            const bool before=dark_theme_;
            if(i.nav==Direction::left)dark_theme_=true;
            if(i.nav==Direction::right)dark_theme_=false;
            if(before!=dark_theme_){dirty_=true;save_delay_=1;f.play(audio::Cue::focus);}
            if(i.is_pressed(Action::confirm)){theme_confirming_=true;theme_confirm_progress_=reduced_?1.f:0.f;theme_chosen_=true;dirty_=true;save_delay_=0;f.play(audio::Cue::select);if(reduced_){theme_choice_=false;theme_confirming_=false;onboarding_step_=0;onboarding_position_.snap(0);}}
            return;
        }
        if(onboarding_step_==onboarding_cards_){if(i.is_pressed(Action::back)){--onboarding_step_;f.play(audio::Cue::back);}else if(i.is_pressed(Action::menu)){onboarding_leaving_=true;f.play(audio::Cue::select);}return;}
        if(onboarding_step_==onboarding_cards_-1){
            const auto c=video_.connection();
            if(i.is_pressed(Action::west)){if(c.saved||c.signed_in){video_.cancel_sign_in();video_.restore_connection();f.play(audio::Cue::select);}else{video_.cancel_sign_in();++onboarding_step_;f.play(audio::Cue::select);}return;}
            if(i.is_pressed(Action::back)){video_.cancel_sign_in();--onboarding_step_;f.play(audio::Cue::back);return;}
            if(i.is_pressed(Action::confirm)){
                if(c.saved||c.signed_in){video_.cancel_sign_in();++onboarding_step_;f.play(audio::Cue::select);}
                else if(c.state!=media::State::loading&&c.user_code.empty()){video_.request_sign_in();f.play(audio::Cue::select);}
            }
            return;
        }
        if(i.is_pressed(Action::back)){if(onboarding_step_>0)--onboarding_step_;else theme_choice_=true;f.play(audio::Cue::back);return;}
        if(i.is_pressed(Action::confirm)){++onboarding_step_;f.play(audio::Cue::select);}
        if(i.is_pressed(Action::west)){onboarding_step_=onboarding_cards_-1;f.play(audio::Cue::select);}
        return;
    }
    if(boot_time_<4.8f){if(i.is_pressed(Action::confirm)){boot_time_=4.8f;boot_note_=13;}return;}
    const bool active=i.pressed||i.nav!=Direction::none||std::abs(i.stick_x)>.1f||std::abs(i.stick_y)>.1f||std::abs(i.stick2_x)>.1f||std::abs(i.stick2_y)>.1f||i.trigger_l>.04f||i.trigger_r>.04f; if(active)idle_=0;
    if(!experience_active_&&i.is_held(Action::menu)&&i.is_pressed(Action::back)){quit_=true;return;}
    if(connection_panel_){if(i.is_pressed(Action::back)){connection_panel_=false;video_.cancel_sign_in();f.play(audio::Cue::back);return;}const auto c=video_.connection();if(i.is_pressed(Action::confirm)&&!c.signed_in){if(c.saved)video_.restore_connection();else if(c.user_code.empty())video_.request_sign_in();}if(i.is_pressed(Action::west)&&c.signed_in)video_.sign_out();return;}
    if(handle_experience(i,f))return;
    if(handle_search(i,f))return;
    if(year_guide_){
        if(guide_trophies_&&trophy_pin_open_){
            if(i.is_pressed(Action::back)||i.is_pressed(Action::north)){trophy_pin_open_=false;trophy_focus_time_=0;if(trophy_pin_renderer_)trophy_pin_renderer_(TrophyView{},0,0,0,0,0,0);f.play(audio::Cue::back);return;}
            const float old_yaw=trophy_pin_yaw_,old_pitch=trophy_pin_pitch_,old_zoom=trophy_pin_zoom_,old_pan=trophy_pin_pan_y_;
            if(std::abs(i.stick2_x)>.08f)trophy_pin_yaw_+=i.stick2_x*dt_*2.3f;
            if(std::abs(i.stick2_y)>.08f)trophy_pin_pitch_=std::clamp(trophy_pin_pitch_+i.stick2_y*dt_*1.6f,-1.1f,1.1f);
            trophy_pin_zoom_=std::clamp(trophy_pin_zoom_+(i.trigger_r-i.trigger_l)*dt_*1.8f,.65f,2.6f);
            if(std::abs(i.stick_y)>.08f)trophy_pin_pan_y_=std::clamp(trophy_pin_pan_y_-i.stick_y*dt_*1.1f,-.65f,.65f);
            const float translation=std::abs(trophy_pin_pan_y_-old_pan);
            const float rotation=std::hypot(trophy_pin_yaw_-old_yaw,trophy_pin_pitch_-old_pitch);
            const float zoom=std::abs(trophy_pin_zoom_-old_zoom);
            // Feel accepted movement only: no pulse at a zoom/pitch limit,
            // at rest, or from the automatic onboarding illustration.
            trophy_pin_haptic_wait_=std::max(0.f,trophy_pin_haptic_wait_-dt_);
            if(rotation>.00001f||zoom>.00001f||translation>.00001f){
                if(trophy_pin_haptic_wait_<=0){
                    const float pan=rotation>.00001f?std::clamp((trophy_pin_yaw_-old_yaw)/(rotation+.00001f),-1.f,1.f):0.f;
                    const auto texture=zoom>.00001f?(trophy_pin_zoom_>old_zoom?hui::audio::Tactile::zoom_in:hui::audio::Tactile::zoom_out):translation>.00001f?hui::audio::Tactile::scroll:hui::audio::Tactile::rotate;
                    f.feel(texture,zoom>.00001f?.10f:.075f,.025f,pan);
                    trophy_pin_haptic_wait_=.075f;
                }
            }else trophy_pin_haptic_wait_=0;
            return;
        }
        if(i.is_pressed(Action::touch)){open_search(f);return;}
        if(i.is_pressed(Action::west)){
            if(guide_trophies_)guide_trophies_=false;
            else if(guide_experiences_){guide_experiences_=false;guide_trophies_=true;}
            else guide_experiences_=true;
            trophy_focus_time_=0;trophy_expanded_=false;trophy_pin_open_=false;
            f.play(audio::Cue::tab);return;
        }
        if(guide_trophies_){
            if(i.is_pressed(Action::back)||i.is_pressed(Action::touch)){
                if(trophy_expanded_&&i.is_pressed(Action::back)){trophy_expanded_=false;f.play(audio::Cue::back);return;}
                year_guide_=false;trophy_focus_time_=0;f.play(audio::Cue::back);return;
            }
            const auto all=trophies_?trophies_->views(true):std::vector<TrophyView>{};
            if(all.empty())return;
            const int before=trophy_focus_;
            if(i.nav==Direction::down)trophy_focus_=std::min(int(all.size())-1,trophy_focus_+1);
            if(i.nav==Direction::up)trophy_focus_=std::max(0,trophy_focus_-1);
            trophy_focus_=std::clamp(trophy_focus_,0,int(all.size())-1);
            if(before!=trophy_focus_){trophy_focus_time_=0;trophy_expanded_=false;f.play(audio::Cue::focus,1,0,.4f);}
            if(i.is_pressed(Action::confirm)){
                const auto&selected=all[size_t(trophy_focus_)];
                if(selected.secret)trophy_expanded_=!trophy_expanded_;
                f.play(audio::Cue::select);
            }
            if(i.is_pressed(Action::north)&&all[size_t(trophy_focus_)].unlocked){trophy_pin_open_=true;trophy_pin_yaw_=trophy_pin_pitch_=trophy_pin_pan_y_=0;trophy_pin_zoom_=1;trophy_pin_haptic_wait_=0;if(trophies_)trophies_->experienceResult("museum",{{"first_pin_3d",1}});f.play(audio::Cue::select);}
            return;
        }
        if(!guide_experiences_&&i.is_pressed(Action::north)){if(active_filter())change_filter(-active_filter(),f);else jump_today(f);open_year_guide();return;}
        if(guide_experiences_){
            if(i.is_pressed(Action::back)||i.is_pressed(Action::touch)){year_guide_=false;f.play(audio::Cue::back);return;}
            const auto& studies=study_catalog();if(studies.empty())return;
            const int before=experience_focus_;
            if(i.nav==Direction::down)experience_focus_=std::min(int(studies.size())-1,experience_focus_+1);
            if(i.nav==Direction::up)experience_focus_=std::max(0,experience_focus_-1);
            if(before!=experience_focus_){experience_description_scroll_=0;experience_description_clock_=0;f.play(audio::Cue::focus,1,0,.4f);}
            if(std::abs(i.stick2_y)>.08f){experience_description_scroll_=std::clamp(experience_description_scroll_+i.stick2_y*dt_*360,0.f,experience_description_max_);experience_description_clock_=-6;}
            if(i.is_pressed(Action::confirm)){open_experience(experience_focus_,{64,350,548,370});f.play(audio::Cue::select);}
            if(i.is_pressed(Action::north)){const auto id=studies[size_t(experience_focus_)].entry_id;year_guide_=false;select(id);detail_=true;f.play(audio::Cue::select);}
            return;
        }
        if(i.is_pressed(Action::back)||i.is_pressed(Action::touch)){year_guide_=false;f.play(audio::Cue::back);return;}
        if(years_.empty())return;
        const int before=year_focus_;
        if(i.nav==Direction::down||i.nav==Direction::right)year_focus_=std::min(int(years_.size())-1,year_focus_+1);
        if(i.nav==Direction::up||i.nav==Direction::left)year_focus_=std::max(0,year_focus_-1);
        if(i.is_pressed(Action::page_next)||i.is_pressed(Action::page_prev)){
            const int from=years_[size_t(year_focus_)];
            const int direction=i.is_pressed(Action::page_next)?1:-1,decade=from/10;
            for(int n=year_focus_+direction;n>=0&&n<int(years_.size());n+=direction){year_focus_=n;if(years_[size_t(n)]/10!=decade)break;}
            show_year_notice(from,years_[size_t(year_focus_)]);
        }
        if(year_focus_!=before)f.play(audio::Cue::focus,1,0,.4f);
        if(i.is_pressed(Action::confirm)){
            const int year=years_[size_t(year_focus_)];year_guide_=false;detail_=false;
            if(history_focus_){
                for(size_t n=0;n<history_catalog_.entries.size();++n)if(history_catalog_.entries[n].year==year){move_history(int(n)-history_focus_index_,f);break;}
            }else for(size_t n=0;n<visible_.size();++n)if(catalog_.entries[size_t(visible_[n])].year==year){focus_=int(n);changed();break;}
            f.play(audio::Cue::select);
        }
        return;
    }
    if(year_panel_.value>.001f)return;
    if(credits_){if(i.is_pressed(Action::back)){credits_=false;settings_=true;f.play(audio::Cue::back);}else if(std::abs(i.stick2_y)>.08f)credits_scroll_.target=std::clamp(credits_scroll_.target+i.stick2_y*dt_*720,0.f,credits_scroll_max_);return;}

    if(settings_){
        if(volumes_open_){
            if(i.is_pressed(Action::back)||i.is_pressed(Action::menu)){
                volumes_open_=false;setting_=2;
                if(i.is_pressed(Action::menu))settings_=false;
                if(dirty_)save_settings();f.play(audio::Cue::back);return;
            }
            const int before=volume_focus_;
            if(i.nav==Direction::down)volume_focus_=std::min(5,volume_focus_+1);
            if(i.nav==Direction::up)volume_focus_=std::max(0,volume_focus_-1);
            if(before!=volume_focus_)f.play(audio::Cue::focus,1,0,.4f);
            if(volume_focus_==5){
                bool next=culture_audio_on_pad_;
                if(i.is_pressed(Action::confirm))next=!next;
                if(i.nav==Direction::left)next=false;
                if(i.nav==Direction::right)next=true;
                if(next!=culture_audio_on_pad_){culture_audio_on_pad_=next;dirty_=true;save_delay_=1.f;f.play(audio::Cue::toggle);}
                return;
            }
            if(i.nav==Direction::left||i.nav==Direction::right){
                const std::array<float*,5> values={&master_volume_,&sfx_volume_,&volume_,&culture_volume_,&pad_volume_};
                auto&value=*values[size_t(std::clamp(volume_focus_,0,4))];
                const float next=std::clamp(value+(i.nav==Direction::left?-.05f:.05f),0.f,1.f);
                if(next!=value){value=next;dirty_=true;save_delay_=1.f;f.play(audio::Cue::slider);}
            }
            return;
        }
        if(i.is_pressed(Action::back)||i.is_pressed(Action::menu)){settings_=false;f.play(audio::Cue::back);return;}
        if(i.nav==Direction::down)setting_=std::min(int(preference_labels.size())-1,setting_+1);if(i.nav==Direction::up)setting_=std::max(0,setting_-1);
        bool edit=i.is_pressed(Action::confirm);
        if(edit){
            if(setting_==0){language_focus_=(language_focus_+(i.nav==Direction::left?4:1))%5;static constexpr const char*locales[]={"en","it","es","fr","de"};language_=locales[language_focus_];apply_language();}
            if(setting_==1){dark_theme_=!dark_theme_;theme_chosen_=true;}
            if(setting_==2){volumes_open_=true;volume_focus_=0;f.play(audio::Cue::select);return;}
            if(setting_==3)connection_panel_=true;
            if(setting_==4){settings_=false;onboarding_=true;language_choice_=true;theme_choice_=true;onboarding_step_=0;onboarding_position_.snap(0);onboarding_fade_.snap(0);onboarding_leaving_=false;}
            if(setting_==general_credits_setting){settings_=false;credits_=true;credits_scroll_.snap(0);}
            if(setting_==reset_trophies_setting){
                if(trophies_&&trophies_->reset()){trophy_notifications_.clearPending();trophy_fallback_queue_.clear();trophy_fallback_time_=0;trophy_fallback_sound_=false;trophy_expanded_=false;trophy_pin_open_=false;if(trophy_pin_renderer_)trophy_pin_renderer_(TrophyView{},0,0,0,0,0,0);trophy_focus_=0;trophy_position_.snap(0);trophy_media_session_.clear();trophy_media_played_=0;notice_=std::string(i18n::tr("Trophy progress reset."));notice_time_=3.5f;f.play(audio::Cue::saved);}
                else{notice_=std::string(i18n::tr("Trophy progress could not be reset."));notice_time_=3.5f;f.play(audio::Cue::error);}return;
            }

            dirty_=true;save_delay_=1.f;f.play(audio::Cue::toggle);
        }return;
    }
    if(i.is_pressed(Action::menu)){settings_=true;f.play(audio::Cue::modal_open);return;}
    if(!history_focus_&&i.is_pressed(Action::r3)&&!object_.error().empty()&&!model_path_.empty()){
        const auto*e=current();object_.request(model_path_,e&&!e->models.empty()?e->models[0].include_groups:std::vector<std::string>{});model_requested_=true;object_texture_=0;object_alpha_=0;f.play(audio::Cue::select);return;
    }
    const bool model_controls=!history_focus_&&object_texture_&&(object_inspect_||story_object()||(!detail_&&!gallery_&&!screening_&&!chapters_));
    if(model_controls){
        if(std::abs(i.stick2_x)>.01f||std::abs(i.stick2_y)>.01f){
            object_angle_+=i.stick2_x*dt_*2;
            object_tilt_offset_=std::clamp(object_tilt_offset_+i.stick2_y*dt_*1.5f,-1.25f,1.25f);
            object_manual_=true;
        }
        if((detail_||object_inspect_)&&(i.trigger_l>.04f||i.trigger_r>.04f))object_zoom_=std::clamp(object_zoom_+(i.trigger_r-i.trigger_l)*dt_,.5f,4.f);
    }
    if(object_inspect_){
        if(i.is_pressed(Action::back)){object_inspect_=false;f.play(audio::Cue::back);return;}
        if(i.nav==Direction::left)object_angle_-=.15f;if(i.nav==Direction::right)object_angle_+=.15f;
        if(i.nav==Direction::up)object_tilt_offset_=std::max(-1.25f,object_tilt_offset_-.1f);
        if(i.nav==Direction::down)object_tilt_offset_=std::min(1.25f,object_tilt_offset_+.1f);
        if(i.is_pressed(Action::confirm)){object_tilt_offset_=0;object_manual_=false;const auto*e=current();object_angle_=e&&!e->models.empty()?e->models[0].initial_angle:0;object_zoom_=e&&e->id=="xbox-series-x"?1.3f:e&&(e->id=="playstation-5"||e->id=="game-boy")?1.6f:2.f;}
        return;
    }
    if(chapters_){
        if(i.is_pressed(Action::back)){snapshot_current();fade_=0;chapters_=false;f.play(audio::Cue::back);return;}
        const int before=chapter_focus_;
        if(i.nav==Direction::down||i.nav==Direction::right)chapter_focus_=std::min(int(catalog_.eras.size())-1,chapter_focus_+1);
        if(i.nav==Direction::up||i.nav==Direction::left)chapter_focus_=std::max(0,chapter_focus_-1);
        if(before!=chapter_focus_){snapshot_current();fade_=0;f.play(audio::Cue::focus,1,0,.6f);}
        if(i.is_pressed(Action::confirm)&&chapter_focus_>=0&&chapter_focus_<int(catalog_.eras.size())){
            section_=0;filter_=0;rebuild();const auto&era=catalog_.eras[size_t(chapter_focus_)];
            for(size_t n=0;n<visible_.size();++n)if(catalog_.entries[size_t(visible_[n])].era_id==era.id){focus_=int(n);break;}
            timeline_.snap(float(focus_));changed();chapters_=false;f.play(audio::Cue::select);
        }
        return;
    }
    if(screening_||playlist_active_)adjust_media_volume(i);
    if(handle_playlist(i,f))return;
    if(gallery_){auto ev=viewer_.handle(i,f);image_index_=viewer_.index();if(ev==ui::Event::cancelled){gallery_=false;f.play(audio::Cue::back);}return;}
    if(screening_){
        if(i.is_pressed(Action::back)){if(fullscreen_)fullscreen_=false;else screening_=false;f.play(audio::Cue::back);return;}
        if(i.is_pressed(Action::north)){film_captions_enabled_=!film_captions_enabled_;f.play(audio::Cue::tab);return;}
        if(i.is_pressed(Action::confirm))video_.pause(!video_.paused());
        if(i.is_pressed(Action::west))fullscreen_=!fullscreen_;
        if(i.nav==Direction::left)video_.seek(std::max(0.,video_.time()-10));
        if(i.nav==Direction::right)video_.seek(video_.time()+10);
        return;
    }
    // Let the closing media return to its source before accepting base input.
    if(gallery_open_.value>.01f||screening_open_.value>.01f||object_open_.value>.01f||(history_transition_&&fade_<1))return;
    if(workshop_active_){if(workshop_.handle(i,f))workshop_active_=false;return;}
    if(i.is_pressed(Action::touch)&&panel_.value<.001f){open_year_guide();f.play(audio::Cue::modal_open);return;}
    if(detail_){
        if(!story_cards_.empty()&&story_cards_[size_t(story_focus_)].kind==StoryCard::experience&&std::abs(story_position_.value-float(story_focus_))<.08f&&i.is_pressed(Action::confirm)){
            open_experience(story_cards_[size_t(story_focus_)].study_index,{132,310,1656,575});f.play(audio::Cue::select);return;
        }
        if(!story_cards_.empty()&&story_cards_[size_t(story_focus_)].kind==StoryCard::interactive&&std::abs(story_position_.value-float(story_focus_))<.08f&&i.is_pressed(Action::confirm)){for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].id=="pixels"){open_experience(int(n),{132,310,1656,575});break;}f.play(audio::Cue::select);return;}
        if(i.is_pressed(Action::back)){detail_=false;f.play(audio::Cue::back);return;}
        if(i.is_pressed(Action::page_prev)){move(-1,f);return;}
        if(i.is_pressed(Action::page_next)){move(1,f);return;}
        if(i.nav==Direction::left)move_story(-1,f);
        if(i.nav==Direction::right)move_story(1,f);
        if(story_cards_.empty())return;
        const auto&card=story_cards_[size_t(story_focus_)];
        const bool reading=story_expanded_||(card.paragraph<0&&scroll_max_>0);
        if(i.nav==Direction::down){if(reading)scroll_.target=std::min(scroll_max_,scroll_.target+145);else move_story(1,f);}
        if(i.nav==Direction::up){if(reading)scroll_.target=std::max(0.f,scroll_.target-145);else move_story(-1,f);}
        if(reading&&std::abs(i.stick_y)>.1f)scroll_.target=std::clamp(scroll_.target+i.stick_y*dt_*680,0.f,scroll_max_);
        if(!story_object()&&std::abs(i.stick2_y)>.08f)scroll_.target=std::clamp(scroll_.target+i.stick2_y*dt_*680,0.f,scroll_max_);
        if(i.is_pressed(Action::west)&&story_object()){
            object_origin_={0,-9,1920,960};object_inspect_=true;idle_=0;f.play(audio::Cue::select);return;
        }
        if(i.is_pressed(Action::west)&&card.image>=0){image_index_=card.image;open_photo(story_actions_.empty()?Rect{1040,330,700,500}:story_actions_[0].bounds);f.play(audio::Cue::select);return;}
        if(i.is_pressed(Action::r3)&&card.paragraph>=0){story_expanded_=!story_expanded_;scroll_.target=0;f.play(audio::Cue::select);return;}
        const auto*e=current();if(!e)return;
        if(i.is_pressed(Action::confirm)&&story_object()&&std::abs(story_position_.value-float(story_focus_))<.08f){
            if(object_texture_){object_inspect_=true;idle_=0;f.play(audio::Cue::select);}return;
        }
        // Cards own the action, not whichever neighbouring photograph happens
        // to pass nearest the centre during an animation.
        if(i.is_pressed(Action::confirm)&&std::abs(story_position_.value-float(story_focus_))<.08f&&story_action_>=0&&story_action_<int(story_actions_.size())){
            const auto action=story_actions_[size_t(story_action_)];idle_=0;
            if(action.video>=0){release_culture_ambience();stop_playlist();video_index_=action.video;screening_origin_=action.bounds;screening_from_story_=true;video_.open(e->videos[size_t(video_index_)].youtube_id);screening_=true;fullscreen_=false;video_frame_alpha_=0;}
            f.play(audio::Cue::select);
        }
        return;
    }
    if(filter_press[0]!=filter_press[1]){change_filter(filter_press[1]?1:-1,f);return;}
    if(history_focus_){
        if(i.is_pressed(Action::north)){if(active_filter())change_filter(-active_filter(),f);else jump_today(f);return;}
        if(i.nav==Direction::down||i.is_pressed(Action::back)){focus_history(false);f.play(audio::Cue::tab);return;}
        if(i.nav==Direction::left)move_history(-1,f);
        if(i.nav==Direction::right)move_history(1,f);
        if(i.is_pressed(Action::page_prev)||i.is_pressed(Action::page_next)){
            const int direction=i.is_pressed(Action::page_prev)?-1:1;
            const int from=current()->year,decade=from/10;int next=history_focus_index_;
            for(int n=next+direction;n>=0&&n<int(history_catalog_.entries.size());n+=direction){next=n;if(history_catalog_.entries[size_t(n)].year/10!=decade)break;}
            move_history(next-history_focus_index_,f);
            show_year_notice(from,current()->year);
        }
        if(std::abs(i.stick2_y)>.08f)scroll_.target=std::clamp(scroll_.target+i.stick2_y*dt_*520,0.f,scroll_max_);
        if(i.is_pressed(Action::west)){open_photo(history_image_bounds());f.play(audio::Cue::select);}
        return;
    }
    if(i.nav==Direction::up){focus_history(true);f.play(audio::Cue::tab);return;}
    if(i.is_pressed(Action::west)){
        if(const auto*e=current();e&&!e->models.empty()){object_origin_={0,-9,1920,960};object_inspect_=true;idle_=0;}
        else open_photo({950,220,826,478});
        f.play(audio::Cue::select);return;
    }
    if(i.is_pressed(Action::r3)&&object_texture_){object_origin_={0,-9,1920,960};object_inspect_=true;idle_=0;f.play(audio::Cue::select);return;}
    if(i.is_pressed(Action::north)){if(active_filter())change_filter(-active_filter(),f);else jump_today(f);return;}
    if(i.nav==Direction::right)move(1,f);if(i.nav==Direction::left)move(-1,f);
    if(i.is_pressed(Action::page_next))chapter(1,f);if(i.is_pressed(Action::page_prev))chapter(-1,f);
    if(i.is_pressed(Action::confirm)&&current()){detail_=true;scroll_.snap(0);f.play(audio::Cue::select);}
}
void Screen::update(float delta){
    refresh_today_date();
    tactile_repeat_=std::max(0.f,tactile_repeat_-(std::isfinite(delta)?std::clamp(delta,0.f,.05f):0.f));
    dt_=std::clamp(delta,0.f,.05f);
    filter_notice_time_=std::max(0.f,filter_notice_time_-dt_);
    year_notice_time_=std::max(0.f,year_notice_time_-dt_);
    if(year_notice_time_>0){
        const float progress=reduced_?1.f:tween::smoothstep(std::clamp((1.35f-year_notice_time_)/.60f,0.f,1.f));
        const int displayed=int(std::lround(year_notice_from_+(year_notice_to_-year_notice_from_)*progress));
        if(displayed!=year_notice_displayed_){year_notice_displayed_=displayed;year_notice_tick_=!reduced_;}
    }else year_notice_tick_=false;
    update_trophies();
    if(theme_confirming_){theme_confirm_progress_=reduced_?1.f:std::min(1.f,theme_confirm_progress_+dt_/0.48f);if(theme_confirm_progress_>=1){theme_confirming_=false;theme_choice_=false;onboarding_step_=0;onboarding_position_.snap(0);}}

    if(onboarding_&&!language_choice_&&!theme_choice_&&onboarding_step_==3)pin_onboarding_time_+=dt_;else pin_onboarding_time_=0;
    if(onboarding_&&!language_choice_&&!theme_choice_&&onboarding_step_==0&&!reduced_){
        const auto random=[this](){if(!intro_m_random_)intro_m_random_=unsigned(hui::sys::monotonic_us())|1u;intro_m_random_^=intro_m_random_<<13;intro_m_random_^=intro_m_random_>>17;intro_m_random_^=intro_m_random_<<5;return intro_m_random_;};
        if(intro_m_active_<0){
            constexpr int cells[]={0,4,5,6,8,9,10,12,14,15,19,20,24};
            int candidates[13],count=0;
            for(int cell=0;cell<13;++cell){
                if(intro_m_previous_>=0){const int a=cells[cell],b=cells[intro_m_previous_];if(std::abs(a/5-b/5)<=1&&std::abs(a%5-b%5)<=1)continue;}
                candidates[count++]=cell;
            }
            intro_m_active_=candidates[random()%unsigned(count)];intro_m_previous_=intro_m_active_;
            intro_m_from_=intro_m_colours_[size_t(intro_m_active_)];intro_m_to_=(intro_m_from_+1+random()%7)%8;intro_m_fade_=0;
        }
        intro_m_fade_+=dt_;
        if(intro_m_fade_>=1.2f){intro_m_colours_[size_t(intro_m_active_)]=intro_m_to_;intro_m_active_=-1;intro_m_fade_=0;}
    }else{intro_m_active_=-1;intro_m_fade_=0;}
    search_prompt_.update(dt_);search_open_.target=search_page_?1.f:0.f;search_open_.update(dt_,reduced_?60.f:13.f);
    search_position_.target=float(search_focus_);search_position_.update(dt_,reduced_?60.f:18.f);
    history_emphasis_.target=history_focus_?1.f:0.f;history_emphasis_.update(dt_,reduced_?60.f:12.f);
    history_position_.target=float(history_focus_index_);history_position_.update(dt_,reduced_?60.f:17.f);
    experience_audio_.volume(.48f*sfx_volume_);
    theme_mix_.target=dark_theme_?1.f:0.f;theme_mix_.update(dt_,12);
    language_selection_.target=float(language_focus_);language_selection_.update(dt_,reduced_?60.f:16.f);
    theme_selection_.target=dark_theme_?0.f:1.f;theme_selection_.update(dt_,reduced_?60.f:16.f);
    guide_mode_.target=guide_experiences_?1.f:0.f;guide_mode_.update(dt_,14);
    if(year_guide_&&guide_trophies_&&!trophy_pin_open_&&!search_page_&&!search_prompt_.visible())trophy_focus_time_+=dt_;
    else trophy_focus_time_=0;
    trophy_position_.target=float(trophy_focus_);trophy_position_.update(dt_,reduced_?60.f:18.f);
    experience_open_.target=experience_active_?1.f:0.f;experience_open_.update(dt_,reduced_?30:12);
    const bool study_complete=experience_active_&&study_&&study_->completion()!=StudyCompletion::playing;
    experience_pause_open_.target=(experience_paused_||study_complete)?1.f:0.f;experience_pause_open_.update(dt_,reduced_?60.f:16.f);
    experience_intro_.target=experience_introduction_?1.f:0.f;experience_intro_.update(dt_,14);
    if(year_guide_&&guide_experiences_&&!guide_trophies_)experience_description_clock_+=dt_;else experience_description_clock_=0;
    experience_position_.target=float(experience_focus_);experience_position_.update(dt_,16);
    if(experience_active_&&!experience_paused_&&!experience_input_paused_&&!experience_introduction_&&experience_intro_.value<.01f&&!study_complete){if(study_){study_->update(dt_);if(trophies_&&experience_index_>=0&&experience_index_<int(study_catalog().size()))trophies_->experienceResult(study_catalog()[size_t(experience_index_)].id,study_->trophy_stats());}}
    if(experience_active_)experience_audio_.paused(experience_paused_||experience_input_paused_||(study_&&study_->completion()!=StudyCompletion::playing));
notice_time_=std::max(0.f,notice_time_-dt_);if(!experience_active_||!experience_paused_)workshop_.update(dt_);time_+=dt_;idle_+=dt_;fade_=std::min(1.f,fade_+dt_*(reduced_?12.f:history_transition_?1.8f:3.5f));
    if(onboarding_){
        onboarding_fade_.target=onboarding_leaving_?0.f:1.f;onboarding_fade_.update(dt_,10);
        if(onboarding_leaving_&&onboarding_fade_.value<.001f){onboarding_=false;onboarding_leaving_=false;onboarding_complete_=true;dirty_=true;save_delay_=0;boot_time_=0;boot_note_=0;}
    }else boot_time_=std::min(5.f,boot_time_+dt_);
    constexpr std::uint32_t decade_colours[]={0xdc9b79,0xc2b179,0xd78a64,0x83b8b0,0xb6a2cf,0x82acc8,0xc8919b,0xb1c098};
    const int decade=std::clamp((int(selected_year())-1950)/10,0,7);
    tone_=gfx::mix(tone_,Color::rgb(decade_colours[decade]),1.f-std::exp(-dt_*2.8f));
    story_position_.target=float(story_focus_);story_position_.update(dt_,reduced_?60:14);story_read_.target=story_expanded_?1.f:0.f;story_read_.update(dt_,14);
    timeline_.target=float(focus_);timeline_.update(dt_,reduced_?60:17);scroll_.update(dt_,reduced_?60:17);panel_.target=settings_||credits_?1.f:0.f;panel_.update(dt_,reduced_?60:13);
    onboarding_position_.target=float(onboarding_step_);onboarding_position_.update(dt_,reduced_?40:12);
    year_panel_.target=year_guide_?1.f:0.f;year_panel_.update(dt_,reduced_?40:12);year_position_.target=float(year_focus_);year_position_.update(dt_,reduced_?50:16);
    const float motion=reduced_?32.f:12.f;
    story_open_.target=detail_?1.f:0.f;story_open_.update(dt_,motion);
    gallery_open_.target=gallery_?1.f:0.f;gallery_open_.update(dt_,motion);
    screening_open_.target=screening_?1.f:0.f;screening_open_.update(dt_,motion);
    video_full_.target=fullscreen_?1.f:0.f;video_full_.update(dt_,motion);
    object_open_.target=object_inspect_?1.f:0.f;object_open_.update(dt_,motion);
    sources_open_.target=story_sources_?1.f:0.f;sources_open_.update(dt_,motion);
    if(gallery_){if(gallery_overlay_image_!=image_index_){gallery_overlay_image_=image_index_;gallery_overlay_age_=0;}gallery_overlay_age_+=dt_;}
    else{gallery_overlay_image_=-1;gallery_overlay_age_=0;}
    gallery_labels_.target=gallery_&&gallery_overlay_age_<3?1.f:0.f;gallery_labels_.update(dt_,9);
    media_hints_.target=idle_<4?1.f:0.f;media_hints_.update(dt_,9);
    update_culture_ambience();
    if(!culture_ambience_.owns_player()&&!screening_&&!playlist_active_&&screening_open_.value<.001f&&video_.state()!=media::State::idle)video_.close();
    if(screening_open_.value<.001f&&!screening_)playlist_closing_=false;
    video_frame_alpha_=std::clamp(video_frame_alpha_+dt_*(video_.texture()?3.f:-5.f),0.f,1.f);
    credits_open_.target=credits_?1.f:0.f;credits_open_.update(dt_,14);credits_scroll_.update(dt_,17);
    settings_scroll_.target=std::max(0.f,float(setting_-8)*68);settings_scroll_.update(dt_,reduced_?60:18);
    image_dialog_open_.target=image_dialog_?1.f:0.f;image_dialog_open_.update(dt_,reduced_?60:16);
    focus_line_.target=volumes_open_?230+volume_focus_*118:240+setting_*68;focus_line_.update(dt_,reduced_?60:18);
    chapter_marker_.target=float(chapter_focus_);chapter_marker_.update(dt_,reduced_?60:17);
    if(chapters_){const auto*e=chapter_object();if(e&&!e->images.empty())cache_.request(image_url(e->images[e->preferred_image]));}
    if(connection_panel_||(onboarding_&&!language_choice_&&!theme_choice_&&onboarding_step_==onboarding_cards_-1)){const auto c=video_.connection();if(!c.qr_url.empty()&&c.qr_url!=connection_qr_value_){yt::QrImage qr;if(yt::make_qr(c.qr_url,8,&qr)&&qr.valid()){if(connection_qr_)glDeleteTextures(1,&connection_qr_);connection_qr_=renderer_.batch().create_texture(qr.width,qr.height,qr.rgba.data());connection_qr_value_=c.qr_url;}}}
    std::vector<std::string> visible_photos;
    if(onboarding_&&!language_choice_&&!theme_choice_&&std::abs(onboarding_position_.value-3.f)<1.5f){visible_photos.push_back("museum-pin:first_pin_3d-colour");cache_.request(visible_photos.back());}

    if(year_guide_&&guide_trophies_&&trophies_){
        const auto pins=trophies_->views(true);const auto add_pin=[&](int n){if(n>=0&&n<int(pins.size()))visible_photos.push_back("museum-pin:"+pins[size_t(n)].badge+"-colour");};
        add_pin(trophy_focus_);for(int offset=1;offset<=5;++offset){add_pin(trophy_focus_-offset);add_pin(trophy_focus_+offset);}
    }
    if(trophy_fallback_time_>0)visible_photos.insert(visible_photos.begin(),"museum-pin:"+trophy_fallback_current_.badge+"-colour");

    if(const auto*e=current()){
        if(gallery_||gallery_open_.value>.001f){if(image_index_>=0&&image_index_<int(e->images.size()))visible_photos.push_back(image_url(e->images[size_t(image_index_)]));}
        else if(chapters_){const auto*chapter=chapter_object();if(chapter&&!chapter->images.empty())visible_photos.push_back(image_url(chapter->images[chapter->preferred_image]));}
        else if(story_open_.value>.25f){
            // A photograph may be the poster for a video action. Keep the card's
            // actual image resident even when the action opens a film instead.
            const int first=std::max(0,int(std::floor(story_position_.value))-1),last=std::min(int(story_cards_.size())-1,int(std::ceil(story_position_.value))+1);
            if(story_focus_>=0&&story_focus_<int(story_cards_.size())){const int image=story_cards_[size_t(story_focus_)].image;if(image>=0&&image<int(e->images.size()))visible_photos.push_back(image_url(e->images[size_t(image)]));}
            for(int n=first;n<=last;++n){const int image=story_cards_[size_t(n)].image;if(image>=0&&image<int(e->images.size())&&std::find(visible_photos.begin(),visible_photos.end(),image_url(e->images[size_t(image)]))==visible_photos.end())visible_photos.push_back(image_url(e->images[size_t(image)]));}
        }
        else if(e->models.empty()&&!e->images.empty())visible_photos.push_back(image_url(e->images[e->preferred_image]));
    }
    const auto model_memory=object_.timings();
    const bool model_pressure=(object_.loading()||object_.ready())&&std::max(model_memory.planned_gpu_bytes,model_memory.estimated_gpu_bytes)>(352u<<20);
    if(!model_pressure)for(const auto&cover:nearby_covers_)if(std::find(visible_photos.begin(),visible_photos.end(),cover)==visible_photos.end())visible_photos.push_back(cover);
    cache_.set_visible(visible_photos);
    const bool photos_retired=cache_.set_model_pressure(model_pressure)>0;
    video_.update(dt_);cache_.upload_pending(renderer_);video_.upload_pending(renderer_);update_playlist();
    media::finish_screening(screening_,fullscreen_,playlist_active_,video_.state()==media::State::ready,video_.ended());
    if(const auto*e=current())for(size_t n=0;n<e->images.size();++n){
        const auto state=cache_.get(image_url(e->images[n]));
        if(state.state==media::State::idle&&std::find(visible_photos.begin(),visible_photos.end(),image_url(e->images[n]))!=visible_photos.end())cache_.request(image_url(e->images[n]));
        if(state.texture)image_fades_[image_url(e->images[n])]=std::min(1.f,image_fades_[image_url(e->images[n])]+dt_*3.f);
    }
    const bool cache_ready=warm_objects();
    // Spend only a small display-frame slice; the renderer raises its byte
    // cap from measured transfer throughput while retaining wall-time/chunk guards.
    const double upload_allowance=std::clamp(1000.0/double(target_refresh_hz_)*.18,.5,2.0);
    const bool uploaded=cache_ready&&!photos_retired&&object_.upload_pending(upload_allowance,true);
    if(uploaded){object_alpha_=0;object_texture_=0;}
    model_wait_+=dt_;
    if(!model_url_.empty()||!model_path_.empty()){
        if(!model_requested_&&model_wait_>=.06f){
            const auto*selected=visible_.empty()?nullptr:&catalog_.entries[size_t(visible_[size_t(focus_)])];
            if(!model_path_.empty()){object_.request(model_path_,selected&&!selected->models.empty()?selected->models[0].include_groups:std::vector<std::string>{});model_requested_=true;}
            else cache_.request(model_url_,false);
        }
        if(!model_url_.empty()&&!model_requested_){const auto model=cache_.get(model_url_);if(model.state==media::State::ready){model_path_=model.path;const auto*selected=visible_.empty()?nullptr:&catalog_.entries[size_t(visible_[size_t(focus_)])];object_.request(model_path_,selected&&!selected->models.empty()?selected->models[0].include_groups:std::vector<std::string>{});model_requested_=true;}}
        const bool object_visible=!search_page_&&!search_prompt_.visible()&&!history_focus_&&!experience_active_&&experience_open_.value<.001f&&!onboarding_&&!settings_&&!credits_&&!year_guide_&&!chapters_&&!gallery_&&!screening_&&(object_inspect_||object_open_.value>.001f||story_object()||story_open_.value<.999f);
        object_render_clock_+=dt_;
        if(model_requested_&&object_.ready()&&object_visible){
            if(!reduced_&&!object_inspect_&&!object_manual_)object_angle_+=dt_*.23f;
            const auto*selected=visible_.empty()?nullptr:&catalog_.entries[size_t(visible_[size_t(focus_)])];
            const float tilt=(selected&&!selected->models.empty()?selected->models[0].initial_tilt:.13f)+object_tilt_offset_;
            const bool z_up=selected&&!selected->models.empty()&&selected->models[0].source_z_up;
            const bool inspecting=object_inspect_||object_open_.value>.001f;
            // A transparent full-width stage lets the model pass in front of
            // the copy instead of clipping against an invisible card edge.
            const float expansion=inspecting?std::clamp(object_open_.value,0.f,1.f):0.f;
            // Match the transparent 2:1 exhibit stage to the output density.
            // Keep the source atlas budget independent of render resolution.
            const int rw=std::max(1920,output_width_);
            const int rh=rw/2;
            const float hero_height=story_object()?580.f:562.f;
            const float center=(story_object()?.328125f:.425f)*(1-expansion);
            const float zoom=object_zoom_*(hero_height+(960-hero_height)*expansion)/960.f;
            const bool changed_pose=object_angle_!=object_render_angle_||tilt!=object_render_tilt_||zoom!=object_render_zoom_;
            const bool resize=rw!=object_render_width_||rh!=object_render_height_;
            // Match the accepted display rate, including automatic rotation.
            // Measured submission cost can back off an over-budget object;
            // a fixed30/60Hz ceiling must not make a120Hz display look uneven.
            const auto timings=object_.timings();
            const float gpu_ms=timings.gpu_samples?float(timings.last_gpu_ms):0;
            const float cost=std::max(object_frame_ms_,gpu_ms)*.001f*1.15f;
            const float interval=cost<=1.f/target_refresh_hz_?0.f:cost;
            if(!object_texture_||resize||(changed_pose&&object_render_clock_>=interval)){
                const auto started=std::chrono::steady_clock::now();
                const float vertical_margin=selected&&selected->id=="playstation-5"?.02f*(1-expansion):0.f;
                object_texture_=object_.render(object_angle_,rw,rh,tilt,z_up,zoom,center,vertical_margin);
                const float ms=std::chrono::duration<float,std::milli>(std::chrono::steady_clock::now()-started).count();
                if(!resize)object_frame_ms_=object_frame_ms_*.75f+ms*.25f;object_render_clock_=0;
                object_render_angle_=object_angle_;object_render_tilt_=tilt;object_render_zoom_=zoom;object_render_width_=rw;object_render_height_=rh;
            }
            object_alpha_=std::min(1.f,object_alpha_+dt_*2.5f);
        }
    }
    viewer_.style.reduced_motion=reduced_;viewer_.update(dt_);
    if(gallery_){image_index_=viewer_.index();prepare_gallery(false);}
    if(dirty_){save_delay_-=dt_;if(save_delay_<=0)save_settings();}
}
void Screen::log_performance()const{
    const auto t=object_.timings();const auto s=object_.stats();
    sys::log("[Museum] 3D ready %d / target %dx%d / triangles %zu draws %zu / upload last %.2f max %.2fms, max tick %zu KiB / GPU %.2f max %.2fms samples %zu / read %.2fms / UI story %d card %d",object_texture_!=0,t.render_width,t.render_height,s.triangles,s.draw_calls,t.last_upload_ms,t.max_upload_ms,t.max_upload_bytes>>10,t.last_gpu_ms,t.max_gpu_ms,t.gpu_samples,t.read_decode_ms,detail_,story_focus_);
    sys::log("[Museum] interface CPU stages / layout %.3fms scene %.3fms display %.3fms / accepted target %.0fHz / atlas storage max %.3fms transfer max %.3fms / model GPU estimate %zu MiB",interface_stage_ms_[0],interface_stage_ms_[1],interface_stage_ms_[2],target_refresh_hz_,t.max_storage_ms,t.max_transfer_ms,t.estimated_gpu_bytes>>20);
}
void Screen::logo(gfx::DrawList&d,float x,float y,float size,Color c)const{const float p=size/5;const int grid[5][5]={{1,0,0,0,1},{1,1,0,1,1},{1,0,1,0,1},{1,0,0,0,1},{1,0,0,0,1}};for(int r=0;r<5;++r)for(int col=0;col<5;++col)if(grid[r][col])d.rounded_rect({x+col*p,y+r*p,p,p},0,c);}
void Screen::heading(gfx::DrawList&d,const std::string&s,float x,float y,float size,float width,Color c)const{float fitted=size;while(fonts_.semibold.font->wrap(s,fitted,width).size()>2&&fitted>20)fitted-=1;ui::paragraph(d,fonts_.semibold,s,x,y,fitted,width,fitted*1.15f,c);}
void Screen::image(gfx::DrawList&d,const Image&i,Rect r,bool fit,float alpha){
    auto a=cache_.get(image_url(i));
    if(!a.texture&&a.state==media::State::idle)a=cache_.request(image_url(i));
    if(!a.texture){
        const auto waiting=image_wait_started_.try_emplace(image_url(i),time_).first;
        if(time_-waiting->second>=.2f){
            constexpr float radius=22,pixel=7,tau=6.28318530718f;
            const float phase=reduced_?-1.57079632679f:time_*tau-1.57079632679f;
            const auto ink=&d==&media_layer_?Color::rgb(0xf1efe7):colours().ink;
            d.ring(r.cx(),r.cy(),radius,1.f,ink.with_alpha(alpha*.16f));
            d.rounded_rect({r.cx()+std::cos(phase)*radius-pixel*.5f,r.cy()+std::sin(phase)*radius-pixel*.5f,pixel,pixel},0,ink.with_alpha(alpha*.8f));
        }
        return;
    }
    image_wait_started_.erase(image_url(i));
    const float aspect=float(a.width)/std::max(1,a.height);Rect uv=gfx::kFullUv;if(fit){if(r.w/r.h>aspect){const float w=r.h*aspect;r.x+=(r.w-w)/2;r.w=w;}else{const float h=r.w/aspect;r.y+=(r.h-h)/2;r.h=h;}}else{const float wanted=r.w/r.h;if(aspect>wanted){uv.w=wanted/aspect;uv.x=(1-uv.w)/2;}else{uv.h=aspect/wanted;uv.y=(1-uv.h)/2;}}const auto f=image_fades_.find(image_url(i));d.image(a.texture,r,uv,Color::rgb(0xffffff,alpha*(f==image_fades_.end()?1.f:f->second)));
}
void Screen::hints(const std::vector<ui::Hint>&h){
    page_.push_opacity(1-std::clamp(panel_.value,0.f,1.f));
    const auto palette=colours();ui::HintLayout l;l.size=30;l.text_size=22;l.cy=1014;l.item_gap=28;
    while(ui::measure_hints(fonts_,h.data(),int(h.size()),l)>1728&&l.text_size>18){l.text_size-=1;l.item_gap=std::max(16.f,l.item_gap-2);l.size=std::max(26.f,l.size-1);}
    auto style=ui::GlyphStyle::mono(palette.ink,Color::rgb(0,0));style.label=palette.muted;
    ui::draw_hints(page_,fonts_,style,h.data(),int(h.size()),96,false,l);
    page_.pop_opacity();
}
void Screen::draw_header(){
    const auto palette=colours();const auto c=palette.ink;
    logo(page_,96,66,34,c);
    ui::text(page_,fonts_.semibold,"PIXEL MUSEUM",150,93,22,c,Align::left,2.f);
    if(!chapters_){
        ui::text(page_,fonts_.semibold,today_date_label(),1824,87,25,c,Align::right);
        const auto matches=today_entries(history_focus_);
        if(!matches.empty()){
            constexpr float period=4.5f,fade=.45f;
            const float clock=std::max(0.f,time_),phase=std::fmod(clock,period);
            const size_t selected=size_t(std::floor(clock/period))%matches.size();
            const float alpha=matches.size()==1?1.f:tween::smoothstep(std::clamp(std::min(phase,period-phase)/fade,0.f,1.f));
            const auto&entries=(history_focus_?history_catalog_:catalog_).entries;
            const auto&title=entries[size_t(matches[selected])].title;
            float size=20;while(size>15&&fonts_.regular.font->measure(title,size)>1000)size-=1;
            page_.push_clip({824,97,1000,30});
            ui::paragraph(page_,fonts_.regular,title,1824,119,size,1000,26,palette.muted.with_alpha(alpha),1,Align::right);
            page_.pop_clip();
        }
    }
    if(notice_time_>0){const float a=std::min({1.f,(3.5f-notice_time_)*4,notice_time_*2});ui::text(page_,fonts_.regular,notice_,960,92,20,c.with_alpha(a),Align::center);}
}
const Entry* Screen::chapter_object()const{
    if(chapter_focus_<0||chapter_focus_>=int(catalog_.eras.size()))return nullptr;
    const auto&id=catalog_.eras[size_t(chapter_focus_)].id;
    for(const auto&e:catalog_.entries)if(e.era_id==id&&e.featured&&!e.images.empty())return &e;
    for(const auto&e:catalog_.entries)if(e.era_id==id&&!e.images.empty())return &e;
    return nullptr;
}
void Screen::draw_chapters(){
    const auto palette=colours();[[maybe_unused]] const auto paper=palette.paper,ink=palette.ink,muted=palette.muted,rule=palette.rule;
    if(catalog_.eras.empty())return;
    const auto&era=catalog_.eras[size_t(chapter_focus_)];const auto accent=tone_;
    page_.gradient_rect({0,128,1920,850},0,gfx::mix(palette.paper,accent,.12f),palette.paper);
    ui::text(page_,fonts_.semibold,std::to_string(era.start_year),-28,910,360,ink.with_alpha(.035f));
    ui::text(page_,fonts_.mono,"SEVEN CHAPTERS / ONE SHARED MEDIUM",96,186,18,ink.with_alpha(.45f),Align::left,1.5f);
    page_.push_opacity(fade_);
    const float y=ui::paragraph(page_,fonts_.semibold,era.title,90,286,66,770,76,ink,2);
    ui::paragraph(page_,fonts_.regular,era.summary,96,y+16,28,710,40,ink.with_alpha(.6f),3);
    if(const auto*e=chapter_object())if(!e->images.empty())image(page_,e->images[e->preferred_image],{160,520,600,330},true);
    page_.pop_opacity();
    const float start=223,step=72;
    page_.line(1004,start,1004,start+6*step+118,2,ink.with_alpha(.13f));
    const float fy=start+chapter_marker_.value*step;
    page_.bordered_rect({1037,fy-40,775,190},0,accent.with_alpha(.12f),1,ink.with_alpha(.14f));
    page_.rounded_rect({997,fy-7,14,14},0,ink);
    for(size_t n=0;n<catalog_.eras.size();++n){const bool selected=int(n)==chapter_focus_;const auto&r=catalog_.eras[n];const float row=start+float(n)*step+(int(n)>chapter_focus_?118:0);char number[10];std::snprintf(number,sizeof(number),"%02zu",n+1);page_.circle(1004,row,selected?0:3,ink.with_alpha(.3f));ui::text(page_,fonts_.mono,number,1060,row+7,20,ink.with_alpha(selected?1.f:.3f));ui::text(page_,fonts_.semibold,r.title,1120,row+8,30,ink.with_alpha(selected?1.f:.43f));if(selected){ui::text(page_,fonts_.mono,std::to_string(r.start_year)+" — "+std::to_string(r.end_year),1120,row+45,18,ink.with_alpha(.4f));ui::paragraph(page_,fonts_.regular,r.summary,1120,row+85,23,650,32,ink.with_alpha(.6f));}}
    ui::text(page_,fonts_.mono,"A HISTORY TOLD THROUGH ITS PEOPLE, MACHINES AND WORLDS",96,936,17,ink.with_alpha(.3f),Align::left,1.f);
    hints({{ui::Button::dpad,"Choose chapter"},{ui::Button::cross,"Enter"},{ui::Button::circle,"Continue timeline"},{ui::Button::options,"Options"}});
}
void Screen::draw_preferences(){
    const auto palette=colours();[[maybe_unused]] const auto paper=palette.paper,ink=palette.ink,muted=palette.muted,rule=palette.rule;
    const float x=1110+(1-panel_.value)*810;overlay_.rounded_rect({0,0,1920,1080},0,Color::rgb(0,.25f*panel_.value));overlay_.glass(renderer_.glass_texture(),{x,0,810,1080},0,paper.with_alpha(.98f));
    overlay_.rounded_rect({x,0,810,1080},0,paper.with_alpha(.96f));
    ui::text(overlay_,fonts_.semibold,volumes_open_?"Volumes":"Options",x+62,134,44,ink);
    if(volumes_open_){
        static constexpr std::array<const char*,5> labels={"Master volume","Sound effects","Ambient music","Cultural timeline audio","Controller audio"};
        const std::array<float,5> values={master_volume_,sfx_volume_,volume_,culture_volume_,pad_volume_};
        overlay_.rounded_rect({x+37,focus_line_.value-32,5,volume_focus_==5?64.f:94.f},0,tone_);
        for(int row=0;row<5;++row){
            const float y=230+row*118,value=std::clamp(values[size_t(row)],0.f,1.f);
            const auto colour=row==volume_focus_?ink:muted;
            ui::text(overlay_,fonts_.semibold,labels[size_t(row)],x+65,y,25,colour);
            char percent[16];std::snprintf(percent,sizeof(percent),"%d %%",int(std::lround(value*100)));
            ui::text(overlay_,fonts_.mono,percent,x+716,y,21,colour,Align::right);
            overlay_.rounded_rect({x+65,y+33,650,4},0,rule);
            if(value>0)overlay_.rounded_rect({x+65,y+33,650*value,4},0,colour);
            overlay_.rounded_rect({x+60+650*value,y+27,10,16},0,colour);
        }
        const float toggle_y=820;
        ui::text(overlay_,fonts_.semibold,"Cultural audio on controller",x+65,toggle_y,25,volume_focus_==5?ink:muted);
        ui::text(overlay_,fonts_.regular,culture_audio_on_pad_?"On":"Off",x+610,toggle_y,21,muted,Align::right);
        overlay_.rounded_rect({x+630,toggle_y-26,86,36},18,culture_audio_on_pad_?ink:rule);
        overlay_.circle(x+630+(culture_audio_on_pad_?66:20),toggle_y-8,14,paper);
        ui::Hint controls[]={{ui::Button::dpad,"Adjust"},{ui::Button::circle,"Options"}};
        ui::HintLayout layout;layout.cy=959;layout.size=28;layout.text_size=22;
        ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),controls,2,x+65,false,layout);
        return;
    }
    const auto& names=preference_labels;
    const char* language_name=language_=="it"?"Italiano":language_=="es"?"Espa\u00f1ol":language_=="fr"?"Fran\u00e7ais":language_=="de"?"Deutsch":"English";
    overlay_.rounded_rect({x+37,focus_line_.value-28,5,56},0,tone_);
    for(int row=0;row<int(names.size());++row){
        const float y=240+row*68;ui::text(overlay_,fonts_.semibold,names[size_t(row)],x+65,y,25,ink);
        if(row==0)ui::text(overlay_,fonts_.regular,language_name,x+716,y,23,muted,Align::right);
        if(row==1)ui::text(overlay_,fonts_.regular,dark_theme_?"Dark":"Light",x+716,y,23,muted,Align::right);
        if(row==3)ui::paragraph(overlay_,fonts_.regular,"An optional connection for films with transcripts.",x+65,y+26,18,640,25,muted,2);
        if(row>=2)ui::text(overlay_,fonts_.regular,">",x+706,y,30,ink);
    }
    ui::text(overlay_,fonts_.mono,"PIXEL MUSEUM / 0.1.0",x+65,959,18,muted,Align::left,1.5f);
}

void Screen::draw_connection(){
    const auto palette=colours();[[maybe_unused]] const auto paper=palette.paper,ink=palette.ink,muted=palette.muted,rule=palette.rule;
    const float x=1110;overlay_.rounded_rect({x,0,810,1080},0,paper);
    const auto c=video_.connection();ui::text(overlay_,fonts_.semibold,"YouTube connection",x+62,134,42,ink);
    const char*message=c.signed_in?"The museum is connected.":!c.user_code.empty()?"Scan the code on your phone and follow YouTube's instructions.":"Some films require a YouTube connection. You can choose to connect an account here.";
    ui::paragraph(overlay_,fonts_.regular,message,x+64,205,27,670,39,muted,5);
    if(!c.user_code.empty()&&!c.signed_in){if(connection_qr_)overlay_.image(connection_qr_,{x+225,350,360,360},gfx::kFullUv,Color::rgb(0xffffff));ui::text(overlay_,fonts_.mono,c.user_code,x+405,768,40,ink,Align::center);ui::paragraph(overlay_,fonts_.regular,c.verification_url,x+64,831,25,670,36,muted,3);}
    else if(c.state==media::State::loading)ui::text(overlay_,fonts_.regular,"Contacting YouTube…",x+64,414,28,muted);
    else if(c.state==media::State::failed)ui::paragraph(overlay_,fonts_.regular,c.error,x+64,414,27,670,39,ink,8);
    ui::Hint h[]={{ui::Button::circle,"Back"},{c.signed_in?ui::Button::square:ui::Button::cross,c.signed_in?"Disconnect":c.saved?"Reconnect":"Connect"}};
    ui::HintLayout l;l.cy=1015;l.size=28;l.text_size=22;ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),h,2,x+65,false,l);
}
void Screen::draw_credits(){
    const auto palette=colours();[[maybe_unused]] const auto paper=palette.paper,ink=palette.ink,muted=palette.muted,rule=palette.rule;
    const float x=1110+(1-panel_.value)*810;
    overlay_.rounded_rect({0,0,1920,1080},0,Color::rgb(0,.25f*panel_.value));
    overlay_.glass(renderer_.glass_texture(),{x,0,810,1080},0,paper.with_alpha(.98f));
    overlay_.rounded_rect({x,0,810,1080},0,paper.with_alpha(.96f));
    ui::text(overlay_,fonts_.semibold,"Credits",x+62,134,42,ink);
    overlay_.push_clip({x+62,230,685,700});overlay_.push_transform(1,0,0,0,-credits_scroll_.value);float y=265;
    y=ui::paragraph(overlay_,fonts_.regular,general_credits_body(),x+64,y,24,665,35,ink,999)+34;
    y=ui::paragraph(overlay_,fonts_.semibold,"Feature resources",x+64,y,26,665,35,ink,999)+24;
    if(feature_resources_lines_.empty())feature_resources_lines_=ui::paragraph_lines(fonts_.regular,feature_resources_sites,21,665,std::numeric_limits<int>::max()).lines;
    const int first=std::max(0,int(std::floor((230+credits_scroll_.value-y)/30))-1);
    const int end=std::min(int(feature_resources_lines_.size()),int(std::ceil((930+credits_scroll_.value-y)/30))+1);
    for(int n=first;n<end;++n)ui::text(overlay_,fonts_.regular,feature_resources_lines_[size_t(n)],x+64,y+float(n)*30,21,muted);
    y+=float(feature_resources_lines_.size())*30+34;
    y=ui::paragraph(overlay_,fonts_.semibold,"Sources and licences",x+64,y,26,665,35,ink)+24;
    const char* paragraphs[]={"Interface foundation — ps5-homebrew-ui by BlackBearReloaded. Its OpenGL renderer, type system, springs, controller components and image viewer form the museum interface.","Optional controller state layout - Based on PSSwanStation by Press5elect. The local reference traces this layout to PSFlyCast.","Native YouTube playback — ytps5-sponsorblock by animatian112, with FFmpeg and its contributors. YouTube films remain hosted by their original publishers. Availability can vary by region and service changes.","Collection photography — the individual creators and archives credited in every exhibit. Hardware photography includes public-domain work by Evan-Amos. Each image retains its source and licence.","Editorial references — Computer History Museum, The Strong, Brookhaven National Laboratory, Smithsonian, the Video Game History Foundation, original developers and publishers. Source records are preserved in the collection metadata.","An original ambient score accompanies the collection. Typography uses Inter, Montserrat, DejaVu Sans Mono and a Noto Sans CJK fallback by Adobe and Noto font contributors, under their respective open font licences.","Wikipedia reference introductions retain article revision, contributor and CC BY-SA links. Historical texts retain their original sources. Minimal ambient silhouettes refer to Pac-Man, Mario and Space Invaders; their characters belong to their respective rights holders.","The museum is an independent historical project. Product names identify the objects being discussed; their owners are not affiliated with this project. External films, photographs and models retain their respective rights."};
    for(const char*p:paragraphs)y=ui::paragraph(overlay_,fonts_.regular,p,x+64,y,24,665,35,ink)+34;
    credits_scroll_max_=std::max(0.f,y-900);overlay_.pop_transform();overlay_.pop_clip();
    if(credits_scroll_max_>0){const float height=700,thumb=std::max(32.f,height*height/(height+credits_scroll_max_)),offset=(height-thumb)*credits_scroll_.value/credits_scroll_max_;overlay_.line(x+768,230,x+768,930,2,muted.with_alpha(.2f));overlay_.line(x+768,230+offset,x+768,230+offset+thumb,3,ink.with_alpha(.65f));}
    ui::Hint h[]={{ui::Button::circle,"Options"},{ui::Button::right_stick,"Read"}};ui::HintLayout l;l.cy=1014;l.size=28;l.text_size=22;ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),h,2,x+64,false,l);
}

void Screen::show_year_notice(int from,int to){
    if(from==to)return;
    year_notice_from_=from;year_notice_to_=to;year_notice_displayed_=from;year_notice_tick_=false;year_notice_time_=1.35f;filter_notice_time_=0;
}
void Screen::draw_filter_notice(){
    const bool year=year_notice_time_>0;
    if((!year&&filter_notice_time_<=0)||onboarding_||experience_active_)return;
    const auto palette=colours();
    const float remaining=year?year_notice_time_:filter_notice_time_;
    const float elapsed=1.35f-remaining;
    const float alpha=std::min(std::clamp(elapsed/.10f,0.f,1.f),std::clamp(remaining/.22f,0.f,1.f));
    const std::string label=year?std::to_string(year_notice_displayed_):std::string(i18n::tr(active_filter_label()));
    float size=year?176.f:80.f;while(size>30&&fonts_.display.measure(label,size)>1720)size-=1;
    overlay_.push_opacity(alpha);
    overlay_.rounded_rect({0,0,1920,1080},0,palette.paper.with_alpha(.82f));
    std::vector<gfx::GlyphQuad> notice_glyphs;
    fonts_.display.font->layout(label,0,0,size,Align::left,notice_glyphs);
    float baseline=540.f+(fonts_.display.font->ascent(size)-fonts_.display.font->descent(size))*.5f;
    if(!notice_glyphs.empty()){
        float top=notice_glyphs.front().y0,bottom=notice_glyphs.front().y1;
        for(const auto&glyph:notice_glyphs){top=std::min(top,glyph.y0);bottom=std::max(bottom,glyph.y1);}
        baseline=540.f-(top+bottom)*.5f;
    }
    ui::text(overlay_,fonts_.display,label,960,baseline,size,palette.ink,Align::center);
    overlay_.pop_opacity();
}

void Screen::draw(int width,int height,unsigned framebuffer){
    auto stage_time=std::chrono::steady_clock::now();
    const auto mark=[&](size_t index){const auto now=std::chrono::steady_clock::now();interface_stage_ms_[index]=std::chrono::duration<double,std::milli>(now-stage_time).count();stage_time=now;};
    interface_stage_ms_.fill(0);
    const auto palette=colours();[[maybe_unused]] const auto paper=palette.paper,ink=palette.ink,muted=palette.muted,rule=palette.rule;
    output_width_=width;output_height_=height;viewer_.style.pixel_scale=1920.f/std::max(1,width);
    if(onboarding_&&onboarding_fade_.value>.999f&&!onboarding_leaving_){
        welcome_.clear();draw_onboarding();mark(0);renderer_.begin();renderer_.draw(welcome_);renderer_.present(framebuffer,width,height);mark(2);return;
    }
    if(experience_active_&&experience_open_.value>.999f){
        experience_layer_.clear();draw_experience();mark(0);renderer_.begin();renderer_.draw(experience_layer_);renderer_.present(framebuffer,width,height);mark(2);return;
    }
    background_.clear();page_.clear();overlay_.clear();media_layer_.clear();
    background_.rounded_rect({0,0,1920,1080},0,paper);draw_header();
    if(chapters_)draw_chapters();else draw_timeline();
    if(object_open_.value>.001f)draw_object();
    if(gallery_open_.value>.001f)draw_gallery();
    if(screening_open_.value>.001f)draw_screening();
    // These very soft wall projections do not carry text or object detail.
    // Shade their continuous light field once at960x540 rather than evaluating
    // the procedural silhouette at8.3million fragments on every UI frame.
    if(!chapters_){
        if(!wall_.texture())wall_.create(960,540,1);
        if(wall_.texture()&&(time_-wall_time_>=1.f/30||wall_time_<0)){
            renderer_.begin();renderer_.draw(background_);
            gfx::BackdropSpec shadow;shadow.mode=gfx::BackdropMode::museum_shadows;shadow.time=reduced_?11.f:time_+5;shadow.colors[0]=ink;shadow.params[0]=.028f;renderer_.backdrop(shadow);
            renderer_.present(wall_.framebuffer(),960,540);wall_.resolve();wall_time_=time_;
        }
    }else wall_time_=-10;
    renderer_.begin();
    if(!chapters_&&wall_.texture()){wall_layer_.clear();wall_layer_.image(wall_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff));renderer_.draw(wall_layer_);}
    else renderer_.draw(background_);
    renderer_.draw(page_);renderer_.draw(media_layer_);
    if(year_panel_.value>.001f){overlay_.clear();renderer_.glass();draw_year_guide();renderer_.draw(overlay_);}
    else if(panel_.value>.001f){renderer_.glass();if(connection_panel_)draw_connection();else{overlay_.push_opacity(1-std::clamp(credits_open_.value,0.f,1.f));draw_preferences();overlay_.pop_opacity();if(credits_open_.value>.001f){overlay_.push_opacity(std::clamp(credits_open_.value,0.f,1.f));draw_credits();overlay_.pop_opacity();}}renderer_.draw(overlay_);}
    if(search_open_.value>.001f||search_prompt_.visible()){
        overlay_.clear();if(search_open_.value>.001f)draw_search();
        if(search_prompt_.visible()){renderer_.glass();ui::Canvas canvas{overlay_,fonts_,renderer_.glass_texture(),time_};search_prompt_.draw(canvas);}
        renderer_.draw(overlay_);
    }
    if(experience_open_.value>.001f){experience_layer_.clear();draw_experience();renderer_.draw(experience_layer_);}
    if(onboarding_){welcome_.clear();draw_onboarding();renderer_.draw(welcome_);}
    if(!onboarding_&&boot_time_<4.8f){draw_boot();renderer_.draw(boot_);}
    if(trophy_fallback_time_>0){overlay_.clear();draw_trophy_fallback();renderer_.draw(overlay_);}
    if(filter_notice_time_>0||year_notice_time_>0){overlay_.clear();draw_filter_notice();renderer_.draw(overlay_);}
    if(composed_.width()!=width||composed_.height()!=height){entry_snapshot_=false;composed_.create(width,height,1);}
    if(!composed_.texture()){renderer_.present(framebuffer,width,height);return;}
    mark(0);renderer_.present(composed_.framebuffer(),width,height);composed_.resolve();mark(1);
    // The PS5 backend resolves glBlitFramebuffer through a CPU readback here
    // (~508ms for3840x2160 in the console trace). Sample the complete scene
    // with the existing GPU batch instead, including the no-transition case.
    if(fade_>=1)entry_snapshot_=false;
    composition_.clear();
    if(history_transition_&&entry_snapshot_&&previous_entry_.texture()&&fade_<1){
        const float travel=tween::smoothstep(fade_);
        const float outgoing=1-tween::smoothstep(std::clamp(fade_*2,0.f,1.f));
        const float incoming=tween::smoothstep(std::clamp((fade_-.5f)*2,0.f,1.f));
        constexpr float top=142,height=842;
        const Rect crop{0,1-top/1080.f,1,-height/1080.f};
        // The chrome remains at its original coordinates. Only the cropped
        // exhibition canvas travels between the two chronological routes.
        composition_.image(composed_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff));
        composition_.push_clip({0,top,1920,height});
        composition_.rounded_rect({0,top,1920,height},0,paper);
        composition_.image(composed_.texture(),{0,top+history_direction_*(1-travel)*height,1920,height},crop,Color::rgb(0xffffff));
        composition_.image(previous_entry_.texture(),{0,top-history_direction_*travel*height,1920,height},crop,Color::rgb(0xffffff));
        composition_.pop_clip();
        for(const auto&chrome:{Rect{1180,0,740,top},Rect{0,top+height,1920,1080-top-height}}){
            composition_.push_clip(chrome);
            composition_.rounded_rect(chrome,0,paper);
            composition_.image(previous_entry_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff,outgoing));
            composition_.image(composed_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff,incoming));
            composition_.pop_clip();
        }
    }else{
        history_transition_=false;
        composition_.image(composed_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff));
        if(entry_snapshot_&&previous_entry_.texture()&&fade_<1)composition_.image(previous_entry_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff,1-tween::smoothstep(fade_)));
        else entry_snapshot_=false;
    }
    renderer_.begin();renderer_.draw(composition_);renderer_.present(framebuffer,width,height);mark(2);
}
}
