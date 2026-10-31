// Pixel Museum - achievements recorded from actual museum interactions.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/trophy_definitions.hpp"
#include "core/save_file.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <cmath>
#include <set>

namespace museum {
void Screen::initialize_trophies(){
    trophies_=std::make_unique<Trophies>(data_+"/trophies-v1.dat");
    if(!trophies_->load())hui::sys::log("[Museum] trophies preserved: %s",trophies_->lastError().c_str());
    trophies_->setDefinitions(make_trophy_definitions());
    std::set<std::string> unique;
    for(const auto&e:catalog_.entries)if(!e.body.empty())unique.insert(story_source(e).id);
    for(const auto&e:history_catalog_.entries)if(!e.body.empty())unique.insert(e.id);
    trophies_->setEligibleCatalogSnapshot({unique.begin(),unique.end()});
    // The shell reads badges in its own namespace: /download0 belongs only
    // to this title and cannot be used as a system-notification image URL.
    trophy_notifications_.start("/data/homebrew/PPSA70421/assets/trophies/fronts");
    trophy_pin_scene_.set_root(root_);
    set_trophy_pin_renderer([this](const TrophyView&v,int width,int height,float yaw,float pitch,float zoom,float pan_y){
        return trophy_pin_scene_.render(v.badge,v.unlocked||trophy_curator_preview_,width,height,yaw,pitch,zoom,pan_y);
    });
}

void Screen::update_trophies(){
    if(!trophies_)return;
    // User-requested system notifications only: never synthesize an in-app
    // trophy toast or sound, including when the OS transport reports failure.
    trophy_fallback_queue_.clear();trophy_fallback_time_=0;trophy_fallback_sound_=false;
    const auto*entry=current();
    const bool browsing=!onboarding_&&!language_choice_&&!theme_choice_;
    if(browsing&&history_focus_&&entry)trophies_->cultureVisit(entry->id);
    if(browsing&&detail_&&!year_guide_&&!settings_&&!experience_active_&&entry&&!story_cards_.empty()){
        const auto&owner=story_source(*entry);
        trophies_->visit(owner.id);
        const auto&card=story_cards_[size_t(std::clamp(story_focus_,0,int(story_cards_.size())-1))];
        if(card.paragraph>=0)trophies_->card(owner.id,card.paragraph);
    }
    if(gallery_&&viewer_.zoom()>=viewer_.style.max_zoom-.001f)trophies_->zoomMaximum();
    const bool music=playlist_active_;
    const bool playing=(music||screening_)&&video_.state()==media::State::ready&&!video_.paused();
    const std::string session=entry?(entry->id+":"+(music?"music:":"video:")+
        std::to_string(music?playlist_playing_:video_index_)+":"+std::to_string(playlist_music_room_)):std::string{};
    const double now=video_.time();
    if(session!=trophy_media_session_){trophy_media_session_=session;trophy_media_played_=0;trophy_media_previous_=now;}
    const double elapsed=now-trophy_media_previous_;
    // Seeking or loading must not count as listening/watching. Only advancing
    // decoded playback with audible volume contributes to the music gate.
    if(playing&&elapsed>0&&elapsed<=double(dt_)*3+.2&&(!music||media_volume_>.001f))
        trophy_media_played_+=std::min(elapsed,double(dt_)*2);
    trophy_media_previous_=now;
    const double duration=video_.duration(),gate=music?10.:30.;
    const bool natural_short_end=video_.ended()&&duration>0&&duration<gate&&
        trophy_media_played_>=duration*.9;
    if(music)trophies_->musicProgress(session,trophy_media_played_,natural_short_end);
    else if(screening_)trophies_->videoProgress(session,trophy_media_played_,natural_short_end);
    for(const auto&unlock:trophies_->drainUnlocks()){
        // Request only the PS5 system toast for each persisted unlock.
        // API acceptance cannot prove actual shell display or sound.
        constexpr bool submit_optional_native_trophy=true;
        const std::string directory="/data/homebrew/PPSA70421/assets/trophies/fronts";
        const std::string icon=directory+"/"+unlock.badge+".png";
        if(submit_optional_native_trophy)trophy_notifications_.submit(unlock,icon);
    }
    for(const auto&fallback:trophy_notifications_.pollFallback()){
        hui::sys::log("[Museum] trophy %s: %s",fallback.unlock.id.c_str(),fallback.reason.c_str());
        // Failure is diagnostic only; no replacement overlay or app sound.
    }
}
}
