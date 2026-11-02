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
    // Breathe in place: travelling phase shifts the central crest off-axis.
    // Odd spatial harmonics keep mirrored peaks balanced on one fixed baseline.
    const float time=std::isfinite(phase)?phase:0.f;
    const float fundamental=.76f*(.85f+.15f*std::sin(time));
    const float overtone=.24f*(.85f+.15f*std::cos(time*.63f));
    const auto point=[&](int i){
        const float u=float(i)/samples,x=u*2.f-1.f;
        const float envelope=std::exp(-5.8f*x*x)*(1.f-x*x);
        const float wave=fundamental*std::sin(21.f*x)+overtone*std::sin(32.f*x);
        return Point{bounds.x+u*bounds.w,bounds.cy()+wave*envelope*bounds.h*.46f};
    };
    auto previous=point(0);
    for(int i=1;i<=samples;++i){const auto next=point(i);out.line(previous.x,previous.y,next.x,next.y,2.5f,color);previous=next;}
}
}
