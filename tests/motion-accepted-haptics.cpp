#include "museum/study_motion.cpp"
#include <cassert>
namespace museum {namespace {
struct MotionHapticsInspection {
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){
  for(int hz:{30,60,120}){
   Jump s;hui::ui::Feedback f;auto i=input();i.stick_x=1;unsigned count=0;
   for(int n=0;n<hz/5;++n){f.clear();s.handle(i,f);count+=f.tactile.size();s.update(1.f/hz);}assert(count==1);
   i.held=hui::action_bit(hui::Action::west);s.handle(i,f);s.update(1.f/hz);f.clear();s.handle(i,f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::touch);
   s.reset();i=input();i.pressed=i.held=hui::action_bit(hui::Action::confirm);s.handle(i,f);s.update(1.f/hz);f.clear();s.handle(input(),f);assert(f.tactile.size()==1);
   s.reset();i=input();i.stick_x=1;s.handle(i,f);s.update(1.f/hz);i.focus_lost=true;f.clear();s.handle(i,f);assert(f.tactile.empty());i.focus_lost=false;i.stick_x=0;f.clear();s.handle(i,f);assert(f.tactile.empty());
   Momentum sonic;i=input();i.pressed=hui::action_bit(hui::Action::confirm);sonic.handle(i,f);sonic.update(1.f/hz);f.clear();sonic.handle(input(),f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::rise);
  }
  hui::ui::Feedback f;Sequencer seq;auto i=input();i.nav=hui::Direction::right;seq.handle(i,f);assert(f.tactile.size()==1);
  seq.cx_=7;f.clear();seq.handle(i,f);assert(f.tactile.empty());i=input();i.pressed=hui::action_bit(hui::Action::north);seq.handle(i,f);assert(f.tactile.size()==1&&!seq.playing_);
  Rhythm rhythm;rhythm.clock_=Rhythm::beat*2;i=input();i.pressed=hui::action_bit(hui::Action::left);f.clear();rhythm.handle(i,f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::error);f.clear();rhythm.handle(i,f);assert(f.tactile.empty());
  Dash dash;i=input();i.stick_y=-1;f.clear();dash.handle(i,f);assert(f.tactile.size()==1);f.clear();dash.handle(i,f);assert(f.tactile.empty());
  Momentum rings;rings.x_=Momentum::ring(0).x;rings.y_=Momentum::ring(0).y;rings.grounded_=false;rings.update(.001f);
  f.clear();rings.handle(input(),f);assert(rings.rings_==1&&f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::ring&&f.tactile.size()==1);
  rings.update(.001f);f.clear();rings.handle(input(),f);assert(rings.rings_==1&&f.speaker_cues.empty()&&f.tactile.empty());
  Momentum charge;i=input();i.stick_y=1;i.pressed=hui::action_bit(hui::Action::confirm);
  for(int n=0;n<4;++n){f.clear();charge.handle(i,f);assert(f.speaker_cues.size()==1&&!f.tactile.empty());}
  f.clear();charge.handle(i,f);assert(charge.charge_==1&&f.speaker_cues.empty()&&f.tactile.empty());
  f.clear();charge.handle(input(),f);charge.update(.001f);f.clear();charge.handle(input(),f);assert(f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::charge);
  Wind wind;i=input();i.stick_x=1;wind.handle(i,f);wind.update(.02f);f.clear();wind.handle(i,f);assert(f.tactile.size()==1);
  i=input();i.held=hui::action_bit(hui::Action::confirm);wind.handle(i,f);wind.update(.02f);f.clear();wind.handle(i,f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::rise);
  i.focus_lost=true;wind.handle(i,f);const auto position=wind.p_;wind.update(.1f);assert(wind.p_.x==position.x&&wind.p_.y==position.y);
  f.clear();wind.handle(input(),f);wind.update(.02f);f.clear();wind.handle(input(),f);assert(f.tactile.empty());
  Rhythm ontime;ontime.clock_=Rhythm::beat*2;i=input();i.pressed=hui::action_bit(hui::Action::confirm);f.clear();ontime.handle(i,f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::confirm);
  f.clear();ontime.handle(input(),f);assert(f.tactile.empty()); // no delayed duplicate success rumble
  std::puts("PASS Motion accepted haptics: actualwalkonce30/60/120, acceptedSquareRun/jump, focusclearsqueue, Sonicphysicaljump, Luminescursor/noop/pause, DDRearlylateerror/duplicate, Celesteaim/nochange");
 }
};}}
int main(){museum::MotionHapticsInspection::run();}
