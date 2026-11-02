// Pixel Museum - one shared content-update sheet for PC and PS5.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
using namespace hui;
using gfx::Rect;using gfx::Color;using gfx::Align;
using DatabasePhase=DatabaseUpdater::Phase;
bool Screen::database_notification_ready()const{
#if defined(MUSEUM_DESKTOP)
    if(application_dialog_||application_open_.value>.001f)return false;
#endif
    return !onboarding_&&!onboarding_leaving_&&!collection_pending_&&boot_time_>=4.8f&&!experience_active_&&experience_open_.value<.001f&&!gallery_&&!screening_&&!object_inspect_&&!search_page_&&!search_prompt_.visible()&&!year_guide_&&!settings_&&!credits_&&!connection_panel_&&!support_dialog_&&support_open_.value<.001f&&!collection_remove_dialog_&&!collection_removal_active()&&panel_.value<.01f;
}
void Screen::open_database_update(ui::Feedback&feedback){
    database_auto_checked_=true;
    auto state=database_updater_.snapshot();
    if(state.phase!=DatabasePhase::available&&state.phase!=DatabasePhase::downloading&&state.phase!=DatabasePhase::ready){database_updater_.check();state=database_updater_.snapshot();}
    database_state_=state;database_dialog_=true;database_focus_=0;database_open_.snap(0);
    if(state.phase==DatabasePhase::available)database_notified_revision_=state.revision;
    if(state.phase==DatabasePhase::ready)database_ready_notified_revision_=state.revision;
    feedback.play(audio::Cue::modal_open);
}
void Screen::observe_database_update(const DatabaseUpdater::Snapshot&state){
    database_state_=state;
    if(database_dialog_){
        database_focus_=std::clamp(database_focus_,0,database_action_count()-1);
        if(state.phase==DatabasePhase::available)database_notified_revision_=state.revision;
        if(state.phase==DatabasePhase::ready)database_ready_notified_revision_=state.revision;
        return;
    }
    if(!database_notification_ready())return;
    const bool available=state.phase==DatabasePhase::available&&state.revision!=database_notified_revision_;
    const bool completed=state.phase==DatabasePhase::ready&&state.revision!=database_ready_notified_revision_;
    if(!available&&!completed)return;
    database_dialog_=true;database_focus_=0;database_open_.snap(0);
    if(available)database_notified_revision_=state.revision;else database_ready_notified_revision_=state.revision;
}
void Screen::update_database(float dt){
#if defined(MUSEUM_DESKTOP)
    if(application_combined_check_&&!database_dialog_){
        database_state_=database_updater_.snapshot();database_open_.target=0;database_open_.update(dt,reduced_?60.f:16.f);return;
    }
#endif
    if(!database_auto_checked_&&database_notification_ready()){database_auto_checked_=true;database_updater_.check();}
    observe_database_update(database_updater_.snapshot());
    database_open_.target=database_dialog_?1.f:0.f;database_open_.update(dt,reduced_?60.f:16.f);
}
int Screen::database_action_count()const{return database_state_.phase==DatabasePhase::available||database_state_.phase==DatabasePhase::failed?2:1;}
const char* Screen::database_action_label(int action)const{
    if(database_state_.phase==DatabasePhase::available)return action?"Update":"Later";
    if(database_state_.phase==DatabasePhase::failed)return action?"Try again":"Later";
    if(database_state_.phase==DatabasePhase::downloading)return "Continue exploring";
    return database_state_.phase==DatabasePhase::checking||database_state_.phase==DatabasePhase::idle?"Close":"Done";
}
Rect Screen::database_action_bounds(int action)const{
    const float rise=(1-std::clamp(database_open_.value,0.f,1.f))*18;
    return {database_action_count()==1?722.5f:470+action*505.f,675+rise,475,78};
}
bool Screen::handle_database_update(const InputFrame&input,ui::Feedback&feedback){
    if(!database_dialog_)return database_open_.value>.001f;
    if(input.focus_lost||!input.connected)return true;
    if(input.is_pressed(Action::back)||input.is_pressed(Action::menu)){database_dialog_=false;feedback.play(audio::Cue::back);return true;}
    const int before=database_focus_;
    if(input.nav==Direction::left||input.nav==Direction::up)database_focus_=0;
    if(input.nav==Direction::right||input.nav==Direction::down)database_focus_=database_action_count()-1;
    if(before!=database_focus_)feedback.play(audio::Cue::focus);
    if(!input.is_pressed(Action::confirm))return true;
    if(database_action_count()==1||database_focus_==0){database_dialog_=false;feedback.play(audio::Cue::back);return true;}
    const bool started=database_state_.phase==DatabasePhase::available?database_updater_.install():database_updater_.check();
    database_state_=database_updater_.snapshot();database_focus_=0;
    feedback.play(started?audio::Cue::select:audio::Cue::error);return true;
}
void Screen::draw_database_update(){
    const float alpha=std::clamp(database_open_.value,0.f,1.f);if(alpha<=0)return;
    const auto p=colours();const float rise=(1-alpha)*18;const Rect card{410,255+rise,1100,560};
    overlay_.push_opacity(alpha);overlay_.rounded_rect({0,0,1920,1080},0,Color::rgb(0,.44f));overlay_.bordered_rect(card,0,p.paper,1,p.rule);
    ui::text(overlay_,fonts_.mono,"DATABASE",470,320+rise,18,p.muted,Align::left,1.8f);
    const auto phase=database_state_.phase;const bool checking=phase==DatabasePhase::idle||phase==DatabasePhase::checking,downloading=phase==DatabasePhase::downloading;
    const char*title=checking?"Checking for updates…":phase==DatabasePhase::current?"Your museum is up to date.":phase==DatabasePhase::available?"New stories are available.":downloading?"Updating the database":phase==DatabasePhase::ready?"Your database is ready.":"The update was interrupted.";
    ui::paragraph(overlay_,fonts_.semibold,title,470,390+rise,38,980,48,p.ink,2);
    if(!database_state_.version.empty()){char label[160];ui::format(label,"Database %s",database_state_.version.c_str());ui::text(overlay_,fonts_.mono,label,470,438+rise,19,p.muted);}
    std::string body;
    if(checking)body=std::string(i18n::tr("Looking for new stories and discoveries."));
    else if(phase==DatabasePhase::current)body=std::string(i18n::tr("You already have the latest museum database."));
    else if(phase==DatabasePhase::available)body=std::string(i18n::tr("New stories and discoveries are ready for your museum."));
    else if(downloading)body=std::string(i18n::tr("Your preferences and trophies stay with you. You can continue exploring while the update is prepared."));
    else if(phase==DatabasePhase::ready)body=std::string(i18n::tr("Open Pixel Museum again to use the new database. Your preferences and trophies have been kept."));
    else body=database_state_.error.empty()?std::string(i18n::tr("The database could not be updated. Please try again later.")):database_state_.error;
    ui::paragraph(overlay_,fonts_.regular,body,470,488+rise,25,970,36,p.muted,3);
    if(checking||downloading){
        overlay_.rounded_rect({470,617+rise,980,4},0,p.rule);
        if(downloading&&database_state_.total_bytes){
            const float progress=std::clamp(float(double(database_state_.downloaded_bytes)/double(database_state_.total_bytes)),0.f,1.f);overlay_.rounded_rect({470,617+rise,980*progress,4},0,tone_);
            char amount[96];std::snprintf(amount,sizeof(amount),"%.1f / %.1f MiB  ·  %.0f %%",database_state_.downloaded_bytes/(1024.*1024.),database_state_.total_bytes/(1024.*1024.),progress*100);ui::text(overlay_,fonts_.mono,amount,470,652+rise,18,p.muted);
        }else{const float x=470+(980-140)*(.5f+.5f*std::sin(time_*2));overlay_.rounded_rect({x,617+rise,140,4},0,tone_);}
    }
    for(int action=0;action<database_action_count();++action){const auto button=database_action_bounds(action);const bool selected=action==database_focus_;overlay_.bordered_rect(button,0,selected?p.ink:p.paper,1,selected?p.ink:p.rule);ui::text(overlay_,fonts_.semibold,database_action_label(action),button.cx(),button.y+48,25,selected?p.paper:p.ink,Align::center);}
    overlay_.pop_opacity();
}
}
