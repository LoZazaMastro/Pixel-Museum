#include "museum/study_arcade.cpp"
#include <cassert>
namespace museum {namespace {
struct ArcadeHapticsInspection {
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){
  for(int hz:{30,60,120}){
   {Paddle game;hui::ui::Feedback out;auto frame=input();game.running_=true;const float base=std::hypot(235.f,80.f);
    for(int rally=1;rally<=32;++rally){const bool ours=rally%2;game.ball_={ours?34.f:646.f,195};game.velocity_={ours?-235.f:235.f,0};game.update(1.f/hz);out.clear();game.handle(frame,out);assert(game.returns_==rally);assert(out.tactile.size()==1&&out.tactile[0].pattern==hui::audio::Tactile::impact);assert((out.tactile[0].pan<0)==ours);assert(out.speaker_cues.size()==unsigned(ours));if(ours)assert(out.speaker_cues[0].cue==hui::audio::SpeakerCue::ball_hit);assert(std::abs(norm(game.velocity_)-base*std::min(3.f,std::pow(1.05f,float(rally))))<.01f);}
    game.ball_={340,8};game.velocity_={0,-100};game.update(1.f/hz);out.clear();game.handle(frame,out);assert(out.tactile.size()==1&&out.tactile[0].pattern==hui::audio::Tactile::rise&&out.speaker_cues.empty());
    game.ball_={340,382};game.velocity_={0,100};game.update(1.f/hz);out.clear();game.handle(frame,out);assert(out.tactile.size()==1&&out.tactile[0].pattern==hui::audio::Tactile::fall);
    Bricks bricks;bricks.running_=true;bricks.ball_={8,220};bricks.velocity_={-100,0};bricks.update(1.f/hz);out.clear();bricks.handle(frame,out);assert(out.tactile.size()==1&&out.speaker_cues.empty());
    bricks.ball_={672,220};bricks.velocity_={100,0};bricks.update(1.f/hz);out.clear();bricks.handle(frame,out);assert(out.tactile.size()==1&&out.speaker_cues.empty());
    bricks.ball_={340,8};bricks.velocity_={0,-100};bricks.update(1.f/hz);out.clear();bricks.handle(frame,out);assert(out.tactile.size()==1&&out.speaker_cues.empty());
    bricks.ball_={8,8};bricks.velocity_={-100,-100};bricks.update(1.f/hz);out.clear();bricks.handle(frame,out);assert(out.tactile.size()==2&&out.speaker_cues.empty()); // Both accepted corner contacts survive one frame.
    Paddle serve;Bricks launch;auto click=input();click.pressed=hui::action_bit(Action::touch);out.clear();serve.handle(click,out);assert(serve.running_);out.clear();launch.handle(click,out);assert(launch.running_&&out.speaker_cues.empty());
    serve.running_=launch.running_=false;click.pressed=0;click.held=hui::action_bit(Action::touch);out.clear();serve.handle(click,out);launch.handle(click,out);assert(!serve.running_&&!launch.running_); // A held click never retriggers.
    Wireframe flight;flight.configure_gyro(false,1.75f);assert(!flight.motion_controls());flight.reset();assert(!flight.gyro_enabled()&&flight.gyro_sensitivity()==1.75f);frame.stick_x=.5f;frame.motion.available=true;flight.handle(frame,out);flight.update(1.f/hz);assert(flight.position_.x>0&&flight.flight_time_>0&&out.speaker_cues.empty());
   }
   Paddle p;hui::ui::Feedback f;auto i=input();i.stick_y=1;unsigned count=0;
   for(int n=0;n<hz/2;++n){f.clear();p.handle(i,f);count+=f.tactile.size();p.update(1.f/hz);}assert(count==1);
   p.player_=352;count=0;f.clear();p.handle(input(),f);for(int n=0;n<hz/2;++n){f.clear();p.handle(i,f);count+=f.tactile.size();p.update(1.f/hz);}assert(count==0);
   i.stick_y=-1;p.handle(i,f);p.update(1.f/hz);f.clear();p.handle(i,f);assert(f.tactile.size()==1);
   p.reset();p.handle(i,f);p.update(1.f/hz);i.focus_lost=true;f.clear();p.handle(i,f);assert(f.tactile.empty());i.focus_lost=false;i.stick_y=0;f.clear();p.handle(i,f);assert(f.tactile.empty());
   Bricks b;i=input();i.stick_x=1;count=0;for(int n=0;n<hz/2;++n){f.clear();b.handle(i,f);count+=f.tactile.size();b.update(1.f/hz);}assert(count==1);
   b.paddle_=629;f.clear();b.handle(input(),f);count=0;for(int n=0;n<hz/2;++n){f.clear();b.handle(i,f);count+=f.tactile.size();b.update(1.f/hz);}assert(count==0);
   Wireframe flight;flight.position_.x=1.5f;i=input();i.stick_x=1;for(int n=0;n<hz/3;++n){f.clear();flight.handle(i,f);for(const auto&e:f.tactile)assert(e.pattern==hui::audio::Tactile::airflow);flight.update(1.f/hz);}
  }
  for(int hz:{30,60,120})for(int edge=0;edge<4;++edge){Orbit wrap;wrap.ship_={edge==0?.1f:edge==1?679.9f:120.f,edge==2?.1f:edge==3?389.9f:120.f};wrap.velocity_={edge==0?-200.f:edge==1?200.f:0.f,edge==2?-200.f:edge==3?200.f:0.f};wrap.update(1.f/hz);assert(!wrap.lost_);assert(wrap.ship_.x>=0&&wrap.ship_.x<680&&wrap.ship_.y>=0&&wrap.ship_.y<390);if(edge==0)assert(wrap.ship_.x>670);if(edge==1)assert(wrap.ship_.x<10);if(edge==2)assert(wrap.ship_.y>380);if(edge==3)assert(wrap.ship_.y<10);}
  hui::ui::Feedback f;Formation inv;inv.fire();assert(inv.accepted_.strength>0);inv.handle(input(),f);assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::impact);
  assert(f.tactile[0].strength>=.4f&&f.tactile[0].strength<=.45f&&f.speaker_cues.size()==1);assert(f.cues.size()==1&&f.cues[0].cue==hui::audio::Cue::invader_shot);assert(inv.formation_speed()==25);inv.hits_=21;assert(inv.formation_speed()==35.f);inv.time_=75;assert(inv.formation_speed()==70.f);inv.reset();inv.bonus_active_=true;inv.bonus_x_=340;inv.shots_[0]={{340,36},true};inv.update(1.f/60);f.clear();inv.handle(input(),f);assert(inv.bonus_hits_==1&&f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::bonus);
  for(auto&shot:inv.shots_)shot.active=true;inv.fire();f.clear();inv.handle(input(),f);assert(f.tactile.empty()&&f.cues.empty()&&f.speaker_cues.empty());
  Gravity t;auto i=input();i.nav=Direction::right;t.handle(i,f);assert(!f.tactile.empty());
  for(int n=0;n<15;++n)t.handle(i,f);f.clear();t.handle(i,f);assert(f.tactile.empty());
  t.type_=1;i=input();i.pressed=hui::action_bit(Action::confirm);f.clear();t.handle(i,f);assert(f.tactile.empty());
  t.type_=0;t.x_=4;t.shape_={V{-1,0},V{0,0},V{1,0},V{2,0}};f.clear();t.handle(i,f);assert(f.tactile.size()==1);
  t.reset();t.drop();f.clear();t.handle(input(),f);assert(f.tactile.size()==1);
  Maze m;i=input();i.nav=Direction::up;f.clear();m.handle(i,f);assert(f.tactile.size()==1);f.clear();m.handle(i,f);assert(f.tactile.empty());
  Orbit o;i=input();i.pressed=i.held=hui::action_bit(Action::confirm);f.clear();o.handle(i,f);assert(f.tactile.size()==1);
  std::puts("PASS Arcade accepted haptics: movement start once at30/60/120, clamped/noop/focus silent, actual projectile vs fullpool, Tetris accepted move/rotation/lock vs clamped/squarepiece, maze changedqueue vs nochange, orbit brake");
 }
};}}
int main(){museum::ArcadeHapticsInspection::run();}
