// Pixel Museum - focused pointer, scrolling and PC navigation regressions.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#if defined(MUSEUM_DESKTOP)
#include "museum/screen.hpp"
#include "museum/general_credits.hpp"
#include "museum/trophy_definitions.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <chrono>
namespace museum {
struct DesktopNavigationInspection {
    static bool run(Screen&s){
        int passed=0,failed=0;
        const auto check=[&](bool ok,const char*label){std::fprintf(stderr,"[Desktop navigation] %s: %s\n",ok?"PASS":"FAIL",label);ok?++passed:++failed;};
        const auto input=[](){hui::InputFrame i;i.connected=true;i.controller_style=hui::DesktopControllerStyle::keyboard_mouse;return i;};
        const auto send=[&](hui::InputFrame i){hui::ui::Feedback f;s.handle(i,f);};
        const auto press=[&](hui::Action a){auto i=input();i.pressed=hui::action_bit(a);send(i);};
        const auto nav=[&](hui::Direction direction){auto i=input();i.nav=direction;send(i);};
        const auto click=[&](float x,float y){auto i=input();i.pointer.available=true;i.pointer.primary_pressed=true;i.pointer.x=x;i.pointer.y=y;send(i);};
        const auto wheel=[&](float x,float y,float amount){auto i=input();i.pointer.available=true;i.pointer.x=x;i.pointer.y=y;i.pointer.wheel_y=amount;send(i);};
        s.collection_pending_=s.onboarding_=s.language_choice_=s.theme_choice_=s.onboarding_leaving_=false;s.boot_time_=5;s.dt_=1.f/60;
        s.database_auto_checked_=s.application_auto_checked_=true;s.database_dialog_=s.application_dialog_=s.support_dialog_=false;
        s.database_open_.snap(0);s.application_open_.snap(0);s.support_open_.snap(0);s.search_prompt_.dismiss();s.search_page_=false;
        s.settings_=s.credits_=s.connection_panel_=s.year_guide_=s.detail_=s.gallery_=s.screening_=s.playlist_active_=s.object_inspect_=s.experience_active_=s.chapters_=false;
        s.volumes_open_=s.desktop_video_open_=false;s.panel_.snap(0);s.story_open_.snap(0);s.gallery_open_.snap(0);s.screening_open_.snap(0);s.object_open_.snap(0);s.year_panel_.snap(0);
        s.desktop_links_.clear();s.desktop_scroll_areas_.clear();s.desktop_scroll_dragging_=false;
        check(!s.trophy_curator_preview_,"normal app initialization does not enable the curator preview");
        if(s.visible_.size()<3){check(false,"a real catalogue is loaded");return false;}
        s.history_focus_=false;s.filter_=0;s.rebuild();s.focus_=int(s.visible_.size()/2);s.timeline_.snap(float(s.focus_));s.changed();
        DesktopVideoSettings video;video.width=1280;video.height=800;
        s.set_desktop_video_modes({{1280,720},{1280,800},{1920,1080},{1920,1200},{2560,1440}},video);
        check(s.desktop_modes_.size()==3&&std::all_of(s.desktop_modes_.begin(),s.desktop_modes_.end(),[](const auto&m){return m.width*9==m.height*16;}),"the resolution list contains only real 16:9 choices");
        check(s.desktop_video_draft_.width==1280&&s.desktop_video_draft_.height==720,"an old non-16:9 preference has a valid draft choice");
        {auto i=input();i.desktop_escape_pressed=true;i.pressed=hui::action_bit(hui::Action::back);send(i);}s.panel_.snap(1);
        check(s.settings_,"Escape opens Options on the main timeline");
        s.setting_=0;nav(hui::Direction::up);check(s.setting_==s.desktop_preference_count()-1,"Options wraps from Video to Exit");
        nav(hui::Direction::down);check(s.setting_==0,"Options wraps from Exit to Video");
        {auto i=input();i.desktop_escape_pressed=true;i.pressed=hui::action_bit(hui::Action::back);send(i);}check(!s.settings_,"Escape closes an open panel");
        s.settings_=true;s.panel_.snap(1);click(850,500);check(!s.settings_,"a click outside Options dismisses it");s.panel_.snap(0);
        check(!s.desktop_pointer_target(1050,80)&&!s.desktop_pointer_target(1200,80)&&!s.desktop_pointer_target(832,79)&&s.desktop_pointer_target(665,79),"the header contains only the route switch");
        const int focus=s.focus_;wheel(900,400,-1);check(s.focus_==focus,"wheel outside the timeline does not change the exhibit");
        wheel(960,850,-1);check(s.focus_==focus+1,"wheel down over the gaming rail advances one exhibit");wheel(960,850,1);check(s.focus_==focus,"wheel up over the gaming rail goes back");
        s.detail_=true;s.story_open_.snap(1);s.prepare_story();s.story_focus_=0;s.story_position_.snap(0);s.scroll_.snap(0);s.scroll_max_=900;
        s.desktop_add_scroll_area(Screen::DesktopScrollTarget::content,{1100,350,560,450},{1674,350,6,450},900,0);
        wheel(1300,450,-1);check(s.scroll_.target==105&&s.story_focus_==0,"wheel over right-column text scrolls text instead of changing cards");
        s.scroll_.snap(0);nav(hui::Direction::down);check(s.scroll_.target==145&&s.story_focus_==0,"keyboard Down scrolls long exhibit text");nav(hui::Direction::up);check(s.scroll_.target==0,"keyboard Up scrolls long exhibit text back");
        click(1677,370);{auto i=input();i.pointer.available=true;i.pointer.primary_held=true;i.pointer.x=1677;i.pointer.y=900;send(i);}
        check(s.desktop_scroll_dragging_&&s.scroll_.value==900,"dragging a scrollbar follows the pointer and clamps at the end");
        {auto i=input();i.pointer.available=true;i.pointer.primary_released=true;send(i);}check(!s.desktop_scroll_dragging_,"releasing the pointer ends scrollbar dragging");
        s.scroll_.snap(900);wheel(1300,450,-1);check(s.story_focus_==0,"a text field still consumes wheel input at its end");
        if(s.story_cards_.size()>1){wheel(300,500,-1);check(s.story_focus_==1,"wheel over the image side changes the story card");}
        s.detail_=false;s.story_open_.snap(0);s.desktop_scroll_areas_.clear();
        send(input());s.filter_trigger_down_={false,false};press(hui::Action::page_next);
        check(s.active_filter()==1,"R1 changes the main timeline filter");send(input());press(hui::Action::page_prev);
        check(s.active_filter()==0,"L1 changes the main timeline filter back");send(input());
        s.focus_=int(s.visible_.size()/2);s.timeline_.snap(float(s.focus_));const int old_decade=s.current()->year/10;
        press(hui::Action::jump_next);check(s.current()->year/10>old_decade&&s.active_filter()==0,"R2 jumps the main timeline decade without changing filter");
        s.year_notice_age_=.35f;const auto notice_age=s.year_notice_age_;s.overlay_.clear();s.draw_filter_notice();
        const float notice_alpha=s.overlay_.instances().empty()?0:s.overlay_.instances().front().color_top[3];
        send(input());press(hui::Action::jump_prev);s.overlay_.clear();s.draw_filter_notice();
        const float repeated_alpha=s.overlay_.instances().empty()?0:s.overlay_.instances().front().color_top[3];
        check(s.current()->year/10<old_decade+1&&s.active_filter()==0,"L2 jumps the main timeline decade without changing filter");
        check(s.year_notice_time_==1.35f&&s.year_notice_age_==notice_age&&notice_alpha>0&&repeated_alpha==notice_alpha,"spaced repeated decade presses extend the hold without restarting the visible overlay fade");
        s.open_year_guide();s.year_panel_.snap(1);
        if(!s.years_.empty()){
            s.year_focus_=0;s.year_position_.snap(0);nav(hui::Direction::up);check(s.year_focus_==int(s.years_.size())-1,"the year atlas wraps to its last year");
            nav(hui::Direction::down);check(s.year_focus_==0,"the year atlas wraps back to its first year");
            const int underlying=s.focus_,history=s.history_focus_index_,filter=s.active_filter();const auto id=s.current()->id;
            for(const auto style:{hui::DesktopControllerStyle::dualsense,hui::DesktopControllerStyle::generic,hui::DesktopControllerStyle::keyboard_mouse}){
                for(const auto action:{hui::Action::page_next,hui::Action::page_prev,hui::Action::jump_next,hui::Action::jump_prev}){
                    send(input());const bool forward=action==hui::Action::page_next||action==hui::Action::jump_next;
                    s.year_focus_=forward?0:int(s.years_.size())-1;const int decade=s.years_[size_t(s.year_focus_)]/10;
                    auto i=input();i.controller_style=style;i.pressed=hui::action_bit(action);send(i);
                    check(forward?s.years_[size_t(s.year_focus_)]/10>decade:s.years_[size_t(s.year_focus_)]/10<decade,"both guide shoulder pairs jump decades for PlayStation/Xbox/keyboard");
                    check(s.focus_==underlying&&s.history_focus_index_==history&&s.current()->id==id&&s.active_filter()==filter&&s.year_notice_time_==0&&!s.year_notice_tick_,"guide decade input preserves the museum entry/filter and emits no year overlay");
                }
            }
            s.year_notice_time_=1;s.overlay_.clear();s.draw_filter_notice();check(s.overlay_.instances().empty(),"the guide suppresses any in-flight timeline notice");s.year_notice_time_=s.year_notice_age_=0;
        }
        click(1900,500);check(!s.year_guide_,"a click outside the year atlas dismisses it");s.year_panel_.snap(0);
        {hui::ui::Feedback f;s.open_search(f);}s.search_prompt_.update(1.f/60);
        {auto i=input();i.text_utf8="Museum";send(i);}check(s.search_prompt_.text()=="Museum","the original search prompt accepts physical keyboard text");
        const auto key=s.search_prompt_.keyboard.key_rect(0,0);click(key.cx(),key.cy());
        check(s.search_prompt_.is_open()&&s.search_prompt_.text()=="Museum1","clicking a real virtual key adds to physical keyboard input");
        check(s.desktop_pointer_target(key.cx(),key.cy()),"native virtual keys are actual interactive pointer targets");
        {const auto cancel=s.desktop_search_button_bounds(0);click(cancel.cx(),cancel.cy());}check(!s.search_prompt_.is_open(),"the original prompt Cancel button closes search");
        {
            std::string query;
            for(const auto&entry:s.catalog_.entries)if(search_collection(s.catalog_,s.history_catalog_all_,entry.title).size()==1){query=entry.title;break;}
            check(!query.empty(),"the real catalogue supplies a unique search fixture");
            {hui::ui::Feedback f;s.open_search(f);}auto physical=input();physical.text_select_all=true;physical.text_utf8=query;physical.text_submit=true;send(physical);
            check(s.search_page_&&s.search_results_.size()==1&&!s.detail_,"physical Enter shows a lone result in the list without opening it");
            {hui::ui::Feedback f;s.open_search(f);}const auto done=s.desktop_search_button_bounds(1);click(done.cx(),done.cy());
            check(s.search_page_&&s.search_results_.size()==1&&!s.detail_,"virtual keyboard Search also keeps a lone result in the list");
            s.search_page_=false;s.search_open_.snap(0);
        }
        s.connection_panel_=true;s.desktop_links_.clear();s.desktop_add_link({1174,806,600,36},"https://www.google.com/device");click(1300,824);std::string url;
        check(s.take_desktop_url_request(url)&&url=="https://www.google.com/device"&&!s.take_desktop_url_request(url),"clicking the visible Google device URL emits one bounded browser request");s.connection_panel_=false;s.desktop_links_.clear();
        s.gallery_=true;s.gallery_overlay_age_=9;s.idle_=9;
        hui::ui::ViewerImage picture;picture.aspect=16.f/9;picture.pixel_width=3840;
        s.viewer_.style.frame=s.viewer_.style.caption=s.viewer_.style.filmstrip=false;s.viewer_.set_images({picture});s.viewer_.set_bounds({0,0,1920,1080});s.viewer_.set_zoom(2,true);
        const auto before=s.viewer_.picture_rect();{auto i=input();i.pointer.available=true;i.pointer.primary_held=true;i.pointer.moved=true;i.pointer.delta_x=120;i.pointer.delta_y=70;send(i);}
        auto after=s.viewer_.picture_rect();check(std::abs(after.x-before.x-120)<.01f&&std::abs(after.y-before.y-70)<.01f,"mouse drag moves a 2x image immediately by exactly its logical pixel delta");
        check(s.gallery_overlay_age_==0&&s.idle_==0,"fresh pointer movement shows the existing image hint fade again");
        s.viewer_.set_zoom(1,true);const auto fitted=s.viewer_.picture_rect();s.viewer_.pan_pixels(1000,-1000);after=s.viewer_.picture_rect();
        check(std::abs(after.x-fitted.x)<.01f&&std::abs(after.y-fitted.y)<.01f,"a fitted 1x image cannot be dragged beyond its bounds");
        s.viewer_.set_zoom(2,true);s.viewer_.pan_pixels(100000,100000);after=s.viewer_.picture_rect();
        check(std::abs(after.x)<.01f&&std::abs(after.y)<.01f,"large pointer drags stop exactly at the crop edge");
        s.viewer_.set_zoom(2,true);s.viewer_.pan_pixels(-100000,-100000);after=s.viewer_.picture_rect();
        check(std::abs(after.x+after.w-1920)<.01f&&std::abs(after.y+after.h-1080)<.01f,"opposite drags clamp to the far crop edge");
        s.viewer_.set_zoom(1,true);s.viewer_.set_zoom(2,true);const auto logical_before=s.viewer_.picture_rect();s.viewer_.pan_pixels(240.f/2,140.f/2);after=s.viewer_.picture_rect();
        check(std::abs(after.x-logical_before.x-120)<.01f&&std::abs(after.y-logical_before.y-70)<.01f,"4K physical deltas scaled into 1920x1080 canvas units remain 1:1 on screen");
        {auto i=input();i.pointer.available=true;i.pointer.wheel_y=1;hui::ui::Feedback f;s.handle(i,f);check(f.cues.empty(),"mouse-wheel zoom produces no sound cue");}
        const auto controls=s.desktop_controls();check(std::none_of(controls.begin(),controls.end(),[](const auto&c){return c.command==104||c.command==105;}),"keyboard and mouse hints offer no +/- zoom button");
        {auto i=input();i.controller_style=hui::DesktopControllerStyle::generic;send(i);}check(hui::ui::control_device()==hui::ui::ControlDevice::xbox,"generic controllers select Xbox glyphs");
        {const auto controls=s.desktop_controls();check(std::any_of(controls.begin(),controls.end(),[](const auto&c){return c.command==104;}),"controller zoom trigger hints remain available");}
        {auto i=input();i.controller_style=hui::DesktopControllerStyle::dualsense;send(i);}check(hui::ui::control_device()==hui::ui::ControlDevice::playstation,"DualSense selects PlayStation glyphs");
        s.gallery_=false;s.gallery_open_.snap(0);s.settings_=true;s.year_guide_=true;s.detail_=true;s.history_focus_=true;
        check(s.desktop_navigation_feedback_state()==15,"the platform can detect only meaningful navigation state changes");
        s.settings_=s.year_guide_=s.detail_=s.history_focus_=false;
        {
            using A=ApplicationUpdater::Phase;using D=DatabaseUpdater::Phase;
            s.application_combined_check_=true;s.application_dialog_=true;s.application_open_.snap(1);s.database_dialog_=false;
            s.application_state_.phase=A::current;s.database_state_.phase=D::available;
            check(s.application_action_count()==2&&std::string(s.application_action_label(1))=="Update","one composite sheet offers the available database update beside a current app");
            s.overlay_.clear();s.draw_application_update();check(!s.overlay_.instances().empty()&&!s.database_dialog_,"the composite status sheet renders without opening a second database popup");
            s.application_state_.phase=A::available;s.database_state_.phase=D::available;
            check(s.application_action_count()==2&&std::string(s.application_action_label(1))=="Update","two available updates share one Update action");
            s.application_state_.phase=A::current;s.database_state_.phase=D::current;
            check(s.application_action_count()==1&&std::string(s.application_action_label(0))=="Done","current app and database produce one up-to-date result");
            s.database_state_.phase=D::failed;
            check(s.application_action_count()==2&&std::string(s.application_action_label(1))=="Try again","a failed database check remains retryable beside a current app");
            s.database_state_.phase=D::downloading;
            check(s.application_action_count()==1&&std::string(s.application_action_label(0))=="Continue exploring","a database download uses one coherent progress result");
            s.database_state_.phase=D::ready;
            check(s.application_action_count()==1&&!s.take_application_restart_request(),"a prepared database alone never launches the application restart helper");
            s.application_state_.phase=A::ready;s.database_state_.phase=D::current;
            check(s.application_action_count()==2&&std::string(s.application_action_label(1))=="Restart now","a verified app update offers restart in the same composite sheet");
            s.application_dialog_=false;s.application_open_.snap(0);s.application_combined_check_=false;
            s.application_state_.phase=A::idle;s.database_state_.phase=D::idle;
        }
        {
            // Fixture thresholds are lower; unlocks still come only from the
            // real progress commit, persistence and drain path.
            const auto file=s.data_+"/navigation-toast-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".dat";
            auto saved=std::move(s.trophies_);s.trophies_=std::make_unique<Trophies>(file);s.trophies_->load();
            auto definitions=make_trophy_definitions();definitions.resize(3);definitions[0].target=1;definitions[1].target=definitions[2].target=2;
            s.trophies_->setDefinitions(definitions);s.trophy_fallback_queue_.clear();s.trophy_fallback_time_=0;s.trophy_fallback_sound_=false;
            s.trophies_->visit("fixture-one");s.update_trophies();
            check(s.trophy_fallback_time_==5&&s.trophy_fallback_current_.id==definitions[0].id,"an earned fixture trophy is routed into the real PC toast");
            check(s.take_trophy_sound()&&!s.take_trophy_sound(),"a new trophy emits exactly one consumable sound");
            s.dt_=.25f;s.update_trophies();check(s.trophy_fallback_time_>0&&s.trophy_fallback_time_<5,"the earned trophy remains visible through its normal lifetime");
            s.dt_=5.1f;s.update_trophies();check(s.trophy_fallback_time_==0&&s.trophy_fallback_queue_.empty(),"the PC toast expires without repeating");
            {Trophies reloaded(file);reloaded.load();reloaded.setDefinitions(definitions);check(!reloaded.visit("fixture-one")&&reloaded.drainUnlocks().empty(),"persisted unlocks do not enqueue a duplicate toast");}
            s.dt_=1.f/60;s.trophies_->visit("fixture-two");s.update_trophies();
            check(s.trophy_fallback_time_>0&&!s.trophy_fallback_queue_.empty(),"multiple earned fixture trophies queue behind the visible one");
            s.settings_=true;s.panel_.snap(1);for(int row=0;row<s.desktop_preference_count();++row)if(s.desktop_preference_setting(row)==reset_trophies_setting)s.setting_=row;
            press(hui::Action::confirm);check(s.trophy_fallback_queue_.empty()&&s.trophy_fallback_time_==0&&!s.take_trophy_sound(),"Reset trophies clears queued PC toasts, lifetime and pending sound");
            s.settings_=false;s.panel_.snap(0);s.trophies_=std::move(saved);
        }
        std::fprintf(stderr,"[Desktop navigation] RESULT %d passed, %d failed\n",passed,failed);return !failed;
    }
};
}
#endif
