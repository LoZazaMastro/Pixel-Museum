// Pixel Museum - desktop navigation, native text entry and display preferences.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/menu_row.hpp"
#include "museum/preferences_layout.hpp"
#if defined(MUSEUM_DESKTOP)
#include "museum/general_credits.hpp"
#include "museum/feature_resources.hpp"
#include "museum/story_card_layout.hpp"
#include "museum/study_controls.hpp"
#include "platform/playback_window.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <tuple>
#include <unordered_set>

namespace museum {
using namespace hui;
using gfx::Rect;using gfx::Color;using gfx::Align;
namespace {
constexpr int search_command=100,filter_command=101,previous_command=102,next_command=103;
constexpr int zoom_out_command=104,zoom_in_command=105,volume_down_command=106,volume_up_command=107;
constexpr int scroll_up_command=108,scroll_down_command=109;
constexpr int frame_limits[]={0,30,60,120,144,165,240};
bool inside(const Rect&r,float x,float y){return x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h;}
int story_card_at(float x,float y,float position,float rise,int count){
    const int index=int(std::round(position+(x-story_card.cx())/story_card_pitch));
    if(index<0||index>=count||y>=938)return -1;
    return inside(story_card_bounds(index-position,rise),x,y)?index:-1;
}
float key_cap_width(const ui::FontRef&font,std::string_view key){return std::max(24.f,font.font->measure(key,16)+16);}
bool browser_url(const std::string& url){
    const auto prefix=url.rfind("https://",0)==0?8u:url.rfind("http://",0)==0?7u:0u;
    if(!prefix||url.size()<=prefix||url.size()>2048||url[prefix]=='/'||url[prefix]=='?'||url[prefix]=='#')return false;
    return std::none_of(url.begin(),url.end(),[](unsigned char c){return c<=32||c==127;});
}
std::size_t previous_character(const std::string&s,std::size_t at){
    return ui::text_entry::previous(s,at);
}
std::size_t next_character(const std::string&s,std::size_t at){
    return ui::text_entry::next(s,at);
}
std::string resolution(int width,int height){
    const auto aspect=desktop_aspect(width,height);
    return std::to_string(width)+" × "+std::to_string(height)+(aspect.empty()?"":" ("+std::string(aspect)+")");
}
std::string playback_time(double value){
    if(!std::isfinite(value)||value<0)return "--:--";
    char text[32];const int seconds=int(std::min(value,359999.));std::snprintf(text,sizeof(text),"%d:%02d",seconds/60,seconds%60);return text;
}
}

void Screen::set_desktop_video_modes(DesktopDisplayModes modes){
    desktop_modes_=std::move(modes);
    select_desktop_resolution(0);
}
void Screen::init_desktop_video_settings(const DesktopVideoSettings& current){
    desktop_video_draft_=current;
    select_desktop_resolution(0);
    desktop_video_=desktop_video_draft_;
}
void Screen::select_desktop_resolution(int direction){
    auto& draft=desktop_video_draft_;
    if(draft.fullscreen&&draft.borderless)return;
    const auto& modes=draft.fullscreen?desktop_modes_.exclusive:desktop_modes_.windowed;
    if(modes.empty())return;
    const auto current=std::find(modes.begin(),modes.end(),DesktopDisplayMode{draft.width,draft.height});
    auto next=current;
    if(current==modes.end()){
        const auto distance=[&](const auto& mode){return std::abs(mode.width-draft.width)+std::abs(mode.height-draft.height);};
        next=std::min_element(modes.begin(),modes.end(),[&](auto a,auto b){return distance(a)<distance(b);});
    }else{
        const auto count=static_cast<int>(modes.size());
        const auto index=static_cast<int>(current-modes.begin());
        next=modes.begin()+(index+direction+count)%count;
    }
    draft.width=next->width;
    draft.height=next->height;
}
bool Screen::take_desktop_video_request(DesktopVideoSettings&value){
    if(!desktop_video_pending_)return false;
    value=desktop_video_request_;desktop_video_pending_=false;return true;
}
void Screen::set_desktop_video_settings_applied(const DesktopVideoSettings&value){
    desktop_video_=value;desktop_video_draft_=value;desktop_video_applying_=false;
    notice_=std::string(i18n::tr("Video settings applied."));notice_time_=3.5f;
}
void Screen::desktop_video_apply_failed(const std::string&reason){
    desktop_video_applying_=false;desktop_video_draft_=desktop_video_;
    notice_=std::string(i18n::tr("Video settings could not be applied."));
    if(!reason.empty())notice_+=" "+reason;
    notice_time_=3.5f;
}
int Screen::desktop_preference_count()const{return int(preference_labels.size())+1;}
int Screen::desktop_preference_setting(int row)const{
    if(row<=0||row>=desktop_preference_count()-1)return -1;
    if(row==desktop_audio_preference_row)return 2;
    if(row==2)return 0;
    if(row==3)return 1;
    const int original=row-1;return original>=remove_collection_setting?original+1:original;
}
const char* Screen::desktop_preference_label(int row)const{
    if(row==0)return "Video";
    if(row==desktop_audio_preference_row)return audio_preference_label;
    if(row==desktop_preference_count()-1)return "Exit";
    return preference_labels[size_t(desktop_preference_setting(row))];
}
std::string Screen::desktop_resources_error()const{
    const auto phase=collection_installer_.snapshot().phase;using Phase=CollectionInstaller::Phase;
    if(collection_media_error_||phase==Phase::failed||phase==Phase::paused||phase==Phase::cancelled||phase==Phase::unconfigured)
        return std::string(i18n::tr("The installed museum resources are missing or damaged. Run Pixel Museum Setup again to repair the installation."));
    return {};
}
bool Screen::handle_desktop_video(const InputFrame&i,ui::Feedback&f){
    if(i.is_pressed(Action::back)||i.is_pressed(Action::menu)){
        desktop_video_open_=false;desktop_video_draft_=desktop_video_;setting_=0;
        if(i.is_pressed(Action::menu))settings_=false;
        f.play(audio::Cue::back);return true;
    }
    if(desktop_video_applying_)return true;
    const int before=desktop_video_focus_;
    if(i.nav==Direction::down)desktop_video_focus_=std::min(4,desktop_video_focus_+1);
    if(i.nav==Direction::up)desktop_video_focus_=std::max(0,desktop_video_focus_-1);
    if(before!=desktop_video_focus_)f.play(audio::Cue::focus);
    const bool edit=i.is_pressed(Action::confirm)||i.nav==Direction::left||i.nav==Direction::right;
    if(!edit)return true;
    const int direction=i.nav==Direction::left?-1:1;
    if(desktop_video_focus_==0&&desktop_video_draft_.fullscreen&&desktop_video_draft_.borderless)return true;
    if(desktop_video_focus_==0)select_desktop_resolution(direction);
    if(desktop_video_focus_==1){
        // Fullscreen -> borderless fullscreen -> windowed, in this order.
        const int mode=desktop_video_draft_.fullscreen?(desktop_video_draft_.borderless?1:0):2;
        const int next=(mode+direction+3)%3;
        desktop_video_draft_.fullscreen=next!=2;desktop_video_draft_.borderless=next==1;
        select_desktop_resolution(0);
    }
    if(desktop_video_focus_==2)desktop_video_draft_.vsync=!desktop_video_draft_.vsync;
    if(desktop_video_focus_==3){
        int index=0;for(size_t n=0;n<std::size(frame_limits);++n)if(frame_limits[n]==desktop_video_draft_.frame_limit)index=int(n);
        index=(index+direction+int(std::size(frame_limits)))%int(std::size(frame_limits));desktop_video_draft_.frame_limit=frame_limits[index];
    }
    if(desktop_video_focus_==4){
        if(!i.is_pressed(Action::confirm))return true;
        desktop_video_request_=desktop_video_draft_;desktop_video_pending_=true;desktop_video_applying_=true;f.play(audio::Cue::select);return true;
    }
    f.play(audio::Cue::toggle);return true;
}
void Screen::draw_desktop_video(float x){
    const auto p=colours();ui::text(overlay_,fonts_.semibold,"Video",x+62,134,44,p.ink);
    ui::paragraph(overlay_,fonts_.regular,"Choose how the museum appears on your display.",x+65,190,22,660,31,p.muted,2);
    const char*labels[]={"Resolution","Display mode","Vertical sync","Frame limit","Apply changes"};
    const bool borderless=desktop_video_draft_.fullscreen&&desktop_video_draft_.borderless;
    const std::string values[]={borderless?std::string(i18n::tr("Desktop")):resolution(desktop_video_draft_.width,desktop_video_draft_.height),std::string(i18n::tr(desktop_video_draft_.fullscreen?(borderless?"Borderless fullscreen":"Fullscreen"):"Windowed")),std::string(i18n::tr(desktop_video_draft_.vsync?"On":"Off")),desktop_video_draft_.frame_limit?std::to_string(desktop_video_draft_.frame_limit)+" FPS":std::string(i18n::tr("Unlimited")),desktop_video_applying_?std::string(i18n::tr("Applying…")):std::string{}};
    for(int row=0;row<5;++row){
        const float y=292+row*104;const bool selected=row==desktop_video_focus_;
        const Rect bounds{x+45,y-40,710,80};
        if(selected)overlay_.rounded_rect(bounds,5,p.ink.with_alpha(.045f));
        if(selected)overlay_.rounded_rect({x+37,menu_text_center(fonts_.semibold,labels[row],y,25)-28,4,56},0,tone_);
        ui::text(overlay_,fonts_.semibold,labels[row],x+65,y,25,selected?p.ink:p.muted);
        ui::text(overlay_,fonts_.regular,values[row],x+716,y,23,p.muted,Align::right);
        if(row<4)overlay_.line(x+65,y+33,x+716,y+33,1,p.rule);
    }
    ui::paragraph(overlay_,fonts_.regular,"Changes take effect when you choose Apply changes.",x+65,848,20,650,29,p.muted,3);
    if(notice_time_>0)ui::paragraph(overlay_,fonts_.regular,notice_,x+65,928,20,650,28,p.ink,2);
}

std::vector<Screen::DesktopControl> Screen::desktop_controls()const{
    std::vector<DesktopControl> result;
    const bool keyboard=desktop_controller_style_==DesktopControllerStyle::keyboard_mouse;
    const bool dualsense=desktop_controller_style_==DesktopControllerStyle::dualsense;
    const auto add=[&](const char*label,int command,const char*key,const char*pad,ui::Button glyph){
        result.push_back({{},std::string(i18n::tr(label)),keyboard?key:dualsense?"":pad,command,glyph});
    };
    const auto action=[&](const char*label,Action command,const char*key,const char*pad,ui::Button glyph){add(label,int(command),key,pad,glyph);};
    const auto back=[&](const char*label="Back"){action(label,Action::back,"Esc","B",ui::Button::circle);};
    const auto select=[&](const char*label="Select"){action(label,Action::confirm,"Enter","A",ui::Button::cross);};
    const auto decade=[&](){
        action("Decade",Action::jump_next,"Z","LT / RT",ui::Button::l2);
        result.back().second=ui::Button::r2;
        if(keyboard)result.back().second_key="C";
    };
    if(application_dialog_){back(application_action_count()==2?"Later":"Close");select(application_action_label(application_focus_));}
    else if(support_dialog_){back("Close");select(support_action_label(support_focus_));}
    else if(database_dialog_){back(database_state_.phase==DatabaseUpdater::Phase::available||database_state_.phase==DatabaseUpdater::Phase::failed?"Later":"Close");select(database_action_label(database_focus_));}
    else if(collection_remove_dialog_){back("Cancel");select();}
    else if(collection_removal_active()){
        if(collection_removal_state_==CollectionRemovalState::failed){select("Try again");back("Close app");}
    }else if(language_choice_){select("Continue");}
    else if(collection_pending_&&!onboarding_){
        back("Close Pixel Museum");
    }else if(onboarding_){
        if(theme_choice_){back();select("Continue");}
        else if(onboarding_step_==onboarding_cards_){back();action("Begin",Action::menu,"Enter","Menu",ui::Button::options);}
        else {back();select(onboarding_step_==onboarding_cards_-1?"Connect / continue":"Continue");action(onboarding_step_==onboarding_cards_-1?"Skip / reconnect":"Skip introduction",Action::west,"Space","X",ui::Button::square);}
    }else if(boot_time_<4.8f){return result;}
    else if(search_prompt_.is_open()){back("Cancel");select(keyboard?"Search":"Select");}
    else if(search_page_){back("Guide");select("Open");add("Search",search_command,"S","View",ui::Button::touchpad);}
    else if(experience_active_){
        if(experience_introduction_){back("Back");select("Enter study");}
        else if(experience_paused_||(study_&&study_->completion()!=StudyCompletion::playing)){back();select();}
        else if(experience_index_>=0&&experience_index_<int(study_catalog().size())){
            for(const auto&control:study_controls(study_catalog()[size_t(experience_index_)].id,true)){
                const auto button=control.hint.button;int command=-1;const char*key="",*pad="";
                switch(button){
                case ui::Button::cross:command=int(Action::confirm);key="Enter";pad="A";break;
                case ui::Button::circle:command=int(Action::back);key="Esc";pad="B";break;
                case ui::Button::square:command=int(Action::west);key="Space";pad="X";break;
                case ui::Button::triangle:command=int(Action::north);key="R";pad="Y";break;
                case ui::Button::l1:command=int(Action::page_prev);key="Q";pad="LB";break;
                case ui::Button::r1:command=int(Action::page_next);key="E";pad="RB";break;
                case ui::Button::l2:command=int(Action::jump_prev);key="Z";pad="LT";break;
                case ui::Button::r2:command=int(Action::jump_next);key="C";pad="RT";break;
                case ui::Button::options:command=int(Action::menu);key="Esc";pad="Menu";break;
                case ui::Button::touchpad:command=int(Action::touch);key="Tab";pad="View";break;
                case ui::Button::left_stick:key="WASD";pad="LS";break;
                case ui::Button::right_stick:key="IJKL";pad="RS";break;
                case ui::Button::dpad:key=control.down?"↓":control.up?"↑":"Arrows";pad="D-pad";break;
                default:continue;
                }
                if(control.hint.second==ui::Button::r1){command=int(Action::page_next);key="Q / E";pad="LB / RB";}
                add(control.hint.label,command,key,pad,button);result.back().second=control.hint.second;
            }
        }else action("Pause",Action::menu,"Esc","Menu",ui::Button::options);
    }else if(settings_||credits_||connection_panel_){
        back(desktop_video_open_||volumes_open_?"Options":"Back");
        if(connection_panel_){const auto c=video_.connection();action(desktop_can_open_sign_in_browser(c)?"Open in browser":c.signed_in?"Disconnect":c.saved?"Reconnect":"Connect",c.signed_in?Action::west:Action::confirm,c.signed_in?"Space":"Enter",c.signed_in?"X":"A",c.signed_in?ui::Button::square:ui::Button::cross);}
        else if(!credits_)select(desktop_video_open_&&desktop_video_focus_==4?"Apply changes":"Select");
    }else if(year_guide_&&guide_trophies_&&trophy_pin_open_){
        back();add("Move",-1,"WASD","LS",ui::Button::left_stick);
        if(!keyboard){add("Rotate",-1,"","RS",ui::Button::right_stick);add("Zoom out",zoom_out_command,"−","LT",ui::Button::l2);add("Zoom in",zoom_in_command,"+","RT",ui::Button::r2);}
    }else if(year_guide_){
        back();select(guide_experiences_?"Enter study":"Open");
        action(guide_trophies_?"Years":guide_experiences_?"Trophies":"Experiences",Action::west,"Space","X",ui::Button::square);
        add("Search",search_command,"S","View",ui::Button::touchpad);
        if(guide_trophies_)action("Inspect 3D",Action::north,"R","Y",ui::Button::triangle);
        else if(!guide_experiences_)decade();
    }else if(gallery_){
        back();
        select("Fit / fill");if(!keyboard){add("Zoom out",zoom_out_command,"−","LT",ui::Button::l2);add("Zoom in",zoom_in_command,"+","RT",ui::Button::r2);}
    }else if(object_inspect_){back();select("Reset view");if(!keyboard){add("Zoom out",zoom_out_command,"−","LT",ui::Button::l2);add("Zoom in",zoom_in_command,"+","RT",ui::Button::r2);}}
    else if(screening_||playlist_active_){
        back(playlist_active_?"Return to exhibit":"Back");select(video_.paused()?"Play":"Pause");
        if(!playlist_active_){
            action(fullscreen_?"Return to frame":"Fullscreen",Action::west,"Space","X",ui::Button::square);
            action(film_captions_enabled_?"Hide subtitles":"Show subtitles",Action::north,"R","Y",ui::Button::triangle);
            if(const auto* audio=film_audio_hint())action(audio,Action::touch,"Tab","View",ui::Button::touchpad);
        }
        add("Volume −",volume_down_command,"−","LT",ui::Button::l2);add("Volume +",volume_up_command,"+","RT",ui::Button::r2);
    }else if(chapters_){back("Continue timeline");select("Enter");action("Options",Action::menu,"Esc","Menu",ui::Button::options);}
    else if(detail_){
        back("Timeline");
        if(!story_cards_.empty()){
            const auto&card=story_cards_[size_t(std::clamp(story_focus_,0,int(story_cards_.size())-1))];
            if(card.kind==StoryCard::soundtrack)select("Listen");
            else if(card.kind==StoryCard::experience||card.kind==StoryCard::interactive)select("Enter study");
            else if(card.kind==StoryCard::film)select("Play film");
            if(story_object()||card.image>=0)action(story_object()?"Inspect 3D":"View image",Action::west,"Space","X",ui::Button::square);
            if(card.paragraph>=0&&scroll_max_>0)action("Read more",Action::r3,"V","R3",ui::Button::right_stick);
        }
    }else{
        if(!history_focus_)select("Open exhibit");
        const auto*entry=current();if(entry&&(!entry->images.empty()||!entry->models.empty()))action(entry->models.empty()?"View image":"Inspect 3D",Action::west,"Space","X",ui::Button::square);
        action(active_filter()?"All":"Today",Action::north,"R","Y",ui::Button::triangle);
        decade();
        if(keyboard)add("Filter",filter_command,"F","",ui::Button::r1);
        else{action("Filter",Action::page_next,"","LB / RB",ui::Button::l1);result.back().second=ui::Button::r1;}
        action("Guide",Action::touch,"Tab","View",ui::Button::touchpad);
        if(keyboard)add("Search",search_command,"S","View",ui::Button::touchpad);
        action("Options",Action::menu,"Esc","Menu",ui::Button::options);
    }
    const bool reading=!application_dialog_&&application_open_.value<.001f&&!support_dialog_&&support_open_.value<.001f&&!database_dialog_&&database_open_.value<.001f&&!onboarding_&&!collection_pending_&&!search_page_&&!search_prompt_.visible()&&!gallery_&&!screening_&&!object_inspect_&&!experience_active_&&
        ((credits_&&credits_scroll_max_>0)||(year_guide_&&guide_experiences_&&experience_description_max_>0)||(!settings_&&!year_guide_&&(detail_||(history_focus_&&!keyboard))&&scroll_max_>0));
    if(reading){add("Scroll up",scroll_up_command,"PgUp","RS",ui::Button::right_stick);add("Scroll down",scroll_down_command,"PgDn","RS",ui::Button::right_stick);}
    float total=0;
    for(auto&control:result){
        const float key_width=keyboard
            ?key_cap_width(fonts_.mono,control.key)+(control.second_key.empty()?0.f:8+key_cap_width(fonts_.mono,control.second_key))
            :ui::button_width(control.glyph,28)+(control.second==ui::Button::none?0.f:12+ui::button_width(control.second,28));
        control.bounds.w=key_width+fonts_.regular.measure(control.label,19)+38;
        total+=control.bounds.w+12;
    }
    const float scale=total>1740?1740/total:1;float x=90;
    for(auto&control:result){control.bounds={x,988,control.bounds.w*scale,52};control.scale=scale;x+=control.bounds.w+12*scale;}
    return result;
}
bool Screen::desktop_footer_input(InputFrame&i,ui::Feedback&f){
    if(!i.pointer.primary_pressed)return false;
    for(const auto&control:desktop_controls()){
        if(!inside(control.bounds,i.pointer.x,i.pointer.y))continue;
        i.pointer.primary_pressed=false;
        if(control.command<0)return true;
        if(!control.second_key.empty()){
            const float split=control.bounds.x+8+(key_cap_width(fonts_.mono,control.key)+4)*control.scale;
            i.pressed|=action_bit(i.pointer.x<split?Action::jump_prev:Action::jump_next);return false;
        }
        if(control.command==filter_command){i.desktop_filter_pressed=true;return false;}
        if(control.command<int(Action::count)){i.pressed|=action_bit(Action(control.command));return false;}
        if(control.command==search_command){chapters_=false;open_search(f);return true;}
        if(control.command==previous_command||control.command==next_command){
            const int direction=control.command==previous_command?-1:1;
            if(gallery_){const int count=int(viewer_.images().size());if(count){viewer_.set_index((viewer_.index()+direction+count)%count,false);image_index_=viewer_.index();f.play(audio::Cue::focus);}return true;}
            i.nav=direction<0?Direction::left:Direction::right;return false;
        }
        if(control.command==zoom_in_command||control.command==zoom_out_command){
            const bool plus=control.command==zoom_in_command;
            if(gallery_){ui::Feedback silent;if(plus)viewer_.zoom_in(silent);else viewer_.zoom_out(silent);}
            else if(year_guide_&&guide_trophies_&&trophy_pin_open_)trophy_pin_zoom_=std::clamp(trophy_pin_zoom_+(plus?.15f:-.15f),.65f,2.6f);
            else object_zoom_=std::clamp(object_zoom_+(plus?.2f:-.2f),.5f,4.f);
            return true;
        }
        if(control.command==volume_down_command||control.command==volume_up_command){
            media_volume_=std::clamp(media_volume_+(control.command==volume_up_command?.05f:-.05f),0.f,1.f);video_.volume(media_volume_);dirty_=true;save_delay_=1;f.play(audio::Cue::slider);return true;
        }
        if(control.command==scroll_up_command||control.command==scroll_down_command){
            const float amount=control.command==scroll_up_command?-240.f:240.f;
            if(credits_)credits_scroll_.target=std::clamp(credits_scroll_.target+amount,0.f,credits_scroll_max_);
            else if(year_guide_&&guide_experiences_){experience_description_scroll_=std::clamp(experience_description_scroll_+amount,0.f,experience_description_max_);experience_description_clock_=-6;}
            else scroll_.target=std::clamp(scroll_.target+amount,0.f,scroll_max_);
            f.play(audio::Cue::focus);return true;
        }
    }
    return false;
}

unsigned Screen::desktop_navigation_feedback_state()const{
    return (settings_?1u:0u)|(year_guide_?2u:0u)|(detail_?4u:0u)|(history_focus_?8u:0u);
}
void Screen::desktop_add_scroll_area(DesktopScrollTarget target,Rect viewport,Rect track,float maximum,float position,float minimum_thumb){
    if(maximum>0&&viewport.w>0&&viewport.h>0&&track.h>0)
        desktop_scroll_areas_.push_back({target,viewport,track,maximum,std::clamp(position,0.f,maximum),minimum_thumb});
}
bool Screen::desktop_scroll_enabled(DesktopScrollTarget target)const{
    if(application_dialog_||application_open_.value>.001f||support_dialog_||support_open_.value>.001f||database_dialog_||database_open_.value>.001f||onboarding_||collection_pending_||collection_remove_dialog_||search_page_||search_prompt_.visible()||experience_active_||gallery_||screening_||playlist_active_||object_inspect_)return false;
    if(target==DesktopScrollTarget::credits)return credits_&&!connection_panel_;
    if(target==DesktopScrollTarget::description)return year_guide_&&guide_experiences_&&!guide_trophies_;
    return !settings_&&!year_guide_&&!credits_&&!connection_panel_&&!chapters_&&(detail_||history_focus_);
}
bool Screen::handle_desktop_scrolling(InputFrame&i,ui::Feedback&){
    const auto&p=i.pointer;
    const auto track_bounds=[](const DesktopScrollArea&a){return Rect{a.track.x-9,a.track.y,a.track.w+18,a.track.h};};
    const auto thumb_height=[](const DesktopScrollArea&a){return std::min(a.track.h,std::max(a.minimum_thumb,a.track.h*a.track.h/(a.track.h+a.maximum)));};
    const auto set_position=[&](DesktopScrollArea&a,float value,bool immediate){
        value=std::clamp(value,0.f,a.maximum);a.position=value;
        if(a.target==DesktopScrollTarget::credits){if(immediate)credits_scroll_.snap(value);else credits_scroll_.target=value;}
        else if(a.target==DesktopScrollTarget::description){experience_description_scroll_=value;experience_description_clock_=-6;}
        else{if(immediate)scroll_.snap(value);else scroll_.target=value;}
    };
    const auto current_target=[&](const DesktopScrollArea&a){return a.target==DesktopScrollTarget::credits?credits_scroll_.target:a.target==DesktopScrollTarget::description?experience_description_scroll_:scroll_.target;};
    if(desktop_scroll_dragging_){
        if(!p.available||(!p.primary_held&&!p.primary_pressed))desktop_scroll_dragging_=false;
        else for(auto&a:desktop_scroll_areas_)if(a.target==desktop_scroll_drag_target_&&desktop_scroll_enabled(a.target)){
            const float travel=a.track.h-thumb_height(a);
            set_position(a,travel>0?(p.y-a.track.y-desktop_scroll_drag_offset_)/travel*a.maximum:0,true);return true;
        }
        if(desktop_scroll_dragging_)desktop_scroll_dragging_=false;
    }
    if(p.available&&p.primary_pressed)for(auto it=desktop_scroll_areas_.rbegin();it!=desktop_scroll_areas_.rend();++it){auto&a=*it;
        if(!desktop_scroll_enabled(a.target)||!inside(track_bounds(a),p.x,p.y))continue;
        const float thumb=thumb_height(a),top=a.track.y+(a.track.h-thumb)*a.position/a.maximum;
        desktop_scroll_dragging_=true;desktop_scroll_drag_target_=a.target;
        desktop_scroll_drag_offset_=p.y>=top&&p.y<top+thumb?p.y-top:thumb*.5f;
        const float travel=a.track.h-thumb;set_position(a,travel>0?(p.y-a.track.y-desktop_scroll_drag_offset_)/travel*a.maximum:0,true);return true;
    }
    if(p.available&&p.wheel_y)for(auto it=desktop_scroll_areas_.rbegin();it!=desktop_scroll_areas_.rend();++it){auto&a=*it;
        if(desktop_scroll_enabled(a.target)&&(inside(a.viewport,p.x,p.y)||inside(track_bounds(a),p.x,p.y))){set_position(a,current_target(a)-p.wheel_y*105,false);return true;}
    }
    const bool arrow=desktop_controller_style_==DesktopControllerStyle::keyboard_mouse&&(i.nav==Direction::up||i.nav==Direction::down);
    if(i.desktop_scroll||arrow)for(auto it=desktop_scroll_areas_.rbegin();it!=desktop_scroll_areas_.rend();++it){auto&a=*it;if(!desktop_scroll_enabled(a.target))continue;
        // On the culture timeline, the keyboard navigates and the mouse reads.
        if(history_focus_&&a.target==DesktopScrollTarget::content)continue;
        // The Guide's arrow keys select years/experiences; its description uses
        // Page Up/Down or the pointer, while exhibit text owns Up/Down.
        if(arrow&&a.target==DesktopScrollTarget::description&&!i.desktop_scroll&&!(p.available&&(inside(a.viewport,p.x,p.y)||inside(track_bounds(a),p.x,p.y))))continue;
        const float amount=i.desktop_scroll?i.desktop_scroll:(i.nav==Direction::down?145.f:-145.f);
        set_position(a,current_target(a)+amount,false);i.nav=Direction::none;i.stick_y=0;i.pressed&=~(action_bit(Action::up)|action_bit(Action::down));return true;
    }
    return false;
}

bool Screen::handle_desktop_search(InputFrame&i,ui::Feedback&f){
    if(!search_prompt_.is_open()||desktop_controller_style_!=DesktopControllerStyle::keyboard_mouse)return false;
    auto text=search_prompt_.text();
    if(text!=desktop_search_observed_){desktop_search_caret_=text.size();desktop_search_selection_=false;}
    desktop_search_caret_=ui::text_entry::boundary(text,desktop_search_caret_);
    const bool cancel=i.is_pressed(Action::back)||(i.pointer.primary_pressed&&inside(desktop_search_button_bounds(0),i.pointer.x,i.pointer.y));
    if(cancel){search_prompt_.dismiss();desktop_search_observed_.clear();f.play(audio::Cue::back);return true;}
    if(i.text_select_all){desktop_search_selection_=true;desktop_search_caret_=text.size();}
    const auto clear_selection=[&]{if(desktop_search_selection_){text.clear();desktop_search_caret_=0;desktop_search_selection_=false;return true;}return false;};
    bool edited=false;
    const auto insert_text=[&](std::string_view typed){
        const auto printable=ui::text_entry::printable(typed);
        if(printable.empty())return;
        edited=clear_selection()||edited;
        edited=ui::text_entry::insert_bounded(text,desktop_search_caret_,printable,96)||edited;
    };
    insert_text(i.text_utf8);
    if(i.text_backspace)edited=clear_selection()||ui::text_entry::erase_previous(text,desktop_search_caret_)||edited;
    if(i.text_delete)edited=clear_selection()||ui::text_entry::erase_next(text,desktop_search_caret_)||edited;
    if(i.text_home){desktop_search_caret_=0;desktop_search_selection_=false;}
    if(i.text_end){desktop_search_caret_=text.size();desktop_search_selection_=false;}
    if(i.text_left||(i.keyboard_active&&i.nav==Direction::left)){desktop_search_caret_=desktop_search_selection_?0:previous_character(text,desktop_search_caret_);desktop_search_selection_=false;}
    if(i.text_right||(i.keyboard_active&&i.nav==Direction::right)){desktop_search_caret_=desktop_search_selection_?text.size():next_character(text,desktop_search_caret_);desktop_search_selection_=false;}
    bool virtual_submit=false;
    auto&keyboard=search_prompt_.keyboard;
    if(i.pointer.available&&(i.pointer.moved||i.pointer.primary_pressed)&&!keyboard.layouts().empty()){
        const auto&rows=keyboard.layouts()[size_t(keyboard.layout())].rows;
        bool hit=false;for(size_t row=0;row<rows.size()&&!hit;++row)for(size_t key=0;key<rows[row].size();++key){
            if(!inside(keyboard.key_rect(int(row),int(key)),i.pointer.x,i.pointer.y))continue;
            hit=true;
            keyboard.set_focus(int(row),int(key));
            if(i.pointer.primary_pressed){
                keyboard.set_length(search_prompt_.field.length());InputFrame tap;tap.connected=true;tap.pressed=action_bit(Action::confirm);
                const auto event=keyboard.handle(tap,f);virtual_submit=event==ui::Event::activated;
                for(int n=0;n<keyboard.erased();++n)edited=clear_selection()||ui::text_entry::erase_previous(text,desktop_search_caret_)||edited;
                insert_text(keyboard.typed());
            }
            break;
        }
    }
    auto&field=search_prompt_.field;field.style.max_length=96;
    if(field.text()!=text)field.set_text(text);
    text=search_prompt_.text();field.set_caret(desktop_search_caret_);desktop_search_caret_=field.caret();desktop_search_observed_=text;
    if(edited)f.play(audio::Cue::type,1,0,.25f);
    const bool submit=virtual_submit||i.text_submit||i.is_pressed(Action::confirm)||(i.pointer.primary_pressed&&inside(desktop_search_button_bounds(1),i.pointer.x,i.pointer.y));
    if(submit){
        const auto first=text.find_first_not_of(" \t\r\n");
        if(first==std::string::npos){f.play(audio::Cue::error);return true;}
        search_query_=text.substr(first,text.find_last_not_of(" \t\r\n")-first+1);
        search_results_=search_collection(catalog_,history_catalog_all_,search_query_);search_focus_=0;search_position_.snap(0);search_page_=true;year_guide_=false;
        desktop_search_submit_rearm_=i.text_submit;
        search_prompt_.dismiss();f.play(audio::Cue::select);return true;
    }
    if(i.pointer.primary_pressed&&inside(field.field_rect(),i.pointer.x,i.pointer.y)){
        ui::Painter measurement(overlay_,fonts_,field.style.theme);
        desktop_search_selection_=false;desktop_search_caret_=field.caret_from_x(measurement,i.pointer.x);
        field.set_caret(desktop_search_caret_);
    }
    return true;
}

bool Screen::handle_desktop_input(InputFrame&i,ui::Feedback&f){
    if(desktop_controller_style_!=i.controller_style){story_text_.clear();story_credits_.clear();}
    desktop_controller_style_=i.controller_style;
    ui::set_control_device(i.controller_style==DesktopControllerStyle::keyboard_mouse?ui::ControlDevice::keyboard_mouse:i.controller_style==DesktopControllerStyle::dualsense?ui::ControlDevice::playstation:ui::ControlDevice::xbox);
    auto pointer=i.pointer;
    if(!pointer.available){pointer.x=desktop_pointer_.x;pointer.y=desktop_pointer_.y;}
    desktop_pointer_=pointer;
    if(desktop_search_submit_rearm_){
        if(desktop_controller_style_!=DesktopControllerStyle::keyboard_mouse)desktop_search_submit_rearm_=false;
        else {
            // Leaving SDL text mode exposes a still-held Enter as a new
            // confirm edge. Consume that press/repeats through its release.
            // Later pointer/footer routing can still select a result explicitly.
            const bool down=i.text_submit||i.is_pressed(Action::confirm)||i.is_held(Action::confirm);
            i.pressed&=~action_bit(Action::confirm);i.held&=~action_bit(Action::confirm);i.text_submit=false;
            if(!down)desktop_search_submit_rearm_=false;
        }
    }
    if(i.focus_lost)return false;
    if(i.pointer.moved||i.pointer.primary_pressed||i.pointer.secondary_pressed||i.pointer.wheel_y||i.keyboard_active||!i.text_utf8.empty()||i.pressed||i.nav!=Direction::none||std::abs(i.stick_x)>.1f||std::abs(i.stick_y)>.1f||std::abs(i.stick2_x)>.1f||std::abs(i.stick2_y)>.1f||i.trigger_l>.04f||i.trigger_r>.04f){idle_=0;if(gallery_)gallery_overlay_age_=0;}
    if(desktop_controller_style_==DesktopControllerStyle::keyboard_mouse&&(gallery_||object_inspect_||(year_guide_&&guide_trophies_&&trophy_pin_open_)))i.trigger_l=i.trigger_r=0;
    if(desktop_controller_style_==DesktopControllerStyle::keyboard_mouse&&year_guide_&&guide_trophies_&&trophy_pin_open_)
        i.stick2_x=i.stick2_y=0;
    if(i.pointer.secondary_pressed&&!experience_active_)i.pressed|=action_bit(Action::back);
    if(application_dialog_){
        if(desktop_footer_input(i,f))return true;
        if(i.pointer.available&&(i.pointer.moved||i.pointer.primary_pressed))for(int action=0;action<application_action_count();++action)if(inside(application_action_bounds(action),i.pointer.x,i.pointer.y)){application_focus_=action;if(i.pointer.primary_pressed)i.pressed|=action_bit(Action::confirm);break;}
        return false;
    }
    if(application_open_.value>.001f)return false;
    if(support_dialog_){
        if(desktop_footer_input(i,f))return true;
        if(i.pointer.available){
            if(i.pointer.primary_pressed)for(const auto&link:desktop_links_)if(link.url==museum_support_url&&inside(link.bounds,i.pointer.x,i.pointer.y)){desktop_url_request_=link.url;f.play(audio::Cue::select);return true;}
            if(i.pointer.moved||i.pointer.primary_pressed)for(int action=0;action<support_action_count();++action)if(inside(support_action_bounds(action),i.pointer.x,i.pointer.y)){support_focus_=action;if(i.pointer.primary_pressed)i.pressed|=action_bit(Action::confirm);break;}
        }
        return false;
    }
    if(support_open_.value>.001f)return false;
    if(database_dialog_){
        if(desktop_footer_input(i,f))return true;
        if(i.pointer.primary_pressed&&i.pointer.available)for(int action=0;action<database_action_count();++action)if(inside(database_action_bounds(action),i.pointer.x,i.pointer.y)){database_focus_=action;i.pressed|=action_bit(Action::confirm);break;}
        return false;
    }
    if(database_open_.value>.001f)return false;
    const bool immersive_view=experience_active_||experience_open_.value>.001f||
        object_inspect_||(year_guide_&&guide_trophies_&&trophy_pin_open_);
    if(i.search_pressed&&boot_time_>=4.8f&&!collection_pending_&&!onboarding_&&!immersive_view&&!collection_remove_dialog_&&!collection_removal_active()){
        settings_=credits_=connection_panel_=desktop_video_open_=chapters_=false;video_.cancel_sign_in();open_search(f);return true;
    }
    if(i.pointer.primary_pressed&&i.pointer.available)for(const auto&link:desktop_links_)if(inside(link.bounds,i.pointer.x,i.pointer.y)){desktop_url_request_=link.url;f.play(audio::Cue::select);return true;}
    if(desktop_footer_input(i,f))return true;
    const auto&p=i.pointer;const bool click=p.primary_pressed,point=p.available&&(click||p.moved);
    if(collection_remove_dialog_){if(click)for(int row=0;row<2;++row)if(inside({470+row*505.f,675+(1-std::clamp(collection_remove_open_.value,0.f,1.f))*18,475,78},p.x,p.y)){collection_remove_focus_=row;i.pressed|=action_bit(Action::confirm);}return false;}
    if(collection_removal_active())return false;
    if(language_choice_){if(point)for(int row=0;row<5;++row)if(inside({135,416+row*88.f,720,76},p.x,p.y)){language_focus_=row;if(click)i.pressed|=action_bit(Action::confirm);}return false;}
    if(collection_pending_&&!onboarding_)return false;
    if(onboarding_){
        if(theme_choice_&&!theme_confirming_&&click)for(int row=0;row<2;++row)if(inside({300+row*710.f,420,610,240},p.x,p.y)){dark_theme_=row==0;i.pressed|=action_bit(Action::confirm);}
        // The final desktop hint names Enter; translate that physical confirm
        // only here, where the original shared intro expects its start action.
        if(!theme_choice_&&onboarding_step_==onboarding_cards_&&desktop_controller_style_==DesktopControllerStyle::keyboard_mouse&&i.is_pressed(Action::confirm))i.pressed|=action_bit(Action::menu);
        return false;
    }
    if(boot_time_<4.8f)return false;
    // Search covers the complete museum. Keep result indices in the complete
    // cultural collection even when the visitor arrived through a filter.
    if(search_prompt_.is_open()&&culture_filter_){culture_filter_=0;rebuild_history_filter();}
    if(handle_desktop_search(i,f))return true;
    const bool overlay=settings_||year_guide_||detail_||credits_||connection_panel_||chapters_||search_page_||gallery_||screening_||playlist_active_||object_inspect_||experience_active_||image_dialog_;
    if(i.desktop_escape_pressed&&!overlay){i.pressed&=~action_bit(Action::back);i.pressed|=action_bit(Action::menu);}
    if(click){
        const float panel_x=options_panel_x();
        if((settings_||credits_||connection_panel_)&&p.x<panel_x){settings_=credits_=connection_panel_=volumes_open_=desktop_video_open_=false;video_.cancel_sign_in();desktop_scroll_dragging_=false;f.play(audio::Cue::back);return true;}
        const bool preview=(guide_experiences_&&inside(guide_preview_bounds(),p.x,p.y))||(guide_trophies_&&trophy_pin_open_&&inside({720,110,1180,840},p.x,p.y));
        if(year_guide_&&!inside({guide_sidebar_x(),0,guide_sidebar_width_,981},p.x,p.y)&&!preview){year_guide_=false;trophy_focus_time_=0;desktop_scroll_dragging_=false;f.play(audio::Cue::back);return true;}
    }
    if(handle_desktop_scrolling(i,f))return true;
    int wheel=0;if(p.wheel_y){desktop_wheel_remainder_+=p.wheel_y;wheel=int(desktop_wheel_remainder_);desktop_wheel_remainder_-=wheel;wheel=std::clamp(wheel,-8,8);}
    if(search_page_){
        if(wheel&&p.available&&inside({96,312,1728,625},p.x,p.y))i.nav=wheel<0?Direction::down:Direction::up;
        if(click&&inside({96,160,1728,125},p.x,p.y)){open_search(f);return true;}
        if(click&&inside({96,312,1728,625},p.x,p.y)){
            const float first=std::max(0.f,search_position_.value-3.f);const int index=int(std::floor((p.y-322)/86+first));
            if(index>=0&&index<int(search_results_.size())){search_focus_=index;i.pressed|=action_bit(Action::confirm);}
        }return false;
    }
    if(experience_active_){
        bool pointer_handled=false;
        if(study_&&i.connected&&!experience_rearm_&&!experience_input_paused_&&!experience_paused_&&experience_pause_open_.value<.01f&&experience_open_.value>.98f&&study_->completion()==StudyCompletion::playing)pointer_handled=study_->desktop_pointer(p,f);
        if(p.secondary_pressed&&!pointer_handled)i.pressed|=action_bit(Action::back);
        if(click&&(experience_paused_||(study_&&study_->completion()!=StudyCompletion::playing))){
            const bool completed=study_&&study_->completion()!=StudyCompletion::playing,flight=!completed&&study_&&study_->flight_settings();
            for(int row=0;row<(flight?4:2);++row){const float y=(completed?620.f:flight?420.f:508.f)+row*(completed?96.f:flight?70.f:78.f);if(inside({680,y-38,560,68},p.x,p.y)){experience_pause_selection_=row;i.pressed|=action_bit(Action::confirm);}}
        }return false;
    }
    if(settings_&&!connection_panel_){
        const float x=options_panel_x();
        if(wheel&&p.available&&inside({x,180,810,760},p.x,p.y))i.nav=wheel<0?Direction::down:Direction::up;
        if(desktop_video_open_){
            if(point)for(int row=0;row<5;++row)if(inside({x+45,252+row*104.f,710,80},p.x,p.y)){desktop_video_focus_=row;if(click){if(row<4&&p.x<x+370)i.nav=Direction::left;else i.pressed|=action_bit(Action::confirm);}}
            return false;
        }
        if(volumes_open_){
            if(point||p.primary_held)for(int row=0;row<audio_slider_count;++row){if(!inside(audio_slider_bounds(x,row),p.x,p.y))continue;volume_focus_=row;
                if(click||p.primary_held){const std::array<float*,audio_slider_count> values={&master_volume_,&sfx_volume_,&volume_,&culture_volume_};const float value=std::clamp((p.x-x-65)/650,0.f,1.f);if(*values[size_t(row)]!=value){*values[size_t(row)]=value;dirty_=true;save_delay_=1;if(click)f.play(audio::Cue::slider);}return true;}}
            return false;
        }
        if(point)for(int row=0;row<desktop_preference_count();++row)if(inside(preference_row_bounds(x,row),p.x,p.y)){setting_=row;if(click)i.pressed|=action_bit(Action::confirm);}
        return false;
    }
    if(credits_)return false;
    if(connection_panel_)return false;
    if(year_guide_){
        const float x=guide_sidebar_x();
        if(wheel&&p.available&&inside({x,160,guide_sidebar_width_,632},p.x,p.y))i.nav=wheel<0?Direction::down:Direction::up;
        if(guide_trophies_&&trophy_pin_open_){if(p.primary_held){trophy_pin_yaw_+=p.delta_x*.009f;trophy_pin_pitch_=std::clamp(trophy_pin_pitch_+p.delta_y*.008f,-1.1f,1.1f);}if(wheel)trophy_pin_zoom_=std::clamp(trophy_pin_zoom_+wheel*.15f,.65f,2.6f);return false;}
        if(click&&guide_experiences_&&inside(guide_preview_bounds(),p.x,p.y)){i.pressed|=action_bit(Action::confirm);return false;}
        if(!click)return false;
        if(guide_trophies_){const auto all=trophies_?trophies_->views(true):std::vector<TrophyView>{};for(int n=std::max(0,int(trophy_position_.value)-3);n<std::min(int(all.size()),int(trophy_position_.value)+6);++n){const float y=470+(n-trophy_position_.value)*91;if(inside({x+40,y-40,680,86},p.x,p.y)&&p.y>=160&&p.y<948){trophy_focus_=n;trophy_focus_time_=0;trophy_expanded_=false;i.pressed|=action_bit(Action::confirm);break;}}}
        else if(guide_experiences_){for(int n=std::max(0,int(experience_position_.value)-4);n<std::min(int(study_catalog().size()),int(experience_position_.value)+6);++n){const float y=470+(n-experience_position_.value)*81;if(inside({x+32,y-33,680,76},p.x,p.y)&&p.y>=160&&p.y<792){experience_focus_=n;experience_description_scroll_=0;experience_description_clock_=0;f.play(audio::Cue::focus);return true;}}}
        else for(int n=std::max(0,int(year_position_.value)-5);n<std::min(int(years_.size()),int(year_position_.value)+7);++n){const float d=n-year_position_.value,y=524+d*66+(d<0?-38:38)*tween::smoothstep(std::min(1.f,std::abs(d)));if(inside({x+130,y-36,490,70},p.x,p.y)&&p.y>=292&&p.y<792){year_focus_=n;i.pressed|=action_bit(Action::confirm);break;}}
        return false;
    }
    if(gallery_){
        if(wheel){ui::Feedback silent;if(wheel>0)viewer_.zoom_in(silent);else viewer_.zoom_out(silent);}
        if(p.primary_held&&(std::abs(p.delta_x)>.01f||std::abs(p.delta_y)>.01f)){viewer_.pan_pixels(p.delta_x,p.delta_y);i.stick_x=i.stick_y=0;i.nav=Direction::none;}
        return false;
    }
    if(object_inspect_){if(wheel)object_zoom_=std::clamp(object_zoom_+wheel*.16f,.5f,4.f);if(p.primary_held){object_angle_+=p.delta_x*.009f;object_tilt_offset_=std::clamp(object_tilt_offset_+p.delta_y*.008f,-1.25f,1.25f);object_manual_=true;}return false;}
    if(screening_||playlist_active_){
        if(wheel){media_volume_=std::clamp(media_volume_+wheel*.05f,0.f,1.f);video_.volume(media_volume_);dirty_=true;save_delay_=1;}
        if(playlist_active_){
            playlist_hover_=-1;
            const auto*list=current_soundtrack();const auto*entry=current();
            if(list&&entry&&p.available){
                const auto rows=playlist_layout(*entry,*list);
                if(inside({100,rows.rows_y-29,1020,rows.visible*56.f},p.x,p.y)){
                    const int row=int((p.y-rows.rows_y+29)/56);
                    if(rows.first+row<int(list->tracks.size()))playlist_hover_=rows.first+row;
                }
            }
        }
        if(!click)return false;
        if(playlist_active_){
            const auto*list=current_soundtrack();if(!list)return false;
            const auto*entry=current();if(!entry)return false;const auto rows=playlist_layout(*entry,*list);
            const float top=rows.rows_y;const int count=rows.visible,first=rows.first;
            if(inside({100,top-29,1020,count*56.f},p.x,p.y)){const int row=int((p.y-top+29)/56);playlist_selection_=std::clamp(first+row,0,int(list->tracks.size())-1);i.pressed|=action_bit(Action::confirm);}
            else if(inside({100,881,1720,33},p.x,p.y)&&video_.state()==media::State::ready){const auto&track=list->tracks[size_t(std::clamp(playlist_playing_,0,int(list->tracks.size())-1))];const media::PlaybackWindow window{track.start_seconds,track.end_seconds};video_.seek(window.seek((p.x-100)/1720*window.duration(video_.duration()),video_.duration()));playlist_completed_=false;return true;}
        }else{
            const float full=std::clamp(video_full_.value,0.f,1.f);const Rect screen{screening_origin_.x*(1-full),screening_origin_.y*(1-full),screening_origin_.w+(1920-screening_origin_.w)*full,screening_origin_.h+(1080-screening_origin_.h)*full};
            const Rect seek=full>.999f?Rect{96,920,1728,36}:Rect{screen.x+30,screen.y+screen.h-66,screen.w-60,36};
            if(inside(seek,p.x,p.y)&&video_.state()==media::State::ready&&video_.duration()>0){video_.seek(std::clamp(double((p.x-seek.x)/seek.w),0.,1.)*video_.duration());film_progress_age_=0;return true;}
            if(inside(screen,p.x,p.y))i.pressed|=action_bit(Action::confirm);
        }return false;
    }
    if(gallery_open_.value>.01f||screening_open_.value>.01f||object_open_.value>.01f||(history_transition_&&fade_<1))return false;
    if(!chapters_&&click&&inside({1470,47,365,88},p.x,p.y)){jump_today(f);return true;}
    if(chapters_){if(wheel)i.nav=wheel<0?Direction::down:Direction::up;if(click)for(int row=0;row<int(catalog_.eras.size());++row){const float y=223+row*72+(row>chapter_focus_?118:0);if(inside({1037,y-38,775,row==chapter_focus_?190.f:68.f},p.x,p.y)){chapter_focus_=row;i.pressed|=action_bit(Action::confirm);break;}}return false;}
    if(detail_){
        const auto canvas=canvas_bounds();
        const float rise=(1-std::clamp(story_open_.value,0.f,1.f))*780;
        const bool extended_side=(p.x<0||p.x>=1920)&&inside(canvas,p.x,p.y);
        const int side_card=extended_side?story_card_at(p.x,p.y,story_position_.value,rise,int(story_cards_.size())):-1;
        if(wheel&&p.available){
            if(inside({canvas.x,142,canvas.w,124},p.x,p.y)){if(history_focus_)move_history(-wheel,f);else move(-wheel,f);return true;}
            if(inside(story_card,p.x,p.y)||side_card>=0){move_story(-wheel,f);return true;}
        }
        if(!click||story_cards_.empty())return false;
        if(side_card>=0&&side_card!=story_focus_){move_story(side_card-story_focus_,f);return true;}
        for(size_t n=0;n<story_actions_.size();++n){const auto&a=story_actions_[n];if(!inside(a.bounds,p.x,p.y))continue;story_action_=int(n);if(a.image>=0){image_index_=a.image;open_photo(a.bounds);f.play(audio::Cue::select);return true;}i.pressed|=action_bit(Action::confirm);return false;}
        const float segment=std::min(78.f,1540.f/std::max(size_t(1),story_cards_.size())),start=960-segment*story_cards_.size()*.5f;
        if(inside({start,916,segment*story_cards_.size(),30},p.x,p.y)){const int n=std::clamp(int((p.x-start)/segment),0,int(story_cards_.size())-1);move_story(n-story_focus_,f);return true;}
        for(int n=std::max(0,story_focus_-1);n<=std::min(int(story_cards_.size())-1,story_focus_+1);++n){const float x=960+(n-story_position_.value)*600;if(n!=story_focus_&&inside({x-270,946,540,34},p.x,p.y)){move_story(n-story_focus_,f);return true;}}
        if(inside({132,310,1656,575},p.x,p.y)){const auto&card=story_cards_[size_t(story_focus_)];if(story_object()||card.kind==StoryCard::experience||card.kind==StoryCard::interactive||card.kind==StoryCard::soundtrack)i.pressed|=action_bit(Action::confirm);}
        return false;
    }
    const auto canvas=canvas_bounds();
    if(wheel&&p.available&&inside({canvas.x,history_focus_?142.f:744.f,canvas.w,history_focus_?130.f:223.f},p.x,p.y)){if(history_focus_)move_history(-wheel,f);else move(-wheel,f);return true;}
    if(!click)return false;
    const int focus=history_focus_?history_focus_index_:focus_,count=history_focus_?int(history_catalog_.entries.size()):int(visible_.size());
    const auto&position=history_focus_?history_position_:timeline_;const int rail_focus=timeline_motion_.rail_focus(focus);
    float nearest=226.f;
    int selected=-1;
    for(int n=std::max(0,rail_focus-4);n<std::min(count,rail_focus+5);++n){
        if(!timeline_motion_.stop_visible(n))continue;
        const float x=timeline_stop_x(n-timeline_motion_.rail_position(position.value),history_focus_);
        if(!inside({x-225,history_focus_?150.f:775.f,450,history_focus_?115.f:170.f},p.x,p.y))continue;
        const float distance=std::abs(p.x-x);
        if(distance<nearest){nearest=distance;selected=timeline_motion_.content_index(n,focus);}
    }
    if(selected>=0){if(history_focus_)move_history(selected-history_focus_index_,f);else if(selected==focus_)i.pressed|=action_bit(Action::confirm);else move(selected-focus_,f);return false;}
    const auto*entry=current();if(!entry)return false;
    if(inside(history_focus_?history_image_bounds():Rect{950,220,826,478},p.x,p.y)){i.pressed|=action_bit(Action::west);return false;}
    if(!history_focus_&&inside({96,240,770,480},p.x,p.y))i.pressed|=action_bit(Action::confirm);
    return false;
}

Rect Screen::desktop_search_button_bounds(int index)const{
    const auto panel=search_prompt_.panel_rect();const auto&style=search_prompt_.style;
    const float inner=panel.w-2*style.padding,width=std::min(style.button_width,(inner-style.button_gap)*.5f),total=2*width+style.button_gap;
    return {panel.x+panel.w-style.padding-total+index*(width+style.button_gap),panel.y+panel.h-style.padding-style.button_height,width,style.button_height};
}

void Screen::draw_desktop_chrome(gfx::DrawList&out){
    const auto p=colours();
    const bool modal=application_dialog_||application_open_.value>.001f||support_dialog_||support_open_.value>.001f||database_dialog_||database_open_.value>.001f||settings_||credits_||connection_panel_||year_guide_||search_page_||search_prompt_.visible()||collection_remove_dialog_;
    const bool dark_media=!modal&&(gallery_||object_inspect_||(screening_&&!playlist_active_)||experience_active_);
    const Color paper=dark_media?Color::rgb(0x101612):p.paper,ink=dark_media?Color::rgb(0xf1efe7):p.ink,quiet=dark_media?Color::rgb(0xa6ada7):p.muted;
    const float hints_alpha=!modal&&gallery_?std::clamp(gallery_labels_.value,0.f,1.f):!modal&&screening_&&!playlist_active_&&video_full_.value>.999f?std::clamp(media_hints_.value,0.f,1.f):1.f;
    if(onboarding_&&!language_choice_&&!theme_choice_&&onboarding_step_==onboarding_cards_){
        out.rounded_rect({430,460,1060,160},0,p.paper);
        // Reuse the intro translations already present in baseline and active
        // database overlays, so either content revision keeps this localized.
        std::string prompt(i18n::tr("Press"));prompt+=' ';
        prompt+=desktop_controller_style_==DesktopControllerStyle::keyboard_mouse?"{cross}":"{options}";
        prompt+=' ';prompt+=i18n::tr("to begin");
        float size=48;while(size>30&&fonts_.display.measure(prompt,size)>1000)--size;
        ui::text(out,fonts_.display,prompt,960,555,size,p.ink,Align::center);
    }
    if(!modal&&screening_&&!playlist_active_&&video_full_.value>.999f){
        out.push_opacity(hints_alpha);
        // Fullscreen films retain a visible, clickable seek bar above the
        // desktop controls instead of leaving it beneath the control strip.
        const bool ready=video_.state()==media::State::ready;const double duration=ready?video_.duration():-1,time=ready?video_.time():-1;
        out.line(96,938,1824,938,2,ink.with_alpha(.25f));
        if(duration>0)out.line(96,938,96+1728*std::clamp(float(time/duration),0.f,1.f),938,2,ink);
        ui::text(out,fonts_.mono,playback_time(time)+" / "+playback_time(duration),96,970,18,ink);
        char status[80];ui::format(status,"Volume %d %%",int(std::round(media_volume_*100)));ui::text(out,fonts_.regular,status,1824,970,18,ink,Align::right);
        out.pop_opacity();
    }
    const auto controls=desktop_controls();if(controls.empty())return;
    const bool transparent=(!modal&&(gallery_||object_inspect_||(screening_&&!playlist_active_&&video_full_.value>.999f)))||(year_guide_&&guide_trophies_&&trophy_pin_open_&&!settings_&&!credits_&&!connection_panel_);
    out.push_opacity(hints_alpha);
    const auto canvas=canvas_bounds();
    if(!transparent)out.rounded_rect({canvas.x,981,canvas.w,99},0,paper);
    const bool controller=desktop_controller_style_!=DesktopControllerStyle::keyboard_mouse;
    for(const auto&control:controls){
        const auto&b=control.bounds;const bool hover=control.command>=0&&desktop_pointer_.available&&inside(b,desktop_pointer_.x,desktop_pointer_.y);
        if(hover)out.rounded_rect(b,5,ink.with_alpha(.055f));
        const float scale=control.scale,x=b.x+8;
        const float left_key=key_cap_width(fonts_.mono,control.key)*scale;
        const float key=controller
            ?(ui::button_width(control.glyph,28)+(control.second==ui::Button::none?0.f:12+ui::button_width(control.second,28)))*scale
            :left_key+(control.second_key.empty()?0.f:(8+key_cap_width(fonts_.mono,control.second_key))*scale);
        const auto shadow=(ink.r+ink.g+ink.b)>1.5f?Color::rgb(0,.65f):Color::rgb(0xffffff,.6f);
        if(controller){
            if(transparent){
                ui::draw_button(out,fonts_,ui::GlyphStyle::mono(shadow,Color::rgb(0,0)),control.glyph,x+4.4f,b.cy()+1.4f,28*scale);
                if(control.second!=ui::Button::none)ui::draw_button(out,fonts_,ui::GlyphStyle::mono(shadow,Color::rgb(0,0)),control.second,x+(ui::button_width(control.glyph,28)+12)*scale+1.4f,b.cy()+1.4f,28*scale);
            }
            ui::draw_button(out,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),control.glyph,x+3,b.cy(),28*scale);
            if(control.second!=ui::Button::none)ui::draw_button(out,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),control.second,x+(ui::button_width(control.glyph,28)+12)*scale,b.cy(),28*scale);
        }
        else{
            const auto cap=[&](const std::string&label,float left,float width){
                const float center=left+width*.5f;
                if(transparent)out.text(*fonts_.mono.font,fonts_.mono.texture,label,center+1.4f,b.y+33.4f,16*scale,shadow,Align::center);
                out.bordered_rect({left,b.y+11,width,30},4,transparent?Color::rgb(0,0):paper,1,ink.with_alpha(.24f));
                out.text(*fonts_.mono.font,fonts_.mono.texture,label,center,b.y+32,16*scale,ink,Align::center);
            };
            cap(control.key,x,left_key);
            if(!control.second_key.empty())cap(control.second_key,x+left_key+8*scale,key_cap_width(fonts_.mono,control.second_key)*scale);
        }
        if(transparent)ui::text(out,fonts_.regular,control.label,x+key+11.4f,b.y+34.4f,19*scale,shadow);
        ui::text(out,fonts_.regular,control.label,x+key+10,b.y+33,19*scale,hover?ink:quiet);
    }
    out.pop_opacity();
}
void Screen::render_desktop_chrome(){desktop_layer_.clear();draw_desktop_chrome(desktop_layer_);renderer_.draw(desktop_layer_);}

bool Screen::take_desktop_url_request(std::string&url){
    if(desktop_url_request_.empty())return false;
    url=std::move(desktop_url_request_);desktop_url_request_.clear();return true;
}
bool Screen::desktop_can_open_sign_in_browser(const media::Connection& c)const{
    return !c.signed_in&&!c.user_code.empty()&&browser_url(c.verification_url);
}
bool Screen::desktop_open_sign_in_browser(const media::Connection& c){
    if(!desktop_can_open_sign_in_browser(c))return false;
    desktop_url_request_=c.verification_url;return true;
}
void Screen::draw_desktop_sign_in_browser(const media::Connection& c,float x){
    if(!desktop_can_open_sign_in_browser(c))return;
    const auto p=colours();const Rect bounds{x+64,886,670,64};
    overlay_.bordered_rect(bounds,4,p.ink.with_alpha(.055f),1,p.ink.with_alpha(.32f));
    const char*label="Open in browser";
    ui::text(overlay_,fonts_.semibold,label,bounds.cx(),menu_text_baseline(fonts_.semibold,label,bounds.cy(),25),25,p.ink,Align::center);
    desktop_add_link(bounds,c.verification_url);
}
void Screen::desktop_add_link(Rect bounds,const std::string&url){
    if(bounds.w<=0||bounds.h<=0||!browser_url(url))return;
    desktop_links_.push_back({bounds,url});
}
void Screen::desktop_add_text_links(const std::string&text,float x,float baseline,float size,Rect clip,bool site_names){
    static const auto sites=[](){
        std::unordered_set<std::string> result;const std::string all=feature_resources_sites;size_t start=0;
        while(start<all.size()){const auto end=all.find(" | ",start);result.insert(all.substr(start,end==std::string::npos?end:end-start));if(end==std::string::npos)break;start=end+3;}
        return result;
    }();
    for(size_t at=0;at<text.size();){
        at=text.find_first_not_of(" \t|",at);if(at==std::string::npos)break;
        const auto end=text.find_first_of(" \t|",at);const auto token=text.substr(at,end==std::string::npos?end:end-at);
        std::string url;
        if(token.rfind("https://",0)==0||token.rfind("http://",0)==0){
            url=token;
            if(const auto*entry=current())for(const auto&source:entry->sources)if(source.url.rfind(token,0)==0){url=source.url;break;}
        }else if(site_names&&sites.contains(token))url="https://"+token;
        if(!url.empty()){
            Rect bounds{x+fonts_.regular.font->measure(std::string_view(text).substr(0,at),size),baseline-fonts_.regular.font->ascent(size),fonts_.regular.font->measure(token,size),size*1.25f};
            const float left=std::max(bounds.x,clip.x),top=std::max(bounds.y,clip.y),right=std::min(bounds.x+bounds.w,clip.x+clip.w),bottom=std::min(bounds.y+bounds.h,clip.y+clip.h);
            desktop_add_link({left,top,right-left,bottom-top},url);
        }
        if(end==std::string::npos)break;at=end+1;
    }
}
bool Screen::desktop_pointer_interactive()const{
    return desktop_pointer_.available&&desktop_pointer_target(desktop_pointer_.x,desktop_pointer_.y);
}
bool Screen::desktop_pointer_target(float x,float y)const{
    if(application_dialog_){for(int action=0;action<application_action_count();++action)if(inside(application_action_bounds(action),x,y))return true;for(const auto&control:desktop_controls())if(control.command>=0&&inside(control.bounds,x,y))return true;return false;}
    if(application_open_.value>.001f)return false;
    if(support_dialog_){
        for(int action=0;action<support_action_count();++action)if(inside(support_action_bounds(action),x,y))return true;
        for(const auto&link:desktop_links_)if(link.url==museum_support_url&&inside(link.bounds,x,y))return true;
        for(const auto&control:desktop_controls())if(control.command>=0&&inside(control.bounds,x,y))return true;
        return false;
    }
    if(support_open_.value>.001f)return false;
    if(database_dialog_){for(int action=0;action<database_action_count();++action)if(inside(database_action_bounds(action),x,y))return true;for(const auto&control:desktop_controls())if(control.command>=0&&inside(control.bounds,x,y))return true;return false;}
    if(database_open_.value>.001f)return false;
    for(const auto&control:desktop_controls())if(control.command>=0&&inside(control.bounds,x,y))return true;
    for(const auto&link:desktop_links_)if(inside(link.bounds,x,y))return true;
    for(const auto&a:desktop_scroll_areas_)if(desktop_scroll_enabled(a.target)&&inside({a.track.x-9,a.track.y,a.track.w+18,a.track.h},x,y))return true;
    if(collection_remove_dialog_){const float rise=(1-std::clamp(collection_remove_open_.value,0.f,1.f))*18;return inside({470,675+rise,475,78},x,y)||inside({975,675+rise,475,78},x,y);}
    if(collection_removal_active())return false;
    if(language_choice_){for(int row=0;row<5;++row)if(inside({135,416+row*88.f,720,76},x,y))return true;return false;}
    if(collection_pending_&&!onboarding_)return false;
    if(onboarding_){return theme_choice_&&!theme_confirming_&&(inside({300,420,610,240},x,y)||inside({1010,420,610,240},x,y));}
    if(boot_time_<4.8f)return false;
    if(search_prompt_.is_open()){
        if(inside(search_prompt_.field.field_rect(),x,y)||inside(desktop_search_button_bounds(0),x,y)||inside(desktop_search_button_bounds(1),x,y))return true;
        const auto&keyboard=search_prompt_.keyboard;
        if(!keyboard.layouts().empty()){const auto&rows=keyboard.layouts()[size_t(keyboard.layout())].rows;for(size_t row=0;row<rows.size();++row)for(size_t key=0;key<rows[row].size();++key)if(inside(keyboard.key_rect(int(row),int(key)),x,y))return true;}
        return false;
    }
    if(search_page_){
        if(inside({96,160,1728,125},x,y))return true;
        const float first=std::max(0.f,search_position_.value-3.f);const int row=int(std::floor((y-322)/86+first));
        return inside({96,312,1728,625},x,y)&&row>=0&&row<int(search_results_.size());
    }
    if(experience_active_){
        const bool completed=study_&&study_->completion()!=StudyCompletion::playing;
        if(experience_paused_||completed){const bool flight=!completed&&study_&&study_->flight_settings();for(int row=0;row<(flight?4:2);++row){const float top=(completed?620.f:flight?420.f:508.f)+row*(completed?96.f:flight?70.f:78.f);if(inside({680,top-38,560,68},x,y))return true;}return false;}
        return study_&&!experience_rearm_&&!experience_input_paused_&&experience_pause_open_.value<.01f&&experience_open_.value>.98f&&study_->desktop_pointer_interactive(x,y);
    }
    if(settings_&&!connection_panel_){
        const float panel_x=options_panel_x();
        if(desktop_video_open_){if(desktop_video_applying_)return false;for(int row=0;row<5;++row)if(inside({panel_x+45,252+row*104.f,710,80},x,y))return true;return false;}
        if(volumes_open_){for(int row=0;row<audio_slider_count;++row)if(inside(audio_slider_bounds(panel_x,row),x,y))return true;return false;}
        for(int row=0;row<desktop_preference_count();++row)if(inside(preference_row_bounds(panel_x,row),x,y))return true;
        return false;
    }
    if(credits_||connection_panel_)return false;
    if(year_guide_){
        if(guide_trophies_&&trophy_pin_open_)return inside({720,110,1180,840},x,y);
        const float panel_x=guide_sidebar_x();
        if(guide_experiences_){
            if(inside(guide_preview_bounds(),x,y))return true;
            for(int n=std::max(0,int(experience_position_.value)-4);n<std::min(int(study_catalog().size()),int(experience_position_.value)+6);++n){const float top=470+(n-experience_position_.value)*81;if(y>=160&&y<792&&inside({panel_x+32,top-33,680,76},x,y))return true;}
        }else if(guide_trophies_){const auto all=trophies_?trophies_->views(true):std::vector<TrophyView>{};for(int n=std::max(0,int(trophy_position_.value)-3);n<std::min(int(all.size()),int(trophy_position_.value)+6);++n){const float top=470+(n-trophy_position_.value)*91;if(y>=160&&y<948&&inside({panel_x+40,top-40,680,86},x,y))return true;}}
        else for(int n=std::max(0,int(year_position_.value)-5);n<std::min(int(years_.size()),int(year_position_.value)+7);++n){const float d=n-year_position_.value,top=524+d*66+(d<0?-38:38)*tween::smoothstep(std::min(1.f,std::abs(d)));if(y>=292&&y<792&&inside({panel_x+130,top-36,490,70},x,y))return true;}
        return false;
    }
    if(gallery_)return viewer_.zoomed()&&inside({0,0,1920,981},x,y);
    if(object_inspect_)return inside({0,42,1920,918},x,y);
    if(screening_||playlist_active_){
        if(playlist_active_){
            const auto*list=current_soundtrack();const auto*entry=current();if(!list||!entry)return false;
            const auto rows=playlist_layout(*entry,*list);const float top=rows.rows_y;const int count=rows.visible;
            return inside({100,top-29,1020,count*56.f},x,y)||(video_.state()==media::State::ready&&inside({100,881,1720,33},x,y));
        }
        const float full=std::clamp(video_full_.value,0.f,1.f);const Rect screen{screening_origin_.x*(1-full),screening_origin_.y*(1-full),screening_origin_.w+(1920-screening_origin_.w)*full,screening_origin_.h+(1080-screening_origin_.h)*full};
        return inside(screen,x,y);
    }
    if(gallery_open_.value>.01f||screening_open_.value>.01f||object_open_.value>.01f||(history_transition_&&fade_<1))return false;
    if(!chapters_&&!today_entries(history_focus_).empty()&&inside({1470,47,365,88},x,y))return true;
    if(chapters_){for(int row=0;row<int(catalog_.eras.size());++row){const float top=223+row*72+(row>chapter_focus_?118:0);if(inside({1037,top-38,775,row==chapter_focus_?190.f:68.f},x,y))return true;}return false;}
    if(detail_){
        for(const auto&action:story_actions_)if(inside(action.bounds,x,y))return true;
        if(story_cards_.empty())return false;
        if(x<0||x>=1920){
            const float rise=(1-std::clamp(story_open_.value,0.f,1.f))*780;
            const int side_card=story_card_at(x,y,story_position_.value,rise,int(story_cards_.size()));
            if(side_card>=0&&side_card!=story_focus_)return true;
        }
        const float segment=std::min(78.f,1540.f/std::max(size_t(1),story_cards_.size())),start=960-segment*story_cards_.size()*.5f;
        if(inside({start,916,segment*story_cards_.size(),30},x,y))return true;
        for(int n=std::max(0,story_focus_-1);n<=std::min(int(story_cards_.size())-1,story_focus_+1);++n){const float left=960+(n-story_position_.value)*600;if(n!=story_focus_&&inside({left-270,946,540,34},x,y))return true;}
        const auto&card=story_cards_[size_t(story_focus_)];return inside({132,310,1656,575},x,y)&&(story_object()||card.kind==StoryCard::experience||card.kind==StoryCard::interactive||card.kind==StoryCard::soundtrack);
    }
    const int focus=history_focus_?history_focus_index_:focus_,count=history_focus_?int(history_catalog_.entries.size()):int(visible_.size());const auto&position=history_focus_?history_position_:timeline_;const int rail_focus=timeline_motion_.rail_focus(focus);
    for(int n=std::max(0,rail_focus-4);n<std::min(count,rail_focus+5);++n){if(!timeline_motion_.stop_visible(n))continue;const float center=timeline_stop_x(n-timeline_motion_.rail_position(position.value),history_focus_);if(inside({center-225,history_focus_?150.f:775.f,450,history_focus_?115.f:170.f},x,y))return true;}
    const auto*entry=current();if(!entry)return false;
    if((!entry->images.empty()||!entry->models.empty())&&inside(history_focus_?history_image_bounds():Rect{950,220,826,478},x,y))return true;
    return !history_focus_&&inside({96,240,770,480},x,y);
}
void Screen::render_desktop_cursor(){
    if(detail_&&!application_dialog_&&application_open_.value<.001f&&!database_dialog_&&database_open_.value<.001f&&!settings_&&!credits_&&!year_guide_&&!search_page_&&!search_prompt_.visible()&&!gallery_&&!screening_&&story_focus_>=0&&story_focus_<int(story_text_.size())&&story_focus_<int(story_cards_.size())){
        const auto&card=story_cards_[size_t(story_focus_)];const auto&text=story_text_[size_t(story_focus_)];
        const bool media=card.image>=0||card.kind==StoryCard::film||card.kind==StoryCard::object,reverse=media&&card.kind==StoryCard::narrative&&(story_focus_%2==0);
        const float shift=(story_focus_-story_position_.value)*story_card_pitch,rise=(1-std::clamp(story_open_.value,0.f,1.f))*780,left=(media?(reverse?1214.f:144.f):184.f)+shift,width=media?560.f:1440.f,top=404+text.title_height+(card.title.empty()?0:28.f);
        const Rect clip{left,std::max(266.f,top-28+rise),width,std::min(938.f,824+rise)-std::max(266.f,top-28+rise)};
        for(const auto&row:text.rows())desktop_add_text_links(row.text,left,top+row.baseline-scroll_.value+rise,row.size,clip);
    }
    const bool visible=desktop_pointer_.available&&inside(canvas_bounds(),desktop_pointer_.x,desktop_pointer_.y),interactive=visible&&desktop_pointer_interactive();
    const float step=std::clamp(dt_,0.f,.1f);
    desktop_cursor_alpha_+=std::clamp((visible?1.f:0.f)-desktop_cursor_alpha_,-step/.1f,step/.1f);
    desktop_cursor_glow_+=std::clamp((interactive?1.f:0.f)-desktop_cursor_glow_,-step/.16f,step/.16f);
    if(desktop_cursor_alpha_<=0)return;
    desktop_cursor_layer_.clear();auto&out=desktop_cursor_layer_;out.push_opacity(desktop_cursor_alpha_);
    // Cursor geometry lives in the same 1920x1080 logical canvas as the UI.
    // Scaling it back to physical pixels made it half-sized on a 4K screen.
    constexpr float pixel=1.f;
    const float x=std::round(desktop_pointer_.x/pixel)*pixel,y=std::round(desktop_pointer_.y/pixel)*pixel;
    const Rect square{x-4*pixel,y-4*pixel,8*pixel,8*pixel};const auto gold=Color::rgb(0xe9b74e);
    if(desktop_cursor_glow_>0){out.shadow(square.inset(-4*pixel),0,13*pixel,gold.with_alpha(.5f*desktop_cursor_glow_));out.shadow(square.inset(-2*pixel),0,5*pixel,gold.with_alpha(desktop_cursor_glow_));}
    const bool dark=desktop_dark_theme();out.bordered_rect(square.inset(-pixel),0,Color::rgb(0,0),pixel,Color::rgb(dark?0x000000:0xffffff,(1-desktop_cursor_glow_)/3));
    out.rounded_rect(square,0,Color::rgb(dark?0xffffff:0x111111));out.pop_opacity();renderer_.draw(out);
}
}
#endif
