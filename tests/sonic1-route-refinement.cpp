#include "museum/study_motion.cpp"
#include <cassert>
#include <cstdio>
namespace museum { namespace {
struct MomentumLoopInspection {
 static void run(){
  for(int hz:{30,60,120}){
   Momentum s;hui::ui::Feedback feedback;hui::InputFrame i;i.connected=true;i.stick_x=1;
   bool jump1=false,jump2=false,jump_upper=false,loop_seen=false,loop_completed=false,tunnel_low=false,tunnel_high=false,damaged=false;
   float previous=s.x_,maxstep=0;int rings_before=0;
   for(int frame=0;frame<hz*40&&!s.finished_;++frame){
    i.pressed=0;i.held=0;i.stick_y=s.x_>600&&s.x_<800?1.f:0.f;
    bool jump=false;
    if(!jump1&&s.x_>1080&&s.grounded_){jump1=true;jump=true;}
    if(false&&!jump_upper&&s.x_>1800&&s.x_<1970&&s.grounded_){jump_upper=true;jump=true;}
    if(!jump2&&s.x_>3360&&s.x_<3470&&s.grounded_){jump2=true;jump=true;}
    if(jump)i.pressed=i.held=hui::action_bit(Action::confirm);
    s.handle(i,feedback);s.update(1.f/hz);
    for(const auto&r:s.loose_)damaged|=r.life>0;loop_seen|=s.loop_>=0;loop_completed|=s.loop_done_;
    if(s.x_>4550&&s.x_<5050){tunnel_low|=s.y_>Momentum::ceiling(s.x_);tunnel_high|=s.y_+26<=Momentum::ceiling(s.x_)-Momentum::tunnel_roof+2;}
    maxstep=std::max(maxstep,std::abs(s.x_-previous));previous=s.x_;rings_before=std::max(rings_before,s.rings_);
    if(frame%(hz*2)==0||(hz==30&&s.x_>1400&&s.x_<2950&&frame%2==0))std::printf("trace %d %d x%.1f y%.1f v%.1f ground%d loop%.2f falls%d rings%d\n",hz,frame,s.x_,s.y_,s.v_,s.grounded_,s.loop_,s.falls_,s.rings_);
   }
   std::printf("route %dHz finish%d loop_seen%d complete%d falls%d rings%d maxstep%.1f low%d high%d\n",hz,s.finished_,loop_seen,loop_completed,s.falls_,rings_before,maxstep,tunnel_low,tunnel_high);
   assert(s.finished_&&s.falls_==0&&!damaged&&loop_seen&&loop_completed&&rings_before>=20);
   assert(maxstep<60);
   // The high route is reached by a deliberate, slower jump, not by placing
   // the character on its platforms. Both branches begin at the real reset.
   Momentum upper;bool first=false,highjump=false,secondgap=false,saw_high=false,enemyjump=false,upperdamage=false;
   for(int frame=0;frame<hz*45&&!upper.finished_;++frame){
    i={};i.connected=true;i.stick_x=1;
    if(upper.x_>600&&upper.x_<800)i.stick_y=1;
    if(!highjump&&upper.x_>1700&&upper.v_>440)i.stick_x=-1;
    bool jump=false;
    if(!first&&upper.x_>1080&&upper.grounded_){first=true;jump=true;}
    if(!highjump&&upper.x_>1800&&upper.x_<1940&&upper.v_<470&&upper.grounded_){highjump=true;jump=true;std::printf("upperjump x%.1f v%.1f y%.1f\n",upper.x_,upper.v_,upper.y_);}
    if(!enemyjump&&upper.x_>3040&&upper.x_<3140&&upper.grounded_){enemyjump=true;jump=true;}
    if(!secondgap&&upper.x_>3360&&upper.x_<3470&&upper.grounded_){secondgap=true;jump=true;}
    if(jump)i.pressed=i.held=hui::action_bit(Action::confirm);
    const float prevx=upper.x_;const int prevfalls=upper.falls_;upper.handle(i,feedback);upper.update(1.f/hz);if(upper.falls_>prevfalls)std::printf("upperfall at%.1f hz%d\n",prevx,hz);
    for(const auto&r:upper.loose_)upperdamage|=r.life>0;saw_high|=upper.grounded_&&upper.x_>=1940&&upper.x_<=2440&&std::abs(upper.y_+26-355)<1;
   }
   std::printf("upper %dHz high%d finish%d falls%d x%.1f\n",hz,saw_high,upper.finished_,upper.falls_,upper.x_);
   assert(saw_high&&upper.finished_&&upper.falls_==0&&!upperdamage);
   Momentum low;bool lowfirst=false,lowsecond=false,skipspring=false,saw_low=false,lowdamage=false;
   for(int frame=0;frame<hz*40&&!low.finished_;++frame){
    i={};i.connected=true;i.stick_x=1;if((low.x_>600&&low.x_<800)||(low.x_>4940&&low.x_<5130))i.stick_y=1;if(low.x_>2950&&low.x_<3210&&low.v_>650)i.stick_x=-1;
    bool jump=false;if(!lowfirst&&low.x_>1080&&low.grounded_){lowfirst=true;jump=true;}
    if(!lowsecond&&low.x_>3210&&low.x_<3370&&low.grounded_){lowsecond=true;jump=true;}
    if(!skipspring&&low.x_>3870&&low.x_<4250&&low.grounded_){skipspring=true;jump=true;}
    if(jump)i.pressed=i.held=hui::action_bit(Action::confirm);
    low.handle(i,feedback);low.update(1.f/hz);
    for(const auto&r:low.loose_)lowdamage|=r.life>0;saw_low|=low.x_>4580&&low.x_<5020&&low.y_>Momentum::ceiling(low.x_)+26;
   }
   std::printf("low %dHz saw%d finish%d falls%d\n",hz,saw_low,low.finished_,low.falls_);assert(saw_low&&low.finished_&&low.falls_==0&&!lowdamage);
   // An underpowered rail must lose contact instead of being forced around.
   Momentum weak;weak.x_=Momentum::loop_x;weak.y_=Momentum::ground(weak.x_)-26;weak.loop_=0;weak.loop_speed_=650;weak.grounded_=false;
   bool detached=false;float weak_prev=weak.x_;float weak_step=0;
   for(int n=0;n<hz*3&&!(detached&&weak.grounded_);++n){weak.handle(i,feedback);weak.update(1.f/hz);weak_step=std::max(weak_step,std::abs(weak.x_-weak_prev));weak_prev=weak.x_;if(weak.loop_<0&&!weak.loop_done_)detached=true;}
   std::printf("weak %dHz detached%d done%d falls%d step%.1f x%.1f\n",hz,detached,weak.loop_done_,weak.falls_,weak_step,weak.x_);assert(detached&&weak.falls_==0&&weak_step<60);
   Momentum nojump;i={};i.connected=true;i.stick_x=1;
   for(int n=0;n<hz*8;++n){nojump.handle(i,feedback);nojump.update(1.f/hz);}
   assert(nojump.falls_>0&&!nojump.finished_);
   // Actual collision at speed must hurt a walking body, not kill an enemy.
   Momentum hit;hit.x_=Momentum::enemy_starts[0]-60;hit.y_=Momentum::ground(hit.x_)-26;hit.v_=700;hit.rings_=8;hit.pending_rumble_=true;i={};i.connected=true;i.stick_x=1;
   for(int n=0;n<hz/4&&hit.rings_>0;++n){hit.handle(i,feedback);hit.update(1.f/hz);}
   assert(hit.rings_==0&&hit.falls_==0&&!hit.enemy_down_[0]&&hit.immune_>0);
   assert(std::count_if(hit.loose_.begin(),hit.loose_.end(),[](const auto&r){return r.life>0;})==8);
   const float push=hit.v_;assert(push<0);
   feedback.clear();hit.handle(i,feedback);assert(!feedback.tactile.empty()&&feedback.tactile[0].strength>=.30f&&!feedback.speaker_cues.empty()&&feedback.speaker_cues[0].cue==hui::audio::SpeakerCue::ring);hit.update(.01f);assert(hit.falls_==0);
   // Ring recovery uses a live particle after its pickup grace period.
   for(int n=0;n<hz/2;++n){hit.handle(i,feedback);hit.update(1.f/hz);}
   auto particle=std::find_if(hit.loose_.begin(),hit.loose_.end(),[](const auto&r){return r.life>0;});assert(particle!=hit.loose_.end());
   hit.x_=particle->p.x;hit.y_=particle->p.y;hit.v_=hit.vy_=0;hit.grounded_=false;hit.update(.001f);assert(hit.rings_>0);
   // An unprotected second collision with no rings resets the experience.
   hit.rings_=0;hit.immune_=0;hit.hurt(hit.x_+1);assert(hit.falls_==1);
   // The same collision while rolling defeats the enemy and stays grounded.
   Momentum rollhit;rollhit.x_=Momentum::enemy_starts[0]-60;rollhit.y_=Momentum::ground(rollhit.x_)-26;rollhit.v_=700;i={};i.connected=true;i.stick_x=1;i.stick_y=1;
   for(int n=0;n<hz/4&&!rollhit.enemy_down_[0];++n){rollhit.handle(i,feedback);rollhit.update(1.f/hz);}
   assert(rollhit.enemy_down_[0]&&rollhit.falls_==0&&rollhit.grounded_&&rollhit.rolling_);
   // Every ring is collectable by the body, never by a draw-only counter.
   Momentum collection;
   for(unsigned n=0;n<collection.taken_.size();++n){const auto p=Momentum::ring(n);assert(std::isfinite(p.x)&&std::isfinite(p.y)&&p.x<Momentum::finish_x);}
   // Reversal should decelerate more decisively than releasing the stick.
   Momentum release,reverse;release.v_=reverse.v_=700;i={};i.connected=true;
   release.handle(i,feedback);release.update(.1f);i.stick_x=-1;reverse.handle(i,feedback);reverse.update(.1f);assert(reverse.v_<release.v_-100);
  }
  std::puts("PASS Sonic1 full real-input route, physical fast loop, underpowered detach, no teleports, ring trail and countersteering at30/60/120Hz");
 }
};}}
int main(){museum::MomentumLoopInspection::run();}
