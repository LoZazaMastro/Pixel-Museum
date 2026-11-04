// Pixel Museum - exercise desktop input against the production screen.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#if defined(MUSEUM_DESKTOP)
#include "museum/screen.hpp"
#include "museum/pixel_palette.hpp"
#include "museum/general_credits.hpp"
#include "museum/preferences_layout.hpp"
#include "host/desktop_navigation_checks.hpp"
#include <cstdlib>
#include <cmath>
#include <cstdio>
namespace museum {
struct DesktopInputInspection {
    static bool run(Screen&s){
        if(std::getenv("MUSEUM_FOCUSED_UI"))return DesktopNavigationInspection::run(s);
        int passed=0,failed=0;
        const auto check=[&](bool good,const char*message){std::fprintf(stderr,"[Desktop UI] %s: %s\n",good?"PASS":"FAIL",message);good?++passed:++failed;};
        s.collection_pending_=false;s.onboarding_=s.language_choice_=s.theme_choice_=false;
        s.database_auto_checked_=true;
        s.application_auto_checked_=true;
        s.onboarding_leaving_=false;s.boot_time_=5;s.dt_=1.f/60;s.settings_=s.credits_=s.connection_panel_=false;
        s.gallery_=s.screening_=s.detail_=s.object_inspect_=s.year_guide_=s.chapters_=false;s.volumes_open_=false;
        s.panel_.snap(0);s.story_open_.snap(0);s.gallery_open_.snap(0);s.screening_open_.snap(0);s.object_open_.snap(0);s.year_panel_.snap(0);
        const auto input=[](){hui::InputFrame i;i.connected=true;i.controller_style=hui::DesktopControllerStyle::keyboard_mouse;return i;};
        const auto send=[&](hui::InputFrame i){hui::ui::Feedback feedback;s.handle(i,feedback);};
        const auto press=[&](hui::Action action){auto i=input();i.pressed=hui::action_bit(action);send(i);};
        const auto click=[&](float x,float y){auto i=input();i.pointer.available=true;i.pointer.primary_pressed=true;i.pointer.x=x;i.pointer.y=y;send(i);};
        if(s.visible_.size()<3){check(false,"catalogue has enough entries for navigation");return false;}
        s.history_focus_=false;s.focus_=int(s.visible_.size()/2);s.timeline_.snap(float(s.focus_));s.timeline_motion_.reset(s.focus_,s.timeline_);s.history_transition_=false;s.fade_=1;
        const int initial=s.focus_;
        {auto i=input();i.pointer.available=true;i.pointer.x=960;i.pointer.y=850;i.pointer.wheel_y=-1;send(i);}check(s.focus_==initial+1,"wheel down over the rail advances the timeline");
        {auto i=input();i.pointer.available=true;i.pointer.x=960;i.pointer.y=850;i.pointer.wheel_y=1;send(i);}check(s.focus_==initial,"wheel up over the rail moves back");
        s.timeline_.snap(float(s.focus_));click(1490,850);check(s.focus_==initial+1,"clicking a visible timeline stop selects that stop");
        s.timeline_.snap(float(s.focus_));click(300,400);check(s.detail_,"clicking the exhibit title opens its story");
        s.detail_=false;s.story_open_.snap(0);s.timeline_.snap(float(s.focus_));
        check(std::string(s.desktop_preference_label(0))=="Video"&&std::string(s.desktop_preference_label(1))=="Audio"&&std::string(s.desktop_preference_label(s.desktop_preference_count()-1))=="Exit","Video and Audio are first, with Exit last in Options");
        {bool removed=true;for(int n=0;n<s.desktop_preference_count();++n)if(std::string(s.desktop_preference_label(n))=="Remove downloaded data")removed=false;check(removed,"PC Options excludes the PS5 downloaded-data removal action");}
        check(std::string(preference_labels[size_t(database_update_setting)])=="Check for updates"&&s.desktop_preference_setting(6)==database_update_setting,"the shared update action is present in PC and PS5 Options");
        DesktopVideoSettings initial_video;initial_video.width=1280;initial_video.height=720;
        s.set_desktop_video_modes({{{1280,720},{1920,1080}},{{1280,720},{1920,1080}}});
        s.init_desktop_video_settings(initial_video);
        press(hui::Action::menu);s.panel_.snap(1);click(1500,240);check(s.desktop_video_open_,"the first Options row opens Video");
        click(1800,292);click(1800,396);click(1800,500);click(1800,604);click(1500,708);
        DesktopVideoSettings requested;
        check(s.take_desktop_video_request(requested)&&requested.width==1920&&requested.height==1080&&requested.fullscreen&&!requested.borderless&&!requested.vsync&&requested.frame_limit==120,"Video controls produce one concrete exclusive-fullscreen apply request");
        check(!s.take_desktop_video_request(requested),"an apply request is consumed once");
        s.set_desktop_video_settings_applied(requested);
        click(1800,396);check(s.desktop_video_draft_.fullscreen&&s.desktop_video_draft_.borderless,"display mode advances from Fullscreen to Borderless fullscreen");
        click(1800,292);check(s.desktop_video_draft_.width==1920&&s.desktop_video_draft_.height==1080,"borderless resolution keeps the saved window and exclusive dimensions");
        click(1500,708);check(s.take_desktop_video_request(requested)&&requested.fullscreen&&requested.borderless,"Apply preserves the borderless display request");s.set_desktop_video_settings_applied(requested);
        click(1800,396);check(!s.desktop_video_draft_.fullscreen&&!s.desktop_video_draft_.borderless,"display mode advances from Borderless fullscreen to Windowed");
        click(1800,396);check(s.desktop_video_draft_.fullscreen&&!s.desktop_video_draft_.borderless,"display mode wraps from Windowed to Fullscreen");
        {auto i=input();i.nav=hui::Direction::left;send(i);send(i);}check(s.desktop_video_draft_.fullscreen&&s.desktop_video_draft_.borderless,"left navigation reverses the same ordered display modes");
        press(hui::Action::back);check(!s.desktop_video_open_&&s.settings_,"Back returns from Video to Options");
        click(1500,preference_row_baseline(1));check(s.volumes_open_,"the second Options row opens Audio");
        click(1175+650*.37f,263);check(std::abs(s.master_volume_-.37f)<.001f,"clicking the volume track sets its actual value");
        press(hui::Action::back);check(s.settings_&&!s.volumes_open_&&s.setting_==1,"Back returns from Audio to its Options row");
        press(hui::Action::back);s.panel_.snap(0);
        {auto i=input();i.search_pressed=true;send(i);}check(s.wants_text_input(),"the desktop search shortcut focuses native text input");
        {auto i=input();i.text_utf8="café";send(i);}
        {auto i=input();i.text_left=true;send(i);}
        {auto i=input();i.text_backspace=true;send(i);}check(s.search_prompt_.text()=="caé","native backspace edits a UTF-8 character at the caret");
        {auto i=input();i.text_delete=true;send(i);}check(s.search_prompt_.text()=="ca","native Delete removes the following UTF-8 character");
        {auto i=input();i.text_select_all=true;i.text_utf8="1985";send(i);}check(s.search_prompt_.text()=="1985","native select-all replaces the search text");
        {auto i=input();i.text_submit=true;send(i);}check(!s.wants_text_input()&&s.search_page_&&s.search_query_=="1985","native Enter submits the physical keyboard query");
        s.search_page_=false;s.search_open_.snap(0);s.year_guide_=false;s.year_panel_.snap(0);s.settings_=true;s.panel_.snap(1);
        s.desktop_controller_style_=hui::DesktopControllerStyle::generic;
        {const auto controls=s.desktop_controls();check(!controls.empty()&&controls.front().key=="B","generic controllers show generic button names");}
        s.desktop_controller_style_=hui::DesktopControllerStyle::dualsense;
        {const auto controls=s.desktop_controls();check(!controls.empty()&&controls.front().key.empty(),"DualSense controls use PlayStation glyphs");}
        {
            auto drawing=make_study("pixels");hui::gfx::DrawList list;hui::ui::Feedback feedback;
            const auto cell=[&](int x,int y){
                list.clear();drawing->draw(list,s.fonts_,{0,0,1000,540},hui::gfx::Color::rgb(0xdc9b79));
                for(const auto&instance:list.instances())if(std::abs(instance.rect[0]-(73+x*19))<.01f&&std::abs(instance.rect[1]-(143+y*19))<.01f&&std::abs(instance.rect[2]-19)<.01f&&std::abs(instance.rect[3]-19)<.01f)return hui::gfx::Color{instance.color_top[0],instance.color_top[1],instance.color_top[2],instance.color_top[3]};
                return hui::gfx::Color{};
            };
            const auto white=[](hui::gfx::Color c){return c.r>.999f&&c.g>.999f&&c.b>.999f;};
            check(drawing&&white(cell(0,0)),"the mouse workshop starts with a white canvas");
            hui::PointerInput pointer;pointer.available=true;pointer.primary_pressed=true;pointer.x=82.5f;pointer.y=152.5f;
            check(drawing->desktop_pointer(pointer,feedback)&&!white(cell(0,0)),"a left click paints the exact grid cell");
            pointer.primary_pressed=false;pointer.primary_held=true;pointer.moved=true;pointer.x=101.5f;drawing->desktop_pointer(pointer,feedback);
            check(!white(cell(1,0)),"dragging the left button paints the next cell");
            pointer.primary_held=false;pointer.secondary_pressed=true;drawing->desktop_pointer(pointer,feedback);
            check(white(cell(1,0)),"a right click erases the cell to white");
            pointer.secondary_pressed=false;pointer.secondary_held=true;pointer.x=82.5f;drawing->desktop_pointer(pointer,feedback);
            check(white(cell(0,0)),"dragging the right button erases continuously");
            pointer.secondary_held=false;pointer.primary_pressed=true;pointer.x=807;pointer.y=260;drawing->desktop_pointer(pointer,feedback);
            pointer.x=120.5f;pointer.y=152.5f;drawing->desktop_pointer(pointer,feedback);
            const auto actual=cell(2,0),expected=hui::gfx::Color::rgb(pixel_palette::colours[1]);
            check(std::abs(actual.r-expected.r)<.001f&&std::abs(actual.g-expected.g)<.001f&&std::abs(actual.b-expected.b)<.001f,"clicking a palette swatch selects its actual paint colour");
            pointer.x=0;pointer.y=0;check(!drawing->desktop_pointer(pointer,feedback),"empty workshop space is not a fake pointer target");
            check(drawing->desktop_pointer_interactive(82.5f,152.5f)&&drawing->desktop_pointer_interactive(807,260)&&!drawing->desktop_pointer_interactive(0,0),"the cursor glows only on real workshop grid and palette targets");
        }
        s.desktop_controller_style_=hui::DesktopControllerStyle::keyboard_mouse;s.desktop_pointer_.available=true;s.desktop_pointer_.x=1500;s.desktop_pointer_.y=240;
        check(s.desktop_pointer_interactive(),"Options rows are interactive cursor targets");
        s.settings_=false;s.panel_.snap(0);s.desktop_pointer_.x=900;s.desktop_pointer_.y=400;
        check(!s.desktop_pointer_interactive(),"plain exhibition background does not light the cursor");
        s.output_width_=1920;s.output_height_=1080;s.dt_=0;s.desktop_cursor_alpha_=1;s.desktop_cursor_glow_=0;s.theme_mix_.snap(0);
        s.renderer_.begin();s.render_desktop_cursor();
        {const auto&pixel=s.desktop_cursor_layer_.instances().back();check(std::abs(pixel.rect[2]-8)<.01f&&std::abs(pixel.rect[3]-8)<.01f&&std::abs(pixel.color_top[0]-17.f/255)<.001f,"the light-theme cursor is the website's exact 8-pixel black square");}
        s.theme_mix_.snap(1);s.renderer_.begin();s.render_desktop_cursor();
        {const auto&pixel=s.desktop_cursor_layer_.instances().back();check(s.desktop_dark_theme()&&pixel.color_top[0]>.999f&&pixel.color_top[1]>.999f&&pixel.color_top[2]>.999f,"the dark-theme cursor is the website's white square");}
        s.settings_=true;s.panel_.snap(1);s.desktop_pointer_.x=1500;s.desktop_pointer_.y=240;s.desktop_cursor_glow_=1;s.renderer_.begin();s.render_desktop_cursor();
        {int shadows=0;for(const auto&shape:s.desktop_cursor_layer_.instances())if(int(shape.params[3])==int(hui::gfx::Shape::shadow)&&std::abs(shape.color_top[0]-233.f/255)<.001f&&std::abs(shape.color_top[1]-183.f/255)<.001f&&std::abs(shape.color_top[2]-78.f/255)<.001f)++shadows;check(shadows==2,"interactive targets add the website's two golden glow shadows");}
        s.desktop_pointer_.available=false;check(!s.desktop_pointer_interactive(),"leaving the app clears the interactive cursor state");
        s.desktop_links_.clear();s.desktop_add_link({1180,300,300,30},"https://example.org/reference");s.desktop_pointer_.available=true;s.desktop_pointer_.x=1200;s.desktop_pointer_.y=310;
        check(s.desktop_pointer_interactive(),"visible HTTP links are true cursor targets");
        click(1200,310);std::string url;check(s.take_desktop_url_request(url)&&url=="https://example.org/reference"&&!s.take_desktop_url_request(url),"clicking a source link yields exactly one native URL request");s.desktop_links_.clear();
        {
            media::Connection pending;pending.user_code="test-fixture";pending.verification_url="https://www.google.com/device";
            check(s.desktop_can_open_sign_in_browser(pending)&&s.desktop_open_sign_in_browser(pending)&&s.take_desktop_url_request(url)&&url==pending.verification_url&&!s.take_desktop_url_request(url),"the sign-in keyboard action yields one browser request without launching or logging in");
            s.connection_panel_=true;s.overlay_.clear();s.draw_desktop_sign_in_browser(pending,1110);
            s.desktop_pointer_.available=true;s.desktop_pointer_.x=1500;s.desktop_pointer_.y=918;
            check(s.desktop_pointer_interactive(),"the visible browser sign-in button is a real glowing pointer target");
            click(1500,918);check(s.take_desktop_url_request(url)&&url==pending.verification_url&&!s.take_desktop_url_request(url),"clicking the sign-in button consumes exactly one verification URL");
            bool rejected=true;
            for(const auto& unsafe:std::array<std::string,6>{"javascript:alert(1)","file:///example","https://","https:///example","https://example.org/\nvalue",std::string("https://example.org/")+std::string(2048,'x')}){
                pending.verification_url=unsafe;rejected&=!s.desktop_open_sign_in_browser(pending)&&!s.take_desktop_url_request(url);
            }
            pending.verification_url="https://www.google.com/device";pending.signed_in=true;rejected&=!s.desktop_open_sign_in_browser(pending);
            pending.signed_in=false;pending.user_code.clear();rejected&=!s.desktop_open_sign_in_browser(pending);
            check(rejected,"browser sign-in rejects unsafe or oversized URLs, missing codes and already connected accounts");
            s.desktop_links_.clear();s.connection_panel_=false;
        }
        {
            DatabaseUpdater::Snapshot available;available.phase=DatabaseUpdater::Phase::available;available.revision=2;available.version="test-2";available.notes["en"]="New museum stories.";
            s.settings_=false;s.panel_.snap(0);s.database_dialog_=false;s.database_open_.snap(0);s.onboarding_=true;
            s.observe_database_update(available);check(!s.database_dialog_,"automatic database notifications wait until the introduction is complete");
            s.onboarding_=false;s.experience_active_=true;s.observe_database_update(available);check(!s.database_dialog_,"automatic database notifications do not interrupt an experience");
            s.experience_active_=false;s.experience_open_.snap(0);s.observe_database_update(available);
            check(s.database_dialog_&&s.database_action_count()==2&&std::string(s.database_action_label(0))=="Later"&&std::string(s.database_action_label(1))=="Update","an available database opens the shared Later / Update confirmation");
            press(hui::Action::back);s.database_open_.snap(0);s.observe_database_update(available);check(!s.database_dialog_,"the same available version notifies once in a session");
            available.revision=3;s.observe_database_update(available);check(s.database_dialog_,"a new database revision can notify in the same session");
            auto progress=available;progress.phase=DatabaseUpdater::Phase::downloading;progress.downloaded_bytes=5;progress.total_bytes=10;s.observe_database_update(progress);s.database_open_.snap(1);s.overlay_.clear();s.draw_database_update();
            bool half=false;for(const auto&shape:s.overlay_.instances())if(std::abs(shape.rect[0]-470)<.01f&&std::abs(shape.rect[1]-617)<.01f&&std::abs(shape.rect[2]-490)<.01f&&std::abs(shape.rect[3]-4)<.01f)half=true;
            check(half&&s.database_action_count()==1,"database progress reflects the actual downloaded byte ratio");
            progress.phase=DatabaseUpdater::Phase::ready;s.observe_database_update(progress);
            check(s.database_dialog_&&std::string(s.database_action_label(0))=="Done"&&s.database_completion_notice_==0,"a database completed in an open sheet keeps the Done action");
            press(hui::Action::back);s.database_open_.snap(0);
            progress.revision=4;s.observe_database_update(progress);
            check(!s.database_dialog_&&s.database_completion_notice_==6.f,"a database completed in the background starts a six-second notice without opening a sheet");
            s.database_completion_notice_=4.f;s.observe_database_update(progress);
            check(!s.database_dialog_&&s.database_completion_notice_==4.f,"observing the same ready database revision does not extend its notice");
            s.database_completion_notice_=0;progress.phase=DatabaseUpdater::Phase::failed;progress.error="Offline";
            s.observe_database_update(progress);check(!s.database_dialog_,"an automatic offline check never opens an error popup");
        }
        {
            check(s.desktop_preference_setting(6)==database_update_setting&&s.desktop_preference_count()==11,"one unified update action keeps eleven PC Options entries");
            const auto last=preference_row_bounds(1110,s.desktop_preference_count()-1);check(last.y+last.h<959,"all Options rows fit above the version and footer");
            ApplicationUpdater::Snapshot available;available.phase=ApplicationUpdater::Phase::available;available.version="0.3.0";available.notes["en"]="A new museum app.";
            s.settings_=false;s.panel_.snap(0);s.application_dialog_=false;s.application_open_.snap(0);s.idle_=2;s.onboarding_=true;
            s.observe_application_update(available);check(!s.application_dialog_,"app-update notifications wait for the introduction to finish");
            s.onboarding_=false;s.experience_active_=true;s.observe_application_update(available);check(!s.application_dialog_,"app-update notifications never interrupt an experience");
            s.experience_active_=false;s.experience_open_.snap(0);s.detail_=true;s.observe_application_update(available);check(!s.application_dialog_,"app-update notifications wait while a story is being read");
            s.detail_=false;s.story_open_.snap(0);s.idle_=0;s.observe_application_update(available);check(!s.application_dialog_,"app-update notifications wait until timeline input is idle");
            s.idle_=2;s.database_dialog_=true;s.observe_application_update(available);check(!s.application_dialog_,"app-update notifications wait for the database sheet to close");
            s.database_dialog_=false;s.database_open_.snap(0);s.observe_application_update(available);
            check(s.application_dialog_&&s.application_action_count()==2&&std::string(s.application_action_label(0))=="Later"&&std::string(s.application_action_label(1))=="Update","an available app version opens a separate Later / Update sheet");
            press(hui::Action::back);s.application_open_.snap(0);s.observe_application_update(available);check(!s.application_dialog_,"the same app version notifies once per session");
            available.version="0.3.1";s.idle_=2;s.observe_application_update(available);check(s.application_dialog_,"a later app version can notify when the visitor is idle again");
            auto progress=available;progress.phase=ApplicationUpdater::Phase::downloading;progress.downloaded_bytes=5;progress.total_bytes=10;s.observe_application_update(progress);s.application_open_.snap(1);s.overlay_.clear();s.draw_application_update();
            bool half=false;for(const auto&shape:s.overlay_.instances())if(std::abs(shape.rect[0]-470)<.01f&&std::abs(shape.rect[1]-617)<.01f&&std::abs(shape.rect[2]-490)<.01f&&std::abs(shape.rect[3]-4)<.01f)half=true;
            check(half&&std::string(s.application_action_label(0))=="Continue exploring","app-update progress uses actual bytes and lets the visitor continue exploring");
            progress.phase=ApplicationUpdater::Phase::current;s.observe_application_update(progress);press(hui::Action::confirm);s.application_open_.snap(0);check(!s.application_dialog_&&!s.take_application_restart_request(),"closing an up-to-date app result never requests a restart");
            progress.phase=ApplicationUpdater::Phase::ready;s.idle_=2;s.observe_application_update(progress);
            check(!s.application_dialog_&&s.application_completion_notice_==6.f&&!s.take_application_restart_request()&&!s.wants_quit(),"an app update completed in the background starts a notice without interrupting or restarting");
            s.application_completion_notice_=4.f;s.observe_application_update(progress);
            check(!s.application_dialog_&&s.application_completion_notice_==4.f,"observing the same ready app version does not extend its notice");
            s.application_completion_notice_=0;s.application_dialog_=true;s.application_open_.snap(1);s.observe_application_update(progress);
            check(s.application_action_count()==2&&std::string(s.application_action_label(0))=="Later"&&std::string(s.application_action_label(1))=="Restart now","the opened update sheet offers Later and Restart now for the prepared app");
            press(hui::Action::confirm);s.application_open_.snap(0);check(!s.application_dialog_&&!s.take_application_restart_request()&&!s.wants_quit(),"Later leaves a prepared app update without exiting");
            s.application_dialog_=true;s.application_open_.snap(1);s.observe_application_update(progress);
            {const auto action=s.application_action_bounds(1);click(action.cx(),action.cy());}
            check(s.take_application_restart_request()&&!s.take_application_restart_request()&&!s.wants_quit(),"clicking Restart now emits one request and waits for safe platform apply");
            s.application_focus_=0;{auto i=input();i.nav=hui::Direction::right;send(i);}press(hui::Action::confirm);
            check(s.take_application_restart_request()&&!s.take_application_restart_request(),"keyboard navigation can confirm the prepared app restart");
            check(!s.begin_application_restart()&&s.application_dialog_&&s.application_state_.phase==ApplicationUpdater::Phase::failed&&!s.wants_quit(),"an unavailable restart helper leaves the app running and shows the failure");
            press(hui::Action::back);s.application_open_.snap(0);s.application_restart_failed_=false;s.application_restart_error_.clear();progress.phase=ApplicationUpdater::Phase::failed;progress.error="Offline";s.observe_application_update(progress);
            check(!s.application_dialog_,"an automatic offline app check never interrupts the visitor");
        }
        s.settings_=false;s.onboarding_=true;s.language_choice_=s.theme_choice_=false;s.onboarding_leaving_=false;s.onboarding_step_=0;s.collection_pending_=true;s.dt_=1.f/60;
        press(hui::Action::confirm);check(s.onboarding_step_==1&&s.collection_pending_,"PC introduction advances while resource validation stays in the background");
        s.collection_pending_=false;s.onboarding_=false;s.settings_=true;s.panel_.snap(1);s.setting_=5;
        press(hui::Action::confirm);check(s.onboarding_&&s.language_choice_&&!s.collection_pending_,"replaying the PC introduction does not re-enter collection installation");
        s.onboarding_=s.language_choice_=s.theme_choice_=false;s.settings_=true;s.panel_.snap(1);
        check(std::string(preference_labels[size_t(general_credits_setting+1)])=="Support the museum"&&s.desktop_preference_setting(s.desktop_preference_count()-2)==museum_support_setting,"Support the museum follows Credits on both platforms and precedes PC Exit");
        click(1500,preference_row_baseline(s.desktop_preference_count()-2));s.support_open_.snap(1);
        check(s.support_dialog_&&s.support_qr_&&!s.take_desktop_url_request(url),"the support row opens a real QR sheet without opening a browser");
        s.overlay_.clear();s.desktop_links_.clear();s.draw_support();
        click(1500,preference_row_baseline(s.desktop_preference_count()-1));check(s.support_dialog_&&!s.wants_quit(),"the support modal blocks clicks on the Exit row underneath");
        {const auto action=s.support_action_bounds(1);click(action.cx(),action.cy());}
        check(s.support_dialog_&&s.take_desktop_url_request(url)&&url==museum_support_url&&!s.take_desktop_url_request(url),"the support browser button emits only the requested Ko-fi URL once");
        s.desktop_pointer_.available=true;s.desktop_pointer_.x=1287;s.desktop_pointer_.y=691;
        check(!s.desktop_pointer_interactive(),"the removed support URL text leaves no invisible link target");
        click(1287,691);check(!s.take_desktop_url_request(url),"only the visible Open Ko-fi button opens a support URL");
        press(hui::Action::back);s.support_open_.snap(0);check(!s.support_dialog_&&s.settings_,"Back closes support and returns to Options");
        click(1500,preference_row_baseline(s.desktop_preference_count()-2));s.support_open_.snap(1);
        {auto i=input();i.nav=hui::Direction::right;send(i);}press(hui::Action::confirm);
        check(s.support_dialog_&&s.take_desktop_url_request(url)&&url==museum_support_url,"keyboard selection opens the support link only on confirm");
        {const auto action=s.support_action_bounds(0);click(action.cx(),action.cy());}
        s.support_open_.snap(0);s.desktop_links_.clear();check(!s.support_dialog_,"clicking Close dismisses the support sheet");
        click(1500,preference_row_baseline(s.desktop_preference_count()-1));check(s.wants_quit(),"clicking the final Options row exits");
        std::fprintf(stderr,"[Desktop UI] %d checks passed, %d failed\n",passed,failed);return failed==0;
    }
};
}
#endif
