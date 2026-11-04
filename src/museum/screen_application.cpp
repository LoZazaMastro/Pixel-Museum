// Pixel Museum - one Windows check for the application and museum database.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#if defined(MUSEUM_DESKTOP)
#include "museum/menu_row.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
using namespace hui;
using gfx::Rect;using gfx::Color;using gfx::Align;
using ApplicationPhase=ApplicationUpdater::Phase;
bool Screen::application_notification_ready()const{
    return idle_>=1.25f&&!detail_&&!chapters_&&story_open_.value<.001f&&gallery_open_.value<.001f&&screening_open_.value<.001f&&object_open_.value<.001f&&!database_dialog_&&database_open_.value<.001f&&database_notification_ready();
}
namespace {
struct CombinedCheck {
    bool checking=false, downloading=false, available=false, failed=false, app_ready=false, database_ready=false;
    bool actionable()const{return !checking&&!downloading&&(available||failed||app_ready);}
};
CombinedCheck combined_check(ApplicationPhase a,DatabaseUpdater::Phase d){
    using D=DatabaseUpdater::Phase;
    return {a==ApplicationPhase::idle||a==ApplicationPhase::checking||d==D::idle||d==D::checking,
        a==ApplicationPhase::downloading||d==D::downloading,
        a==ApplicationPhase::available||d==D::available,
        a==ApplicationPhase::failed||d==D::failed,
        a==ApplicationPhase::ready,d==D::ready};
}
const char* update_status(ApplicationPhase phase){
    switch(phase){
    case ApplicationPhase::idle:case ApplicationPhase::checking:return "Checking...";
    case ApplicationPhase::current:return "Up to date";
    case ApplicationPhase::available:return "Available";
    case ApplicationPhase::downloading:return "Downloading...";
    case ApplicationPhase::ready:return "Ready";
    default:return "Could not check";
    }
}
const char* database_status(DatabaseUpdater::Phase phase){
    using D=DatabaseUpdater::Phase;
    switch(phase){
    case D::idle:case D::checking:return "Checking...";
    case D::current:return "Up to date";
    case D::available:return "Available";
    case D::downloading:return "Downloading...";
    case D::ready:return "Ready";
    default:return "Could not check";
    }
}
}
void Screen::open_update_check(ui::Feedback& feedback){
    application_combined_check_=true;
    application_auto_checked_=database_auto_checked_=true;
    auto a=application_updater_.snapshot();
    auto d=database_updater_.snapshot();
    if(a.phase!=ApplicationPhase::downloading&&a.phase!=ApplicationPhase::ready)application_updater_.check();
    if(d.phase!=DatabaseUpdater::Phase::downloading&&d.phase!=DatabaseUpdater::Phase::ready)database_updater_.check();
    database_dialog_=false;database_open_.snap(0);
    application_dialog_=true;application_focus_=0;application_open_.snap(0);
    database_state_=database_updater_.snapshot();observe_application_update(application_updater_.snapshot());
    feedback.play(audio::Cue::modal_open);
}
void Screen::open_application_update(ui::Feedback& feedback){open_update_check(feedback);}
void Screen::observe_application_update(const ApplicationUpdater::Snapshot& snapshot){
    application_state_=snapshot;
    if(application_restart_failed_){application_state_.phase=ApplicationPhase::failed;application_state_.error=application_restart_error_;}
    if(application_state_.phase==ApplicationPhase::ready&&!application_state_.version.empty()&&application_state_.version!=application_ready_notified_version_){
        application_ready_notified_version_=application_state_.version;
        if(!application_dialog_)application_completion_notice_=6.f;
    }
    if(application_dialog_){
        if(application_combined_check_&&database_state_.phase==DatabaseUpdater::Phase::available)
            database_notified_revision_=database_state_.revision;
        application_focus_=std::clamp(application_focus_,0,application_action_count()-1);
        if(application_state_.phase==ApplicationPhase::available)application_notified_version_=application_state_.version;
        return;
    }
    if(!application_notification_ready())return;
    const auto& version=application_state_.version;
    const bool available=application_state_.phase==ApplicationPhase::available&&!version.empty()&&version!=application_notified_version_;
    const bool database_available=application_combined_check_&&database_state_.phase==DatabaseUpdater::Phase::available&&database_state_.revision!=database_notified_revision_;
    if(!available&&!database_available)return;
    if(database_available)database_notified_revision_=database_state_.revision;
    application_dialog_=true;application_focus_=0;application_open_.snap(0);
    if(available)application_notified_version_=version;
}
void Screen::update_application(float dt){
    application_completion_notice_=std::max(0.f,application_completion_notice_-dt);
    if(!application_auto_checked_&&application_notification_ready()){
        application_combined_check_=true;application_auto_checked_=database_auto_checked_=true;
        application_updater_.check();database_updater_.check();
    }
    if(application_combined_check_)database_state_=database_updater_.snapshot();
    observe_application_update(application_updater_.snapshot());
    application_open_.target=application_dialog_?1.f:0.f;application_open_.update(dt,reduced_?60.f:16.f);
}
int Screen::application_action_count()const{
    if(application_combined_check_)return combined_check(application_state_.phase,database_state_.phase).actionable()?2:1;
    return application_state_.phase==ApplicationPhase::available||application_state_.phase==ApplicationPhase::ready||application_state_.phase==ApplicationPhase::failed?2:1;
}
const char* Screen::application_action_label(int action)const{
    if(application_combined_check_){
        const auto state=combined_check(application_state_.phase,database_state_.phase);
        if(state.actionable())return action?(state.available?"Update":state.app_ready?"Restart now":"Try again"):"Later";
        if(state.downloading)return "Continue exploring";
        return state.checking?"Close":"Done";
    }
    if(application_state_.phase==ApplicationPhase::available)return action?"Update":"Later";
    if(application_state_.phase==ApplicationPhase::ready)return action?"Restart now":"Later";
    if(application_state_.phase==ApplicationPhase::failed)return action?"Try again":"Later";
    if(application_state_.phase==ApplicationPhase::downloading)return "Continue exploring";
    return application_state_.phase==ApplicationPhase::current?"Done":"Close";
}
Rect Screen::application_action_bounds(int action)const{
    const float rise=(1-std::clamp(application_open_.value,0.f,1.f))*18;
    return {application_action_count()==1?722.5f:470+action*505.f,675+rise,475,78};
}
bool Screen::handle_application_update(const InputFrame& input,ui::Feedback& feedback){
    if(!application_dialog_)return application_open_.value>.001f;
    if(input.focus_lost||!input.connected)return true;
    if(input.is_pressed(Action::back)||input.is_pressed(Action::menu)){application_dialog_=false;feedback.play(audio::Cue::back);return true;}
    const int before=application_focus_;
    if(input.nav==Direction::left||input.nav==Direction::up)application_focus_=0;
    if(input.nav==Direction::right||input.nav==Direction::down)application_focus_=application_action_count()-1;
    if(before!=application_focus_)feedback.play(audio::Cue::focus);
    if(!input.is_pressed(Action::confirm))return true;
    if(application_action_count()==1||application_focus_==0){application_dialog_=false;feedback.play(audio::Cue::back);return true;}
    if(application_combined_check_){
        const auto state=combined_check(application_state_.phase,database_state_.phase);
        bool started=false;
        if(state.available){
            if(application_state_.phase==ApplicationPhase::available)started=application_updater_.install()||started;
            if(database_state_.phase==DatabaseUpdater::Phase::available)started=database_updater_.install()||started;
        }else if(state.app_ready||application_restart_failed_){application_restart_request_=true;feedback.play(audio::Cue::select);return true;}
        else{
            if(application_state_.phase==ApplicationPhase::failed)started=application_updater_.check()||started;
            if(database_state_.phase==DatabaseUpdater::Phase::failed)started=database_updater_.check()||started;
        }
        application_state_=application_updater_.snapshot();database_state_=database_updater_.snapshot();application_focus_=0;
        feedback.play(started?audio::Cue::select:audio::Cue::error);return true;
    }
    if(application_state_.phase==ApplicationPhase::ready||application_restart_failed_){application_restart_request_=true;feedback.play(audio::Cue::select);return true;}
    const bool started=application_state_.phase==ApplicationPhase::available?application_updater_.install():application_updater_.check();
    application_state_=application_updater_.snapshot();application_focus_=0;
    feedback.play(started?audio::Cue::select:audio::Cue::error);return true;
}
bool Screen::take_application_restart_request(){const bool requested=application_restart_request_;application_restart_request_=false;return requested;}
bool Screen::begin_application_restart(){
    application_restart_request_=false;
    if(application_updater_.begin_restart(language_))return true;
    application_restart_failed_=true;application_restart_error_=application_updater_.snapshot().error;
    if(application_restart_error_.empty())application_restart_error_="Pixel Museum could not restart to finish the update. Please try again.";
    application_dialog_=true;application_focus_=0;application_open_.snap(1);observe_application_update(application_updater_.snapshot());
    return false;
}
void Screen::draw_application_update(){
    const float alpha=std::clamp(application_open_.value,0.f,1.f);if(alpha<=0)return;
    const auto p=colours();const float rise=(1-alpha)*18;
    overlay_.push_opacity(alpha);overlay_.rounded_rect(canvas_bounds(),0,Color::rgb(0,.44f));overlay_.bordered_rect({410,255+rise,1100,560},0,p.paper,1,p.rule);
    if(application_combined_check_){
        const auto state=combined_check(application_state_.phase,database_state_.phase);
        ui::text(overlay_,fonts_.mono,"Check for updates",470,320+rise,18,p.muted,Align::left,1.8f);
        const char* title=state.checking?"Checking for updates...":state.downloading?"Updating Pixel Museum":state.available?"Updates are available.":state.app_ready||state.database_ready?"Your update is ready.":state.failed?"The check could not be completed.":"Your museum is up to date.";
        ui::paragraph(overlay_,fonts_.semibold,title,470,390+rise,38,980,48,p.ink,2);
        ui::text(overlay_,fonts_.regular,"Pixel Museum",470,460+rise,25,p.ink);
        ui::text(overlay_,fonts_.regular,update_status(application_state_.phase),1450,460+rise,23,p.muted,Align::right);
        ui::text(overlay_,fonts_.regular,"Database",470,510+rise,25,p.ink);
        ui::text(overlay_,fonts_.regular,database_status(database_state_.phase),1450,510+rise,23,p.muted,Align::right);
        const char* body=state.checking?"Looking for app and database updates.":state.downloading?"You can continue exploring while the updates are prepared.":state.available?"Download the available updates for Pixel Museum.":state.app_ready?"Restart Pixel Museum to finish installing the update.":state.database_ready?"Open Pixel Museum again to use the new database.":state.failed?"Please try again later.":"You already have the latest app and database.";
        ui::paragraph(overlay_,fonts_.regular,body,470,565+rise,23,970,32,p.muted,2);
        if(state.checking||state.downloading){
            overlay_.rounded_rect({470,627+rise,980,4},0,p.rule);
            const auto total=application_state_.total_bytes+database_state_.total_bytes;
            const auto done=application_state_.downloaded_bytes+database_state_.downloaded_bytes;
            if(state.downloading&&total){
                const float q=std::clamp(float(double(done)/double(total)),0.f,1.f);
                overlay_.rounded_rect({470,627+rise,980*q,4},0,tone_);
                ui::text(overlay_,fonts_.mono,update_download_amount(done,total),470,654+rise,18,p.muted);
            }
            else{const float x=470+(980-140)*(.5f+.5f*std::sin(time_*2));overlay_.rounded_rect({x,627+rise,140,4},0,tone_);}
        }
    }else{
    ui::text(overlay_,fonts_.mono,"APP UPDATE",470,320+rise,18,p.muted,Align::left,1.8f);
    const auto phase=application_state_.phase;const bool checking=phase==ApplicationPhase::idle||phase==ApplicationPhase::checking,downloading=phase==ApplicationPhase::downloading;
    const char* title=checking?"Checking for app updates…":phase==ApplicationPhase::current?"Pixel Museum is up to date.":phase==ApplicationPhase::available?"A new Pixel Museum version is available.":downloading?"Updating Pixel Museum":phase==ApplicationPhase::ready?"Your app update is ready.":"Pixel Museum could not be updated.";
    float title_size=38;while(title_size>29&&fonts_.semibold.measure(title,title_size)>980)title_size-=1;
    ui::text(overlay_,fonts_.semibold,title,470,390+rise,title_size,p.ink);
    if(!application_state_.version.empty())ui::text(overlay_,fonts_.mono,"Pixel Museum "+application_state_.version,470,438+rise,19,p.muted);
    if(!application_state_.current_version.empty()){char installed[160];ui::format(installed,"Installed version %s",application_state_.current_version.c_str());ui::text(overlay_,fonts_.mono,installed,1450,438+rise,19,p.muted,Align::right);}
    std::string body;
    if(checking)body=std::string(i18n::tr("Looking for a new version of Pixel Museum."));
    else if(phase==ApplicationPhase::current)body=std::string(i18n::tr("You already have the latest version of Pixel Museum."));
    else if(phase==ApplicationPhase::available){
        const auto note=application_state_.notes.find(language_),english=application_state_.notes.find("en");
        body=note!=application_state_.notes.end()?note->second:english!=application_state_.notes.end()?english->second:std::string(i18n::tr("A new version is ready to download. Your collection, preferences and trophies are kept."));
    }else if(downloading)body=std::string(i18n::tr("Pixel Museum is downloading the new version. You can continue exploring while it is prepared."));
    else if(phase==ApplicationPhase::ready)body=std::string(i18n::tr("Restart Pixel Museum to finish installing the update. Your collection, preferences and trophies are kept."));
    else body=std::string(i18n::tr(application_state_.error.empty()?"Your current version is unchanged. Please try again later.":application_state_.error));
    ui::paragraph(overlay_,fonts_.regular,body,470,488+rise,25,970,36,p.muted,3);
    if(checking||downloading){
        overlay_.rounded_rect({470,617+rise,980,4},0,p.rule);
        if(downloading&&application_state_.total_bytes){
            const float progress=std::clamp(float(double(application_state_.downloaded_bytes)/double(application_state_.total_bytes)),0.f,1.f);overlay_.rounded_rect({470,617+rise,980*progress,4},0,tone_);
            ui::text(overlay_,fonts_.mono,update_download_amount(application_state_.downloaded_bytes,application_state_.total_bytes),470,652+rise,18,p.muted);
        }else{const float x=470+(980-140)*(.5f+.5f*std::sin(time_*2));overlay_.rounded_rect({x,617+rise,140,4},0,tone_);}
    }
    }
    for(int action=0;action<application_action_count();++action){const auto button=application_action_bounds(action);const bool selected=action==application_focus_;overlay_.bordered_rect(button,0,selected?p.ink:p.paper,1,selected?p.ink:p.rule);ui::text(overlay_,fonts_.semibold,application_action_label(action),button.cx(),menu_text_baseline(fonts_.semibold,application_action_label(action),button.cy(),25),25,selected?p.paper:p.ink,Align::center);}
    overlay_.pop_opacity();
}
}
#endif
