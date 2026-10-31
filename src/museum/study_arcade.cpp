// Pixel Museum - seven original studies of motion, rules and space.
// Copyright (C) 2026 Andrea Sgarro. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include "museum/flight_motion.hpp"
#include "museum/haptic_interactions.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <string_view>
namespace museum {
namespace {
using hui::Action;using hui::Direction;using hui::InputFrame;
using hui::gfx::Color;using hui::gfx::Rect;using hui::gfx::DrawList;using hui::gfx::Align;
using hui::ui::Fonts;using hui::ui::Feedback;
constexpr float pi=3.14159265359f;
constexpr Color ink{.153f,.188f,.165f,1};
struct V {float x=0,y=0;V operator+(V b)const{return{x+b.x,y+b.y};}V operator-(V b)const{return{x-b.x,y-b.y};}V operator*(float b)const{return{x*b,y*b};}};
float norm(V a){return std::sqrt(a.x*a.x+a.y*a.y);}
float bounded_dt(float dt){return std::isfinite(dt)&&dt>0?std::min(dt,.05f):0;}
float axis(const InputFrame&i,bool horizontal){const float value=horizontal?i.stick_x:i.stick_y;if(std::isfinite(value)&&std::abs(value)>.04f)return std::clamp(value,-1.f,1.f);return horizontal?float(i.is_held(Action::right))-float(i.is_held(Action::left)):float(i.is_held(Action::down))-float(i.is_held(Action::up));}
std::uint32_t random(std::uint32_t&seed){seed=seed*1664525u+1013904223u;return seed;}
class Scene:public Study {
protected:
 std::array<hui::audio::TactileEvent,8> pending_pulses_{};unsigned pending_pulse_count_=0;
 AcceptedMotionHaptics motion_haptics_;hui::audio::TactileEvent accepted_{hui::audio::Tactile::focus,0,0,0};bool active_input_=true;int speaker_pending_=-1;float speaker_pitch_=1,speaker_gain_=.12f;
 void speaker(hui::audio::SpeakerCue cue,float pitch=1,float gain=.12f){if(active_input_){speaker_pending_=int(cue);speaker_pitch_=pitch;speaker_gain_=gain;}}
 void pulse(hui::audio::Tactile kind,float strength=.07f,float seconds=.025f,float pan=0){if(active_input_){if(pending_pulse_count_<pending_pulses_.size())pending_pulses_[pending_pulse_count_++]={kind,strength,seconds,pan};if(strength>=accepted_.strength)accepted_={kind,strength,seconds,pan};}}
 struct Dot {V p,v;float life=0;};std::array<Dot,24>dots_{};unsigned cursor_=0;float rumble_=0,time_=0,touch_time_=0;Color accent_{};
 void event(V p,int note,float strength=.10f,hui::audio::Tactile pattern=hui::audio::Tactile::impact,float pan=0){sound(note);pulse(pattern,strength,.035f,pan);for(unsigned i=0;i<5;++i){auto&d=dots_[cursor_++%dots_.size()];const float a=float(i)*1.256637f+time_;d={p,{std::cos(a)*38,std::sin(a)*38},.45f};}}
 bool input(const InputFrame&i,Feedback&f,bool suppress_motion=false){if(i.focus_lost||!i.connected){active_input_=false;speaker_pending_=-1;pending_pulse_count_=0;rumble_=0;accepted_={hui::audio::Tactile::focus,0,0,0};motion_haptics_.reset();return false;}active_input_=true;if(speaker_pending_>=0){f.speak(hui::audio::SpeakerCue(speaker_pending_),speaker_pitch_,speaker_gain_);speaker_pending_=-1;}const bool semantic=rumble_>0||accepted_.strength>0;if(rumble_>0){f.feel(hui::audio::Tactile::impact,rumble_,.055f);rumble_=0;}if(pending_pulse_count_){for(unsigned n=0;n<pending_pulse_count_;++n){const auto&e=pending_pulses_[n];f.feel(e.pattern,e.strength,e.seconds,e.pan);}}else if(accepted_.strength>0)f.feel(accepted_.pattern,accepted_.strength,accepted_.seconds,accepted_.pan);pending_pulse_count_=0;accepted_={hui::audio::Tactile::focus,0,0,0};motion_haptics_.drain(f,semantic||suppress_motion);if(i.is_pressed(Action::west)){reset();sound(60);f.feel(hui::audio::Tactile::back,.08f,.04f);return false;}return true;}
 void touch_feedback(float old,float value,Feedback&f){if(std::abs(value-old)>2&&time_>=touch_time_){f.feel(hui::audio::Tactile::touch,.045f,.018f,std::clamp((value-old)/60.f,-1.f,1.f));touch_time_=time_+.08f;}}
 void animate(float dt){motion_haptics_.advance(dt);time_+=dt;for(auto&d:dots_)if(d.life>0){d.life=std::max(0.f,d.life-dt);d.p=d.p+d.v*dt;}}
 virtual bool night_field()const{return false;}
 bool begin(DrawList&l,Fonts&,Rect r,Color accent,const char*,const char*){
  if(r.w<1||r.h<1)return false;
  const float scale=std::min(r.w/740.f,r.h/470.f);
  l.push_clip(r);l.rounded_rect(r,0,night_field()?Color::rgb(0x101512):Color::rgb(0xf1efe7));
  l.push_transform(scale,0,0,r.cx()-370*scale,r.cy()-280*scale);accent_=accent;return true;
 }
 void panel(DrawList&l,Fonts&f,const char*kind,int value,const char*,const char*status=""){
  const Color foreground=night_field()?Color::rgb(0xf1efe7):ink;
  // A small, drawn emblem identifies the resource; the number is the focus.
  if(std::string_view(kind)=="ROWS CLEARED"){
   // The row total stands alone, without a second pictogram.
  }else if(std::string_view(kind)=="MARKERS PASSED")l.ring(57,77,9,2,accent_);
  else{float star[20];for(int n=0;n<10;++n){const float angle=-pi/2+float(n)*pi/5,radius=n%2?4.6f:10.f;star[n*2]=57+std::cos(angle)*radius;star[n*2+1]=77+std::sin(angle)*radius;}l.polygon(star,10,accent_);}
  char n[32];hui::ui::format(n,"%d",value);hui::ui::text(l,f.display,n,std::string_view(kind)=="ROWS CLEARED"?48:82,91,32,foreground);
  if(status[0])hui::ui::text(l,f.semibold,status,690,89,13,foreground.with_alpha(.65f),Align::right);
 }
 void finish(DrawList&l){for(const auto&d:dots_)if(d.life>0)l.circle(30+d.p.x,119+d.p.y,2.1f*d.life/.45f,accent_.with_alpha(d.life/.45f));l.pop_transform();l.pop_clip();}
 void clean(){dots_={};pending_pulse_count_=0;rumble_=0;accepted_={hui::audio::Tactile::focus,0,0,0};active_input_=true;speaker_pending_=-1;motion_haptics_.reset();note_=-1;time_=touch_time_=0;}
};
class Paddle final:public Scene {
 friend struct ArcadeHapticsInspection;
 friend struct ArcadeTouchInspection;
 friend struct PongMultiplayerInspection;
 float player_=195,opponent_=195,control_=0,opponent_control_=0;V ball_{340,195},velocity_{235,80};bool running_=false,two_players_=false;int returns_=0,best_returns_=0,player_score_=0,opponent_score_=0;float previous_x_=340,previous_y_=195;
 static float rally_multiplier(int returns){return returns>=23?3.f:std::min(3.f,std::pow(1.05f,float(std::max(0,returns))));}
 float opponent_speed()const{return 175.f*std::clamp(norm(velocity_)/std::hypot(235.f,80.f),1.f,3.f);}
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"consecutive_returns",std::uint64_t(best_returns_)}};}
 Paddle(){reset();}
 bool local_multiplayer()const override{return true;}
 void reset()override{clean();player_=opponent_=195;control_=opponent_control_=0;ball_={340,195};velocity_={235,80};previous_x_=340;previous_y_=195;running_=two_players_=false;returns_=best_returns_=player_score_=opponent_score_=0;}
 const char*help()const override{return "Move the left stick up or down to meet the ball. X or a touchpad click serves. Aim with the edge of the paddle to change the return. Square restarts.";}
 void handle(const InputFrame&i,Feedback&f)override{
  control_=opponent_control_=0;two_players_=false;if(!input(i,f))return;
  control_=axis(i,false);
  if(i.touch.available&&i.touch.count&&std::isfinite(i.touch.points[0].y)){const float previous=player_;player_=std::clamp(38.f+i.touch.points[0].y*314.f,38.f,352.f);touch_feedback(previous,player_,f);control_=0;}
  const auto&second=i.secondary;two_players_=second.connected&&!second.focus_lost;
  if(two_players_){
   opponent_control_=std::isfinite(second.stick_y)&&std::abs(second.stick_y)>.04f?std::clamp(second.stick_y,-1.f,1.f):float(second.is_held(Action::down))-float(second.is_held(Action::up));
   if(second.touch.available&&second.touch.count&&std::isfinite(second.touch.points[0].y)){const float previous=opponent_;opponent_=std::clamp(38.f+second.touch.points[0].y*314.f,38.f,352.f);touch_feedback(previous,opponent_,f);opponent_control_=0;}
   if(second.is_pressed(Action::west)){reset();f.feel(hui::audio::Tactile::back,.08f,.04f);return;}
  }
  const bool serve=i.is_pressed(Action::confirm)||i.is_pressed(Action::touch)||(two_players_&&(second.is_pressed(Action::confirm)||second.is_pressed(Action::touch)));
  if(serve&&!running_){running_=true;sound(60);f.feel(hui::audio::Tactile::confirm,.10f,.035f);}
 }
 void update(float dt)override{
  dt=bounded_dt(dt);animate(dt);const float before_player=player_;player_=std::clamp(player_+control_*310*dt,38.f,352.f);motion_haptics_.record(0,player_-before_player,active_input_&&std::abs(control_)>.2f);
  if(two_players_){const float before=opponent_;opponent_=std::clamp(opponent_+opponent_control_*310*dt,38.f,352.f);motion_haptics_.record(0,opponent_-before,active_input_&&std::abs(opponent_control_)>.2f);}
  if(!running_)return;
  if(!two_players_){const float limit=opponent_speed()*dt;opponent_+=std::clamp(ball_.y-opponent_,-limit,limit);opponent_=std::clamp(opponent_,38.f,352.f);}
  previous_x_=ball_.x;previous_y_=ball_.y;
  for(int k=0;k<3;++k){const float step=dt/3;const V before=ball_;ball_=ball_+velocity_*step;
   if(ball_.y<8){ball_.y=8;velocity_.y=std::abs(velocity_.y);sound(64);pulse(hui::audio::Tactile::rise,.11f,.045f,std::clamp((ball_.x-340)/340.f,-1.f,1.f));}
   if(ball_.y>382){ball_.y=382;velocity_.y=-std::abs(velocity_.y);sound(64);pulse(hui::audio::Tactile::fall,.11f,.045f,std::clamp((ball_.x-340)/340.f,-1.f,1.f));}
   const bool left=velocity_.x<0&&before.x>=33&&ball_.x<=33&&std::abs(ball_.y-player_)<45;const bool right=velocity_.x>0&&before.x<=647&&ball_.x>=647&&std::abs(ball_.y-opponent_)<45;
   if(left||right){const float offset=(ball_.y-(left?player_:opponent_))/38;++returns_;best_returns_=std::max(best_returns_,returns_);const float multiplier=rally_multiplier(returns_),speed=std::hypot(235.f,80.f)*multiplier;const float slope=std::clamp(offset,-1.f,1.f)*.8f;const float horizontal=speed/std::sqrt(1+slope*slope);velocity_={(left?1.f:-1.f)*horizontal,slope*horizontal};ball_.x=left?33:647;event(ball_,left?72:67,left?.14f:.10f,hui::audio::Tactile::impact,left?-.8f:.8f);if(left||two_players_)speaker(hui::audio::SpeakerCue::ball_hit,1.f+(multiplier-1.f)*.3f,.12f);}
   if(ball_.x<0||ball_.x>680){if(ball_.x<0)++opponent_score_;else ++player_score_;running_=false;ball_={340,195};velocity_={235,80};returns_=0;event({340,195},48,.13f);break;}
  }
 }
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(r.w<1||r.h<1)return;
  const float scale=std::min(r.w/1040.f,r.h/552.f);l.push_clip(r);l.rounded_rect(r,0,Color::rgb(0xf1efe7));l.push_transform(scale,0,0,r.x+(r.w-1040*scale)/2,r.y+(r.h-552*scale)/2);accent_=a;
  constexpr float x=180,y=118;
  l.bordered_rect({x,y,680,390},2,ink.with_alpha(.025f),.8f,ink.with_alpha(.16f));
  char score[48];std::snprintf(score,sizeof(score),"%d  :  %d",player_score_,opponent_score_);hui::ui::text(l,f.display,score,520,78,42,ink,Align::center);
  for(int n=0;n<16;++n)l.line(x+340,y+10+float(n)*24,x+340,y+18+float(n)*24,.7f,ink.with_alpha(.15f));
  l.rounded_rect({x+20,y+player_-38,10,76},4,a);l.rounded_rect({x+650,y+opponent_-38,10,76},4,two_players_?a:ink.with_alpha(.58f));
  if(running_)for(int n=1;n<=4;++n){const float t=float(n)/5;l.circle(x+ball_.x+(previous_x_-ball_.x)*t*4,y+ball_.y+(previous_y_-ball_.y)*t*4,6*(1-t),a.with_alpha(.22f*(1-t)));}
  l.circle(x+ball_.x,y+ball_.y,7,ink);
  for(const auto&d:dots_)if(d.life>0)l.circle(x+d.p.x,y+d.p.y,2.1f*d.life/.45f,a.with_alpha(d.life/.45f));
  l.pop_transform();
  if(!two_players_&&r.w>=1500)hui::ui::text(l,f.regular,"Connect a second controller to play together.",r.x+r.w-48,r.y+r.h-20,18,ink.with_alpha(.62f),Align::right);
  l.pop_clip();
 }
};
class Bricks final:public Scene {
 friend struct ArcadeHapticsInspection;
 friend struct ArcadeTouchInspection;
 std::array<bool,32>bricks_{};float paddle_=340,control_=0;V ball_{340,345},velocity_{160,-230};bool running_=false;int broken_=0;
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"bricks_broken",std::uint64_t(broken_)}};}
 StudyCompletion completion()const override{return broken_==32?StudyCompletion::experience_complete:StudyCompletion::playing;}
 Bricks(){reset();}void reset()override{clean();bricks_.fill(true);paddle_=340;control_=0;ball_={340,345};velocity_={160,-230};running_=false;broken_=0;}
 const char*help()const override{return "Move left or right to catch the ball. X or a touchpad click launches it. Break the wall by choosing the angle of each return. Square rebuilds the wall.";}
 void handle(const InputFrame&i,Feedback&f)override{control_=0;if(!input(i,f))return;control_=axis(i,true);if(i.touch.available&&i.touch.count&&std::isfinite(i.touch.points[0].x)){const float previous=paddle_;paddle_=std::clamp(51.f+i.touch.points[0].x*578.f,51.f,629.f);touch_feedback(previous,paddle_,f);control_=0;}if((i.is_pressed(Action::confirm)||i.is_pressed(Action::touch))&&!running_&&broken_<32){running_=true;sound(60);f.feel(hui::audio::Tactile::confirm,.24f,.055f);}}
 void update(float dt)override{dt=bounded_dt(dt);animate(dt);const float before_paddle=paddle_;paddle_=std::clamp(paddle_+control_*360*dt,51.f,629.f);motion_haptics_.record(paddle_-before_paddle,0,active_input_&&std::abs(control_)>.2f);if(!running_){ball_={paddle_,345};return;}for(int k=0;k<4;++k){V before=ball_;ball_=ball_+velocity_*(dt/4);if(ball_.x<8){ball_.x=8;velocity_.x=std::abs(velocity_.x);pulse(hui::audio::Tactile::touch,.22f,.055f,std::clamp((ball_.x-340)/340.f,-1.f,1.f));}if(ball_.x>672){ball_.x=672;velocity_.x=-std::abs(velocity_.x);pulse(hui::audio::Tactile::touch,.22f,.055f,std::clamp((ball_.x-340)/340.f,-1.f,1.f));}if(ball_.y<8){ball_.y=8;velocity_.y=std::abs(velocity_.y);pulse(hui::audio::Tactile::touch,.22f,.055f,std::clamp((ball_.x-340)/340.f,-1.f,1.f));}if(velocity_.y>0&&before.y<=348&&ball_.y>=348&&std::abs(ball_.x-paddle_)<57){ball_.y=348;velocity_.y=-std::abs(velocity_.y);velocity_.x=(ball_.x-paddle_)*4.8f;event(ball_,67,.38f,hui::audio::Tactile::confirm,std::clamp((ball_.x-paddle_)/57.f,-1.f,1.f));}for(unsigned n=0;n<bricks_.size();++n)if(bricks_[n]){const float x=20+float(n%8)*81,y=30+float(n/8)*32;if(ball_.x>x-7&&ball_.x<x+74+7&&ball_.y>y-7&&ball_.y<y+22+7){bricks_[n]=false;++broken_;if(before.y<=y-7||before.y>=y+29)velocity_.y=-velocity_.y;else velocity_.x=-velocity_.x;event(ball_,72+int(n/8)*2,.44f,hui::audio::Tactile::impact,std::clamp((ball_.x-340)/340.f,-1.f,1.f));break;}}if(broken_==32){running_=false;break;}if(ball_.y>399){running_=false;velocity_={160,-230};sound(48);pulse(hui::audio::Tactile::error,.50f,.10f);break;}}}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{if(!begin(l,f,r,a,"A wall becomes a field of choices","One ball, a movable surface, and a structure that changes."))return;l.bordered_rect({30,119,680,390},0,Color{0,0,0,0},.8f,Color::rgb(0x7b807c,.65f));for(unsigned n=0;n<bricks_.size();++n)if(bricks_[n])l.rounded_rect({50+float(n%8)*81,149+float(n/8)*32,74,22},2,hui::gfx::mix(a,ink,float(n/8)*.13f).with_alpha(.58f+float(n/8)*.11f));l.shadow({30+paddle_-48,476,96,9},3,7,a.with_alpha(.16f));l.rounded_rect({30+paddle_-48,474,96,9},4,a);l.circle(30+ball_.x,119+ball_.y,6.5f,ink);panel(l,f,"SCORE",broken_*100,"A return from the edge sends the ball along a different path.",broken_==32?"COMPLETE":running_?"":"READY");finish(l);}
};
class Formation final:public Scene {
 bool night_field()const override{return true;}
 friend struct ArcadeHapticsInspection;
 friend struct ArcadeInspection;
 struct Shot{V p;bool active=false;};std::array<Shot,10>shots_{},hostile_{};std::array<bool,21>alive_{};
 float player_=340,control_=0,origin_=90,depth_=62,direction_=1,fire_wait_=0,enemy_wait_=1.1f,invincible_=0;
 float bonus_x_=-60,bonus_wait_=3,bonus_flash_=0;bool bonus_active_=false;
 bool firing_=false,ended_=false;int hits_=0,shield_=3,points_=0,bonus_hits_=0;unsigned pending_shots_=0;std::uint32_t seed_=712;
 float formation_speed()const{return 25.f*std::min(2.8f,1.f+1.8f*std::clamp(time_/75.f,0.f,1.f)+.4f*std::clamp(float(hits_)/21.f,0.f,1.f));}
 void fire(){for(auto&s:shots_)if(!s.active){s={{player_,344},true};fire_wait_=.19f;++pending_shots_;pulse(hui::audio::Tactile::impact,.42f,.055f);break;}}
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"enemies_destroyed",std::uint64_t(hits_)}};}
 StudyCompletion completion()const override{return hits_==21?StudyCompletion::experience_complete:StudyCompletion::playing;}
 Formation(){reset();}
 void reset()override{clean();shots_={};hostile_={};alive_.fill(true);player_=340;control_=0;origin_=90;depth_=62;direction_=1;fire_wait_=0;enemy_wait_=1.1f;invincible_=0;firing_=ended_=false;hits_=points_=bonus_hits_=0;pending_shots_=0;shield_=3;seed_=712;bonus_x_=-60;bonus_wait_=3;bonus_flash_=0;bonus_active_=false;}
 const char*help()const override{return "D-pad / left stick: move. Hold Cross to fire. Avoid falling pulses. A mothership occasionally crosses above the formation for bonus points. Square restarts.";}
 void handle(const InputFrame&i,Feedback&f)override{control_=0;firing_=false;if(!input(i,f)){pending_shots_=0;return;}for(unsigned n=0;n<pending_shots_;++n){f.cues.push_back({hui::audio::Cue::invader_shot,1.f,0.f,.20f,hui::audio::SoundSet::count});f.speak(hui::audio::SpeakerCue::invader_shot,1.f,.18f);}pending_shots_=0;control_=axis(i,true);firing_=i.is_held(Action::confirm)||i.is_pressed(Action::confirm);}
 void update(float dt)override{
  dt=bounded_dt(dt);animate(dt);if(ended_)return;const float before_player=player_;player_=std::clamp(player_+control_*290*dt,20.f,660.f);motion_haptics_.record(player_-before_player,0,active_input_&&std::abs(control_)>.2f);invincible_=std::max(0.f,invincible_-dt);
  fire_wait_-=dt;enemy_wait_-=dt;bonus_flash_=std::max(0.f,bonus_flash_-dt);
  if(firing_&&fire_wait_<=0)fire();
  if(!bonus_active_){bonus_wait_-=dt;if(bonus_wait_<=0){bonus_x_=-35;bonus_active_=true;sound(69);}}
  else{bonus_x_+=82*dt;if(bonus_x_>720){bonus_active_=false;bonus_wait_=10;}}
  origin_+=direction_*formation_speed()*dt;if(origin_<25||origin_>190){origin_=std::clamp(origin_,25.f,190.f);direction_=-direction_;depth_+=15;}
  if(enemy_wait_<=0){const unsigned first=random(seed_)%alive_.size();for(unsigned k=0;k<alive_.size();++k){const unsigned n=(first+k)%alive_.size();if(alive_[n]){for(auto&s:hostile_)if(!s.active){s={{origin_+float(n%7)*72,depth_+float(n/7)*49},true};break;}break;}}enemy_wait_=.8f;}
  for(auto&s:shots_)if(s.active){const float before=s.p.y;s.p.y-=390*dt;
   if(bonus_active_&&std::abs(s.p.x-bonus_x_)<30&&before>=17&&s.p.y<=35){bonus_active_=false;bonus_wait_=11;bonus_flash_=1.1f;s.active=false;++bonus_hits_;points_+=150;event({bonus_x_,26},81,.48f,hui::audio::Tactile::confirm,std::clamp((bonus_x_-340)/340.f,-1.f,1.f));speaker(hui::audio::SpeakerCue::bonus,1.15f,.15f);continue;}
   if(s.p.y<0){s.active=false;continue;}
   for(unsigned n=0;n<alive_.size();++n)if(alive_[n]&&std::abs(s.p.x-origin_-float(n%7)*72)<18&&std::abs(s.p.y-depth_-float(n/7)*49)<17){alive_[n]=false;s.active=false;++hits_;points_+=25+int(2-n/7)*10;event(s.p,67+int(n%5)*2,.38f,hui::audio::Tactile::impact,std::clamp((s.p.x-340)/340.f,-1.f,1.f));break;}}
  for(auto&s:hostile_)if(s.active){s.p.y+=170*dt;if(s.p.y>390){s.active=false;continue;}if(invincible_<=0&&std::abs(s.p.x-player_)<19&&std::abs(s.p.y-354)<16){s.active=false;--shield_;invincible_=1.2f;event({player_,354},48,.52f);}}
  ended_=hits_==21||shield_<=0||depth_>260;
 }
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(!begin(l,f,r,a,"A pattern with a moving edge","Watch the formation; the occasional bonus asks you to look beyond it."))return;
  const Color amber=a,white=Color::rgb(0xf1efe7);accent_=amber;
  l.rounded_rect({30,119,680,390},2,Color::rgb(0x101512));
  for(int n=0;n<46;++n){const float x=40+float((n*137)%660),y=128+float((n*89)%370);l.circle(x,y,n%4==0?1.2f:.65f,white.with_alpha(.10f+.10f*float(n%3)));}
  if(bonus_active_){const float x=30+bonus_x_,y=145;l.rounded_rect({x-27,y-5,54,11},5,amber);l.rounded_rect({x-15,y-12,30,11},6,amber.with_alpha(.72f));for(int k=0;k<4;++k)l.circle(x-15+k*10.f,y+8,2,white);}
  if(bonus_flash_>0)hui::ui::text(l,f.mono,"+150",30+bonus_x_,155,15,amber,Align::center);
  for(unsigned n=0;n<alive_.size();++n)if(alive_[n]){const float x=30+origin_+float(n%7)*72,y=119+depth_+float(n/7)*49;
   l.bordered_rect({x-14,y-10,28,20},3,amber.with_alpha(.14f),1.1f,amber);l.line(x-7,y,x+7,y,.8f,amber);}
  for(const auto&s:shots_)if(s.active)l.line(30+s.p.x,119+s.p.y,30+s.p.x,127+s.p.y,2,amber);
  for(const auto&s:hostile_)if(s.active)l.circle(30+s.p.x,119+s.p.y,3,white.with_alpha(.78f));
  if(invincible_<=0||std::fmod(time_,.16f)<.08f)l.triangle({30+player_-14,119+341,28,24},white);
  for(int n=0;n<shield_;++n)l.circle(52+float(n)*17,493,3,amber);
  char caption[130];hui::ui::format(caption,"%d / 21 gaps. %d mothership bonuses. A shot spent on the bonus cannot cover the approaching formation.",hits_,bonus_hits_);
  panel(l,f,"SCORE",points_,caption,ended_?(hits_==21?"COMPLETE":"GAME OVER"):"");finish(l);
 }
};
// Fixed classic 28-by-31 board geometry; the study ends when this board is cleared.
class Maze final:public Scene {
 bool night_field()const override{return true;}
 friend struct ArcadeHapticsInspection;
 friend struct ArcadeInspection;
 static constexpr int w=28,h=31,tunnel_row=14,house=14*w+13,fruit_cell=17*w+13;
 static constexpr float tile=12.8f,ox=370-w*tile*.5f,oy=88.4f;
 inline static constexpr std::array<std::string_view,h> layout={
  "############################",
  "#............##............#",
  "#.####.#####.##.#####.####.#",
  "#o####.#####.##.#####.####o#",
  "#.####.#####.##.#####.####.#",
  "#..........................#",
  "#.####.##.########.##.####.#",
  "#.####.##.########.##.####.#",
  "#......##....##....##......#",
  "######.##### ## #####.######",
  "     #.##### ## #####.#     ",
  "     #.##          ##.#     ",
  "     #.## ###--### ##.#     ",
  "######.## #      # ##.######",
  "      .   #      #   .      ",
  "######.## #      # ##.######",
  "     #.## ######## ##.#     ",
  "     #.##          ##.#     ",
  "     #.## ######## ##.#     ",
  "######.## ######## ##.######",
  "#............##............#",
  "#.####.#####.##.#####.####.#",
  "#.####.#####.##.#####.####.#",
  "#o..##.......  .......##..o#",
  "###.##.##.########.##.##.###",
  "###.##.##.########.##.##.###",
  "#......##....##....##......#",
  "#.##########.##.##########.#",
  "#.##########.##.##########.#",
  "#..........................#",
  "############################",
 };
 struct Actor {int cell=0,next=0,dir=1;float progress=0,rest=0;};
 std::array<bool,w*h>open_{},dots_{},powers_{};
 Actor player_{};std::array<Actor,4>ghosts_{};std::array<bool,4>edible_{};
 std::vector<std::vector<V>> walls_;
 int queued_=3,remaining_=0,eaten_=0,points_=0,lives_=3,fruit_round_=0,chain_=0;
 float power_=0,fruit_=0,immune_=0;bool over_=false,won_=false;
 static constexpr int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
 static bool pen(int cell){const int x=cell%w,y=cell/w;return (y>=13&&y<=15&&x>=11&&x<=16)||(y==12&&(x==13||x==14));}
 int neighbour(int cell,int dir,bool ghost=false)const{
  int x=cell%w+dx[dir],y=cell/w+dy[dir];
  if(y==tunnel_row){if(x<0)x=w-1;if(x>=w)x=0;}
  if(x<0||x>=w||y<0||y>=h||!open_[size_t(y*w+x)])return -1;
  const int target=y*w+x;
  if(pen(target)&&(!ghost||!pen(cell)))return -1;
  return target;
 }
 V position(const Actor&a)const{const float x=float(a.cell%w),y=float(a.cell/w);float nx=float(a.next%w),ny=float(a.next/w);
  if(nx-x>1)nx-=w;else if(x-nx>1)nx+=w;
  return{x+(nx-x)*a.progress,y+(ny-y)*a.progress};
 }
 V effect_position(int cell)const{return{ox-30+(float(cell%w)+.5f)*tile,oy-119+(float(cell/w)+.5f)*tile};}
 void place_actors(){player_={23*w+13,23*w+12,3,0,0};queued_=3;
  ghosts_={Actor{11*w+13,11*w+13,3,0,0},Actor{house,house,0,0,1.1f},Actor{14*w+11,14*w+11,1,0,3.3f},Actor{14*w+16,14*w+16,3,0,4.4f}};edible_.fill(false);power_=0;
 }
 int ghost_direction(const Actor&a,unsigned which){
  if(pen(a.cell)){if(a.cell%w!=13)return a.cell%w<13?1:3;return 0;}
  V target=position(player_);
  if(which==1){target.x+=dx[player_.dir]*4;target.y+=dy[player_.dir]*4;}
  else if(which==2){target.x+=dx[player_.dir]*2;target.y+=dy[player_.dir]*2;target=target*2-position(ghosts_[0]);}
  else if(which==3&&norm(position(a)-target)<8)target={1,29};
  int target_cell=player_.cell;float best=1e9f;
  for(int n=0;n<w*h;++n)if(open_[size_t(n)]&&!pen(n)){const float d=std::abs(float(n%w)-target.x)+std::abs(float(n/w)-target.y);if(d<best){best=d;target_cell=n;}}
  std::array<int,w*h>distance;distance.fill(999);std::array<int,w*h>queue{};int first=0,last=1;queue[0]=target_cell;distance[size_t(target_cell)]=0;
  while(first<last){const int current=queue[size_t(first++)];for(int dir=0;dir<4;++dir){const int next=neighbour(current,dir,true);if(next>=0&&distance[size_t(next)]==999){distance[size_t(next)]=distance[size_t(current)]+1;queue[size_t(last++)]=next;}}}
  const bool fleeing=power_>0&&edible_[which];int selected=a.dir,value=fleeing?-1:10000;
  for(int pass=0;pass<2;++pass){bool found=false;for(int dir=0;dir<4;++dir){const int next=neighbour(a.cell,dir,true);if(next<0||(pass==0&&dir==(a.dir+2)%4))continue;
    const int d=distance[size_t(next)];if(!found||(fleeing?d>value:d<value)){selected=dir;value=d;found=true;}}
   if(found)return selected;}
  return selected;
 }
 void advance(Actor&a,float amount,bool player,unsigned which=0){
  if(a.rest>0)return;
  if(player&&a.progress<.00001f&&neighbour(a.cell,queued_)>=0){a.dir=queued_;a.next=neighbour(a.cell,a.dir);}
  if(a.next==a.cell){if(player&&neighbour(a.cell,queued_)>=0)a.dir=queued_;else if(!player)a.dir=ghost_direction(a,which);
   const int next=neighbour(a.cell,a.dir,!player);if(next<0)return;a.next=next;}
  a.progress+=amount;
  if(a.progress>=1){a.progress-=1;a.cell=a.next;
   if(player&&neighbour(a.cell,queued_)>=0)a.dir=queued_;else if(!player)a.dir=ghost_direction(a,which);
   const int next=neighbour(a.cell,a.dir,!player);a.next=next<0?a.cell:next;if(next<0)a.progress=0;}
 }
 float ghost_speed(const Actor&g,unsigned which)const{
  if(g.cell/w==tunnel_row&&(g.cell%w<6||g.cell%w>21))return 2.15f;
  return power_>0&&edible_[which]?2.8f:4.1f+float(which)*.08f;
 }
 void collect(){if(player_.progress>.28f)return;const auto cell=size_t(player_.cell);
  if(dots_[cell]){dots_[cell]=false;--remaining_;++eaten_;points_+=10;pulse(hui::audio::Tactile::touch,.18f,.035f);speaker(hui::audio::SpeakerCue::tool,eaten_%2?.9f:1.1f,.13f);}
  if(powers_[cell]){powers_[cell]=false;--remaining_;++eaten_;power_=7.5f;chain_=0;edible_.fill(true);points_+=50;event(effect_position(player_.cell),77);
   for(auto&g:ghosts_){if(g.cell!=g.next){std::swap(g.cell,g.next);g.progress=1-g.progress;}g.dir=(g.dir+2)%4;}}
  if(fruit_>0&&player_.cell==fruit_cell){fruit_=0;points_+=100;event(effect_position(fruit_cell),81);}
  if(fruit_round_<2&&eaten_>=(fruit_round_==0?70:170)){++fruit_round_;fruit_=9.5f;}
  if(remaining_==0){won_=over_=true;event(effect_position(player_.cell),84,.14f);}
 }
 void build_walls(){
  struct Edge{int a,b;bool used=false;};std::vector<Edge> edges;
  const auto vertex=[](int x,int y){return y*(w+1)+x;};
  const auto solid=[this](int x,int y){return x<0||x>=w||y<0||y>=h||!open_[size_t(y*w+x)];};
  for(int y=0;y<h;++y)for(int x=0;x<w;++x)if(open_[size_t(y*w+x)]){
   if(solid(x,y-1))edges.push_back({vertex(x,y),vertex(x+1,y)});
   if(solid(x+1,y)&&!(y==tunnel_row&&x==w-1))edges.push_back({vertex(x+1,y),vertex(x+1,y+1)});
   if(solid(x,y+1))edges.push_back({vertex(x+1,y+1),vertex(x,y+1)});
   if(solid(x-1,y)&&!(y==tunnel_row&&x==0))edges.push_back({vertex(x,y+1),vertex(x,y)});
  }
  walls_.clear();
  for(auto&first:edges)if(!first.used){std::vector<V> path;Edge* edge=&first;const int start=edge->a;
   while(edge&&!edge->used){edge->used=true;path.push_back({float(edge->a%(w+1)),float(edge->a/(w+1))});const int end=edge->b;
    if(end==start){path.push_back(path.front());break;}
    edge=nullptr;for(auto&next:edges)if(!next.used&&next.a==end){edge=&next;break;}
    if(!edge)path.push_back({float(end%(w+1)),float(end/(w+1))});
   }
   if(path.size()>1)walls_.push_back(std::move(path));
  }
 }
 void draw_walls(DrawList&l,Color blue)const{
  const auto line=[&](V a,V b){l.line(ox+a.x*tile,oy+a.y*tile,ox+b.x*tile,oy+b.y*tile,1.35f,blue);};
  for(const auto&path:walls_){const bool closed=path.front().x==path.back().x&&path.front().y==path.back().y;const size_t count=path.size()-(closed?1:0);
   for(size_t n=0;n<count;++n){const V p=path[n],prev=path[n?n-1:(closed?count-1:0)],next=path[n+1<count?n+1:(closed?0:count-1)];
    const V incoming=prev-p,outgoing=next-p;const float a=norm(incoming),b=norm(outgoing);V enter=p,leave=p;
    if(a>.01f&&b>.01f){enter=p+incoming*(.23f/a);leave=p+outgoing*(.23f/b);V before=enter;
     for(int k=1;k<=4;++k){const float t=k*.25f;const V q=enter*((1-t)*(1-t))+p*(2*(1-t)*t)+leave*(t*t);line(before,q);before=q;}}
    if(n+1<count||closed){const V after=path[n+1<count?n+1:0];V end=after;const bool end_corner=closed||n+2<count;if(end_corner){const V direction=p-after;end=after+direction*(.23f/std::max(.01f,norm(direction)));}line(leave,end);}
   }
  }
 }
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"pac_dots_cleared",won_?1u:0u}};}
 StudyCompletion completion()const override{return won_?StudyCompletion::experience_complete:StudyCompletion::playing;}
 Maze(){reset();}
 void reset()override{clean();open_.fill(false);dots_.fill(false);powers_.fill(false);remaining_=0;
  for(int y=0;y<h;++y)for(int x=0;x<w;++x){const auto cell=size_t(y*w+x);const char mark=layout[size_t(y)][size_t(x)];
   const bool outside=(y>=10&&y<=19&&y!=tunnel_row&&(x<5||x>22));open_[cell]=mark!='#'&&!outside;
   dots_[cell]=mark=='.';powers_[cell]=mark=='o';if(dots_[cell]||powers_[cell])++remaining_;}
  points_=eaten_=fruit_round_=chain_=0;lives_=3;power_=fruit_=0;immune_=1.5f;over_=won_=false;place_actors();build_walls();
 }
 const char*help()const override{return "D-pad / left stick: choose your next turn. Clear 240 dots and four power pellets. Chase frightened ghosts for 200, 400, 800 and 1600 points. Cherries appear after 70 and 170 pellets. Square restarts this single-board experience.";}
 void handle(const InputFrame&i,Feedback&f)override{if(!input(i,f)||over_)return;int wanted=-1;
  if(i.nav==Direction::up)wanted=0;if(i.nav==Direction::right)wanted=1;if(i.nav==Direction::down)wanted=2;if(i.nav==Direction::left)wanted=3;
  const float x=axis(i,true),y=axis(i,false);if(std::max(std::abs(x),std::abs(y))>.35f)wanted=std::abs(x)>std::abs(y)?(x>0?1:3):(y>0?2:0);
  if(wanted>=0){if(queued_!=wanted){queued_=wanted;motion_haptics_.step(wanted==1?1.f:wanted==3?-1.f:0.f,wanted==2?1.f:wanted==0?-1.f:0.f);motion_haptics_.drain(f,!f.tactile.empty());}if(wanted==(player_.dir+2)%4&&player_.next!=player_.cell){std::swap(player_.cell,player_.next);player_.progress=1-player_.progress;player_.dir=wanted;}}
 }
 void update(float dt)override{dt=bounded_dt(dt);animate(dt);if(over_)return;
  const int steps=std::max(1,int(std::ceil(dt/.01f)));const float step=dt/steps;
  for(int s=0;s<steps&&!over_;++s){power_=std::max(0.f,power_-step);fruit_=std::max(0.f,fruit_-step);immune_=std::max(0.f,immune_-step);
   advance(player_,5.1f*step,true);collect();for(unsigned n=0;n<ghosts_.size();++n){auto&g=ghosts_[n];g.rest=std::max(0.f,g.rest-step);advance(g,ghost_speed(g,n)*step,false,n);
    V gap=position(g)-position(player_);if(std::abs(gap.x)>w*.5f)gap.x+=(gap.x>0?-w:w);
    if(g.rest<=0&&norm(gap)<.52f){if(power_>0&&edible_[n]){points_+=200*(1<<std::min(chain_++,3));edible_[n]=false;g={house,house,0,0,1.4f};event(effect_position(player_.cell),79);}
     else if(immune_<=0){--lives_;event(effect_position(player_.cell),48,.16f);if(!lives_){over_=true;break;}place_actors();immune_=1.7f;break;}}}
  }
 }
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(!begin(l,f,r,a,"",""))return;
  const Color white=Color::rgb(0xf1efe7),blue=Color::rgb(0x255bff),yellow=Color::rgb(0xffdf00),night=Color::rgb(0x101512);accent_=yellow;
  draw_walls(l,blue);
  for(int y=0;y<h;++y)for(int x=0;x<w;++x){const auto n=size_t(y*w+x);const float px=ox+(x+.5f)*tile,py=oy+(y+.5f)*tile;
   if(powers_[n]){if(std::fmod(time_,.45f)<.30f)l.circle(px,py,3.6f,white);}
   else if(dots_[n])l.circle(px,py,1.15f,Color::rgb(0xffc7ad));}
  l.line(ox+13*tile,oy+12.5f*tile,ox+15*tile,oy+12.5f*tile,1.6f,Color::rgb(0xffb8dd));
  if(fruit_>0){const float x=ox+13.5f*tile,y=oy+17.5f*tile;l.circle(x-2.5f,y,3.5f,Color::rgb(0xf83b41));l.circle(x+3,y+1.5f,3.5f,Color::rgb(0xf83b41));l.line(x-2.5f,y-3,x+2,y-8,1,Color::rgb(0x67c94f));l.line(x+3,y-2,x+2,y-8,1,Color::rgb(0x67c94f));}
  const std::array<Color,4> colours={Color::rgb(0xff3030),Color::rgb(0xffa8dd),Color::rgb(0x35e5ec),Color::rgb(0xffac45)};
  for(unsigned n=0;n<ghosts_.size();++n){const auto&g=ghosts_[n];const auto p=position(g);const bool afraid=power_>0&&edible_[n];
   const bool flash_white=afraid&&power_<2&&int(time_*7)%2;
   const Color colour=afraid?(flash_white?white:Color::rgb(0x283be5)):colours[n];
   for(int wrap=-1;wrap<=1;++wrap){const float px=p.x+wrap*w;if(px<-.5f||px>w-.5f)continue;const float x=ox+(px+.5f)*tile,y=oy+(p.y+.5f)*tile;
    l.circle(x,y-1.4f,5.5f,colour);l.rounded_rect({x-5.5f,y-1.5f,11,6.3f},0,colour);
    for(int k=0;k<3;++k)l.triangle({x-5.5f+k*3.67f,y+3.7f,3.67f,2.6f},colour);
    if(afraid){const Color face=flash_white?Color::rgb(0xf83b41):white;l.circle(x-2,y-1,1,face);l.circle(x+2,y-1,1,face);for(int k=0;k<4;++k)l.line(x-3+k*1.5f,y+2+(k%2),x-1.5f+k*1.5f,y+2+((k+1)%2),.75f,face);}
    else{for(int side:{-1,1}){const float ex=x+side*2.4f;l.circle(ex,y-1.3f,2,white);l.circle(ex+dx[g.dir]*.7f,y-1.3f+dy[g.dir]*.7f,1,Color::rgb(0x1831ad));}}
   }
  }
  const auto p=position(player_);
  if(immune_<=0||int(time_*9)%2==0)for(int wrap=-1;wrap<=1;++wrap){const float px=p.x+wrap*w;if(px<-.5f||px>w-.5f)continue;const float x=ox+(px+.5f)*tile,y=oy+(p.y+.5f)*tile;
   l.circle(x,y,5.6f,yellow);const float heading=player_.dir*pi*.5f,mouth_angle=.12f+.36f*std::abs(std::sin(time_*12));const float mouth[]={x,y,x+std::sin(heading-mouth_angle)*8,y-std::cos(heading-mouth_angle)*8,x+std::sin(heading+mouth_angle)*8,y-std::cos(heading+mouth_angle)*8};l.polygon(mouth,3,night);}
  hui::ui::text(l,f.mono,"SCORE",ox,62,11,white);char score[32];hui::ui::format(score,"%d",points_);hui::ui::text(l,f.mono,score,ox,80,17,white);
  if(power_>0){char timer[32];hui::ui::format(timer,"%.1f",power_);hui::ui::text(l,f.mono,"POWER",ox+w*tile,62,11,Color::rgb(0x8eabff),Align::right);hui::ui::text(l,f.mono,timer,ox+w*tile,80,17,Color::rgb(0x8eabff),Align::right);}
  if(over_)hui::ui::text(l,f.mono,won_?"COMPLETE":"GAME OVER",370,oy+17.7f*tile,12,won_?yellow:Color::rgb(0xff5656),Align::center);
  for(int n=0;n<lives_;++n){const float x=ox+12+n*18.f,y=oy+h*tile+13;l.circle(x,y,5,yellow);const float mouth[]={x,y,x+7,y-3,x+7,y+3};l.polygon(mouth,3,night);}
  finish(l);
 }
};
class Gravity final:public Scene {
 friend struct ArcadeHapticsInspection;
 friend struct ArcadeInspection;
 static constexpr int cols=10,rows=14;std::array<unsigned,cols*rows>board_{};std::array<V,4>shape_{};int x_=4,y_=0,type_=0,lines_=0,max_lines_single_piece_=0;float fall_=0,soft_=0;bool over_=false;std::uint32_t seed_=491;
 int level()const{return lines_/10;}
 float gravity_interval()const{const int n=level();constexpr int frames[]={48,43,38,33,28,23,18,13,8,6};return float(n<10?frames[n]:n<13?5:n<16?4:n<19?3:n<29?2:1)/60.f;}
 bool fits(int x,int y,const std::array<V,4>&shape)const{for(V p:shape){const int bx=x+int(p.x),by=y+int(p.y);if(bx<0||bx>=cols||by>=rows)return false;if(by>=0&&board_[size_t(by*cols+bx)])return false;}return true;}
 void spawn(){type_=int(random(seed_)%5);if(type_==0)shape_={V{-1,0},V{0,0},V{1,0},V{2,0}};else if(type_==1)shape_={V{0,0},V{1,0},V{0,1},V{1,1}};else if(type_==2)shape_={V{-1,0},V{0,0},V{1,0},V{0,1}};else if(type_==3)shape_={V{-1,0},V{0,0},V{1,0},V{1,1}};else shape_={V{-1,1},V{0,1},V{0,0},V{1,0}};x_=4;y_=0;fall_=0;over_=!fits(x_,y_,shape_);}
 void lock(){for(V p:shape_){int x=x_+int(p.x),y=y_+int(p.y);if(y<0){over_=true;return;}board_[size_t(y*cols+x)]=unsigned(type_)+1;}int cleared=0;for(int y=rows-1;y>=0;--y){bool full=true;for(int x=0;x<cols;++x)if(!board_[size_t(y*cols+x)])full=false;if(full){for(int yy=y;yy>0;--yy)for(int x=0;x<cols;++x)board_[size_t(yy*cols+x)]=board_[size_t((yy-1)*cols+x)];for(int x=0;x<cols;++x)board_[size_t(x)]=0;++cleared;++y;}}max_lines_single_piece_=std::max(max_lines_single_piece_,cleared);lines_+=cleared;if(cleared)event({340,320},72+cleared*2,.13f);else{sound(55);pulse(hui::audio::Tactile::impact,.10f,.04f);}spawn();}
 void drop(){while(fits(x_,y_+1,shape_))++y_;lock();}
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"max_lines_single_piece",std::uint64_t(max_lines_single_piece_)}};}
 Gravity(){reset();}void reset()override{clean();board_={};seed_=491;lines_=max_lines_single_piece_=0;soft_=0;over_=false;spawn();}
 const char*help()const override{return "D-pad left and right move the falling shape. X turns it. Down lowers it faster. Up drops it into place. Complete a row to make room. Square restarts.";}
 void handle(const InputFrame&i,Feedback&f)override{soft_=0;if(!input(i,f)||over_)return;soft_=std::max(0.f,axis(i,false));int dx=0;if(i.nav==Direction::left)dx=-1;if(i.nav==Direction::right)dx=1;if(dx&&fits(x_+dx,y_,shape_)){x_+=dx;motion_haptics_.step(float(dx),0);motion_haptics_.drain(f,!f.tactile.empty());}if(i.is_pressed(Action::confirm)&&type_!=1){auto rotated=shape_;for(auto&p:rotated){float x=p.x;p.x=-p.y;p.y=x;}for(int kick:{0,-1,1,-2,2})if(fits(x_+kick,y_,rotated)){shape_=rotated;x_+=kick;sound(64);f.feel(hui::audio::Tactile::touch,.07f,.025f);break;}}if(i.is_pressed(Action::up)||(i.nav==Direction::up&&!i.nav_repeat))drop();}
 void update(float dt)override{dt=bounded_dt(dt);animate(dt);if(over_)return;fall_+=dt;const float interval=soft_>.3f?std::min(gravity_interval(),2.f/60.f):gravity_interval();while(fall_>=interval&&!over_){fall_-=interval;if(fits(x_,y_+1,shape_)){++y_;if(soft_>.3f)pulse(hui::audio::Tactile::focus,.04f,.015f);}else lock();}}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(!begin(l,f,r,a,"Gravity makes a drawing accumulate","Choose a position before the next shape becomes part of the floor."))return;
  constexpr float cell=24,ox=248,oy=145;
  for(int y=0;y<rows;++y)for(int x=0;x<cols;++x){const unsigned value=board_[size_t(y*cols+x)];l.rounded_rect({ox+float(x)*cell,oy+float(y)*cell,22,22},1,value?hui::gfx::mix(a,ink,float(value-1)*.12f):ink.with_alpha(.025f));}
  if(!over_){
   int ghost=y_;while(fits(x_,ghost+1,shape_))++ghost;
   for(V p:shape_){
    // A dark outline stays readable even when the selected accent is pale.
    l.bordered_rect({ox+float(x_+int(p.x))*cell,oy+float(ghost+int(p.y))*cell,22,22},1,a.with_alpha(.18f),2,ink.with_alpha(.78f));
    if(y_+int(p.y)>=0)l.rounded_rect({ox+float(x_+int(p.x))*cell,oy+float(y_+int(p.y))*cell,22,22},1,a);
   }
  }
  l.line(ox-7,oy+rows*cell+3,ox+cols*cell+5,oy+rows*cell+3,1,ink.with_alpha(.35f));
  // Labels resolve independently of their numeric values in every UI locale.
  hui::ui::text(l,f.mono,"LINES",48,76,11,ink.with_alpha(.65f));
  hui::ui::text(l,f.mono,"LEVEL",690,76,11,ink.with_alpha(.65f),Align::right);
  char count[24];std::snprintf(count,sizeof(count),"%d",lines_);hui::ui::text(l,f.mono,count,48,112,32,ink);
  std::snprintf(count,sizeof(count),"%d",level());hui::ui::text(l,f.mono,count,690,112,32,ink,Align::right);
  if(over_)hui::ui::text(l,f.mono,"GAME OVER",370,112,15,ink,Align::center);
  finish(l);
 }
};
class Orbit final:public Scene {
 bool night_field()const override{return true;}
 friend struct ArcadeHapticsInspection;
 V ship_{500,195},velocity_{0,100};float heading_=pi/2,turn_=0,thrust_=0;bool brake_=false,lost_=false;std::array<V,160>trail_{};unsigned trail_at_=0,trail_count_=0;float trail_wait_=0;std::array<bool,4>beacons_{};int passes_=0;
public:
 Orbit(){reset();}void reset()override{clean();ship_={500,195};velocity_={0,100};heading_=pi/2;turn_=thrust_=0;brake_=lost_=false;trail_at_=trail_count_=0;trail_wait_=0;beacons_={};passes_=0;}
 const char*help()const override{return "The centre pulls your craft into an orbit. Move the left stick sideways to turn, and up to thrust. Hold X to brake. Pass the four markers. Square restarts.";}
 void handle(const InputFrame&i,Feedback&f)override{const bool previous_brake=brake_;turn_=thrust_=0;brake_=false;if(!input(i,f)||lost_)return;turn_=axis(i,true);thrust_=std::max(0.f,-axis(i,false));brake_=i.is_held(Action::confirm);if(i.is_pressed(Action::confirm)&&!lost_)f.feel(hui::audio::Tactile::touch,.075f,.025f);else if(previous_brake&&!brake_)f.feel(hui::audio::Tactile::touch,.05f,.02f);}
 void update(float dt)override{dt=bounded_dt(dt);animate(dt);if(lost_)return;const float old_heading=heading_;heading_+=turn_*2.4f*dt;motion_haptics_.record(heading_-old_heading,thrust_*dt,active_input_&&(std::abs(turn_)>.2f||thrust_>.2f));for(int k=0;k<4;++k){const float step=dt/4;V d=V{340,195}-ship_;const float radius=std::max(30.f,norm(d));const V gravity=d*(1600000.f/(radius*radius*radius));V force{std::cos(heading_)*thrust_*85,std::sin(heading_)*thrust_*85};velocity_=velocity_+(gravity+force)*step;if(brake_)velocity_=velocity_*std::exp(-.7f*step);ship_=ship_+velocity_*step;ship_.x=std::fmod(std::fmod(ship_.x,680.f)+680.f,680.f);ship_.y=std::fmod(std::fmod(ship_.y,390.f)+390.f,390.f);if(norm(ship_-V{340,195})<37){lost_=true;event({std::clamp(ship_.x,0.f,680.f),std::clamp(ship_.y,0.f,390.f)},48,.16f);break;}}trail_wait_+=dt;if(trail_wait_>.03f){trail_wait_=0;trail_[trail_at_++%trail_.size()]=ship_;trail_count_=std::min(unsigned(trail_.size()),trail_count_+1);}for(unsigned n=0;n<4;++n){const float theta=float(n)*pi/2;const V p{340+std::cos(theta)*160,195+std::sin(theta)*160};if(!beacons_[n]&&norm(ship_-p)<22){beacons_[n]=true;++passes_;event(ship_,65+int(n)*3,.07f);}}}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(!begin(l,f,r,a,"A path held by a pull","Pointing the craft and changing its route are different actions."))return;
  const Color pale=Color::rgb(0xf1efe7),teal=a;accent_=teal;
  l.rounded_rect({30,119,680,390},2,Color::rgb(0x101512));
  for(int n=0;n<35;++n)l.circle(42+float(n*139%650),129+float(n*97%365),.8f,pale.with_alpha(.18f));
  l.push_clip({31,120,678,388});
  for(unsigned n=1;n<trail_count_;++n){const unsigned first=(trail_at_-trail_count_+n-1)%trail_.size(),second=(first+1)%trail_.size();const V p=trail_[first],q=trail_[second];if(std::abs(p.x-q.x)>340||std::abs(p.y-q.y)>195)continue;l.line(30+p.x,119+p.y,30+q.x,119+q.y,1.2f,teal.with_alpha(.65f*float(n)/float(trail_count_)));}
  l.ring(370,314,160,.65f,pale.with_alpha(.15f));l.circle(370,314,33,pale.with_alpha(.36f));l.ring(370,314,37,.7f,pale.with_alpha(.3f));
  for(unsigned n=0;n<4;++n){const float theta=float(n)*pi/2,x=370+std::cos(theta)*160,y=314+std::sin(theta)*160;if(beacons_[n])l.circle(x,y,3,teal.with_alpha(.36f));else l.ring(x,y,7,1,teal);}
  if(!lost_){const float x=30+ship_.x,y=119+ship_.y;
   // The long cyan vector shows velocity; the small ivory hull shows heading.
   const V end=ship_+velocity_*.42f;l.line(x,y,30+end.x,119+end.y,1,teal.with_alpha(.8f));
   const float va=std::atan2(velocity_.y,velocity_.x);l.line(30+end.x,119+end.y,30+end.x-7*std::cos(va-.4f),119+end.y-7*std::sin(va-.4f),1,teal);l.line(30+end.x,119+end.y,30+end.x-7*std::cos(va+.4f),119+end.y-7*std::sin(va+.4f),1,teal);
   l.triangle({x-7,y-9,14,18},pale,0,heading_+pi/2);
   if(thrust_>0)l.line(x-std::cos(heading_)*9,y-std::sin(heading_)*9,x-std::cos(heading_)*(13+thrust_*8),y-std::sin(heading_)*(13+thrust_*8),2,a);}
  l.pop_clip();panel(l,f,"MARKERS PASSED",passes_,"The cyan line shows velocity. The ivory hull points where thrust will push. Braking removes the motion that keeps you in orbit.",lost_?"ORBIT LOST":passes_==4?"COMPLETE":"");finish(l);
 }
};
class Wireframe final:public Scene {
 friend struct ArcadeHapticsInspection;
 friend struct FlightInspection;
 struct Gate{float z,x,y;int result=0;};
 static constexpr std::array<V,12>route_{{{.15f,0},{-.55f,-.35f},{.65f,.35f},{.15f,-.55f},{-.75f,.25f},{.6f,.5f},{.85f,-.35f},{-.45f,-.5f},{-.8f,.4f},{.65f,.2f},{0,-.55f},{0,0}}};
 std::array<Gate,60>gates_{};V position_{},control_{};FlightMotion gyro_;hui::MotionData motion_{};bool gyro_enabled_=true;float sensitivity_=1;
 bool paused_=false,finished_=false;int passed_=0,missed_=0,processed_=0,event_=0;float flash_=0,arrival_=0,event_pan_=0,flight_time_=0,airflow_wait_=0,airflow_strength_=0,airflow_pan_=0;
 static constexpr float near_plane=.28f,half_width=.63f,half_height=.47f,focal=335;
 float forward_speed()const{return 3.6f*(1.f+std::clamp(float(processed_)/10.f,0.f,1.f));}
 V project(float x,float y,float z)const{return{500+(x-position_.x)*focal/std::max(near_plane,z),302+(y-position_.y)*focal/std::max(near_plane,z)};}
 void rectangle(DrawList&l,float x,float y,float z,float hx,float hy,Color c,float stroke){V p[4]={project(x-hx,y-hy,z),project(x+hx,y-hy,z),project(x+hx,y+hy,z),project(x-hx,y+hy,z)};for(unsigned n=0;n<4;++n)l.line(p[n].x,p[n].y,p[(n+1)%4].x,p[(n+1)%4].y,stroke,c);}
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"gates_passed",std::uint64_t(passed_)}};}
 StudyCompletion completion()const override{return finished_&&arrival_>.6f?StudyCompletion::experience_complete:StudyCompletion::playing;}
 Wireframe(){reset();}
 void reset()override{clean();position_=control_={};gyro_.reset();motion_={};paused_=finished_=false;passed_=missed_=processed_=event_=0;flash_=arrival_=event_pan_=flight_time_=airflow_wait_=airflow_strength_=airflow_pan_=0;for(unsigned n=0;n<gates_.size();++n)gates_[n]={7+float(n)*6.2f,route_[n%route_.size()].x,route_[n%route_.size()].y,0};}
 bool motion_controls()const override{return gyro_enabled_;}
 bool flight_settings()const override{return true;}
 bool gyro_enabled()const override{return gyro_enabled_;}
 float gyro_sensitivity()const override{return sensitivity_;}
 void configure_gyro(bool enabled,float sensitivity)override{if(enabled!=gyro_enabled_)gyro_.reset();gyro_enabled_=enabled;sensitivity_=std::isfinite(sensitivity)?std::clamp(sensitivity,.5f,2.f):1.f;if(!enabled)motion_={};}
 const char*help()const override{return "Hold still briefly to set a neutral pose, then tilt through a long sequence of approaching openings. The stick is always available. A quiet pointer marks the next opening; its centre lights when your flight line fits inside. Recenter when your seating position changes, or restart the route.";}
 void handle(const InputFrame&i,Feedback&f)override{
  control_={};paused_=i.focus_lost||!i.connected;if(paused_){gyro_.reset();motion_={};event_=0;pending_pulse_count_=0;airflow_strength_=airflow_wait_=0;motion_haptics_.reset();accepted_={hui::audio::Tactile::focus,0,0,0};rumble_=0;active_input_=false;return;}
  auto gameplay=i;if(finished_)gameplay.pressed&=~hui::action_bit(Action::west);
  if(!input(gameplay,f,event_!=0))return;
  if(event_){const auto pattern=event_==3?hui::audio::Tactile::confirm:event_==2?hui::audio::Tactile::error:hui::audio::Tactile::passage;
   f.feel(pattern,event_==3?.42f:event_==2?.28f:.34f,event_==3?.20f:event_==2?.12f:.16f,event_pan_);event_=0;airflow_strength_=0;airflow_wait_=.20f;}
  else if(airflow_strength_>0&&!finished_){f.feel(hui::audio::Tactile::airflow,airflow_strength_,.12f,airflow_pan_);airflow_strength_=0;}
  if(finished_)return;
  motion_=gyro_enabled_?i.motion:hui::MotionData{};
  if(i.is_pressed(Action::north)){gyro_.reset();f.feel(hui::audio::Tactile::focus,.07f,.025f);}
  control_={axis(i,true),axis(i,false)};
 }
 void update(float dt)override{
  dt=bounded_dt(dt);if(paused_||dt<=0)return;animate(dt);const bool was_calibrated=gyro_.calibrated();gyro_.update(motion_,dt);if(!was_calibrated&&gyro_.calibrated())pulse(hui::audio::Tactile::confirm,.09f,.03f);
  flash_=std::max(0.f,flash_-dt*2.3f);arrival_+=((finished_?1.f:0.f)-arrival_)*(1-std::exp(-dt*5));
  if(finished_)return;
  const auto tilt=gyro_enabled_&&motion_.available?gyro_.value():std::array<float,2>{};
  const V steering{std::abs(control_.x)>.04f?control_.x:std::clamp(tilt[0]*sensitivity_,-1.f,1.f),std::abs(control_.y)>.04f?control_.y:std::clamp(tilt[1]*sensitivity_,-1.f,1.f)};
  const auto before_position=position_;
  position_.x=std::clamp(position_.x+steering.x*1.8f*dt,-1.5f,1.5f);position_.y=std::clamp(position_.y+steering.y*1.8f*dt,-1.15f,1.15f);
  motion_haptics_.record(position_.x-before_position.x,position_.y-before_position.y,active_input_&&norm(steering)>.15f);
  // A controller still finding its neutral pose cannot lose gates. Manual
  // stick steering remains usable even if the optional sensor is moving.
  if(motion_.available&&!gyro_.calibrated()&&norm(control_)<.08f)return;
  flight_time_+=dt;const float forward=forward_speed();
  airflow_wait_=std::max(0.f,airflow_wait_-dt);
  if(airflow_wait_<=0){
   airflow_strength_=.065f+.045f*float(processed_)/float(gates_.size())+.025f*std::min(1.f,norm(steering));
   airflow_pan_=std::clamp(steering.x*.55f,-.55f,.55f);airflow_wait_=.10f;
  }
  for(auto&g:gates_){if(g.result)continue;g.z-=forward*dt;if(g.z>near_plane)continue;
   const float dx=position_.x-g.x,dy=position_.y-g.y;
   const bool inside=std::abs(dx)<half_width&&std::abs(dy)<half_height;
   g.result=inside?1:-1;++processed_;event_pan_=std::clamp(dx/half_width,-.8f,.8f);
   if(inside){++passed_;sound(72+passed_%5);event_=1;}else{++missed_;flash_=1;sound(48);event_=2;}
   if(processed_==int(gates_.size())){finished_=true;event_=missed_?2:3;sound(missed_?76:84);}
  }
 }
 void draw(DrawList&l,Fonts&f,Rect r,Color)override{
  if(r.w<=0||r.h<=0)return;
  const Color phosphor=Color::rgb(0xf1efe7),base=Color::rgb(0x0d1310);
  const float scale=std::min(r.w/1000,r.h/600);l.push_clip(r);l.rounded_rect(r,0,base);l.push_transform(scale,0,0,r.x+(r.w-1000*scale)/2,r.y+(r.h-600*scale)/2);
  l.rounded_rect({0,0,1000,600},0,base);
  if(flash_>0)l.rounded_rect({0,0,1000,600},0,phosphor.with_alpha(.045f*flash_));
  for(float x:{-2.5f,2.5f})for(float y:{-1.7f,1.7f}){const V p=project(x,y,near_plane),q=project(x,y,70);l.line(p.x,p.y,q.x,q.y,.8f,phosphor.with_alpha(.12f));}
  for(int n=int(gates_.size())-1;n>=0;--n){const auto&g=gates_[size_t(n)];if(g.result||g.z>80)continue;
   const float opacity=std::clamp(1-g.z/70,.12f,.85f);
   rectangle(l,0,0,g.z,2.5f,1.7f,phosphor.with_alpha(opacity*.14f),.65f);
   rectangle(l,g.x,g.y,g.z,half_width,half_height,phosphor.with_alpha(opacity),1.1f);
  }
  l.line(491,302,509,302,1.2f,phosphor);l.line(500,293,500,311,1.2f,phosphor);
  if(processed_<int(gates_.size())){
   const auto&g=gates_[size_t(processed_)];const float dx=g.x-position_.x,dy=g.y-position_.y;
   const bool aligned=std::abs(dx)<half_width&&std::abs(dy)<half_height;
   const float distance=std::hypot(dx,dy),factor=distance>.001f?std::min(75.f,distance*95)/distance:0;
   const float x=500+dx*factor,y=302+dy*factor;
   l.ring(x,y,aligned?7.f:10.f,1,phosphor.with_alpha(aligned?.85f:.38f));
   if(aligned)l.circle(500,302,2.3f,phosphor.with_alpha(.85f));
   if(distance>.12f)l.line(500+dx*18/std::max(.1f,distance),302+dy*18/std::max(.1f,distance),x-dx*12/std::max(.1f,distance),y-dy*12/std::max(.1f,distance),.8f,phosphor.with_alpha(.15f));
  }
  const float progress=float(processed_)/float(gates_.size());
  l.rounded_rect({350,49,300,2},0,phosphor.with_alpha(.15f));
  l.rounded_rect({350,49,300*progress,2},0,phosphor.with_alpha(.7f));
  char count[64];hui::ui::format(count,"%d / %zu",passed_,gates_.size());
  hui::ui::text(l,f.display,count,500,85,25,phosphor.with_alpha(.6f),Align::center);
  if(motion_.available&&!gyro_.calibrated()){
   l.bordered_rect({477,490,46,24},8,base,1,phosphor.with_alpha(.5f));
   l.arc(500,502,32,1,time_*2,pi*1.3f,phosphor.with_alpha(.4f));
   hui::ui::text(l,f.regular,"Hold the controller still to set your neutral position",500,550,20,phosphor,Align::center);
  }else if(flight_time_<5){
   hui::ui::text(l,f.regular,motion_.available?"Tilt the controller to steer through the openings":"Steer through the openings",500,550,20,phosphor.with_alpha(std::min(1.f,5-flight_time_)),Align::center);
  }
  if(finished_){l.ring(500,302,30+arrival_*15,1.2f,phosphor.with_alpha(arrival_*.6f));if(!missed_){l.line(484,302,496,314,2,phosphor.with_alpha(arrival_));l.line(496,314,520,288,2,phosphor.with_alpha(arrival_));}else{l.arc(500,302,18,1.8f,-pi*.7f,pi*1.7f,phosphor.with_alpha(arrival_));l.line(487,287,487,299,1.8f,phosphor.with_alpha(arrival_));l.line(487,287,499,287,1.8f,phosphor.with_alpha(arrival_));}}
  l.pop_transform();l.pop_clip();
 }
};
} // namespace
std::unique_ptr<Study> make_study_arcade(const std::string&key){
 if(key=="paddle")return std::make_unique<Paddle>();
 if(key=="bricks")return std::make_unique<Bricks>();
 if(key=="formation")return std::make_unique<Formation>();
 if(key=="maze")return std::make_unique<Maze>();
 if(key=="gravity")return std::make_unique<Gravity>();
 if(key=="orbit")return std::make_unique<Orbit>();
 if(key=="wireframe")return std::make_unique<Wireframe>();
 return {};
}
} // namespace museum
