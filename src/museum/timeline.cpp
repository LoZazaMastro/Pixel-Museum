// Pixel Museum — one continuous chronology, with immediate focus previews.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/experience_mark.hpp"
#include "museum/timeline_hero.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <limits>
namespace museum {
using namespace hui;
using gfx::Color;using gfx::Align;
void Screen::draw_timeline(){
    if(history_focus_){draw_history_page();return;}
    const auto* e=current();if(!e)return;
    const auto palette=colours();const Color paper=palette.paper,ink=palette.ink,quiet=palette.muted;
    const Color surface=gfx::mix(paper,tone_,.18f);
    
    const float opened=std::clamp(story_open_.value,0.f,1.f),lift=714*opened;
    // Fully opened stories hide the hero completely. Avoid re-fitting its
    // potentially long title/summary every frame; the visible chronology rail
    // below still draws, and all transition frames retain their original path.
    if(opened<1.f){
    background_.rounded_rect({0,142,1920,624},0,surface.with_alpha(1-opened));
    const float shift=(timeline_.target-timeline_.value)*42;
    page_.push_clip({0,142,1920,624});
    page_.push_transform(1,0,0,0,-lift);
    page_.push_opacity(1-opened);
    page_.push_opacity(history_transition_?1.f:fade_);
    page_.push_transform(1,0,0,0,(history_transition_?0.f:1-fade_)*16);
    ui::text(page_,fonts_.mono,history_focus_?"CULTURE & DISCOVERY":ui::upper(e->kind),100,189,17,quiet,Align::left,1.4f);
    const auto date=date_label(*e,false);
    if(!date.empty())ui::text(page_,fonts_.mono,ui::upper(date),100,225,18,quiet,Align::left,1.f);
    const float year_baseline=date.empty()?274.f:319.f;
    ui::text(page_,fonts_.display,std::to_string(e->year),96,year_baseline,74,ink);
    const auto hero=timeline_hero_text(*fonts_.semibold.font,*fonts_.regular.font,e->title,e->summary,year_baseline+62);
    ui::paragraph(page_,fonts_.semibold,e->title,94,hero.title_baseline,hero.title_size,770,hero.title_size*1.15f,ink);
    ui::paragraph(page_,fonts_.regular,e->summary,100,hero.summary_baseline,hero.summary_size,hero.summary_width,hero.summary_size*1.4f,quiet);
    if(object_texture_&&!history_focus_){
        if(object_open_.value<.001f)page_.image(object_texture_,{shift,-9,1920,960},gfx::kCanvasUv,Color::rgb(0xffffff,object_alpha_));
    }else if(e->models.empty()&&!e->images.empty()){
        const auto&photo=e->images[e->preferred_image];
        image(page_,photo,{950+shift,220,826,478},true);
    }else{
        int study=-1;
        if(e->models.empty())for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].entry_id==e->id){study=int(n);break;}
        if(study>=0){
            draw_study_preview(page_,study,{950+shift,220,826,478});
            ui::text(page_,fonts_.regular,"Original interactive study",1776,730,19,quiet,Align::right);
        }else logo(page_,1240+shift,330,180,ink.with_alpha(.08f));
    }
    if(!e->models.empty()&&!object_texture_){
        const auto& error=object_.error();
        const std::string status=error.empty()?"Loading model":error;
        ui::paragraph(page_,fonts_.regular,status,1776,730,19,780,27,quiet,99,Align::right);
    }
    page_.pop_transform();page_.pop_opacity();
    page_.pop_opacity();page_.pop_transform();page_.pop_clip();
    }

    // One continuous route. Its geometry never changes with item type.
    const float rail_y=944-lift,step=340;
    page_.push_opacity(1);
    page_.line(0,rail_y,1920,rail_y,1,ink.with_alpha(.19f));
    page_.line(904,rail_y,1016,rail_y,4,gfx::mix(ink,tone_,.68f));
    page_.push_clip({0,744-lift,1920,223});
    const int rail_focus=timeline_motion_.rail_focus(focus_);
    for(int n=std::max(0,rail_focus-4);n<std::min(int(visible_.size()),rail_focus+5);++n){
        const int content=timeline_motion_.content_index(n,focus_);
        const auto& item=catalog_.entries[size_t(visible_[size_t(content)])];
        const float distance=float(n)-timeline_motion_.rail_position(timeline_.value);
        const float hover=std::clamp(1.f-std::abs(distance),0.f,1.f);
        // The focused stop has its own generous reading space. The extra
        // distance eases in continuously as its neighbours move away.
        const float extra=190*tween::smoothstep(std::min(1.f,std::abs(distance)));
        const float x=960+distance*step+(distance<0?-extra:extra);
        const auto text_colour=gfx::mix(quiet.with_alpha(.6f),ink,hover);
        bool playable=false;for(const auto&study:study_catalog())if(study.entry_id==item.id){playable=true;break;}
        const bool music=!item.soundtrack.tracks.empty()||std::any_of(item.soundtrack_rooms.begin(),item.soundtrack_rooms.end(),[](const Soundtrack&room){return !room.tracks.empty();});
        page_.line(x,rail_y-5,x,rail_y+5,1,ink.with_alpha(.25f));
        ui::text(page_,fonts_.mono,date_label(item),x,923-lift,(16+5*hover)*(1-opened)+18*opened,text_colour,Align::center);
        // Fixed line breaks prevent titles jumping between one and two lines
        // while they travel into focus. Only their size and opacity animate.
        float reference_size=26;
        while(fonts_.regular.font->wrap(item.title,reference_size,450).size()>2&&reference_size>15)reference_size-=1;
        const auto lines=ui::paragraph_lines(fonts_.regular,item.title,reference_size,450);
        const float size=reference_size*(.72f+.28f*hover)*(1-.2f*opened);
        const float baseline=883-lift-float(lines.lines.size()-1)*size*1.15f;
        // Symbols track the actual first text line while hover/opening scales
        // animate; a fixed icon baseline can intersect a wrapped title.
        const float icon_y=baseline-fonts_.regular.font->ascent(size)-27.f;
        if(playable)draw_experience_mark(page_,x-(music?24.f:0.f),icon_y,30,text_colour);
        if(music){const float note_x=x+(playable?24.f:0.f);page_.line(note_x,icon_y-9,note_x,icon_y+5,2,text_colour);page_.line(note_x,icon_y-9,note_x+10,icon_y-12,2,text_colour);page_.circle(note_x-3,icon_y+6,4,text_colour);}

        ui::paragraph(page_,fonts_.regular,lines,x,baseline,size,size*1.15f,text_colour,Align::center);
    }
    page_.pop_clip();page_.pop_opacity();
    if(opened>.001f)draw_detail();
    std::vector<ui::Hint> controls;
    if(!history_focus_&&!e->models.empty())controls.push_back({ui::Button::square,"Inspect 3D"});
    else if(!e->images.empty())controls.push_back({ui::Button::square,"View image"});
    controls.push_back({ui::Button::l1,"Decade",ui::Button::r1});
    controls.push_back({ui::Button::triangle,active_filter()?"All":"Today"});
    if(!history_focus_)controls.push_back({ui::Button::l2,"Filter",ui::Button::r2});
    controls.push_back({ui::Button::touchpad,"Guide"});
    if(history_focus_&&scroll_max_>0)controls.push_back({ui::Button::right_stick,"Read"});
    controls.push_back({ui::Button::options,"Options"});
    if(!gallery_&&!screening_&&gallery_open_.value<.001f&&screening_open_.value<.001f){page_.push_opacity(1-opened);hints(controls);page_.pop_opacity();}
}
}
