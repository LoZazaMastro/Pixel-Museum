#pragma once
#include "ui/feedback.hpp"
#include <algorithm>
#include <cmath>
namespace museum {
// Feed actual accepted state displacement, never raw controller samples.
class AcceptedMotionHaptics {
 float cooldown_=0;int direction_=0;bool pending_=false;float pan_=0;
public:
 void reset(){cooldown_=0;direction_=0;pending_=false;pan_=0;}
 void advance(float dt){if(std::isfinite(dt)&&dt>0)cooldown_=std::max(0.f,cooldown_-dt);}
 void record(float dx,float dy,bool active){
  if(!active){direction_=0;return;}
  if(!std::isfinite(dx)||!std::isfinite(dy)||std::hypot(dx,dy)<.00001f)return;
  const int direction=std::abs(dx)>=std::abs(dy)?(dx>0?1:-1):(dy>0?2:-2);
  if(direction!=direction_&&cooldown_<=0){pending_=true;pan_=std::clamp(dx/(std::abs(dx)+std::abs(dy)+.00001f),-1.f,1.f);cooldown_=.08f;direction_=direction;}
 }
 void step(float dx,float dy){direction_=0;record(dx,dy,true);}
 void drain(hui::ui::Feedback&f,bool suppress=false){if(pending_&&!suppress)f.feel(hui::audio::Tactile::focus,.075f,.028f,pan_);pending_=false;}
};
}
