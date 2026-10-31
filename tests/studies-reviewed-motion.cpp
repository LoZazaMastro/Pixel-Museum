// Deterministic traversal exercises the real authored route and its collisions.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study_motion.cpp"
#include <cassert>
namespace museum { namespace {
struct MotionInspection {
 static void run(){
  hui::ui::Feedback feedback;hui::InputFrame i;i.connected=true;
  // Entire current ground/pipe/block route is covered at 30/60/120Hz by mario-corrections.
  Momentum roll;i={};i.connected=true;i.stick_x=1;
  for(int frame=0;frame<100;++frame){roll.handle(i,feedback);roll.update(1.f/120);}
  const float velocity=roll.v_;assert(velocity>100);i.stick_x=0;roll.handle(i,feedback);roll.update(1.f/120);assert(roll.v_>velocity*.95f);
  i.stick_y=1;for(int frame=0;frame<90;++frame){roll.handle(i,feedback);roll.update(1.f/120);}assert(std::abs(roll.v_)<velocity*.5f);
  roll.reset();roll.x_=1120;roll.y_=Momentum::ground(1120)-26;roll.v_=680;
  i={};i.connected=true;i.stick_x=1;i.held=i.pressed=hui::action_bit(Action::confirm);roll.handle(i,feedback);i.pressed=0;
  for(int frame=0;frame<150;++frame){roll.handle(i,feedback);roll.update(1.f/120);}
  std::fprintf(stderr,"roll gap: x%.2f y%.2f grounded%d falls%d\n",roll.x_,roll.y_,roll.grounded_,roll.falls_);
  assert(roll.x_>1470&&roll.falls_==0&&roll.checkpoint_);
  roll.x_=1820;roll.y_=260;roll.v_=0;roll.vy_=100;roll.grounded_=false;i={};i.connected=true;
  for(int frame=0;frame<90;++frame){roll.handle(i,feedback);roll.update(1.f/120);}
  assert(roll.grounded_&&std::abs(roll.y_-(385-26))<.1f); // the upper route is a real collision surface
  roll.banked_=2;roll.banked_taken_.fill(false);roll.banked_taken_[0]=roll.banked_taken_[1]=true;roll.taken_.fill(true);roll.rings_=18;roll.y_=850;roll.grounded_=false;roll.update(1.f/120);
  assert(roll.rings_==2&&roll.taken_[0]&&!roll.taken_[7]&&roll.x_>=1500); // lost unbanked rings are collectible again
  std::puts("PASS momentum: retained inertia, deliberate braking, gap-crossing jump, physical upper ledge and recoverable banked-ring checkpoint");
  roll.reset();i={};i.connected=true;i.stick_y=1;i.pressed=hui::action_bit(Action::confirm);
  for(int tap=0;tap<4;++tap){roll.handle(i,feedback);roll.update(1.f/120);}
  assert(roll.charge_>.99f&&roll.grounded_&&roll.jump_==0);
  i={};i.connected=true;i.stick_x=1;roll.handle(i,feedback);assert(roll.v_>700&&roll.charge_==0);
  std::puts("PASS momentum: crouched Cross charges without jumping; release launches stored speed");
  Dash dash;i={};i.connected=true;i.pressed=i.held=hui::action_bit(Action::confirm);dash.handle(i,feedback);
  i.pressed=0;for(int frame=0;frame<20;++frame){dash.handle(i,feedback);dash.update(1.f/120);}
  assert(!dash.grounded_&&dash.p_.y<475); // gravity-driven jump, not free top-down movement
  i.pressed=hui::action_bit(Action::page_next);i.stick_x=1;dash.handle(i,feedback);assert(!dash.charged_&&dash.air_dashes_==1);
  dash.handle(i,feedback);assert(dash.air_dashes_==1); // repeat input cannot create a second air burst
  std::puts("PASS dash: real jump and a single air burst; full three-room traversal covered by study-dash test");
  ExperienceAudio score_audio;Rhythm rhythm;rhythm.attach_audio(&score_audio);
  std::array<float,512> pcm{};
  for(unsigned offset=0;offset<105600;offset+=256){pcm.fill(0);score_audio.render(pcm.data(),std::min(256u,105600-offset));}
  rhythm.update(.001f);rhythm.take_note();i={};i.connected=true;i.pressed=hui::action_bit(Action::confirm);rhythm.handle(i,feedback);
  assert(rhythm.take_note()==62); // first scoring beat is measured from audio, not dt
  rhythm.handle(i,feedback);assert(rhythm.take_note()==-1);
  for(unsigned offset=0;offset<47040;offset+=256){pcm.fill(0);score_audio.render(pcm.data(),std::min(256u,47040-offset));}
  rhythm.update(.001f);rhythm.take_note();rhythm.handle(i,feedback);assert(rhythm.take_note()==50);
  std::puts("PASS rhythm: on-time and off-time input follow actual rendered music clock independently of UI dt");


 }
};
}}
int main(){museum::MotionInspection::run();}
