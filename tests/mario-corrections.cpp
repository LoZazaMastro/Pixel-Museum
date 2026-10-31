#include "museum/study_motion.cpp"
#include <cassert>
namespace museum { namespace {
struct MarioInspection {
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){
  static_assert(Jump::lights.size()==35);
  for(const auto light:Jump::lights)assert(light.x>0&&light.y>0); // no implicit origin coin
  Jump walk,run;hui::ui::Feedback f;auto i=input();i.stick_x=1;
  for(int n=0;n<20;++n){walk.handle(i,f);walk.update(1.f/120);}
  i.held=i.pressed=hui::action_bit(hui::Action::west);
  for(int n=0;n<20;++n){run.handle(i,f);run.update(1.f/120);i.pressed=0;}
  assert(run.p_.x>walk.p_.x+8&&run.running_);assert(run.p_.x>105);
  Jump pipe;pipe.p_={537,535};pipe.vx_=200;i=input();i.stick_x=1;
  pipe.handle(i,f);pipe.update(1.f/120);assert(pipe.p_.x<=538&&pipe.vx_==0);
  pipe.p_={580,450};pipe.vy_=300;pipe.handle(input(),f);
  for(int n=0;n<30;++n)pipe.update(1.f/120);
  assert(pipe.grounded_&&pipe.p_.y==475);
  Jump coin;coin.p_=Jump::lights[0];coin.handle(input(),f);coin.update(.001f);assert(coin.collected_==1&&coin.score_==100);
  f.clear();coin.handle(input(),f);assert(f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::coin&&!f.tactile.empty());
  coin.update(.001f);assert(coin.score_==100);f.clear();coin.handle(input(),f);assert(f.speaker_cues.empty());
  Jump block;block.p_={205,490};block.vy_=-650;block.grounded_=false;
  for(int n=0;n<10;++n){block.handle(input(),f);block.update(1.f/120);}
  assert(block.block_used_[0]&&block.mushroom_active_&&block.score_==0);
  block.p_={205,490};block.vy_=-650;
  for(int n=0;n<10;++n){block.handle(input(),f);block.update(1.f/120);}
  assert(block.score_==0); // the first used block never duplicates its power-up
  Jump stomp;stomp.p_={Jump::enemy_x(0,.001f),510};stomp.vy_=300;stomp.grounded_=false;stomp.update(.02f);
  assert(stomp.enemy_down_[0]&&stomp.score_==200&&stomp.vy_<0);
  Jump low,high;low.p_={4121,535};high.p_={4121,285};low.update(.001f);high.update(.001f);
  assert(low.finished_&&high.finished_&&high.flag_score_>low.flag_score_&&high.score_<=5000);
  assert(high.completion()==StudyCompletion::playing);
  for(int n=0;n<260;++n)high.update(1.f/120);
  assert(high.completion()==StudyCompletion::experience_complete&&high.p_.x==4270&&high.p_.y==535);
  // The staircase ends150px before the pole: no invisible bridge.
  Jump air;air.p_={4050,375};air.vy_=0;air.grounded_=false;air.update(.1f);assert(air.p_.y>375&&!air.grounded_);
  for(int hz:{30,60,120}){
   Jump travel;travel.p_={1141,445};auto down=input();down.held=hui::action_bit(hui::Action::down);
   for(int n=0;n<hz*2;++n){travel.handle(down,f);travel.update(1.f/hz);}
   assert(travel.secret_&&travel.p_.x==180&&travel.p_.y+travel.half_height()==550&&travel.pipe_from_<0);
   // Entered a different room, not a teleport between overworld pipe tops.
   auto jump=input();jump.pressed=jump.held=hui::action_bit(hui::Action::confirm);travel.handle(jump,f);
   float highest=travel.p_.y;for(int n=0;n<hz;++n){travel.update(1.f/hz);highest=std::min(highest,travel.p_.y);}
   assert(highest>370&&travel.secret_); // inlet bottom266 is unreachable from floor550.
   auto right=input();right.stick_x=1;right.held=hui::action_bit(hui::Action::confirm);bool horizontal=false,upward=false;float previous_x=0,previous_y=0;unsigned coin_sounds=0;
   for(int n=0;n<hz*7&&(travel.secret_||travel.pipe_from_>=0);++n){
    right.pressed=travel.secret_&&travel.grounded_&&travel.p_.x>250&&travel.p_.x<1000?hui::action_bit(hui::Action::confirm):0;
    f.clear();travel.handle(right,f);for(const auto&cue:f.speaker_cues)if(cue.cue==hui::audio::SpeakerCue::coin)++coin_sounds;travel.update(1.f/hz);
    if(travel.pipe_from_==3){if(travel.pipe_time_>.05f&&travel.pipe_time_<.3f&&travel.p_.x>previous_x)horizontal=true;
     if(travel.pipe_time_>.4f&&travel.p_.y<previous_y)upward=true;previous_x=travel.p_.x;previous_y=travel.p_.y;}
   }
   assert(horizontal&&upward&&!travel.secret_&&travel.pipe_from_<0);
   assert(travel.collected_>=3&&coin_sounds>=3);
   assert(travel.p_.x>2590&&travel.p_.x<2680&&travel.p_.y==445);
   Jump outlet;outlet.p_={2632,445};for(int n=0;n<hz;++n){outlet.handle(down,f);outlet.update(1.f/hz);}assert(!outlet.secret_&&outlet.pipe_from_<0);
   // Off-centre/down on ordinary ground never teleports or emits pipe effects.
   Jump noop;for(int n=0;n<hz;++n){noop.handle(down,f);noop.update(1.f/hz);}assert(noop.pipe_from_<0&&noop.p_.x==105);
  }
  Jump brick;brick.p_={300,490};brick.vy_=-650;brick.grounded_=false;
  for(int n=0;n<10;++n){brick.handle(input(),f);brick.update(1.f/120);}assert(brick.vy_>0&&brick.p_.y>=485&&brick.collected_==0);
  for(int hz:{30,60,120}){
   Jump route;int since_jump=0;
   for(int tick=0;tick<hz*70&&!route.finished_;++tick){
    auto command=input();command.stick_x=1;command.held=hui::action_bit(hui::Action::west)|hui::action_bit(hui::Action::confirm);
    bool danger=false;
    for(const auto&pipe:Jump::pipes)if((pipe.x-route.p_.x>0&&pipe.x-route.p_.x<125)||(std::abs(route.p_.y+15-pipe.y)<1&&route.p_.x>pipe.x+pipe.w-45))danger=true;
    for(unsigned n=0;n<6;++n){const auto b=Jump::platforms[n];const float end=b.x+b.w;if(route.p_.x<end&&end-route.p_.x<100)danger=true;}
    for(unsigned n=0;n<Jump::enemy_starts.size();++n)if(!route.enemy_down_[n]&&Jump::enemy_x(n,route.time_)-route.p_.x>0&&Jump::enemy_x(n,route.time_)-route.p_.x<105)danger=true;
    if(route.p_.x>3630)danger=true;
    if(route.grounded_&&danger&&since_jump>hz/5){command.pressed=hui::action_bit(hui::Action::confirm);since_jump=0;}
    route.handle(command,f);route.update(1.f/hz);++since_jump;
   }
   std::fprintf(stderr,"Mario%dHz x%.1f checkpoint%d falls%d finished%d\n",hz,route.p_.x,route.checkpoint_,route.falls_,route.finished_);
   assert(route.finished_&&route.checkpoint_==0&&route.falls_<=2);
  }
  std::puts("PASS Mario: run, solid bricks, separate secret room/high inlet/right-up outlet/no-op, isolated flag jump, score by height, slide/walk ending and30/60/120Hz traversal");
 }
};
}}
int main(){museum::MarioInspection::run();}
