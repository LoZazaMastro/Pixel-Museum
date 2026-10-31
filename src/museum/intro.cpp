// Pixel Museum — scattered light, thirteen notes, then a passage through the M.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include <algorithm>
#include <cmath>
namespace museum {
namespace {
constexpr int order[13][2]={{0,4},{4,0},{0,0},{4,4},{1,1},{4,2},{0,2},{3,1},{0,3},{4,1},{2,2},{0,1},{4,3}};
constexpr int notes[13]={50,57,60,62,64,65,69,72,74,76,77,81,86};
constexpr std::uint32_t pixel_colours[13]={0xa5c8c0,0xd4b9d5,0xe2b994,0xa8bdce,0xd3cf9f,0xcba4ae,0xb8cfae,0xd8b5a1,0xa8bcca,0xc3b3d7,0xe2ccad,0xb8cfc6,0xd4c7bd};
}
int Screen::take_startup_note(int* pixel_ordinal){
    if(pixel_ordinal)*pixel_ordinal=-1;
    if(onboarding_)return -1;
    if(experience_active_&&!experience_introduction_&&study_){
        const int note=study_->take_note();return experience_input_paused_?-1:note;
    }
    if(boot_time_>2.9f||boot_note_>=13)return -1;
    if(boot_time_>=.12f+float(boot_note_)*.185f){
        if(pixel_ordinal)*pixel_ordinal=int(boot_note_);
        return notes[boot_note_++];
    }
    return -1;
}
void Screen::draw_boot(){
    using namespace hui;using gfx::Color;
    boot_.clear();const auto palette=colours();
    // Background masks share edges. SDF rectangles soften each edge separately,
    // exposing the page below as thin seams beside the M during the passage.
    // Flat quads tile the background with exact raster edges instead.
    const auto background=[&](gfx::Rect r,Color colour){
        if(r.w<=0||r.h<=0)return;
        const float xy[]={r.x,r.y,r.x+r.w,r.y,r.x+r.w,r.y+r.h,r.x,r.y+r.h};
        boot_.polygon(xy,4,colour);
    };
    const float flight=tween::clamp01((boot_time_-3.f)/1.8f);
    if(reduced_){
        const float opacity=1-tween::smoothstep(flight);
        background({0,0,1920,1080},palette.paper.with_alpha(opacity));
        for(int i=0;i<13;++i){
            const float lit=tween::smoothstep((boot_time_-.12f-float(i)*.185f)/.26f);
            boot_.rounded_rect({835+float(order[i][0])*50,415+float(order[i][1])*50,50,50},0,Color::rgb(pixel_colours[i],lit*opacity));
        }
        const float word=tween::smoothstep((boot_time_-2.45f)/.45f)*opacity;
        if(word>0)ui::text(boot_,fonts_.regular,"PIXEL MUSEUM",960,742,24,palette.ink.with_alpha(word*.8f),gfx::Align::center,5);
        return;
    }
    const float eased=tween::cubic_in_out(flight);
    const float zoom=std::exp(std::log(72.f)*eased);
    // Aim through the real negative space below the M's central diagonal.
    // The four black masks open a window onto the already-rendered museum.
    const float cell=50*zoom;
    const float origin_x=960-2.5f*cell;
    const float aim_y=615+(540-615)*tween::smoothstep(flight*3);
    const float origin_y=aim_y-4.f*cell;
    if(flight<=0){background({0,0,1920,1080},palette.paper);}
    else{
        const float left=std::clamp(origin_x+cell,0.f,1920.f);
        const float right=std::clamp(origin_x+4*cell,0.f,1920.f);
        const float top=std::clamp(origin_y+3*cell,0.f,1080.f);
        const float bottom=std::clamp(origin_y+5*cell,0.f,1080.f);
        background({0,0,1920,top},palette.paper);
        background({0,bottom,1920,1080-bottom},palette.paper);
        background({0,top,left,bottom-top},palette.paper);
        background({right,top,1920-right,bottom-top},palette.paper);
        background({left,top,right-left,bottom-top},palette.paper.with_alpha(1-tween::smoothstep(flight*7)));
    }
    for(int i=0;i<13;++i){
        const float lit=tween::smoothstep((boot_time_-.12f-float(i)*.185f)/.26f);
        if(lit<=0)continue;
        const auto c=gfx::mix(Color::rgb(pixel_colours[i]),palette.paper,eased*.7f).with_alpha(lit);
        const float x=origin_x+float(order[i][0])*cell,y=origin_y+float(order[i][1])*cell;
        const float inset=(1-lit)*cell*.12f;
        if(flight>0){
            const float d=cell*.07f*flight;
            boot_.rounded_rect({x+d,y+d,cell,cell},0,Color::rgb(0x252b29,lit));
        }
        boot_.rounded_rect({x+inset,y+inset,cell-inset*2,cell-inset*2},0,c);
    }
    const float word=tween::smoothstep((boot_time_-2.45f)/.45f)*(1-tween::smoothstep(flight*4));
    if(word>0)ui::text(boot_,fonts_.regular,"PIXEL MUSEUM",960,742,24,palette.ink.with_alpha(word*.8f),gfx::Align::center,5);
}
}
