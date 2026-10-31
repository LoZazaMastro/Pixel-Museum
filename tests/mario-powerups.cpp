#include "museum/study_motion.cpp"
#include <cassert>
namespace museum { namespace {
struct MarioInspection {
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){hui::ui::Feedback f;
  Jump first;first.p_={205,490};first.vy_=-650;first.grounded_=false;
  for(int n=0;n<10;++n){first.handle(input(),f);first.update(1.f/120);}
  assert(first.block_used_[0]&&first.mushroom_active_&&first.collected_==0);
  const float emerged=first.mushroom_.y;first.update(.1f);assert(first.mushroom_.y<emerged);
  for(int hz:{30,60,120}){Jump bounce;bounce.mushroom_active_=true;bounce.mushroom_emerge_=.5f;bounce.mushroom_={537,550};bounce.mushroom_vx_=76;
   bounce.handle(input(),f);bounce.update(1.f/hz);assert(bounce.mushroom_vx_==-76);const float x=bounce.mushroom_.x;bounce.update(1.f/hz);assert(std::abs((x-bounce.mushroom_.x)*hz-76)<.02f);
  }
  Jump grown;grown.mushroom_active_=true;grown.mushroom_emerge_=.5f;grown.mushroom_={105,550};grown.handle(input(),f);grown.update(.001f);
  assert(grown.large_&&!grown.mushroom_active_&&grown.half_height()==30&&grown.p_.y+grown.half_height()==550);
  auto down=input();down.held=hui::action_bit(hui::Action::down);grown.handle(down,f);assert(grown.crouching_&&grown.half_height()==15&&grown.p_.y+15==550);
  down.pressed=hui::action_bit(hui::Action::confirm);grown.handle(down,f);grown.update(.01f);assert(grown.vy_<0&&grown.crouching_);
  grown.handle(input(),f);assert(!grown.crouching_&&grown.half_height()==30);
  Jump low_ceiling;low_ceiling.p_={300,490};low_ceiling.mushroom_active_=true;low_ceiling.mushroom_emerge_=.5f;low_ceiling.mushroom_={300,505};low_ceiling.handle(input(),f);low_ceiling.update(.001f);assert(low_ceiling.large_&&low_ceiling.crouching_);low_ceiling.handle(input(),f);assert(low_ceiling.crouching_);
  Jump brick;brick.large_=true;brick.p_={300,500};brick.vy_=-650;brick.grounded_=false;brick.handle(input(),f);brick.update(.02f);assert(brick.brick_broken_[0][0]);
  unsigned count=0;for(const auto&s:brick.shards_)if(s.life>0)++count;assert(count==4);const auto shard=brick.shards_[0];brick.update(.05f);assert(brick.shards_[0].p.x!=shard.p.x&&brick.shards_[0].vy>shard.vy);
  Jump small;small.p_={300,485};small.vy_=-650;small.grounded_=false;small.handle(input(),f);small.update(.02f);assert(!small.brick_broken_[0][0]&&small.vy_>0);
  Jump normal;normal.p_={380,490};normal.vy_=-650;normal.grounded_=false;normal.handle(input(),f);normal.update(.02f);assert(normal.block_used_[1]&&normal.collected_==1&&normal.coin_pop_[1]>=0);
  const auto age=normal.coin_pop_[1];normal.update(.1f);assert(normal.coin_pop_[1]>age);for(int n=0;n<8;++n)normal.update(.1f);assert(normal.coin_pop_[1]<0&&normal.collected_==1);
  Jump hit;hit.large_=true;hit.p_={Jump::enemy_x(0,.001f),520};hit.handle(input(),f);hit.update(.001f);assert(!hit.large_&&hit.falls_==0&&hit.immune_>0);
  hit.block_used_[0]=true;hit.immune_=0;hit.update(.001f);assert(hit.falls_==1&&hit.p_.x==105&&hit.checkpoint_==0&&!hit.block_used_[0]);
  hit.checkpoint_=5;hit.p_={3300,800};hit.immune_=0;hit.update(.001f);assert(hit.p_.x==105&&hit.checkpoint_==0);
  hui::gfx::DrawList visible,hidden;Jump tube;tube.draw_actor(visible,105,paper);assert(!visible.instances().empty());tube.pipe_from_=1;tube.draw_actor(hidden,105,paper);assert(hidden.instances().empty());
  down.pressed=0;for(int hz:{30,60,120}){Jump travel;travel.p_={1141,445};for(int n=0;n<hz/3;++n){travel.handle(down,f);travel.update(1.f/hz);}assert(travel.pipe_from_==1);
   for(int n=0;n<hz;++n){travel.handle(input(),f);travel.update(1.f/hz);}assert(travel.secret_&&travel.pipe_from_<0);
  }
  for(int hz:{30,60,120}){Jump route;int since=0;
   for(int tick=0;tick<hz*70&&!route.finished_;++tick){auto command=input();command.stick_x=1;command.held=hui::action_bit(hui::Action::west)|hui::action_bit(hui::Action::confirm);bool danger=false;
    for(const auto pipe:Jump::pipes)if((pipe.x-route.p_.x>0&&pipe.x-route.p_.x<125)||(std::abs(route.p_.y+15-pipe.y)<1&&route.p_.x>pipe.x+pipe.w-45))danger=true;
    for(unsigned n=0;n<6;++n){const auto b=Jump::platforms[n];if(route.p_.x<b.x+b.w&&b.x+b.w-route.p_.x<100)danger=true;}
    for(unsigned n=0;n<4;++n)if(!route.enemy_down_[n]&&Jump::enemy_x(n,route.time_)-route.p_.x>0&&Jump::enemy_x(n,route.time_)-route.p_.x<105)danger=true;
    if(route.p_.x>3630)danger=true;if(route.grounded_&&danger&&since>hz/5){command.pressed=hui::action_bit(hui::Action::confirm);since=0;}
    route.handle(command,f);route.update(1.f/hz);++since;
   }
   std::printf("Mario route%dHz x%.1f deaths%d finished%d checkpoints%d\n",hz,route.p_.x,route.falls_,route.finished_,route.checkpoint_);assert(route.finished_&&route.checkpoint_==0);
  }
  std::puts("PASS Mario causality: first mushroom emerges/moves/reverses at identical speed30/60/120; pickup2xheight, crouch+jump, bigbrick4fallingpixelshards/smallbounce, questioncoinpopdisappears, shrinkthenstartdeath/no checkpoint, actorhiddeninpipe/realroomentry.");
 }
};
}}
int main(){museum::MarioInspection::run();}
