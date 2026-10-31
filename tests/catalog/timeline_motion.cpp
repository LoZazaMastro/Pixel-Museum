#include "museum/timeline_motion.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
using namespace hui;
static void exercise(int hz,bool culture,bool stick){
    museum::TimelineMotion motion;tween::Spring position;int focus=culture?25:10;position.snap(float(focus));
    InputFrame frame;frame.connected=true;frame.nav=Direction::right;
    if(stick)frame.stick_x=.9f;else frame.held=action_bit(Action::right);
    const float dt=1.f/hz;motion.input(frame,dt,focus,true,position);++focus;position.target=float(focus);position.update(dt,17);
    assert(!motion.locked&&position.value>float(focus-1)&&position.value<float(focus));
    float age=dt,last_repeat=0;int anchor=-1;bool saw_lock=false;
    for(int n=1;n<hz*2;++n){
        age+=dt;frame.nav=Direction::none;frame.nav_repeat=false;
        if(age>.35f&&age-last_repeat>=.11f){last_repeat=age;frame.nav=Direction::right;frame.nav_repeat=true;}
        motion.input(frame,dt,focus,true,position);
        if(frame.nav_repeat)focus=std::min(focus+1,40);
        position.target=float(focus);position.update(dt,17);
        if(motion.locked){
            if(!saw_lock){assert(age>=.65f);anchor=motion.anchor;saw_lock=true;}
            assert(motion.anchor==anchor&&motion.rail_position(position.value)==float(anchor));
            assert(motion.content_index(anchor,focus)==focus);
            assert(motion.content_index(anchor-1,focus)==anchor-1);
        }
    }
    assert(saw_lock);frame={};frame.connected=true;motion.input(frame,dt,focus,true,position);
    assert(!motion.locked&&position.value==float(focus)&&position.velocity==0);
    // Reversal, loss of focus, other surfaces, and both finite boundaries.
    for(int boundary:{0,40}){
        focus=boundary;motion.locked=true;motion.anchor=20;motion.direction=1;position.snap(20);
        frame.nav=Direction::left;frame.held=action_bit(Action::left);motion.input(frame,dt,focus,true,position);
        assert(!motion.locked&&motion.direction==-1&&position.value==float(focus));
        motion.locked=true;frame.focus_lost=true;motion.input(frame,dt,focus,true,position);assert(!motion.locked&&motion.age==0);
        frame.focus_lost=false;motion.locked=true;motion.input(frame,dt,focus,false,position);assert(!motion.locked);
    }
}
int main(){for(int hz:{30,60,120})for(bool culture:{false,true})for(bool stick:{false,true})exercise(hz,culture,stick);std::puts("PASS timeline motion:30/60/120Hz;game+culture;Dpad+stick;tap/hold/release/reversal/focus/boundary");}
