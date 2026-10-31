// Pixel Museum - an atlas of playable ideas, opened directly from exhibit cards.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/study_controls.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {

using namespace hui;
using gfx::Rect;using gfx::Color;using gfx::Align;
namespace {
std::string study_referent(const StudyInfo&info,const Catalog&catalog){
    if(info.id=="pocket-budget")return "Gunpei Yokoi / Game Boy";
    if(info.id=="adaptive-pulse")return "Koji Kondo";
    if(info.id=="jump-lab")return "Shigeru Miyamoto";
    if(const auto*entry=catalog.find_entry(info.entry_id))return entry->title;
    return info.entry_id;
}
}
void Screen::open_experience(int index,Rect origin){
    const auto&all=study_catalog();if(index<0||index>=int(all.size()))return;
    auto candidate=make_study(all[size_t(index)].id);
    if(!candidate&&all[size_t(index)].id!="pixels")return;
    experience_index_=index;experience_origin_=origin;study_=std::move(candidate);
    experience_audio_.stop();if(study_){study_->reset();study_->attach_audio(&experience_audio_);}else workshop_.reset();
    experience_audio_.start(all[size_t(index)].id);experience_audio_.paused(false);
    experience_paused_=false;experience_completion_seen_=false;experience_pause_selection_=0;experience_pause_open_.snap(0);
    experience_introduction_=false;experience_intro_.snap(0);experience_active_=true;motion_calibrated_=false;
}
bool Screen::handle_experience(const InputFrame&i,ui::Feedback&f){
    if(!experience_active_)return experience_open_.value>.001f;
    const auto completion=study_?study_->completion():StudyCompletion::playing;
    if(completion!=StudyCompletion::playing){
        if(!experience_completion_seen_){
            experience_completion_seen_=true;experience_pause_selection_=0;
            f.feel(audio::Tactile::confirm,.25f,.13f);
            return true;
        }
        if(experience_pause_open_.value<.90f)return true;
        // A completed level has its own explicit choice. Neither a held button
        // nor Options can skip this sheet and silently advance the level.
        const int before=experience_pause_selection_;
        if(i.nav==Direction::up)experience_pause_selection_=0;
        if(i.nav==Direction::down)experience_pause_selection_=1;
        if(before!=experience_pause_selection_)f.play(audio::Cue::focus);
        if(i.is_pressed(Action::back)){experience_pause_selection_=1;f.play(audio::Cue::back);}
        if(i.is_pressed(Action::confirm)){
            if(experience_pause_selection_==1){experience_audio_.stop();experience_active_=false;}
            else{study_->continue_level();experience_audio_.paused(false);}
            experience_paused_=false;experience_completion_seen_=false;
            experience_pause_selection_=0;f.play(audio::Cue::select);
        }
        return true;
    }
    if(i.is_pressed(Action::menu)){
        if(!experience_paused_&&study_){auto lost=i;lost.focus_lost=true;ui::Feedback discarded;study_->handle(lost,discarded);study_->take_note();}
        experience_paused_=!experience_paused_;experience_pause_selection_=0;
        experience_audio_.paused(experience_paused_);f.play(experience_paused_?audio::Cue::modal_open:audio::Cue::modal_close);return true;
    }
    if(experience_paused_){
        const bool flight=study_&&study_->flight_settings();
        const int last=flight?3:1;
        const int before=experience_pause_selection_;
        if(i.nav==Direction::up)experience_pause_selection_=std::max(0,experience_pause_selection_-1);
        if(i.nav==Direction::down)experience_pause_selection_=std::min(last,experience_pause_selection_+1);
        if(before!=experience_pause_selection_)f.play(audio::Cue::focus);
        if(flight&&(i.nav==Direction::left||i.nav==Direction::right)){
            if(experience_pause_selection_==1){study_->configure_gyro(!study_->gyro_enabled(),study_->gyro_sensitivity());f.play(audio::Cue::toggle);}
            if(experience_pause_selection_==2){const float old=study_->gyro_sensitivity(),value=std::clamp(old+(i.nav==Direction::right?.25f:-.25f),.5f,2.f);if(value!=old){study_->configure_gyro(study_->gyro_enabled(),value);f.play(audio::Cue::slider,1.f,i.nav==Direction::right?.4f:-.4f);}}
        }
        if(i.is_pressed(Action::back)){experience_paused_=false;experience_audio_.paused(false);f.play(audio::Cue::back);}
        else if(i.is_pressed(Action::confirm)){
            if(flight&&experience_pause_selection_==1){study_->configure_gyro(!study_->gyro_enabled(),study_->gyro_sensitivity());f.play(audio::Cue::toggle);return true;}
            if(flight&&experience_pause_selection_==2){if(study_->gyro_sensitivity()!=1.f){study_->configure_gyro(study_->gyro_enabled(),1.f);f.play(audio::Cue::slider);}return true;}
            if(experience_pause_selection_==last){experience_audio_.stop();experience_active_=false;}
            else experience_audio_.paused(false);
            experience_paused_=false;f.play(audio::Cue::select);
        }
        return true;
    }
    // Drain no gameplay input while the pause sheet is fading away.
    if(experience_pause_open_.value>.01f)return true;
    if(experience_open_.value<.98f)return true;
    if(experience_introduction_){
        if(i.is_pressed(Action::confirm)){experience_introduction_=false;f.play(audio::Cue::select);}
        return true;
    }
    if(experience_intro_.value>.01f)return true;
    auto control=i;

    if(study_){
        study_->handle(control,f);
    }else{
        const auto previous_x=workshop_.cursor_x(),previous_y=workshop_.cursor_y();
        const auto tactile_count=f.tactile.size();
        if(i.touch.available&&i.touch.count&&std::isfinite(i.touch.points[0].x)&&std::isfinite(i.touch.points[0].y)){
            const auto&p=i.touch.points[0];const unsigned x=unsigned(std::clamp(int(p.x*8),0,7)),y=unsigned(std::clamp(int(p.y*8),0,7));
            workshop_.set_cursor(x,y);control.nav=Direction::none;
        }
        if(i.is_pressed(Action::touch))control.pressed|=action_bit(Action::confirm);
        workshop_.handle(control,f);
        if((previous_x!=workshop_.cursor_x()||previous_y!=workshop_.cursor_y())&&f.tactile.size()==tactile_count&&tactile_repeat_<=0){f.feel(audio::Tactile::focus,.045f,.018f,float(int(workshop_.cursor_x())-int(previous_x))*.25f);tactile_repeat_=.08f;}
    }
    return true;
}
void Screen::draw_study_preview(gfx::DrawList&list,int index,Rect bounds){
    const auto&all=study_catalog();if(index<0||index>=int(all.size()))return;
    if(study_preview_index_!=index){study_preview_=make_study(all[size_t(index)].id);if(study_preview_)study_preview_->reset();study_preview_index_=index;}
    if(study_preview_&&!reduced_&&!experience_active_&&study_preview_frame_time_!=time_){
        study_preview_->update(std::clamp(dt_,0.f,.05f));study_preview_frame_time_=time_;
    }
    const auto palette=colours();list.push_clip(bounds);
    if(study_preview_)study_preview_->draw(list,fonts_,bounds,tone_);
    else{list.rounded_rect(bounds,0,palette.paper);workshop_.draw(list,fonts_,bounds,tone_,false);}
    list.pop_clip();
}
void Screen::draw_experience_library(float){
    const auto palette=colours();const Color ink=palette.ink,quiet=palette.muted;
    const auto&all=study_catalog();
    ui::text(overlay_,fonts_.mono,"EXPERIENCES",64,92,19,quiet,Align::left,2);
    overlay_.push_clip({32,160,680,632});
    const int first=std::max(0,int(experience_position_.value)-4),last=std::min(int(all.size())-1,int(experience_position_.value)+5);
    for(int n=first;n<=last;++n){
        const float d=float(n)-experience_position_.value,focus=std::max(0.f,1-std::abs(d)),y=470+d*81;
        const auto&entry=all[size_t(n)];float size=23+6*focus;
        char label[40];hui::ui::format(label,"%02d",n+1);
        // Reserve the number's own advance plus a visible gap and SDF padding.
        const float title_width=676-fonts_.mono.measure(label,16)-32-110;
        overlay_.line(64,y-14,78+focus*16,y-14,1+focus,tone_.with_alpha(.3f+.7f*focus));
        while(fonts_.semibold.measure(entry.title,size)>title_width&&size>22)--size;
        const bool two_lines=fonts_.semibold.measure(entry.title,size)>title_width;
        if(two_lines){const auto title=ui::paragraph_lines(fonts_.semibold,entry.title,22,title_width,99);ui::paragraph(overlay_,fonts_.semibold,title,110,y-12,22,24,ink.with_alpha(.35f+.65f*focus));}
        else ui::text(overlay_,fonts_.semibold,entry.title,110,y,size,ink.with_alpha(.35f+.65f*focus));
        const auto referent=study_referent(entry,catalog_);float referent_size=16;
        while(fonts_.regular.measure(referent,referent_size)>534&&referent_size>12)--referent_size;
        ui::text(overlay_,fonts_.regular,referent,110,y+(two_lines?39:25),referent_size,quiet.with_alpha(.5f+.5f*focus));
        ui::text(overlay_,fonts_.mono,label,676,y,16,quiet,Align::right);
    }
    overlay_.pop_clip();
    if(!all.empty()){
        const auto&selected=all[size_t(std::clamp(experience_focus_,0,int(all.size())-1))];
        overlay_.line(64,812,676,812,1,ink.with_alpha(.15f));
        const auto lines=ui::paragraph_lines(fonts_.regular,selected.explanation,21,612,999);
        experience_description_max_=std::max(0.f,float(lines.lines.size())*30-140);
        experience_description_scroll_=std::clamp(experience_description_scroll_,0.f,experience_description_max_);
        if(experience_description_max_>0&&experience_description_clock_>0&&!reduced_){const float travel=experience_description_max_/22.f,phase=std::fmod(experience_description_clock_,travel+4.f);experience_description_scroll_=std::clamp((phase-2.f)*22.f,0.f,experience_description_max_);}
        overlay_.push_clip({64,830,612,140});
        ui::paragraph(overlay_,fonts_.regular,lines,64,850-experience_description_scroll_,21,30,quiet);
        overlay_.pop_clip();
        if(experience_description_max_>0){overlay_.line(690,830,690,970,1,quiet.with_alpha(.2f));const float thumb=std::max(16.f,140.f*140.f/(experience_description_max_+140));const float y=830+(140-thumb)*experience_description_scroll_/experience_description_max_;overlay_.line(690,y,690,y+thumb,2,tone_);}
    }
    const ui::Hint buttons[]={{ui::Button::square,"Years"},{ui::Button::triangle,"Exhibit"},{ui::Button::right_stick,"Read"}};
    ui::HintLayout l;l.cy=1014;l.size=25;l.text_size=18;l.item_gap=23;
    ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),buttons,3,64,false,l);
}
void Screen::draw_experience(){
    const auto&all=study_catalog();if(experience_index_<0||experience_index_>=int(all.size()))return;
    const auto&info=all[size_t(experience_index_)];
    const auto completion=study_?study_->completion():StudyCompletion::playing;
    const bool completed=completion!=StudyCompletion::playing;
    const bool final=completion==StudyCompletion::experience_complete;
    const Color background=Color::rgb(0x0b100e),ink=Color::rgb(0xf1efe7);
    const bool arcade_paper=info.id=="paddle"||info.id=="bricks"||info.id=="gravity";
    const bool workshop_paper=info.id=="pixels"||info.id=="cartridge-rules"||info.id=="pocket-budget"||info.id=="adaptive-pulse"||info.id=="jump-lab"||info.id=="city-system";
    const bool motion_dark=info.id=="jump"||info.id=="momentum"||info.id=="dash"||info.id=="rhythm"||info.id=="sequencer"||info.id=="wind";
    const Color canvas=info.id=="pixels"?Color::rgb(0xf1efe7):arcade_paper?Color::rgb(0xf1efe7):workshop_paper?Color{.945f,.937f,.906f,1}:motion_dark?Color{.035f,.055f,.065f,1}:Color::rgb(info.id=="portals"||info.id=="wireframe"?0x0d1310:0x101512);
    const Color control_ink=arcade_paper||workshop_paper?Color::rgb(0x24302a):ink;
    const float a=tween::smoothstep(std::clamp(experience_open_.value,0.f,1.f));
    const Rect from=experience_origin_,full{0,0,1920,1080};
    const Rect box{from.x*(1-a),from.y*(1-a),from.w+(full.w-from.w)*a,from.h+(full.h-from.h)*a};
    experience_layer_.push_clip(box);experience_layer_.push_opacity(a);
    // Extend each study's own canvas into its aspect-ratio margins. The play
    // geometry stays undistorted; no unrelated black bars surround the scene.
    experience_layer_.rounded_rect(box,0,canvas);
    const float scale=box.w/1920;experience_layer_.push_transform(scale,0,0,box.x,box.y);
    // The game uses the screen; only the persistent control strip is reserved.
    if(study_)study_->draw(experience_layer_,fonts_,{0,0,1920,960},tone_);
    else workshop_.draw(experience_layer_,fonts_,{0,0,1920,960},tone_,true);
    experience_layer_.gradient_rect({0,960,1920,120},0,canvas,gfx::mix(canvas,tone_,.055f));
    const float pause=experience_pause_open_.value;
    if(!completed&&pause<.999f){
        experience_layer_.push_opacity(1-pause);
        draw_study_controls(experience_layer_,fonts_,info.id,{64,990,1792,88},control_ink,canvas,true);
        experience_layer_.pop_opacity();
    }
    if(pause>.001f){
        experience_layer_.push_opacity(pause);
        experience_layer_.rounded_rect({0,0,1920,1080},0,background.with_alpha(.88f));
        experience_layer_.push_transform(1,0,0,0,(1-pause)*18);
        const bool flight=!completed&&study_&&study_->flight_settings();
        ui::text(experience_layer_,fonts_.display,completed?(final?"Experience complete":"Level complete"):"Paused",960,completed?310.f:flight?330.f:420.f,56,ink,Align::center);
        if(completed){
            char progress[80];hui::ui::format(progress,"%s / %d of %d",final?"COMPLETED":"LEVEL",study_->level_number(),study_->level_count());
            ui::text(experience_layer_,fonts_.mono,progress,960,372,18,tone_,Align::center);
            const auto referent=study_referent(info,catalog_);
            ui::text(experience_layer_,fonts_.regular,referent,960,420,22,ink.with_alpha(.65f),Align::center);
            ui::paragraph(experience_layer_,fonts_.regular,final?"Continue to play again, or return to the museum.":"Continue when you are ready for the next level.",960,500,21,1040,32,ink.with_alpha(.65f),2,Align::center);
        }
        char sensitivity[64];hui::ui::format(sensitivity,"Sensitivity  %.2fx",flight?study_->gyro_sensitivity():1.f);
        const char*flight_choices[]={"Continue",flight&&study_->gyro_enabled()?"Gyroscope  On":"Gyroscope  Off",sensitivity,"Exit experience"};
        const char*choices[]={"Continue","Exit experience"};
        for(int n=0;n<(flight?4:2);++n){
            const float y=(completed?620.f:flight?420.f:508.f)+n*(completed?96.f:flight?70.f:78.f);
            if(n==experience_pause_selection_)experience_layer_.line(740,y+17,1180,y+17,2,tone_);
            ui::text(experience_layer_,fonts_.semibold,flight?flight_choices[n]:choices[n],960,y,30,ink.with_alpha(n==experience_pause_selection_?1.f:.5f),Align::center);
        }
        experience_layer_.pop_transform();experience_layer_.pop_opacity();
    }
    experience_layer_.pop_transform();experience_layer_.pop_opacity();experience_layer_.pop_clip();
}
}
