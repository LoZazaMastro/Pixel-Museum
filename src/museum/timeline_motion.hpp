#pragma once
#include "core/input.hpp"
#include "core/tween.hpp"
#include <algorithm>
#include <cmath>
namespace museum {
// Accelerated held browsing shows only the live central stop.
struct TimelineMotion {
    int direction=0,anchor=0;
    float age=0;
    bool locked=false;
    void reset(int focus,hui::tween::Spring&position){
        if(locked)position.snap(float(focus));
        direction=0;age=0;locked=false;anchor=focus;
    }
    void input(const hui::InputFrame&i,float dt,int focus,bool enabled,hui::tween::Spring&position){
        if(!enabled||i.focus_lost||!i.connected){reset(focus,position);return;}
        int next=0;
        if(i.is_held(hui::Action::left)!=i.is_held(hui::Action::right))next=i.is_held(hui::Action::right)?1:-1;
        else if(std::abs(i.stick_x)>.45f&&std::abs(i.stick_x)>std::abs(i.stick_y))next=i.stick_x>0?1:-1;
        else if(!i.nav_repeat){if(i.nav==hui::Direction::left)next=-1;if(i.nav==hui::Direction::right)next=1;}
        if(next!=direction){reset(focus,position);direction=next;}
        if(!direction)return;
        age+=std::isfinite(dt)?std::clamp(dt,0.f,.05f):0.f;
        if(!locked&&age>=.65f&&i.nav_repeat){locked=true;anchor=focus;position.snap(float(focus));}
    }
    bool stop_visible(int slot)const{return !locked||slot==anchor;}
    int rail_focus(int focus)const{return locked?anchor:focus;}
    float rail_position(float position)const{return locked?float(anchor):position;}
    int content_index(int slot,int focus)const{return locked&&slot==anchor?focus:slot;}
};
}
