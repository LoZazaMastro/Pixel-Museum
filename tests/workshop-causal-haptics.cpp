#include "museum/study_workshops.cpp"
#include "audio/controller_feedback.hpp"
#include <array>
#include <cassert>
#include <cstdio>
namespace museum {
struct WorkshopInspection {
 static hui::InputFrame frame(bool held=false){hui::InputFrame i;i.connected=true;if(held)i.held=hui::action_bit(hui::Action::confirm);return i;}
 static void driven(const hui::ui::Feedback&f){
  assert(f.tactile.size()==1&&f.tactile[0].strength>=.06f);
  hui::audio::ControllerFeedback out;out.enabled(true);assert(out.post(f.tactile[0]));
  std::array<float,800> pcm{};out.render_haptics(pcm.data(),400);double energy=0;
  for(float n:pcm){assert(std::isfinite(n)&&std::abs(n)<=.7f);energy+=n*n;}
  assert(energy>.01); // The real synthesis path drives finite samples.
 }
 static void run(){for(int hz:{30,60,120}){
  const float dt=1.f/hz;hui::ui::Feedback f;
  JumpLab ceiling;ceiling.y_=-7.8f;ceiling.vy_=-80;ceiling.grounded_=false;
  ceiling.handle(frame(true),f);ceiling.update(dt);assert(ceiling.y_==-8&&ceiling.vy_==0);
  f.clear();ceiling.handle(frame(true),f);driven(f);
  ceiling.update(dt);f.clear();ceiling.handle(frame(true),f);assert(f.tactile.empty());
  JumpLab descending;descending.y_=-7;descending.vy_=80;descending.grounded_=false;
  f.clear();descending.handle(frame(true),f);descending.update(dt);descending.handle(frame(true),f);assert(f.tactile.empty());
  JumpLab short_landing;short_landing.y_=285.5f;short_landing.vy_=100;short_landing.grounded_=false;
  f.clear();short_landing.handle(frame(true),f);short_landing.update(dt);assert(short_landing.grounded_&&short_landing.trace_count_==0);
  f.clear();short_landing.handle(frame(true),f);driven(f);
  short_landing.update(dt);f.clear();short_landing.handle(frame(true),f);assert(f.tactile.empty());
  for(bool held:{false,true}){
   JumpLab lab;lab.y_=150;lab.vy_=-200;lab.grounded_=false;
   f.clear();lab.handle(frame(held),f);lab.update(dt);lab.handle(frame(held),f);
   if(held)assert(f.tactile.empty());else{driven(f);lab.update(dt);f.clear();lab.handle(frame(),f);assert(f.tactile.empty());}
   AdaptivePulse pulse;pulse.y_=100;pulse.vy_=-300;pulse.jump_age_=.2f;pulse.grounded_=false;
   f.clear();pulse.handle(frame(held),f);pulse.update(dt);pulse.handle(frame(held),f);
   if(held)assert(f.tactile.empty());else{driven(f);pulse.update(dt);f.clear();pulse.handle(frame(),f);assert(f.tactile.empty());}
  }
  JumpLab paused;paused.y_=-7.8f;paused.vy_=-80;paused.grounded_=false;
  f.clear();paused.handle(frame(true),f);paused.update(dt);auto lost=frame(true);lost.focus_lost=true;
  paused.handle(lost,f);assert(f.tactile.empty());paused.update(dt);paused.handle(frame(true),f);assert(f.tactile.empty());
 }
 std::puts("PASS workshop causal haptics at30/60/120Hz: ceiling and short landing contacts, accepted jump shortening vs held, one-shot clamps, focus cancellation, real bounded PCM.");}
};
}
int main(){museum::WorkshopInspection::run();}
