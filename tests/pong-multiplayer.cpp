#include "museum/study_arcade.cpp"
#include <cassert>
namespace museum {namespace {
struct PongMultiplayerInspection{
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){for(int hz:{30,60,120}){
  const float dt=1.f/hz,base=std::hypot(235.f,80.f);hui::ui::Feedback f;
  float previous_ai_speed=0;
  for(float ratio:{1.f,1.5f,2.f,3.f,10.f}){Paddle ai;ai.running_=true;ai.ball_={340,330};ai.velocity_={base*ratio,0};ai.update(dt);const float speed=(ai.opponent_-195)/dt;assert(speed>=174.99f&&speed<=210.01f&&speed>=previous_ai_speed-.01f);assert(speed<310);if(ratio==1)assert(std::abs(speed-175)<.01f);previous_ai_speed=speed;}
  // Even a fast rally leaves a real scoring window. The previous 525px/s
  // opponent intercepted this shot; the bounded one cannot teleport to it.
  Paddle winnable;winnable.running_=true;winnable.ball_={590,270};winnable.velocity_={base*3,0};
  for(int step=0;step<hz&&winnable.running_;++step)winnable.update(dt);
  assert(winnable.player_score_==1&&winnable.opponent_score_==0);
  Paddle rally;rally.running_=true;
  for(int hit=1;hit<=60;++hit){const bool left=hit%2;const float previous_speed=std::hypot(rally.velocity_.x,rally.velocity_.y);rally.ball_={left?34.f:646.f,195};rally.velocity_={left?-previous_speed:previous_speed,0};rally.update(dt);assert(rally.returns_==hit);const float expected=base*std::min(3.f,std::pow(1.05f,float(hit)));assert(std::abs(std::hypot(rally.velocity_.x,rally.velocity_.y)-expected)<.001f);}
  assert(rally.rally_multiplier(0)==1.f&&rally.rally_multiplier(23)==3.f&&rally.rally_multiplier(100)==3.f);
  rally.ball_={340,8.1f};rally.velocity_={0,-base};const int exchanges=rally.returns_;rally.update(dt);assert(rally.returns_==exchanges);
  rally.reset();assert(rally.returns_==0&&std::abs(std::hypot(rally.velocity_.x,rally.velocity_.y)-base)<.001f);
  Paddle game;auto i=input();i.secondary.connected=true;i.secondary.stick_y=1;
  game.handle(i,f);game.update(dt);assert(game.local_multiplayer()&&game.two_players_);assert(game.player_==195);assert(std::abs(game.opponent_-195-310*dt)<.001f);
  i.secondary.stick_y=0;game.running_=true;game.ball_={340,330};const float at_rest=game.opponent_;game.handle(i,f);game.update(dt);assert(game.opponent_==at_rest); // No AI assists the human player.
  i.secondary.connected=false;game.handle(i,f);game.update(dt);assert(!game.two_players_&&game.opponent_>at_rest);
  i.secondary.connected=true;i.secondary.held=hui::action_bit(Action::up);game.handle(i,f);const float before=game.opponent_;game.update(dt);assert(game.opponent_<before);
  i.secondary.held=0;i.secondary.touch.available=true;i.secondary.touch.count=1;i.secondary.touch.points[0].y=.25f;game.handle(i,f);assert(std::abs(game.opponent_-116.5f)<.001f);
  game.running_=false;i.secondary.touch={};i.secondary.pressed=hui::action_bit(Action::touch);game.handle(i,f);assert(game.running_);
  game.ball_={679,195};game.velocity_={235,0};game.update(dt);assert(!game.running_&&game.player_score_==1&&game.opponent_score_==0&&game.returns_==0);
  game.running_=true;game.ball_={1,195};game.velocity_={-235,0};game.update(dt);assert(!game.running_&&game.player_score_==1&&game.opponent_score_==1);
  i.secondary.focus_lost=true;i.secondary.pressed=hui::action_bit(Action::confirm);game.handle(i,f);assert(!game.running_&&!game.two_players_);
  i.focus_lost=true;i.secondary.focus_lost=false;i.secondary.stick_y=1;const float frozen=game.opponent_;game.handle(i,f);game.update(dt);assert(game.opponent_==frozen);
  game.reset();assert(game.player_score_==0&&game.opponent_score_==0);
 }
 std::puts("PASS Pong30/60/120: AI stays175-210px/s and scoreable at maximum rally speed; two independent paddles, no AI takeover during human idle, unplug fallback, d-pad/touch, second-pad serve, real goals, focus isolation and reset.");}
};}}
int main(){museum::PongMultiplayerInspection::run();}
