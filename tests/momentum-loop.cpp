#include "museum/study_motion.cpp"
#include <cassert>
namespace museum { namespace {
struct MomentumLoopInspection {
 static void run(){
  for(int hz:{30,60,120}){
   Momentum s;hui::ui::Feedback f;int loop_frames=0;bool upper_ring=false;
   for(int frame=0;frame<hz*20&&!s.loop_done_;++frame){
    hui::InputFrame i;i.connected=true;i.stick_x=1;s.handle(i,f);s.update(1.f/hz);
    if(s.loop_>=0){++loop_frames;assert(std::abs(std::hypot(s.x_-650,s.y_-(Momentum::ground(650)-126))-100)<.01f);if(s.taken_[8]||s.taken_[9])upper_ring=true;}
   }
   assert(s.loop_done_&&loop_frames>hz&&upper_ring&&s.v_>=360);
   assert(s.taken_[8]&&s.taken_[9]);
  }
  {Momentum s;s.loop_done_=true;s.respawn();assert(!s.loop_done_);s.checkpoint_=true;s.loop_done_=true;s.respawn();assert(s.loop_done_);}
  {Momentum spring;spring.x_=2420;spring.y_=Momentum::ground(2420)-26;spring.grounded_=true;spring.update(.001f);assert(spring.vy_<-700&&!spring.grounded_);
   Momentum high;high.x_=2420;high.y_=299;high.grounded_=true;high.update(.001f);assert(high.vy_==0&&high.grounded_);}
  for(int hz:{30,60,120}){
   Momentum s;s.x_=2960;s.y_=Momentum::ground(s.x_)-26;s.loop_done_=true;s.checkpoint_=true;s.grounded_=true;
   hui::ui::Feedback f;bool hit=false;
   for(int tick=0;tick<hz;++tick){hui::InputFrame i;i.connected=true;i.held=hui::action_bit(hui::Action::confirm);if(tick==0)i.pressed=i.held;s.handle(i,f);const float old_vy=s.vy_;s.update(1.f/hz);
    assert(s.y_-26>=Momentum::ceiling(s.x_)-.01f);
    if(old_vy<0&&s.vy_>=0&&s.y_-26<Momentum::ceiling(s.x_)+1)hit=true;
   }assert(hit);
   s.x_=2820;s.y_=Momentum::ground(s.x_)-26;s.v_=450;s.vy_=0;s.grounded_=true;
   for(int tick=0;tick<hz*4&&s.x_<3230;++tick){hui::InputFrame i;i.connected=true;i.stick_x=1;s.handle(i,f);s.update(1.f/hz);if(s.x_>Momentum::tunnel_left&&s.x_<Momentum::tunnel_right)assert(s.y_-26>=Momentum::ceiling(s.x_)-.01f);}
   assert(s.x_>=3230&&s.falls_==0);
  }
  // Last enemy is760px before the finish. Every point of the approach is flat,
  // free of gaps and ceilings: the sign is a destination, not an ambush.
  assert(Momentum::enemy_starts.back()+700<4100);
  // A banked restart has enough flat runway to accelerate before the first
  // enemy. Ring trails describe the same ballistic jump used by the player.
  assert(Momentum::enemy_starts.front()-1510>=280);
  for(unsigned n=12;n<17;++n){const auto p=Momentum::ring(n);const float t=(p.x-1100)/650;
   assert(std::abs(p.y-(Momentum::ground(1100)-26-650*t+725*t*t))<.01f);}
  for(unsigned n=17;n<23;++n)assert(Momentum::ring(n).y==Momentum::ledges[0].y-26);
  for(unsigned n=23;n<29;++n)assert(Momentum::ring(n).y==Momentum::ledges[1].y-26);
  for(float x=3400;x<=4200;x+=5){assert(Momentum::ground(x)==510&&!Momentum::gap(x)&&!Momentum::in_tunnel(x));}
  {Momentum airborne;airborne.x_=4095;airborne.y_=300;airborne.grounded_=false;airborne.update(.001f);assert(!airborne.finished_);}
  for(int hz:{30,60,120}){
   Momentum s;hui::ui::Feedback f;int last_jump=-hz;
   for(int tick=0;tick<hz*45&&!s.finished_;++tick){hui::InputFrame i;i.connected=true;i.stick_x=1;
    const bool hazard=(s.x_>1040&&s.x_<1150)||(s.x_>Momentum::spikes_left-110&&s.x_<Momentum::spikes_left)||(s.x_>2440&&s.x_<2550);
    if(hazard&&s.grounded_&&tick-last_jump>hz/4){i.pressed=hui::action_bit(hui::Action::confirm);last_jump=tick;}
    s.handle(i,f);s.update(1.f/hz);
   }
   std::fprintf(stderr,"Sonic%dHz x%.1f falls%d loop%d finish%d rings%d\n",hz,s.x_,s.falls_,s.loop_done_,s.finished_,s.rings_);
   assert(s.finished_&&s.loop_done_&&s.checkpoint_&&s.falls_<3&&s.rings_>5);
   assert(s.completion()==StudyCompletion::playing);for(int n=0;n<hz*2;++n)s.update(1.f/hz);assert(s.completion()==StudyCompletion::experience_complete);
  }
  std::puts("PASS Sonic tunnel: jump hits actual underside, no roof penetration, input-only run traverses curved underpass without falls at30/60/120Hz");
  std::puts("PASS Sonic loop: input-only run enters real360-degree constrained path at30/60/120Hz, picks both loop rings, exits with momentum");
 }
};
}}
int main(){museum::MomentumLoopInspection::run();}
