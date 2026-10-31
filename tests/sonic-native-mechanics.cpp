#include "museum/study_motion.cpp"
#include <cassert>
#include <cstdio>
namespace museum {namespace {struct MomentumLoopInspection {
 static void run(){
  Momentum s;
  assert(std::size(s.native_rings)==155&&std::size(s.native_enemies)==22&&std::size(s.native_platforms)==23);
  for(unsigned n=0;n<155;++n)for(unsigned m=n+1;m<155;++m)assert(distance(s.ring(n),s.ring(m))>1);
  for(bool rolling:{false,true}){Momentum a;const auto e=a.enemy(0);a.x_=e.x;a.y_=e.y;a.grounded_=true;a.v_=rolling?300:0;a.rings_=3;a.rolling_=rolling;a.update(.004f);if(rolling){assert(a.enemy_down_[0]&&a.rings_==3);}else{assert(!a.enemy_down_[0]&&a.rings_==0&&a.loose_[0].life>0);assert(a.accepted_.strength>=.30f&&!a.pending_rumble_&&a.speaker_count_>0);}}
  s.rings_=7;s.banked_=7;s.checkpoint_x_=4584*s.unit;s.checkpoint_y_=576*s.unit-26;s.loop_done_=true;s.respawn();assert(s.rings_==0&&s.banked_==0&&!s.loop_done_&&s.x_==4584*s.unit);
  s.checkpoint_x_=6528*s.unit;s.loop_done_=false;s.respawn();assert(s.loop_done_&&s.rings_==0);
  for(float speed:{160.f,1000.f}){Momentum a;a.x_=a.loop_x-.01f;a.y_=a.land_floor(a.x_,704*a.unit,32,32)-26;a.v_=speed;a.rolling_=true;a.update(.008f);assert(a.loop_>=0);for(int n=0;n<360;++n)a.update(1.f/120);if(speed>900)assert(a.loop_done_);else assert(!a.loop_done_&&a.falls_==0);}
  Momentum tube;tube.x_=6176*tube.unit-.01f;tube.y_=640*tube.unit-26;tube.v_=400;tube.rolling_=true;tube.update(.008f);assert(tube.tube_distance_>=0);float previous=tube.x_,previous_y=tube.y_;bool exited=false;for(int n=0;n<1200;++n){tube.update(1.f/120);assert(distance({previous,previous_y},{tube.x_,tube.y_})<16);previous=tube.x_;previous_y=tube.y_;if(tube.tube_distance_<0){exited=true;break;}}assert(exited&&tube.v_>400&&tube.falls_==0);
  Momentum p;unsigned n=0;while(n<23&&(p.native_platforms[n].type!=0x18||p.native_platforms[n].subtype!=1))++n;assert(n<23);const auto start=p.platform(n,0);p.x_=start.x;p.y_=start.y-26;p.standing_platform_=int(n);p.grounded_=true;p.update(.1f);assert(p.x_>start.x&&p.standing_platform_==int(n));
  printf("PASS:155unique rings;23native platforms;walk damage/rolling attack;strong semantic haptic+speaker;checkpoint health/loop plane;weak loop fallback;full loop;energy-driven continuous S tunnel;moving-platform carry\n");
 }
};}}
int main(){museum::MomentumLoopInspection::run();}
