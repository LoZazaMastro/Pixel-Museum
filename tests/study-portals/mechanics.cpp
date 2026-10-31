#include "museum/study_space.cpp"
#include <cassert>
#include <limits>
namespace museum {
struct PortalInspection {
 static hui::InputFrame input(float x=0){hui::InputFrame i;i.connected=true;i.stick_x=x;return i;}
 static void step(PortalStudy&s,float dt,float x=0,bool jump=false){auto i=input(x);if(jump)i.pressed=hui::action_bit(hui::Action::confirm);hui::ui::Feedback f;s.handle(i,f);s.update(dt);assert(std::isfinite(s.p_.x)&&std::isfinite(s.p_.y)&&std::isfinite(s.v_.x)&&std::isfinite(s.v_.y));assert(f.rumble_strength>=0&&f.rumble_strength<=1);}
 static void select(PortalStudy&s,int which){hui::ui::Feedback f;for(int n=0;n<4&&s.selected_!=which;++n){auto i=input();i.stick2_x=1;s.handle(i,f);s.handle(input(),f);}assert(s.selected_==which);}
 static void place(PortalStudy&s,int which,bool blue){select(s,which);auto i=input();i.pressed=hui::action_bit(blue?hui::Action::jump_prev:hui::Action::jump_next);hui::ui::Feedback f;s.handle(i,f);s.handle(input(),f);assert((blue?s.blue_:s.orange_)==which);}
 static void carry(PortalStudy&s){auto i=input();i.pressed=hui::action_bit(hui::Action::north);hui::ui::Feedback f;s.handle(i,f);s.handle(input(),f);}
 static void frame_path(PortalStudy&s,float dt,bool stop_at_plate=false){
  if(s.chamber_==0){for(int n=0;n<int(9/dt)&&!s.complete_;++n){step(s,dt,1);}}
  else if(s.chamber_==1){for(int n=0;n<int(9/dt)&&!s.complete_;++n){float axis=1;if(s.crossings_>0&&s.p_.x>910)axis=-1;if(s.crossings_>0&&s.grounded_)axis=s.p_.x>918?-1:1;step(s,dt,axis);}}
  else if(s.chamber_==3){
   bool redirected=false;
   for(int n=0;n<int(12/dt)&&!s.complete_;++n){
    if(!redirected&&s.crossings_>0){place(s,2,false);redirected=true;}
    const float axis=s.crossings_<2?0:s.grounded_?std::clamp((714-s.p_.x)*.025f,-1.f,1.f):-1.f;
    step(s,dt,axis);
   }
  }
  else {
   // Solve the actual cube puzzle using only controller input after setup:
   // collect at the start, carry through the redirected fall, brake above the
   // switch, release it, then walk to the now-unlocked exit.
   if(!s.carrying_)carry(s);
   bool dropped=false;
   for(int n=0;n<int(14/dt)&&!s.complete_;++n){
    float axis=1;
    if(s.crossings_>0){
     if(!dropped){
      const float target=679; // held cube drops25px in front, at switch704
      const float error=target-s.p_.x;
      axis=s.grounded_?std::clamp(error*.025f,-1.f,1.f):std::clamp(error*.06f-s.v_.x*.025f,-1.f,1.f);
      if(s.grounded_&&std::abs(error)<3)axis=0;
      if(s.grounded_&&std::abs(error)<4&&std::abs(s.v_.x)<8){step(s,dt,.08f);carry(s);dropped=true;}
     }else axis=s.plate_down_?-.8f:0;
    }
    step(s,dt,axis);if(stop_at_plate&&s.plate_down_)return;
   }
  }
 }
 static void run(){
  for(auto a:std::array<PortalStudy::V,4>{{{1,0},{-1,0},{0,1},{0,-1}}})for(auto b:std::array<PortalStudy::V,4>{{{1,0},{-1,0},{0,1},{0,-1}}})for(int n=0;n<100;++n){PortalStudy::V v{std::sin(float(n))*730,std::cos(float(n))*930};auto out=PortalStudy::through(v,a,b);auto back=PortalStudy::through({-out.x,-out.y},b,a);assert(std::abs(PortalStudy::speed(v)-PortalStudy::speed(out))<.001f);assert(std::hypot(v.x+back.x,v.y+back.y)<.001f);}
  for(float dt:{1.f/30,1.f/60,1.f/120})for(int chamber=0;chamber<4;++chamber){PortalStudy s;s.setup(chamber);place(s,0,true);place(s,chamber==2?2:1,false);frame_path(s,dt);std::fprintf(stderr,"chamber%d %.0fHz p %.1f %.1f speed %.1f crossings%d falls%d complete%d\n",chamber+1,1/dt,s.p_.x,s.p_.y,PortalStudy::speed(s.v_),s.crossings_,s.falls_,s.complete_);assert(s.complete_&&(s.crossings_>0||s.cube_crossings_>0)&&s.falls_==0);assert(std::abs(s.incoming_speed_-s.outgoing_speed_)<.001f);}

  // A real carried object, rather than reaching the upper ledge alone,
  // controls the exit. Removing its weight relocks the door immediately.
  for(float dt:{1.f/30,1.f/60,1.f/120}){
   PortalStudy s;s.setup(2);place(s,0,true);place(s,2,false);frame_path(s,dt,true);
   assert(!s.complete_&&s.plate_down_&&!s.carrying_&&s.cube_grounded_&&std::abs(s.cube_.y-290)<.01f);
   for(int n=0;n<int(.3f/dt);++n)step(s,dt);assert(s.gate_>.95f);
   carry(s);assert(s.carrying_&&!s.plate_down_);step(s,dt);assert(!s.complete_);
   for(int n=0;n<int(.3f/dt);++n)step(s,dt);assert(s.gate_<.05f);
  }
  {PortalStudy s;s.setup(2);place(s,0,true);place(s,2,false);
   for(int n=0;n<2000;++n){float x=1;if(s.crossings_>0)x=std::clamp((605-s.p_.x)*.06f-s.v_.x*.025f,-1.f,1.f);step(s,1.f/120,x);}
   assert(s.crossings_>0&&s.grounded_&&!s.complete_&&!s.plate_down_);
   s.p_={650,286};s.v_={};for(int n=0;n<120;++n)step(s,1.f/120,-1);assert(s.p_.x>=s.exit_.x+s.exit_.w+PortalStudy::half_w-.01f);
  }
  // A released cube obeys the same directed velocity rule, and cannot
  // trigger a switch simply by passing above it or being held over it.
  {PortalStudy s;s.setup(2);place(s,0,true);place(s,2,false);s.cube_={480,508};s.cube_velocity_={0,600};s.cube_grounded_=false;
   s.cube_physics(.01f);assert(s.cube_cooldown_>0&&std::abs(s.cube_.x-870)<.01f&&std::abs(s.cube_velocity_.y+609.5f)<.01f&&!s.plate_down_);
   s.cube_={704,260};s.cube_velocity_={};s.cube_grounded_=false;s.cube_physics(.001f);assert(!s.plate_down_);
  }
  // The final exit requires the ceiling drop AND moving the exit portal.
  // Neither the direct floor pair, repeated jumping, nor leaving the loop
  // connected reaches the ledge. Successful trajectories preserve speed.
  for(float dt:{1.f/30,1.f/60,1.f/120}){
   PortalStudy direct;direct.setup(3);place(direct,0,true);place(direct,2,false);
   for(int n=0;n<int(10/dt);++n)step(direct,dt,direct.p_.x>600?-1.f:0,n%2==0);
   assert(!direct.complete_);
   PortalStudy loop;loop.setup(3);place(loop,0,true);place(loop,1,false);
   for(int n=0;n<int(3/dt);++n)step(loop,dt);
   assert(loop.crossings_>=2&&!loop.complete_&&loop.p_.x<400);
   PortalStudy solved;solved.setup(3);place(solved,0,true);place(solved,1,false);frame_path(solved,dt);
   assert(solved.complete_&&solved.crossings_==2&&solved.incoming_speed_>800&&std::abs(solved.incoming_speed_-solved.outgoing_speed_)<.001f);
  }
  // Touchpad chooses an actual marked surface, without placing a portal.
  // A still-held contact and triggers across focus loss cannot issue a
  // fresh command until released. Disconnection also freezes physics.
  {PortalStudy s;s.setup(2);auto i=input();i.touch.available=true;i.touch.count=1;i.touch.points[0]={.87f,520.f/600,1};hui::ui::Feedback f;
   s.handle(i,f);assert(s.selected_==2&&s.blue_<0&&s.orange_<0);f.clear();for(int n=0;n<20;++n)s.handle(i,f);assert(f.tactile.empty());
   i.focus_lost=true;i.trigger_l=1;const auto p=s.p_;const float time=s.clock_;s.handle(i,f);s.update(.05f);assert(s.p_.x==p.x&&s.clock_==time);
   i.focus_lost=false;i.touch.points[0].x=.48f;s.handle(i,f);assert(s.selected_==2&&s.blue_<0);
   s.handle(input(),f);s.handle(i,f);assert(s.selected_==0&&s.blue_==0);
   i.connected=false;s.handle(i,f);s.update(.05f);assert(s.p_.x==p.x&&s.clock_==time);
   s.handle(input(),f);s.update(.01f);assert(s.clock_>time);
   const int selected=s.selected_;i=input();i.touch.available=true;i.touch.count=1;i.touch.points[0].x=std::numeric_limits<float>::quiet_NaN();s.handle(i,f);assert(s.selected_==selected);
  }
  // Prediction is read-only and follows the actual input-driven frame
  // integration through a portal to within a few simulation pixels.
  {PortalStudy s;s.setup(1);place(s,0,true);place(s,1,false);s.p_={480,420};s.v_={0,500};s.grounded_=false;
   const auto p=s.p_,v=s.v_,c=s.cube_;const int event=s.event_;s.forecast();
   assert(s.p_.x==p.x&&s.p_.y==p.y&&s.v_.y==v.y&&s.cube_.x==c.x&&s.event_==event&&s.crossings_==0);
   const auto prediction=s.forecast_;const unsigned count=s.forecast_count_;assert(count>5);
   PortalStudy actual=s;
   for(unsigned n=0;n<count;++n){for(int tick=0;tick<4;++tick)step(actual,1.f/120);
    float distance=1e9f;for(int k=std::max(0,int(n)-1);k<=std::min(int(count)-1,int(n)+1);++k)distance=std::min(distance,std::hypot(prediction[size_t(k)].x-actual.p_.x,prediction[size_t(k)].y-actual.p_.y));
    assert(distance<7.f);
   }assert(actual.crossings_>0);
  }

  // Neither holding Jump nor the wrong orientation replaces the spatial solution.
  for(int stage=0;stage<PortalStudy::chamber_count;++stage){PortalStudy s;s.setup(stage);for(int n=0;n<1800;++n)step(s,1.f/120,stage==3?-1.f:1.f,n%2==0);assert(!s.complete_&&s.crossings_==0);}
  {PortalStudy s;s.setup(2);place(s,0,true);place(s,1,false);for(int n=0;n<1600;++n)step(s,1.f/120,1,n%2==0);assert(!s.complete_);}
  {PortalStudy s;hui::ui::Feedback f;auto jump=input();jump.pressed=hui::action_bit(hui::Action::confirm);s.handle(jump,f);assert(s.v_.y==-340&&!s.grounded_);s.update(.02f);const float vy=s.v_.y;s.handle(jump,f);assert(s.v_.y==vy); // no airborne jump reset
   auto lost=input(1);lost.focus_lost=true;lost.pressed=hui::action_bit(hui::Action::west);const auto p=s.p_;const float clock=s.clock_;s.handle(lost,f);s.update(.04f);assert(s.p_.x==p.x&&s.p_.y==p.y&&s.clock_==clock);s.handle(input(),f);s.update(.01f);assert(s.p_.y!=p.y);
   auto select=input();select.stick2_x=1;s.handle(select,f);assert(s.selected_==1);for(int n=0;n<30;++n)s.handle(select,f);assert(s.selected_==1);select.stick2_x=.4f;s.handle(select,f);select.stick2_x=1;s.handle(select,f);assert(s.selected_==1);s.handle(input(),f);s.handle(select,f);assert(s.selected_==0);
   place(s,0,true);f.clear();auto orange=input();orange.pressed=hui::action_bit(hui::Action::jump_next);s.handle(orange,f);assert(s.orange_==-1&&s.blue_==0&&!f.tactile.empty()&&f.tactile[0].pattern==hui::audio::Tactile::error);
  }
  {PortalStudy s;place(s,0,true);place(s,1,false);s.v_={200,0};s.cooldown_=0;assert(!s.traverse({430,400},{420,400}));assert(!s.traverse({420,300},{430,300})); // backside and outside aperture
   assert(s.traverse({420,486},{430,486})&&s.crossings_==1);assert(!s.traverse({580,486},{570,486}));hui::ui::Feedback f;s.handle(input(),f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::zoom_in&&f.tactile[0].pan>0&&f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::portal_cross);f.clear();s.handle(input(),f);assert(f.tactile.empty());
  }
  {PortalStudy s;for(int chamber=0;chamber<PortalStudy::chamber_count;++chamber){
   assert(s.chamber_==chamber);place(s,0,true);place(s,chamber==2?2:1,false);frame_path(s,1.f/120);assert(s.complete_);
   const auto expected=chamber+1==PortalStudy::chamber_count?StudyCompletion::experience_complete:StudyCompletion::level_complete;
   assert(s.completion()==expected&&s.level_number()==chamber+1&&s.level_count()==4);
   const auto p=s.p_;auto next=input();next.pressed=hui::action_bit(hui::Action::confirm);hui::ui::Feedback f;s.handle(next,f);
   for(int n=0;n<50;++n)step(s,1.f/120);
   assert(s.chamber_==chamber&&s.complete_&&s.p_.x==p.x&&s.p_.y==p.y); // No confirm-driven silent advance.
   s.continue_level();assert(s.chamber_==(chamber+1)%PortalStudy::chamber_count&&!s.complete_&&s.blue_==-1&&s.orange_==-1);
  }}
  {PortalStudy s;s.setup(2);place(s,0,true);place(s,2,false);auto reset=input();reset.pressed=hui::action_bit(hui::Action::west);hui::ui::Feedback f;s.handle(reset,f);assert(s.chamber_==2&&s.blue_==-1&&s.orange_==-1&&s.crossings_==0&&s.p_.x==s.spawn_.x);s.update(std::numeric_limits<float>::quiet_NaN());s.update(-1);s.update(std::numeric_limits<float>::infinity());assert(s.clock_==0);}
  {for(int stage=0;stage<4;++stage){PortalStudy s;s.setup(stage);for(int n=0;n<6000;++n){auto i=input(std::sin(float(n)*.023f));i.stick2_x=std::sin(float(n)*.04f);i.trigger_l=n%199<50?1:0;i.trigger_r=n%263<60?1:0;if(n%37==0)i.pressed|=hui::action_bit(hui::Action::north);if(n%23==0)i.pressed|=hui::action_bit(hui::Action::confirm);if(n%1703==0)i.pressed|=hui::action_bit(hui::Action::west);i.focus_lost=n%721<10;if(n%907==0)i.stick_x=std::numeric_limits<float>::quiet_NaN();hui::ui::Feedback f;s.handle(i,f);s.update(n%101==0?.5f:1.f/120);assert(std::isfinite(s.p_.x)&&std::isfinite(s.p_.y)&&std::isfinite(s.v_.x)&&std::isfinite(s.v_.y)&&std::isfinite(s.clock_));assert(std::isfinite(s.cube_.x)&&std::isfinite(s.cube_.y)&&std::isfinite(s.cube_velocity_.x)&&std::isfinite(s.cube_velocity_.y));assert(s.blue_<s.surface_count_&&s.orange_<s.surface_count_);for(auto cue:f.tactile)assert(cue.strength>=0&&cue.strength<=1&&std::isfinite(cue.pan));}}}
  std::puts("Portal cube pressure causal gate/relocking; touch selection/focus/reconnect; lossless cube portal speed; forecast actual-frame parity PASS");
  std::puts("Portal no jump-spam shortcut; wrong exit fails; aperture/backside/cooldown; per-event haptics; pause/reset/continue;30000 finite frames PASS");
  std::puts("Portal directed momentum and four input-solvable chambers at30/60/120Hz PASS");
 }
 static std::unique_ptr<Study> preview(int chamber){
  auto s=std::make_unique<PortalStudy>();s->setup(chamber);place(*s,0,true);place(*s,chamber==2?2:1,false);
  if(chamber==2){carry(*s);for(int n=0;n<235;++n)step(*s,1.f/120,1);}
  else if(chamber==3){for(int n=0;n<240&&s->crossings_<2;++n){if(s->crossings_==1&&s->orange_!=2)place(*s,2,false);step(*s,1.f/120);}for(int n=0;n<40;++n)step(*s,1.f/120,-1);}
  else for(int n=0;n<(chamber==0?80:235);++n)step(*s,1.f/120,1);
  return s;
 }
};
}
void check_portal_mechanics(){museum::PortalInspection::run();}
std::unique_ptr<museum::Study> portal_preview(int chamber){return museum::PortalInspection::preview(chamber);}
