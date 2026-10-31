// Pixel Museum — a continuous, gently moving line for the listening room.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/draw_list.hpp"
#include <cmath>
namespace museum {
inline void draw_music_waveform(hui::gfx::DrawList& out,hui::gfx::Rect bounds,
                                hui::gfx::Color color,float phase){
    constexpr int samples=240;
    struct Point {float x,y;};
    const auto point=[&](int i){
        const float u=float(i)/samples,x=u*2.f-1.f;
        const float envelope=std::exp(-5.8f*x*x)*(1.f-x*x);
        const float wave=.76f*std::sin(21.f*x-phase)+.24f*std::sin(32.f*x+phase*.63f);
        return Point{bounds.x+u*bounds.w,bounds.cy()+wave*envelope*bounds.h*.46f};
    };
    auto previous=point(0);
    for(int i=1;i<=samples;++i){const auto next=point(i);out.line(previous.x,previous.y,next.x,next.y,2.5f,color);previous=next;}
}
}
