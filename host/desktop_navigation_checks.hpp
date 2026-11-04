// Pixel Museum - focused pointer, scrolling and PC navigation regressions.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#if defined(MUSEUM_DESKTOP)
#include "museum/screen.hpp"
#include "museum/general_credits.hpp"
#include "museum/localization.hpp"
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
        const auto pad_press=[&](hui::Action a){auto i=input();i.controller_style=hui::DesktopControllerStyle::dualsense;i.pressed=hui::action_bit(a);send(i);};
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
        s.desktop_controller_style_=hui::DesktopControllerStyle::keyboard_mouse;s.boot_time_=1;
        check(s.desktop_controls().empty()&&!s.desktop_pointer_target(150,1014),"the startup animation displays no Continue hint or footer hit target");
        s.collection_pending_=true;
        {const auto hints=s.desktop_controls();check(hints.size()==1&&hints.front().command==int(hui::Action::back),"startup collection validation only displays a close hint");}
        s.collection_pending_=false;s.boot_time_=5;
        if(s.visible_.size()<3){check(false,"a real catalogue is loaded");return false;}
        s.history_focus_=false;s.filter_=0;s.rebuild();s.focus_=int(s.visible_.size()/2);s.timeline_.snap(float(s.focus_));s.changed();
        const DesktopDisplayMode ultrawide_presets[]={{2560,1080},{3440,1440},{3840,1600},{5120,2160}};
        check(std::all_of(std::begin(ultrawide_presets),std::end(ultrawide_presets),[&](auto mode){
            return desktop_aspect(mode.width,mode.height)=="21:9"&&
                   std::find(s.desktop_modes_.windowed.begin(),s.desktop_modes_.windowed.end(),mode)!=s.desktop_modes_.windowed.end();
        })&&!desktop_resolution_listed({1440,576})&&desktop_aspect(1920,1080)=="16:9"&&
        desktop_aspect(5120,1440)=="32:9"&&desktop_aspect(5120,1600)=="32:10",
        "video settings include all four windowed 21:9 presets and omit low ultrawide modes");
        DesktopVideoSettings video;video.width=1280;video.height=800;
        s.set_desktop_video_modes({{{1280,720},{1920,1080},{3440,1440}},
            {std::begin(desktop_window_presets),std::end(desktop_window_presets)}});
        s.init_desktop_video_settings(video);
        check(s.desktop_video_draft_.width==1280&&s.desktop_video_draft_.height==720,"an old unsupported preference has a valid draft choice");
        {auto i=input();i.desktop_escape_pressed=true;i.pressed=hui::action_bit(hui::Action::back);send(i);}s.panel_.snap(1);
        check(s.settings_,"Escape opens Options on the main timeline");
        s.setting_=0;nav(hui::Direction::up);check(s.setting_==s.desktop_preference_count()-1,"Options wraps from Video to Exit");
        nav(hui::Direction::down);check(s.setting_==0,"Options wraps from Exit to Video");
        {auto i=input();i.desktop_escape_pressed=true;i.pressed=hui::action_bit(hui::Action::back);send(i);}check(!s.settings_,"Escape closes an open panel");
        s.settings_=true;s.panel_.snap(1);click(850,500);check(!s.settings_,"a click outside Options dismisses it");s.panel_.snap(0);
        check(!s.desktop_pointer_target(1050,80)&&!s.desktop_pointer_target(1200,80)&&!s.desktop_pointer_target(832,79)&&!s.desktop_pointer_target(665,79),"the former header shortcuts and route switch are not pointer targets");
        const int focus=s.focus_;wheel(900,400,-1);check(s.focus_==focus,"wheel outside the timeline does not change the exhibit");
        wheel(960,850,-1);check(s.focus_==focus+1,"wheel down over the gaming rail advances one exhibit");wheel(960,850,1);check(s.focus_==focus,"wheel up over the gaming rail goes back");
        if(s.visible_.size()>=9){
            const int old_width=s.output_width_,old_height=s.output_height_;
            s.output_width_=3440;s.output_height_=1440;
            s.timeline_motion_.reset(focus,s.timeline_);
            const auto canvas=s.canvas_bounds();
            check(std::abs(canvas.x+330)<.01f&&std::abs(canvas.cx()-960)<.01f&&canvas.h==1080,"ultrawide grows the canvas symmetrically around the original exhibit coordinates");
            s.panel_.snap(1);
            check(s.options_panel_x()+s.options_panel_width()==canvas.x+canvas.w&&s.options_panel_width()==810,
                "Options retains its original width and reaches the ultrawide right edge");
            s.panel_.snap(0);
            check(s.desktop_pointer_target(-250,850),"the extra ultrawide stop is an interactive target");
            wheel(-250,850,-1);check(s.focus_==focus+1,"wheel over the ultrawide extension navigates the rail");
            s.focus_=focus;s.timeline_motion_.reset(focus,s.timeline_);s.changed(true);
            s.output_width_=old_width;s.output_height_=old_height;
        }
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
        if(s.history_catalog_.entries.size()>=3){
            s.history_focus_=true;s.history_focus_index_=int(s.history_catalog_.entries.size()/2);
            s.history_position_.snap(float(s.history_focus_index_));s.history_transition_=false;s.fade_=1;
            s.scroll_.snap(0);s.scroll_max_=900;
            s.desktop_add_scroll_area(Screen::DesktopScrollTarget::content,{100,402,640,390},{748,402,6,390},900,0);
            const int history=s.history_focus_index_;
            wheel(300,450,-1);
            check(s.scroll_.target==105&&s.history_focus_index_==history,"wheel over cultural text scrolls the text without changing its entry");
            nav(hui::Direction::up);
            check(s.scroll_.target==105&&s.history_focus_index_==history,"Up on the cultural timeline does not scroll the text");
            nav(hui::Direction::right);check(s.history_focus_index_==history+1&&s.scroll_.target==0,"Right advances to the next cultural entry");
            nav(hui::Direction::left);check(s.history_focus_index_==history,"Left returns to the previous cultural entry");
            wheel(960,200,-1);check(s.history_focus_index_==history+1,"wheel over the cultural rail still changes entries");
            nav(hui::Direction::down);check(!s.history_focus_,"Down leaves the cultural timeline instead of scrolling the text");
            s.history_transition_=false;s.fade_=1;s.desktop_scroll_areas_.clear();s.scroll_max_=0;
        }
        send(input());s.filter_trigger_down_={false,false};pad_press(hui::Action::page_next);
        check(s.active_filter()==1,"R1 changes the main timeline filter");send(input());pad_press(hui::Action::page_prev);
        check(s.active_filter()==0,"L1 changes the main timeline filter back");send(input());
        const auto hint=[](const auto& hints,std::string_view key){
            return std::find_if(hints.begin(),hints.end(),[&](const auto& control){return control.key==key;});
        };
        const auto hints=s.desktop_controls();
        const auto filter_hint=hint(hints,"F"),search_hint=hint(hints,"S");
        check(filter_hint!=hints.end()&&filter_hint->label==i18n::tr("Filter")&&search_hint!=hints.end()&&search_hint->label==i18n::tr("Search"),"keyboard hints map F to Filter and S to Search");
        if(filter_hint!=hints.end()){
            click(filter_hint->bounds.cx(),filter_hint->bounds.cy());
            check(s.active_filter()==1,"clicking the F hint applies the main timeline filter");
        }
        s.filter_=0;s.rebuild(false);
        {auto i=input();i.desktop_filter_pressed=true;send(i);}
        check(s.active_filter()==1,"physical F changes the main timeline filter");
        s.filter_=0;s.rebuild(false);
        s.focus_=int(s.visible_.size()/2);s.timeline_.snap(float(s.focus_));const int old_decade=s.current()->year/10;
        pad_press(hui::Action::jump_next);check(s.current()->year/10>old_decade&&s.active_filter()==0,"R2 jumps the main timeline decade without changing filter");
        s.year_notice_age_=.35f;const auto notice_age=s.year_notice_age_;s.overlay_.clear();s.draw_filter_notice();
        const float notice_alpha=s.overlay_.instances().empty()?0:s.overlay_.instances().front().color_top[3];
        send(input());pad_press(hui::Action::jump_prev);s.overlay_.clear();s.draw_filter_notice();
        const float repeated_alpha=s.overlay_.instances().empty()?0:s.overlay_.instances().front().color_top[3];
        check(s.current()->year/10<old_decade+1&&s.active_filter()==0,"L2 jumps the main timeline decade without changing filter");
        check(s.year_notice_time_==1.35f&&s.year_notice_age_==notice_age&&notice_alpha>0&&repeated_alpha==notice_alpha,"spaced repeated decade presses extend the hold without restarting the visible overlay fade");
        send(input());
        {
            const auto visible_hints=s.desktop_controls();const auto decade_hint=hint(visible_hints,"Z");
            check(decade_hint!=visible_hints.end()&&decade_hint->second_key=="C"&&decade_hint->label==i18n::tr("Decade"),"Z and C share a Decade label but have distinct keycaps");
            const auto click_decade=[&](bool forward){
                const auto visible=s.desktop_controls();const auto control=hint(visible,"Z");
                if(control==visible.end()||control->second_key!="C")return false;
                const auto width=[&](std::string_view key){return std::max(24.f,s.fonts_.mono.font->measure(key,16)+16);};
                const float offset=forward?width(control->key)+8+width(control->second_key)*.5f:width(control->key)*.5f;
                const float x=control->bounds.x+8+offset*control->scale,y=control->bounds.cy();
                const bool clickable=s.desktop_pointer_target(x,y);click(x,y);return clickable;
            };
            const int decade=s.current()->year/10;
            const bool clicked_next=click_decade(true);const int advanced=s.current()->year/10;
            check(clicked_next&&advanced>decade,"clicking the C keycap jumps forward by decade");
            const bool clicked_previous=click_decade(false);
            check(clicked_previous&&s.current()->year/10<advanced&&s.active_filter()==0,"clicking the Z keycap jumps back without changing the filter");
        }
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
        {
            auto shortcut=input();shortcut.search_pressed=true;
            s.experience_active_=true;send(shortcut);
            check(s.experience_active_&&!s.search_prompt_.is_open(),"S stays inside an active experience");
            s.experience_active_=false;s.experience_open_.snap(.5f);send(shortcut);
            check(!s.search_prompt_.is_open(),"S waits for the experience to close");
            s.experience_open_.snap(0);
            s.year_guide_=s.guide_trophies_=s.trophy_pin_open_=true;send(shortcut);
            check(s.trophy_pin_open_&&!s.search_prompt_.is_open(),"S stays inside the 3D pin viewer");
            s.year_guide_=s.guide_trophies_=s.trophy_pin_open_=false;
        }
        {const auto visible=s.desktop_controls();const auto search=hint(visible,"S");if(search!=visible.end())click(search->bounds.cx(),search->bounds.cy());}
        check(s.search_prompt_.is_open(),"clicking the S hint opens search");
        s.search_prompt_.update(1.f/60);
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
            auto held_enter=input();held_enter.pressed=held_enter.held=hui::action_bit(hui::Action::confirm);send(held_enter);
            check(s.search_page_&&s.search_results_.size()==1&&!s.detail_,"Enter held through the change from text mode does not open the first result");
            send(input());
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
            check(s.trophy_fallback_time_==6.f&&s.trophy_fallback_current_.id==definitions[0].id,"an earned fixture trophy starts a six-second PC toast");
            check(s.take_trophy_sound()&&!s.take_trophy_sound(),"a new trophy emits exactly one consumable sound");
            s.dt_=.25f;s.update_trophies();check(s.trophy_fallback_time_>0&&s.trophy_fallback_time_<6.f,"the earned trophy remains visible through its normal lifetime");
            DatabaseUpdater::Snapshot database;database.phase=DatabaseUpdater::Phase::ready;database.revision=2;
            ApplicationUpdater::Snapshot application;application.phase=ApplicationUpdater::Phase::ready;application.version="test-ready";
            s.observe_database_update(database);s.observe_application_update(application);
            check(!s.database_dialog_&&!s.application_dialog_&&s.database_completion_notice_==6.f&&s.application_completion_notice_==6.f,"both background completion notices can coexist with an earned trophy");
            s.database_completion_notice_=s.application_completion_notice_=5.75f;
            const auto panels=[&](){
                s.renderer_.begin();s.render_notifications();
                std::vector<std::pair<float,float>> bounds;
                for(const auto& shape:s.overlay_.instances()){
                    if(shape.rect[0]==1160&&shape.rect[2]==680&&shape.color_top[3]>0)
                        bounds.emplace_back(shape.rect[1],shape.rect[1]+shape.rect[3]);
                }
                std::sort(bounds.begin(),bounds.end());return bounds;
            };
            const auto notices=panels();
            check(notices.size()==3&&notices[0].second<notices[1].first&&notices[1].second<notices[2].first,"the trophy, database and application notices have separate visible panels");
            s.history_transition_=true;s.fade_=.4f;
            check(panels()==notices,"notification panels keep the same bounds while the timeline transitions");
            s.history_transition_=false;s.fade_=1;s.database_completion_notice_=s.application_completion_notice_=0;
            s.dt_=6.1f;s.update_trophies();check(s.trophy_fallback_time_==0&&s.trophy_fallback_queue_.empty(),"the PC toast expires without repeating");
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
