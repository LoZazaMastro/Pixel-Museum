// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/draw_list.hpp"
#include <algorithm>
namespace museum {
// A collection symbol, distinct from the controller's navigation glyphs.
inline void draw_experience_mark(hui::gfx::DrawList&list,float cx,float cy,float width,hui::gfx::Color colour){
    const float stroke=std::max(1.2f,width*.036f);
    const auto line=[&](float ax,float ay,float bx,float by){list.line(cx+ax*width,cy+ay*width,cx+bx*width,cy+by*width,stroke,colour);};
    const auto curve=[&](float ax,float ay,float bx,float by,float dx,float dy,float ex,float ey){
        float px=ax,py=ay;
        for(int n=1;n<=10;++n){const float t=float(n)/10,u=1-t;
            const float x=u*u*u*ax+3*u*u*t*bx+3*u*t*t*dx+t*t*t*ex;
            const float y=u*u*u*ay+3*u*u*t*by+3*u*t*t*dy+t*t*t*ey;
            line(px,py,x,y);px=x;py=y;
        }
    };
    curve(-.32f,-.22f,-.18f,-.32f,.18f,-.32f,.32f,-.22f);
    curve(.32f,-.22f,.42f,-.12f,.53f,.28f,.37f,.30f);
    curve(.37f,.30f,.29f,.32f,.22f,.12f,.13f,.10f);
    line(.13f,.10f,-.13f,.10f);
    curve(-.13f,.10f,-.22f,.12f,-.29f,.32f,-.37f,.30f);
    curve(-.37f,.30f,-.53f,.28f,-.42f,-.12f,-.32f,-.22f);
    line(-.26f,-.055f,-.14f,-.055f);line(-.20f,-.115f,-.20f,.005f);
    for(const auto&point:{hui::gfx::Rect{.20f,-.12f,0,0},hui::gfx::Rect{.26f,-.055f,0,0},hui::gfx::Rect{.20f,.01f,0,0},hui::gfx::Rect{.14f,-.055f,0,0}})
        list.circle(cx+point.x*width,cy+point.y*width,std::max(.8f,width*.018f),colour);
}
}
