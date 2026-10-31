// Pixel Museum - original, playable studies of movement and musical timing.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include "museum/haptic_interactions.hpp"
#include "museum/experience_audio.hpp"
#include "museum/rhythm_chart.hpp"
#include "ui/glyphs.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>

namespace museum {
namespace {
using hui::Action;
using hui::gfx::Color;
using hui::gfx::DrawList;
using hui::gfx::Rect;
constexpr float pi=3.14159265358979323846f;
constexpr Color paper{.91f,.91f,.85f,1};
constexpr Color muted{.52f,.56f,.57f,1};
constexpr Color ink{.035f,.055f,.065f,1};
constexpr std::array<int,8> notes{62,65,67,69,72,74,77,79};
float bounded_dt(float dt){return std::isfinite(dt)?std::clamp(dt,0.f,.1f):0.f;}
float axis(const hui::InputFrame&i,Action negative,Action positive,float analogue){
    const float digital=(i.is_held(positive)?1.f:0.f)-(i.is_held(negative)?1.f:0.f);
    return digital!=0?digital:std::clamp(analogue,-1.f,1.f);
}
void label(DrawList&d,hui::ui::Fonts&f,const char*s,float x,float y,float size,Color c=paper){
    if(f.regular.font)hui::ui::text(d,f.regular,s,x,y,size,c);
}
void number(DrawList&d,hui::ui::Fonts&f,const char*format,int value,float x,float y,Color c=paper){
    const bool squares=format[0]=='S';
    if(squares){for(int n=0;n<3;++n)d.bordered_rect({x+float(n)*5,y-17-float(n)*3,10,10},1,ink,1.2f,c);}
    else{d.circle(x+10,y-10,4,c);for(int n=0;n<6;++n){const float a=float(n)*pi/3;d.line(x+10+std::cos(a)*7,y-10+std::sin(a)*7,x+10+std::cos(a)*11,y-10+std::sin(a)*11,1,c);}}
    char s[40];hui::ui::format(s,squares?"%d":"%d / 7",value);hui::ui::text(d,f.display,s,x+32,y,26,c);
}
struct Point{float x=0,y=0;};
float distance(Point a,Point b){return std::hypot(a.x-b.x,a.y-b.y);}
struct Canvas {
    DrawList&d;
    Canvas(DrawList&list,Rect r):d(list){
        d.push_clip(r);d.rounded_rect(r,0,ink);const float scale=std::max(.001f,std::min(r.w/1400.f,r.h/700.f));
        d.push_transform(scale,0,0,r.cx()-700.f*scale,r.cy()-350.f*scale);
        d.rounded_rect({0,0,1400,700},0,ink);
    }
    ~Canvas(){d.pop_transform();d.pop_clip();}
};
class Motion:public Study {
protected:
 std::array<hui::audio::SpeakerCue,8> speaker_{};std::array<float,8> speaker_pitch_{};unsigned speaker_count_=0;
 void speak(hui::audio::SpeakerCue cue,float pitch=1){if(active_input_&&speaker_count_<speaker_.size()){speaker_[speaker_count_]=cue;speaker_pitch_[speaker_count_++]=pitch;}}
 AcceptedMotionHaptics motion_haptics_;bool active_input_=true;hui::audio::TactileEvent accepted_{hui::audio::Tactile::focus,0,0,0};
 void pulse(hui::audio::Tactile kind,float strength=.07f,float seconds=.025f,float pan=0){if(active_input_&&strength>=accepted_.strength)accepted_={kind,strength,seconds,pan};}
    float input_x_=0,input_y_=0,time_=0,flash_=0;
    bool held_cross_=false,pending_rumble_=false;
    bool common(const hui::InputFrame&i,hui::ui::Feedback&feedback,bool square_reset=true,bool suppress_motion=false){
        if(i.focus_lost||!i.connected){active_input_=false;input_x_=input_y_=0;held_cross_=pending_rumble_=false;speaker_count_=0;accepted_={hui::audio::Tactile::focus,0,0,0};motion_haptics_.reset();return true;}active_input_=true;
        if(square_reset&&i.is_pressed(Action::west)){reset();feedback.feel(hui::audio::Tactile::back,.10f,.05f);return true;}
        for(unsigned n=0;n<speaker_count_;++n)feedback.speak(speaker_[n],speaker_pitch_[n]);speaker_count_=0;
        const bool semantic=pending_rumble_||accepted_.strength>0;if(pending_rumble_){feedback.feel(hui::audio::Tactile::impact,.12f,.06f);pending_rumble_=false;}else if(accepted_.strength>0)feedback.feel(accepted_.pattern,accepted_.strength,accepted_.seconds,accepted_.pan);accepted_={hui::audio::Tactile::focus,0,0,0};motion_haptics_.drain(feedback,semantic||suppress_motion);
        input_x_=axis(i,Action::left,Action::right,i.stick_x);
        input_y_=axis(i,Action::up,Action::down,i.stick_y);
        held_cross_=i.is_held(Action::confirm);return false;
    }
    void clear(){active_input_=true;speaker_count_=0;accepted_={hui::audio::Tactile::focus,0,0,0};motion_haptics_.reset();input_x_=input_y_=time_=flash_=0;held_cross_=pending_rumble_=false;note_=-1;}
    void tick(float dt){motion_haptics_.advance(dt);time_+=dt;flash_=std::max(0.f,flash_-dt);}
    void event(int n){sound(n);flash_=.4f;pending_rumble_=active_input_;}
};

// Variable jump height, acceleration and a small coyote window. The route is
// An original route: legible landings, power-ups and a hidden coin room.
#include "museum/jump_study.inc"

// A rolling body: slopes change speed, reversing direction takes time, and
// braking deliberately discards momentum while a jump opens another route.
class Momentum final:public Motion {
 friend struct MotionHapticsInspection;
 friend struct MomentumLoopInspection;
 friend struct MotionInspection;
 #include "museum/sonic_native_route.inc"
 static constexpr float unit=1.6f,radius=26,gravity=1280,finish_x=9568*unit;
 static constexpr float loop_x=5504*unit,loop_y=608*unit,loop_radius=80*unit-radius;
 float x_=130,y_=0,v_=0,vy_=0,spin_=0,best_=0,jump_=0,coyote_=0,immune_=0,charge_=0,camera_=0,camera_y_=0;
 double active_seconds_=0;bool finish_under_45_=false;
 float loop_=-1,loop_speed_=0,finish_time_=0,spring_cooldown_=0,loop_retry_=0,checkpoint_x_=130,checkpoint_y_=0,view_height_=400;
 bool loop_done_=false,brake_feedback_=false;
 float tube_distance_=-1,tube_speed_=0;unsigned tube_number_=0;
 int rings_=0,banked_=0,falls_=0,standing_platform_=-1;
 bool grounded_=true,finished_=false,checkpoint_=false,brake_=false,rolling_=false,air_spin_=false;
 struct LooseRing{Point p{},v{};float life=0;};std::array<LooseRing,16>loose_{};
 std::array<bool,155>taken_{},banked_taken_{};std::array<bool,22>enemy_down_{};
 std::array<float,23>platform_fall_{};std::array<bool,2>post_taken_{};
 static Point ring(unsigned n){return {native_rings[n].x*unit,native_rings[n].y*unit};}
 static unsigned column(float x){return unsigned(std::clamp(int(x/unit),0,10239));}
 static bool solid(float x,float y){
  if(x<0||x>=10240*unit||y<0||y>=1280*unit)return false;
  const auto c=column(x);for(unsigned i=column_offset[c];i<column_offset[c+1];++i)if(y>=land_spans[i].top*unit&&y<land_spans[i].bottom*unit)return true;return false;
 }
 static float land_floor(float x,float bottom,float above=8,float below=28){
  float found=1e8f;const auto c=column(x);
  for(unsigned i=column_offset[c];i<column_offset[c+1];++i){const float y=land_spans[i].top*unit;if(y>=bottom-above&&y<=bottom+below)found=std::min(found,y);}
  for(const auto&b:native_bridges){const float left=(b.x-b.subtype*8-8)*unit,right=(b.x+b.subtype*8+8)*unit,y=(b.y-8)*unit;
   if(x>=left&&x<=right&&y>=bottom-above&&y<=bottom+below)found=std::min(found,y);}
  return found;
 }
 static float ground(float x){return land_floor(x,1280*unit,1280*unit,0);}
 static float ground_near(float x,float y){return land_floor(x,y,24,150);}
 Point tube_point(float distance)const{const float native=std::clamp(distance/unit,0.f,native_tube_distance[96]);unsigned n=1;while(n<96&&native_tube_distance[n]<native)++n;const float t=(native-native_tube_distance[n-1])/(native_tube_distance[n]-native_tube_distance[n-1]);const auto a=native_tube_points[n-1],b=native_tube_points[n];return{(a.x+(b.x-a.x)*t+tube_number_*512)*unit,(a.y+(b.y-a.y)*t+tube_number_*256)*unit};}
 float walk_floor(float x,float bottom,float above,float below)const{
  // Crossing a GHZ loop changes the foreground collision plane. Its exit
  // crosses behind the rising entrance ribbon and joins the same flat floor.
  if(loop_done_&&x>=5376*unit&&x<5632*unit&&bottom>640*unit){const float y=704*unit;return y>=bottom-above&&y<=bottom+below?y:1e8f;}
  return land_floor(x,bottom,above,below);
 }
 bool walk_solid(float x,float y)const{if(loop_done_&&x>=5376*unit&&x<5632*unit&&y>640*unit)return false;return solid(x,y);}
 float body_floor(float x,float bottom,float above,float below)const{return std::min({walk_floor(x-13,bottom,above,below),walk_floor(x,bottom,above,below),walk_floor(x+13,bottom,above,below)});}
 static float smooth_top(int x,float y){
  float sum=0,count=0;for(int c=std::max(0,x-6);c<=std::min(10239,x+6);++c)for(unsigned n=column_offset[c];n<column_offset[c+1];++n)if(std::abs(land_spans[n].top-y)<=8){sum+=land_spans[n].top;++count;break;}
  float result=count?sum/count:y,low=y,high=y;unsigned samples=0;
  for(int c=std::max(0,x-64);c<=std::min(10239,x+64);c+=4){float nearest=1e8f;for(unsigned n=column_offset[c];n<column_offset[c+1];++n)if(std::abs(land_spans[n].top-y)<std::abs(nearest-y))nearest=land_spans[n].top;if(std::abs(nearest-y)<=64){low=std::min(low,nearest);high=std::max(high,nearest);++samples;}}
  if(samples>24){const float flatten=std::clamp((16-(high-low))/4,0.f,1.f),nominal=std::round(low/16)*16;result+=(nominal-result)*flatten;}
  return result*unit;
 }
 Point platform(unsigned n,float t)const{
  const auto&p=native_platforms[n];float x=p.x,y=p.y-(p.type==0x1a?32:9);const float phase=(1-std::cos(t*pi*.5f))*.5f;
  if(p.type==0x18){if(p.subtype==1)x+=64*phase;else if(p.subtype==5)x-=64*phase;else if(p.subtype==2)y+=64*phase;else if(p.subtype==6)y-=64*phase;}
  if((p.subtype==3||p.type==0x1a)&&platform_fall_[n]>.35f){const float elapsed=platform_fall_[n]-.35f;y+=std::min(1000.f,200*elapsed*elapsed);}
  return{x*unit,y*unit};
 }
 float platform_half(unsigned n)const{return(native_platforms[n].type==0x1a?48.f:32.f)*unit;}
 float platform_floor(unsigned n,float x,float t)const{const auto p=platform(n,t);if(native_platforms[n].type!=0x1a)return p.y;float local=(x-p.x)/unit;if(native_platforms[n].subtype&128)local=-local;return p.y-16*unit*std::clamp((local+32)/60,0.f,1.f);}
 Point enemy(unsigned n)const{
  const auto&e=native_enemies[n];float x=e.x,y=e.y;
  if(e.type==0x40){x+=24*std::sin(time_*1.3f);const float floor=land_floor(x*unit,(e.y+20)*unit,48*unit,48*unit);if(floor<1e7f)y=floor/unit-20;}
  else if(e.type==0x1f){x+=12*std::sin(time_*.8f);const float floor=land_floor(x*unit,(e.y+20)*unit,48*unit,48*unit);if(floor<1e7f)y=floor/unit-16;}
  else if(e.type==0x22){x+=20*std::sin(time_*.7f);y+=3*std::sin(time_*4);}
  else if(e.type==0x2b){const float phase=std::fmod(time_+n*.43f,3.4f);y+=phase<1.5f?-std::sin(phase/1.5f*pi)*106:0;}
  return{x*unit,y*unit};
 }
 void collect_ring(){++rings_;sound(84);pulse(hui::audio::Tactile::touch,.10f,.022f);speak(hui::audio::SpeakerCue::ring,1.f+.035f*(rings_%6));}
 void hurt(float source_x){
  if(immune_>0)return;if(rings_<=0){respawn();return;}
  const int count=std::min(16,rings_);for(auto&r:loose_)r.life=0;
  for(int n=0;n<count;++n){const float angle=pi*(.12f+.76f*(count==1?.5f:float(n)/(count-1)));const float speed=n%2?330.f:430.f;loose_[n]={{x_,y_},{std::cos(angle)*speed,-std::sin(angle)*speed},8.f};}
  rings_=banked_=0;immune_=1.8f;rolling_=air_spin_=false;charge_=0;loop_=-1;tube_distance_=-1;loop_retry_=.6f;grounded_=false;vy_=-380;v_=source_x<x_?320.f:-320.f;standing_platform_=-1;
  pending_rumble_=false;sound(48);pulse(hui::audio::Tactile::impact,.30f,.10f);speak(hui::audio::SpeakerCue::ring,.55f);
 }
 void respawn(){x_=checkpoint_x_;y_=checkpoint_y_;v_=vy_=jump_=charge_=0;loop_=-1;loop_done_=checkpoint_x_>5632*unit;tube_distance_=-1;loop_retry_=0;coyote_=.1f;grounded_=true;immune_=.8f;rings_=banked_=0;taken_=banked_taken_;++falls_;rolling_=air_spin_=false;standing_platform_=-1;for(auto&r:loose_)r.life=0;event(50);}
 void collect_near(){for(unsigned n=0;n<taken_.size();++n)if(!taken_[n]&&distance({x_,y_},ring(n))<radius+12){taken_[n]=true;collect_ring();}}
public:
 Momentum(){reset();}
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"finish_under_45_seconds",finish_under_45_?1u:0u}};}
 StudyCompletion completion()const override{return finished_&&finish_time_>=1.2f?StudyCompletion::experience_complete:StudyCompletion::playing;}
 void reset()override{
  clear();x_=130;y_=land_floor(x_,960*unit,64,64)-radius;checkpoint_x_=x_;checkpoint_y_=y_;
  active_seconds_=0;finish_under_45_=false;
  v_=vy_=spin_=best_=jump_=immune_=charge_=camera_=finish_time_=spring_cooldown_=loop_retry_=0;view_height_=400;camera_y_=std::clamp(y_-230,0.f,1648.f);
  coyote_=.1f;grounded_=true;finished_=checkpoint_=brake_=false;rings_=banked_=falls_=0;taken_.fill(false);banked_taken_.fill(false);enemy_down_.fill(false);post_taken_.fill(false);platform_fall_.fill(0);standing_platform_=-1;loop_=-1;loop_speed_=0;tube_distance_=-1;tube_speed_=0;tube_number_=0;loop_done_=brake_feedback_=rolling_=air_spin_=false;for(auto&r:loose_)r.life=0;
 }
 const char*help()const override{return "D-pad / left stick: lean and build speed. Cross jumps. Hold Down while moving to roll; steer against your movement to brake. At rest, hold Down and tap Cross to store a rolling start; release Down to launch. Carry momentum across gaps; the higher route holds extra rings. A starpost saves your return position. Square restarts.";}
 void handle(const hui::InputFrame&i,hui::ui::Feedback&f)override{
  const bool braking=brake_;brake_=false;if(common(i,f)){charge_=0;return;}brake_=input_y_>.35f;
  if(brake_&&grounded_&&std::abs(v_)>150&&!rolling_){rolling_=true;pulse(hui::audio::Tactile::touch,.15f,.04f);}
  if(grounded_&&std::abs(v_)<90)rolling_=false;
  if(braking&&!brake_&&charge_>.05f&&grounded_){const float dir=std::abs(input_x_)>.2f?(input_x_<0?-1.f:1.f):v_<-5?-1.f:1.f;v_=dir*std::max(std::abs(v_),300+charge_*660);charge_=0;rolling_=true;event(77);speak(hui::audio::SpeakerCue::charge,1.5f);}
  if(i.is_pressed(Action::confirm)&&!finished_){if(brake_&&grounded_&&std::abs(v_)<130){rolling_=false;const float before=charge_;charge_=std::min(1.f,charge_+.28f);if(charge_>before){sound(62+int(charge_*12));f.feel(hui::audio::Tactile::touch,.04f+.09f*charge_,.025f);f.speak(hui::audio::SpeakerCue::charge,.7f+.8f*charge_);}}else jump_=.13f;}
 }
 void update(float dt)override{
  dt=bounded_dt(dt);tick(dt);if(!active_input_)return;
  immune_=std::max(0.f,immune_-dt);spring_cooldown_=std::max(0.f,spring_cooldown_-dt);loop_retry_=std::max(0.f,loop_retry_-dt);
  if(finished_){finish_time_+=dt;v_*=std::exp(-dt*6);x_=std::min(finish_x+160,x_+v_*dt);return;}
  const float old_feedback_x=x_,old_time=time_-dt;const int steps=std::max(1,int(std::ceil(dt/.004f)));const float h=dt/steps;
  for(int step=0;step<steps;++step){
   active_seconds_+=double(h);
   const float t=old_time+(step+1)*h;
   if(tube_distance_>=0){const auto before=tube_point(tube_distance_-1),after=tube_point(tube_distance_+1);const float length=std::max(.01f,distance(before,after));const Point tangent{(after.x-before.x)/length,(after.y-before.y)/length};tube_speed_+=(gravity*tangent.y-.035f*tube_speed_+(input_x_*tube_speed_<0?input_x_*900:0))*h;tube_speed_=std::clamp(tube_speed_,-1600.f,1600.f);tube_distance_+=tube_speed_*h;const auto p=tube_point(tube_distance_);x_=p.x;y_=p.y;v_=tube_speed_*tangent.x;vy_=tube_speed_*tangent.y;spin_+=tube_speed_*h/25;collect_near();if(tube_distance_>=native_tube_distance[96]*unit){tube_distance_=-1;grounded_=true;v_=tube_speed_;vy_=0;y_=(896+tube_number_*256)*unit-radius;air_spin_=false;rolling_=true;pulse(hui::audio::Tactile::touch,.12f,.04f);}else if(tube_distance_<0){grounded_=false;loop_retry_=.3f;}continue;}
   if(standing_platform_>=0){const auto a=platform(standing_platform_,t-h),b=platform(standing_platform_,t);x_+=b.x-a.x;y_+=b.y-a.y;if(native_platforms[standing_platform_].subtype==3||native_platforms[standing_platform_].type==0x1a)platform_fall_[standing_platform_]+=h;}
   if(loop_>=0){
    loop_speed_-=gravity*std::sin(loop_)*h;const float next=loop_+loop_speed_*h/loop_radius;loop_=std::clamp(next,0.f,2*pi);x_=loop_x+loop_radius*std::sin(loop_);y_=loop_y+loop_radius*std::cos(loop_);spin_+=loop_speed_*h/25;collect_near();
    if(loop_>=2*pi){loop_=-1;loop_done_=true;v_=loop_speed_;vy_=0;grounded_=false;air_spin_=true;rolling_=true;event(79);}
    else if(next<0||loop_speed_*loop_speed_/loop_radius+gravity*std::cos(loop_)<0){v_=loop_speed_*std::cos(loop_);vy_=-loop_speed_*std::sin(loop_);loop_=-1;loop_retry_=.6f;grounded_=false;}
    continue;
   }
   for(auto&r:loose_)if(r.life>0){r.life=std::max(0.f,r.life-h);const float previous=r.p.y;r.p.x+=r.v.x*h;r.v.x*=std::exp(-h*.5f);r.v.y+=900*h;r.p.y+=r.v.y*h;const float floor=land_floor(r.p.x,previous+9,1,std::max(10.f,r.v.y*h+9));if(r.v.y>0&&r.p.y+9>=floor){r.p.y=floor-9;r.v.y=-std::abs(r.v.y)*.55f;}if(r.life<7.65f&&distance({x_,y_},r.p)<37){r.life=0;collect_ring();}}
   jump_=std::max(0.f,jump_-h);coyote_=grounded_?.1f:std::max(0.f,coyote_-h);
   if(jump_>0&&coyote_>0){vy_=-690;grounded_=false;standing_platform_=-1;rolling_=false;air_spin_=true;coyote_=jump_=0;sound(74);pulse(hui::audio::Tactile::rise,.12f,.04f);}
   const bool counter=grounded_&&std::abs(input_x_)>.2f&&input_x_*v_<0;float grade=0;
   if(grounded_&&standing_platform_<0){const float a=land_floor(x_-4,y_+radius,16,16),b=land_floor(x_+4,y_+radius,16,16);if(a<1e7f&&b<1e7f)grade=std::clamp((b-a)/8,-1.5f,1.5f);}
   v_+=(input_x_*(grounded_?(counter?1900.f:rolling_?0.f:470.f):540.f)+(grounded_?(rolling_?900.f:410.f)*grade:0))*h;
   v_*=std::exp(-(grounded_?(rolling_?.035f:brake_?5.f:.17f):.025f)*h);v_=std::clamp(v_,-1050.f,1050.f);
   const float old_x=x_,old_y=y_,old_bottom=y_+radius;const bool was_grounded=grounded_;x_=std::clamp(x_+v_*h,40.f,finish_x+200);spin_+=v_*h/25;
   if(!loop_done_&&loop_retry_<=0&&was_grounded&&old_x<loop_x&&x_>=loop_x&&std::abs(old_bottom-704*unit)<45&&v_>80){loop_=0;loop_speed_=v_;x_=loop_x;y_=loop_y+loop_radius;grounded_=false;standing_platform_=-1;rolling_=air_spin_=true;event(77);continue;}
   bool entered_tube=false;for(unsigned n=0;n<2;++n){const float start=(6176+n*512)*unit;if(loop_retry_<=0&&was_grounded&&v_>80&&old_x<start&&x_>=start&&std::abs(old_bottom-(640+n*256)*unit)<45){tube_number_=n;tube_distance_=x_-start;tube_speed_=v_;const auto p=tube_point(tube_distance_);x_=p.x;y_=p.y;grounded_=false;standing_platform_=-1;rolling_=air_spin_=true;entered_tube=true;break;}}if(entered_tube)continue;
   grounded_=false;int new_platform=-1;
   if(was_grounded){
    float floor=body_floor(x_,old_bottom,12,28);
    for(unsigned n=0;n<23;++n){const auto p=platform(n,t);const float top=platform_floor(n,x_,t);if(std::abs(x_-p.x)<platform_half(n)+9&&std::abs(old_bottom-top)<10&&top<floor){floor=top;new_platform=int(n);}}
    if(floor<1e7f){y_=floor-radius;vy_=0;grounded_=true;}
    else if(walk_solid(x_+(v_>=0?radius*.7f:-radius*.7f),old_y)||walk_solid(x_+(v_>=0?radius*.7f:-radius*.7f),old_y+radius*.55f)){x_=old_x;v_=0;y_=old_y;grounded_=true;}
   }
   if(!grounded_){
    vy_+=gravity*h;y_+=vy_*h;
    if(vy_>=0){float floor=body_floor(x_,old_bottom,20,std::max(8.f,vy_*h+3));
     for(unsigned n=0;n<23;++n){const auto p=platform(n,t);const float top=platform_floor(n,x_,t);if(std::abs(x_-p.x)<platform_half(n)+9&&old_bottom<=top+2&&y_+radius>=top&&top<floor){floor=top;new_platform=int(n);}}
     if(y_+radius>=floor){y_=floor-radius;vy_=0;grounded_=true;}
    }else if(walk_solid(x_,y_-radius)&&!walk_solid(x_,old_y-radius)){y_=old_y;vy_=0;pulse(hui::audio::Tactile::touch,.10f,.03f);}
    if(!grounded_&&(walk_solid(x_+(v_>=0?radius*.7f:-radius*.7f),y_)||(vy_>=0&&walk_solid(x_+(v_>=0?radius*.7f:-radius*.7f),y_+radius*.55f)))){x_=old_x;v_=0;}
   }
   standing_platform_=grounded_?new_platform:-1;
   if(was_grounded&&!grounded_&&rolling_)air_spin_=true;
   if(!was_grounded&&grounded_){air_spin_=false;rolling_=brake_&&std::abs(v_)>150;pulse(hui::audio::Tactile::touch,.1f,.03f);}
   for(const auto&s:native_springs)if(spring_cooldown_<=0&&std::abs(x_-s.x*unit)<20*unit&&y_+radius>=s.y*unit-18*unit&&y_+radius<=s.y*unit+14*unit&&vy_>=0){vy_=-1020;grounded_=false;standing_platform_=-1;air_spin_=rolling_=false;coyote_=0;spring_cooldown_=.5f;sound(79);pulse(hui::audio::Tactile::rise,.20f,.065f);break;}
   collect_near();
   for(unsigned n=0;n<22;++n)if(!enemy_down_[n]){const auto e=enemy(n);const float w=native_enemies[n].type==0x22?30.f:25.f;if(std::abs(x_-e.x)<radius+w&&std::abs(y_-e.y)<radius+20){if(air_spin_||rolling_){enemy_down_[n]=true;if(!grounded_){vy_=-320;air_spin_=true;}sound(74);pulse(hui::audio::Tactile::impact,.16f,.04f);}else hurt(e.x);}}
   for(const auto&s:native_spikes){const bool single=(s.subtype>>4)==2;const float w=(single?4:20)*unit,height=16*unit;if(std::abs(x_-s.x*unit)<radius*.8f+w&&std::abs(y_-s.y*unit)<radius*.85f+height)hurt(s.x*unit);}
   for(unsigned n=0;n<2;++n){const auto&p=native_posts[n];if(!post_taken_[n]&&std::abs(x_-p.x*unit)<35&&std::abs(y_-p.y*unit)<95){post_taken_[n]=true;checkpoint_=true;checkpoint_x_=p.x*unit;const float floor=land_floor(checkpoint_x_,p.y*unit,8,100);checkpoint_y_=floor-radius;banked_=rings_;banked_taken_=taken_;event(77);}}
   if(y_>1280*unit+100)respawn();
   if(old_x<finish_x&&x_>=finish_x){finished_=true;finish_under_45_=active_seconds_<45.0;finish_time_=0;event(81);speak(hui::audio::SpeakerCue::bonus);break;}
  }
  motion_haptics_.record(x_-old_feedback_x,0,active_input_&&loop_<0&&std::abs(input_x_)>.2f);
  float landing=land_floor(x_+std::clamp(v_*.2f,-150.f,150.f),y_+radius,0,1000);
  if(landing>1e7f)landing=land_floor(x_,y_+radius,0,1000);
  const float desired_height=grounded_||loop_>=0?400.f:std::clamp((landing-y_)+180,400.f,650.f);
  view_height_+=(desired_height-view_height_)*(1-std::exp(-dt*5));
  const float target=std::clamp(x_-view_height_*.675f+std::clamp(v_*.14f,-70.f,110.f),0.f,10240*unit-view_height_*2);
  camera_+=(target-camera_)*(1-std::exp(-dt*7));
  const bool see_loop=std::abs(x_-loop_x)<260&&y_>loop_y-180&&y_<loop_y+220;
  const float target_y=std::clamp(see_loop?loop_y-view_height_*.5f:y_-view_height_*(grounded_?.575f:.25f),0.f,1280*unit-view_height_);camera_y_+=(target_y-camera_y_)*(1-std::exp(-dt*(grounded_?7.f:3.5f)));
  camera_y_=std::clamp(camera_y_,std::max(0.f,y_-view_height_+radius+35),std::max(0.f,y_-radius-35));
  if(!grounded_)charge_=0;
 }
 void draw(DrawList&d,hui::ui::Fonts&,Rect r,Color accent)override{
  d.push_clip(r);d.rounded_rect(r,0,ink);const float width=view_height_*2,height=view_height_;const float scale=std::min(r.w/width,r.h/height);d.push_transform(scale,0,0,r.cx()-width*.5f*scale,r.cy()-height*.5f*scale);
  const float camera=camera_,cy=camera_y_;const Color surface=paper.with_alpha(.72f),ground_fill=hui::gfx::mix(ink,paper,.055f);
  // Only native collision boundaries are drawn. Adjacent columns share their
  // endpoints, so slopes remain continuous and do not inherit editor markers.
  const int first=std::max(0,int(camera/unit)-1),last=std::min(10239,int((camera+width)/unit)+2);
  for(int x=first;x<last;x+=4){const int end=std::min(x+4,last);
   for(unsigned n=column_offset[x];n<column_offset[x+1];++n){const auto a=land_spans[n];float top=smooth_top(x,a.top),bottom=a.visual_bottom*unit;
    if(bottom<cy-2||top>cy+height+2)continue;
    if(x>=5376&&x<5632&&a.top>=512&&a.top<705)continue;
    if((x>=6144&&x<6400&&a.top>=608&&a.top<=928)||(x>=6656&&x<6912&&a.top>=864&&a.top<=1184))continue;
    float next_top=top,next_bottom=bottom;for(unsigned j=column_offset[end];j<column_offset[end+1];++j){const auto b=land_spans[j];if(std::abs(int(a.top)-b.top)<=8&&std::abs(int(a.bottom)-b.bottom)<=32){next_top=smooth_top(end,b.top);next_bottom=b.visual_bottom*unit;break;}}
    const float points[]{x*unit-camera,top-cy,end*unit-camera,next_top-cy,end*unit-camera,next_bottom-cy,x*unit-camera,bottom-cy};d.polygon(points,4,ground_fill);
    const float edge[]{x*unit-camera,top-cy-.7f,end*unit-camera,next_top-cy-.7f,end*unit-camera,next_top-cy+.7f,x*unit-camera,top-cy+.7f};d.polygon(edge,4,surface);
   }
  }
  for(const auto&b:native_bridges){const float left=(b.x-b.subtype*8-8)*unit,top=(b.y-8)*unit;if(left>camera+width+50||left+b.subtype*16*unit<camera-50)continue;
   for(unsigned n=0;n<=b.subtype;++n){const float x=left+n*16*unit;d.bordered_rect({x-camera,top-cy,16*unit,9*unit},2,ink,1,paper.with_alpha(.6f));}d.line(left-camera,top+14*unit-cy,left+(b.subtype+1)*16*unit-camera,top+14*unit-cy,1,paper.with_alpha(.22f));}
  // The original block silhouette surrounds a smooth 160px inner opening.
  // Clear its interior once; collision tile seams are not visual ornaments.
  const float lx=loop_x-camera,ly=loop_y-cy;
  if(lx>-200&&lx<width+200){const float loop_body[]{5376*unit-camera,512*unit-cy,5632*unit-camera,512*unit-cy,5632*unit-camera,640*unit-cy,5568*unit-camera,704*unit-cy,5440*unit-camera,704*unit-cy,5376*unit-camera,640*unit-cy};d.polygon(loop_body,6,ground_fill);d.circle(lx,ly,80*unit,ink);d.ring(lx,ly,80*unit,1.7f,surface);d.line(5376*unit-camera,512*unit-cy,5632*unit-camera,512*unit-cy,1.5f,surface);}
  for(unsigned tunnel=0;tunnel<2;++tunnel){const float dx=tunnel*512*unit,dy=tunnel*256*unit,left=6144*unit+dx-camera;if(left>width+60||left+256*unit<-60)continue;
   d.rounded_rect({left,608*unit+dy-cy,256*unit,320*unit},0,ground_fill);
   d.push_clip({left,608*unit+dy-cy,256*unit,320*unit});
   for(unsigned pass=0;pass<2;++pass){const Color color=pass?ink:surface;const float thickness=pass?60.f:63.f;d.line((pass?6080:6144)*unit+dx-camera,624*unit+dy-cy,6176*unit+dx-camera,624*unit+dy-cy,thickness,color);for(unsigned n=1;n<97;++n){const auto a=native_tube_points[n-1],b=native_tube_points[n];d.line(a.x*unit+dx-camera,a.y*unit+dy-cy,b.x*unit+dx-camera,b.y*unit+dy-cy,thickness,color);}d.line(6400*unit+dx-camera,880*unit+dy-cy,(pass?6496:6432)*unit+dx-camera,880*unit+dy-cy,thickness,color);}
   d.pop_clip();
  }
  for(unsigned n=0;n<23;++n){const auto p=platform(n,time_);if(p.x<camera-90||p.x>camera+width+90||p.y<cy-40||p.y>cy+height+40)continue;
   if(native_platforms[n].type==0x1a){const float left=p.x-platform_half(n),right=p.x+platform_half(n),yl=platform_floor(n,left,time_),yr=platform_floor(n,right,time_);const float points[]{left-camera,yl-cy,right-camera,yr-cy,right-camera,yr+35*unit-cy,left-camera,yl+35*unit-cy};d.polygon(points,4,paper.with_alpha(.07f));d.line(left-camera,yl-cy,right-camera,yr-cy,1.7f,surface);}
   else{d.bordered_rect({p.x-32*unit-camera,p.y-cy,64*unit,9*unit},2,ink,1.7f,surface);d.line(p.x-22*unit-camera,p.y+14*unit-cy,p.x+22*unit-camera,p.y+14*unit-cy,.7f,paper.with_alpha(.2f));}}
  for(const auto&s:native_spikes){if(s.x*unit<camera-50||s.x*unit>camera+width+50)continue;const bool single=(s.subtype>>4)==2;for(int n=single?0:-1;n<=(single?0:1);++n){const float x=s.x*unit+n*16*unit-camera,y=s.y*unit-cy;d.triangle({x-4*unit,y-16*unit,8*unit,32*unit},accent.with_alpha(.75f));}}
  for(const auto&s:native_springs){const float x=s.x*unit-camera,y=s.y*unit-cy;if(x<-50||x>width+50)continue;d.bordered_rect({x-17*unit,y-14*unit,34*unit,5*unit},1,ink,1.6f,accent);for(int n=0;n<3;++n){const float yy=y-8*unit+n*5*unit;d.line(x-10*unit,yy,x+10*unit,yy+2.5f*unit,1,paper);d.line(x+10*unit,yy+2.5f*unit,x-10*unit,yy+5*unit,1,paper);}}
  for(unsigned n=0;n<155;++n)if(!taken_[n]){const auto p=ring(n);if(p.x>=camera-12&&p.x<=camera+width+12&&p.y>=cy-12&&p.y<=cy+height+12)d.ring(p.x-camera,p.y-cy,9,1.7f,accent);}
  for(const auto&p:loose_)if(p.life>0&&(p.life>2||int(time_*12)%2==0))d.ring(p.p.x-camera,p.p.y-cy,9,1.7f,accent);
  for(unsigned n=0;n<22;++n)if(!enemy_down_[n]){const auto p=enemy(n);const float x=p.x-camera,y=p.y-cy;if(x<-70||x>width+70||y<-70||y>height+70)continue;const auto type=native_enemies[n].type;
   if(type==0x40){d.bordered_rect({x-24,y-19,48,26},11,ink,1.7f,paper);d.ring(x-8,y+10,11,2,accent);d.circle(x+15,y-11,3,accent);d.line(x+10,y-18,x+15,y-28,1.3f,paper);d.circle(x+15,y-28,2,accent);}
   else if(type==0x1f){d.bordered_rect({x-19,y-14,38,25},8,ink,1.7f,paper);for(float side:{-1.f,1.f}){d.line(x+side*17,y+6,x+side*29,y+12,1.7f,paper);d.line(x+side*29,y+12,x+side*34,y+4,1.7f,paper);d.line(x+side*16,y-3,x+side*31,y-18,1.7f,accent);d.line(x+side*31,y-18,x+side*25,y-24,1.7f,accent);d.line(x+side*31,y-18,x+side*37,y-24,1.7f,accent);}d.circle(x-7,y-6,2,accent);d.circle(x+7,y-6,2,accent);}
   else if(type==0x22){d.bordered_rect({x-27,y-9,54,18},8,ink,1.7f,paper);d.line(x-7,y-9,x-18,y-25-4*std::sin(time_*25),1.7f,accent);d.line(x+7,y-9,x+18,y-25-4*std::sin(time_*25),1.7f,accent);d.triangle({x-22,y+8,10,15},accent);d.circle(x+18,y-2,3,accent);}
   else{d.bordered_rect({x-13,y-22,26,44},12,ink,1.7f,paper);d.circle(x+4,y-12,3,accent);d.line(x-11,y+7,x-22,y+17,1.6f,accent);d.line(x+11,y+7,x+22,y+17,1.6f,accent);d.triangle({x-10,y+20,20,12},accent);}
  }
  for(unsigned n=0;n<2;++n){const auto&p=native_posts[n];const float x=p.x*unit-camera,y=p.y*unit-cy;if(x<-30||x>width+30)continue;d.line(x,y-50,x,y+13,1.6f,paper.with_alpha(.6f));d.ring(x,y-50,10,1.6f,post_taken_[n]?accent:paper);d.circle(x,y-50,3,post_taken_[n]?accent:ink);}
  const float sx=finish_x-camera,sy=1216*unit-cy;d.line(sx,sy-65,sx,sy,1.7f,paper);const float sign_width=finished_?std::max(2.f,38*std::abs(std::cos(std::min(finish_time_,1.2f)*pi*5))):38.f;d.bordered_rect({sx-sign_width*.5f,sy-101,sign_width,43},3,ink,1.7f,accent);
  if(sign_width>24){const float face_y=sy-80;if(finished_){d.arc(sx,face_y,10,1.5f,-pi*.7f,pi*1.5f,paper);d.circle(sx+5,face_y-3,2,accent);d.line(sx-6,face_y-7,sx-14,face_y-3,1.5f,accent);d.line(sx-7,face_y,sx-14,face_y+4,1.5f,accent);}else{d.ring(sx,face_y-1,9,1.4f,paper);d.circle(sx-4,face_y-4,2,accent);d.circle(sx+4,face_y-4,2,accent);d.line(sx,face_y+1,sx-13,face_y+6,2,paper);d.line(sx,face_y+1,sx+13,face_y+6,2,paper);d.line(sx-6,face_y+10,sx+6,face_y+10,1,paper);}}
  const float px=x_-camera,py=y_-cy;
  if(immune_<=0||int(time_*10)%2==0){d.circle(px,py,radius,accent.with_alpha(.14f));d.ring(px,py,radius,1.9f,accent);for(int n=0;n<3;++n)d.arc(px,py,18,1.5f,spin_+n*pi*2/3,pi*.42f,paper.with_alpha(.9f));if(grounded_&&!rolling_&&charge_<=0){const float facing=v_<-5?-1.f:1.f;for(int n=0;n<3;++n){const float y=py-17+n*12;d.line(px-facing*15,y,px-facing*(32-n*2),y+7,1.7f,accent);d.line(px-facing*(32-n*2),y+7,px-facing*15,y+12,1.7f,accent);}d.circle(px+facing*9,py-8,3,paper);d.line(px-15,py+24,px+2,py+24,2.5f,paper);d.line(px+8,py+24,px+22,py+24,2.5f,accent);}if(charge_>0)d.arc(px,py,34,1.7f,-pi*.5f,2*pi*charge_,accent);}
  d.pop_transform();d.pop_clip();
 }
};

class Dash final:public Motion {
 friend struct MotionHapticsInspection;
    friend struct MotionInspection;
    friend struct DashInspection;
    struct Platform {float x,y,w;};
    struct Room {std::array<Platform,8> platforms;unsigned count;Point crystal;Point exit;};
    static constexpr std::array<Room,5> rooms{{
      {{{{50,550,400},{810,500,540},{0,0,0}}},2,{650,370},{1250,500}},
      {{{{50,550,280},{920,420,430},{0,0,0}}},2,{565,260},{1250,420}},
      {{{{50,580,290},{480,430,210},{1000,270,350}}},3,{820,170},{1250,270}},
      // A readable staircase teaches safe landings before the rising gap.
      // The diamond connects a diagonal launch to a horizontal second dash.
      {{{{60,600,180},{280,550,120},{450,500,130},{620,450,110},{1130,250,130},{1260,190,90}}},6,{950,165},{1310,190}},
      // Lower route right, reverse onto the upper balcony, then cross the
      // visibly bounded high passage using its single airborne refill.
      {{{{60,600,180},{300,530,140},{530,450,180},{370,290,160},{1110,250,150},{1260,190,90}}},6,{850,165},{1310,190}}
    }};
    static constexpr std::array<Rect,2> final_passage{{{600,100,470,24},{960,290,90,410}}};
    struct Spikes {float x,y,w;};
    static constexpr std::array<Spikes,4> teaching_spikes{{{240,650,40},{400,650,50},{580,650,40},{730,650,400}}};
    static constexpr std::array<Spikes,5> final_spikes{{{240,650,60},{440,650,90},{710,650,250},{1050,650,60},{960,290,90}}};
    Point p_{},direction_{1,0};float vx_=0,vy_=0,dash_=0,coyote_=0,jump_buffer_=0,transition_=0,gem_glow_=0,charge_visual_=1,landing_glow_=0;Point landing_{};
    bool charged_=true,grounded_=true,finished_=false,gem_taken_=false,paused_=false,room_complete_=false;
    unsigned room_=0,falls_=0,tail_=0,air_dashes_=0;float facing_=1,aim_feedback_time_=0;int aim_sector_=-1;
    std::array<Point,18>trail_{};
    std::array<hui::audio::TactileEvent,6> tactile_{};unsigned tactile_count_=0;
    void feel(hui::audio::Tactile pattern,float strength,float seconds){
      if(tactile_count_<tactile_.size())tactile_[tactile_count_++]={pattern,strength,seconds,0};
    }
    void enter(unsigned room,bool fallen=false){
      room_=room;const auto& floor=rooms[room].platforms[0];p_={floor.x+65,floor.y-15};
      vx_=vy_=dash_=jump_buffer_=gem_glow_=0;charge_visual_=1;landing_glow_=0;landing_={};coyote_=.11f;grounded_=charged_=true;
      input_x_=input_y_=0;
      gem_taken_=false;air_dashes_=0;room_complete_=false;trail_.fill(p_);tail_=0;
      if(fallen){++falls_;sound(48);feel(hui::audio::Tactile::error,.24f,.09f);}
    }
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"completed",completion()==StudyCompletion::experience_complete?1u:0u}};}
    Dash(){reset();}
    void reset()override{clear();direction_={1,0};facing_=1;room_=falls_=tactile_count_=0;transition_=0;charge_visual_=1;landing_glow_=0;paused_=finished_=false;aim_feedback_time_=0;aim_sector_=-1;enter(0);}
    StudyCompletion completion()const override{return finished_?StudyCompletion::experience_complete:room_complete_?StudyCompletion::level_complete:StudyCompletion::playing;}
    int level_number()const override{return int(room_)+1;}
    int level_count()const override{return int(rooms.size());}
    void continue_level()override{if(finished_)reset();else if(room_complete_)enter(room_+1);}
    const char*help()const override{return "Jump between safe ledges, follow the dotted direction guide to aim one air dash, and touch a floating diamond to restore it. Landing restores the dash too. Reach each lit doorway; a fall returns to the current room.";}
    void handle(const hui::InputFrame&i,hui::ui::Feedback&f)override{
      paused_=i.focus_lost||!i.connected;if(paused_){active_input_=false;input_x_=input_y_=0;held_cross_=pending_rumble_=false;speaker_count_=0;accepted_={hui::audio::Tactile::focus,0,0,0};motion_haptics_.reset();jump_buffer_=0;tactile_count_=0;return;}
      if(common(i,f,true,tactile_count_>0||dash_>0||time_<aim_feedback_time_))return;
      for(unsigned n=0;n<tactile_count_;++n){const auto&t=tactile_[n];f.feel(t.pattern,t.strength,t.seconds,t.pan);}tactile_count_=0;
      if(!std::isfinite(input_x_))input_x_=0;if(!std::isfinite(input_y_))input_y_=0;
      if(finished_||room_complete_||transition_>0||!i.connected)return;
      if(std::abs(input_x_)>.15f)facing_=input_x_<0?-1.f:1.f;
      const float aim_magnitude=std::hypot(input_x_,input_y_);
      if(aim_magnitude<.15f)aim_sector_=-1;
      else if(charged_&&aim_magnitude>.25f){const int sector=int(std::floor((std::atan2(input_y_,input_x_)+pi)*4/pi+.5f))%8;
       if(sector!=aim_sector_&&time_>=aim_feedback_time_){aim_sector_=sector;aim_feedback_time_=time_+.08f;f.feel(hui::audio::Tactile::focus,.045f,.018f,input_x_*.6f);}}
      if(i.is_pressed(Action::confirm))jump_buffer_=.13f;
      if((i.released&hui::action_bit(Action::confirm))&&vy_<-260&&dash_<=0){vy_=-260;f.feel(hui::audio::Tactile::touch,.045f,.018f);}
      if(i.is_pressed(Action::page_next)&&charged_){
        float x=std::abs(input_x_)>.25f?input_x_:0,y=std::abs(input_y_)>.25f?input_y_:0;
        const float m=std::hypot(x,y);direction_=m>.1f?Point{x/m,y/m}:Point{facing_,0};
        dash_=.22f;charged_=false;grounded_=false;coyote_=jump_buffer_=0;
        vx_=direction_.x*1180;vy_=direction_.y*1180;++air_dashes_;
        sound(74);f.feel(hui::audio::Tactile::impact,.30f,.065f,direction_.x*.6f);
      }
    }
    void update(float dt)override{
      if(paused_)return;dt=bounded_dt(dt);tick(dt);
      charge_visual_+=((charged_?1.f:0.f)-charge_visual_)*(1-std::exp(-dt*14));landing_glow_=std::max(0.f,landing_glow_-dt);
      gem_glow_=std::max(0.f,gem_glow_-dt);if(finished_||room_complete_)return;
      const float feedback_x=p_.x;const int steps=std::max(1,int(std::ceil(dt/.006f)));const float h=dt/steps;
      for(int s=0;s<steps;++s){
        coyote_=grounded_?.11f:std::max(0.f,coyote_-h);jump_buffer_=std::max(0.f,jump_buffer_-h);
        if(jump_buffer_>0&&coyote_>0&&dash_<=0){vy_=-650;grounded_=false;jump_buffer_=coyote_=0;sound(67);feel(hui::audio::Tactile::rise,.15f,.045f);}
        const bool bursting=dash_>0,was_grounded=grounded_;const float old_bottom=p_.y+15;
        if(bursting){dash_=std::max(0.f,dash_-h);vx_=direction_.x*1180;vy_=direction_.y*1180;}
        else{const float target=input_x_*330;vx_+=(target-vx_)*std::min(1.f,h*(grounded_?18.f:9.f));vy_+=1500*h;}
        const Point before=p_;
        p_.x=std::clamp(p_.x+vx_*h,63.f,1337.f);p_.y+=vy_*h;
        if(bursting&&dash_<=0){vx_*=.35f;vy_*=.15f;}
        if(p_.y<112){p_.y=112;vy_=std::max(0.f,vy_);dash_=0;}
        grounded_=false;const auto&r=rooms[room_];
        // The final rooms are architecture, not one-way floating outlines:
        // columns, roof, undersides and sides share their visible collision.
        auto collide=[&](const Rect& b){
          if(p_.x+13<=b.x||p_.x-13>=b.x+b.w||p_.y+15<=b.y||p_.y-15>=b.y+b.h)return;
          if(before.y+15<=b.y+.5f&&vy_>=0){p_.y=b.y-15;vy_=0;dash_=0;grounded_=true;}
          else if(before.y-15>=b.y+b.h-.5f&&vy_<0){p_.y=b.y+b.h+15;vy_=0;dash_=0;}
          else if(before.x+13<=b.x+.5f&&vx_>0){p_.x=b.x-13;vx_=0;dash_=0;}
          else if(before.x-13>=b.x+b.w-.5f&&vx_<0){p_.x=b.x+b.w+13;vx_=0;dash_=0;}
        };
        if(room_>=3)for(unsigned n=0;n<r.count;++n){const auto&b=r.platforms[n];
          if(room_==4&&n==3)collide({48,b.y,b.x+b.w-48,24});
          else collide({b.x,b.y,b.w,700-b.y});
        }
        if(room_==4)for(const auto& b:final_passage)collide(b);
        for(unsigned n=0;n<r.count;++n){const auto&b=r.platforms[n];
          if(vy_>=0&&old_bottom<=b.y+.5f&&p_.y+15>=b.y&&p_.x+12>b.x&&p_.x-12<b.x+b.w){
            p_.y=b.y-15;vy_=0;grounded_=true;dash_=0;
            break;
          }
        }
        if(grounded_){
          if(!was_grounded){landing_={p_.x,p_.y+15};landing_glow_=.25f;}
          if(!charged_){charged_=true;air_dashes_=0;sound(76);feel(hui::audio::Tactile::touch,.11f,.035f);}
          else if(!was_grounded)feel(hui::audio::Tactile::touch,.07f,.025f);
        }
        if(!gem_taken_&&distance(p_,r.crystal)<(room_>=3?48.f:36.f)){gem_taken_=true;charged_=true;gem_glow_=.65f;sound(79);feel(hui::audio::Tactile::rise,.22f,.085f);}
        bool hit_spike=false;
        auto hazard=[&](const Spikes&b){
          if(p_.x+11<=b.x||p_.x-11>=b.x+b.w||p_.y-14>=b.y||p_.y+14<=b.y-16)return;
          for(float x=b.x;x<b.x+b.w;x+=15){const float half=std::min(15.f,b.x+b.w-x)*.5f,centre=x+half;
            const float near=std::clamp(centre,p_.x-11,p_.x+11);
            const float top=b.y-16+std::min(1.f,std::abs(near-centre)/half)*16;
            if(p_.y+14>top&&p_.y-14<b.y)hit_spike=true;
          }
        };
        if(room_==3)for(const auto&b:teaching_spikes)hazard(b);
        if(room_==4)for(const auto&b:final_spikes)hazard(b);
        if(hit_spike){enter(room_,true);break;}
        if(p_.y>750){enter(room_,true);break;}
        if(grounded_&&std::abs(p_.y+15-r.exit.y)<1&&p_.x>r.exit.x-20){
          sound(84);feel(hui::audio::Tactile::confirm,.28f,.13f);
          room_complete_=true;if(room_+1==rooms.size())finished_=true;
          break;
        }
      }
      motion_haptics_.record(p_.x-feedback_x,0,active_input_&&dash_<=0&&std::abs(input_x_)>.2f);
      trail_[tail_++%trail_.size()]=p_;
    }
    void draw(DrawList&d,hui::ui::Fonts&f,Rect r,Color accent)override{
      Canvas canvas(d,r);const auto&room=rooms[room_];
      static constexpr const char*titles[]={"One jump, one dash","Refill above the gap","Land to restore your dash","Two measured steps","The final ascent"};
      label(d,f,titles[room_],270,54,24,paper);
      // A measured architectural silhouette, not a literal scenic imitation.
      for(unsigned n=0;n<room.count;++n){const auto&b=room.platforms[n];
        if(room_==4&&n==3){d.bordered_rect({48,b.y,b.x+b.w-48,24},0,paper.with_alpha(.085f),2,paper.with_alpha(.65f));continue;}
        d.rounded_rect({b.x,b.y,b.w,700-b.y},0,paper.with_alpha(room_>=3?.085f:.035f));
        d.line(b.x,b.y,b.x+b.w,b.y,3,paper.with_alpha(.8f));
        d.line(b.x,b.y,b.x,b.y+18,1,paper.with_alpha(.25f));d.line(b.x+b.w,b.y,b.x+b.w,b.y+18,1,paper.with_alpha(.25f));
      }
      if(room_>=3){
        d.bordered_rect({48,100,1304,600},0,ink.with_alpha(0),1,paper.with_alpha(.18f));
        d.rounded_rect({48,650,1304,50},0,paper.with_alpha(.06f));
        for(unsigned n=0;n<room.count;++n){const auto&b=room.platforms[n];
          if(room_==4&&n==3)continue;
          for(float y=b.y+40;y<690;y+=40)d.line(b.x+8,y,b.x+b.w-8,y,1,paper.with_alpha(.08f));
          d.line(b.x,b.y,b.x,700,1,paper.with_alpha(.24f));d.line(b.x+b.w,b.y,b.x+b.w,700,1,paper.with_alpha(.24f));
        }
        auto draw_spikes=[&](const Spikes&b){for(float x=b.x;x<b.x+b.w;x+=15)d.triangle({x,b.y-16,std::min(15.f,b.x+b.w-x),16},accent.with_alpha(.9f));};
        if(room_==3)for(const auto&b:teaching_spikes)draw_spikes(b);
        if(room_==4){
          for(const auto&b:final_passage)d.bordered_rect(b,0,paper.with_alpha(.085f),2,paper.with_alpha(.65f));
          for(const auto&b:final_spikes)draw_spikes(b);
          // Tiny directional chevrons mark the upper balcony's reversal.
          d.line(470,269,450,269,1,accent.with_alpha(.55f));d.line(450,269,457,263,1,accent.with_alpha(.55f));
        }
      }
      for(unsigned n=0;n<rooms.size();++n){const float x=52+n*37.f;d.rounded_rect({x,46,26,4},1,n<room_||finished_?accent:n==room_?paper:muted.with_alpha(.25f));}
      // The same diamond means one available dash in the HUD and a refill
      // in the world. A spent dash leaves an outline instead of a text label.
      d.rotated_rect({1284,40,18,18},1,pi*.25f,accent.with_alpha(.18f+.82f*charge_visual_));
      d.ring(1293,49,19,1,accent.with_alpha(.2f+.3f*charge_visual_));
      if(finished_){d.line(680,48,692,60,2,paper);d.line(692,60,716,36,2,paper);}
      if(charged_&&!finished_){
        const float x=std::abs(input_x_)>.25f?input_x_:0,y=std::abs(input_y_)>.25f?input_y_:0,m=std::hypot(x,y);
        const Point aim=m>.1f?Point{x/m,y/m}:Point{facing_,0};
        for(int n=0;n<8;++n){const float from=28+n*25.f,to=from+10;d.line(p_.x+aim.x*from,p_.y+aim.y*from,p_.x+aim.x*to,p_.y+aim.y*to,1,accent.with_alpha(.35f*(1-n/9.f)));}
        const float ex=p_.x+aim.x*236,ey=p_.y+aim.y*236;
        d.line(ex,ey,ex-aim.x*10+aim.y*7,ey-aim.y*10-aim.x*7,1,accent.with_alpha(.4f));
        d.line(ex,ey,ex-aim.x*10-aim.y*7,ey-aim.y*10+aim.x*7,1,accent.with_alpha(.4f));
      }
      if(landing_glow_>0){const float spread=12+(1-landing_glow_/.25f)*28;d.line(landing_.x-spread,landing_.y,landing_.x+spread,landing_.y,2,accent.with_alpha(landing_glow_*2));}
      if(!gem_taken_){const auto b=room.crystal;const float pulse=1+.06f*std::sin(time_*3);
        d.rotated_rect({b.x-12*pulse,b.y-12*pulse,24*pulse,24*pulse},1,pi*.25f,accent);
        d.ring(b.x,b.y,29+std::sin(time_*3),1,accent.with_alpha(.22f));
      }else if(gem_glow_>0){const auto b=room.crystal;d.ring(b.x,b.y,29+(1-gem_glow_/.65f)*48,1,accent.with_alpha(gem_glow_*.4f));}
      const auto exit=room.exit;d.bordered_rect({exit.x-24,exit.y-88,48,88},24,accent.with_alpha(.035f),2,accent.with_alpha(.75f));
      d.line(exit.x-8,exit.y-44,exit.x+9,exit.y-44,1.8f,paper);d.line(exit.x+3,exit.y-50,exit.x+9,exit.y-44,1.8f,paper);d.line(exit.x+3,exit.y-38,exit.x+9,exit.y-44,1.8f,paper);
      if(dash_>0)for(std::size_t n=0;n<trail_.size();++n){const auto b=trail_[(tail_+n)%trail_.size()];d.rounded_rect({b.x-11,b.y-13,22,26},4,accent.with_alpha(.15f*n/trail_.size()));}
      const float squish=grounded_?1.f:dash_>0?.88f:1.04f;
      d.rounded_rect({p_.x-13,p_.y-15*squish,26,30*squish},5,charged_?paper:accent);
      d.circle(p_.x+facing_*5,p_.y-5,2,ink);
      if(!grounded_&&charged_)d.rotated_rect({p_.x-3,p_.y-27,6,6},0,pi*.25f,accent);
      if(transition_>0)d.rounded_rect({0,0,1400,700},0,ink.with_alpha(std::clamp(1-std::abs(transition_-.25f)/.25f,0.f,1.f)));
    }
};

class Rhythm final:public Motion {
 friend struct MotionHapticsInspection;
 friend struct RhythmInspection;
 float clock_=0,judgement_=0;
 const char*result_="READY";
 static constexpr float beat=ExperienceAudio::beat_seconds;
 // The rendered sample clock leads the audible PS5 output by the observed
 // 200 ms. Delay both note positions and judging, without shifting the PCM.
 static constexpr float output_latency=.200f;
 ExperienceAudio*audio_=nullptr;
 float audible_clock()const{return std::max(0.f,float(audio_->time_s())-output_latency);}
 RhythmChart chart_;
 static constexpr std::array<Action,8> actions{Action::left,Action::right,Action::up,Action::down,Action::confirm,Action::back,Action::north,Action::west};
 void judgement(){judgement_=.65f;result_=chart_.award==100?"PERFECT":chart_.award==50?"GOOD":"MISS";}
 static void icon(DrawList&d,hui::ui::Fonts&f,unsigned lane,float x,float y,float size,Color c){
  if(lane>=4){constexpr std::array<hui::ui::Button,4> buttons{hui::ui::Button::cross,hui::ui::Button::circle,hui::ui::Button::triangle,hui::ui::Button::square};hui::ui::draw_button(d,f,hui::ui::GlyphStyle::mono(c,ink),buttons[lane-4],x-size*.5f,y,size);return;}
  // Directional arrows are actual vector silhouettes, not font-dependent text.
  const float dx=lane==0?-1:lane==1?1:0,dy=lane==2?-1:lane==3?1:0;
  const float tipx=x+dx*size*.35f,tipy=y+dy*size*.35f;
  d.line(x-dx*size*.32f,y-dy*size*.32f,tipx,tipy,3,c);
  d.line(tipx,tipy,x+dx*size*.04f-dy*size*.28f,y+dy*size*.04f+dx*size*.28f,3,c);
  d.line(tipx,tipy,x+dx*size*.04f+dy*size*.28f,y+dy*size*.04f-dx*size*.28f,3,c);
 }
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"completed_without_misses",completion()==StudyCompletion::experience_complete&&chart_.hits==RhythmChart::notes.size()&&chart_.misses==0?1u:0u}};}
 Rhythm(){reset();}
 ~Rhythm()override{if(audio_)audio_->stop();}
 void attach_audio(ExperienceAudio*audio)override{if(audio_)audio_->stop();audio_=audio;if(audio_)audio_->start();}
 void reset()override{clear();clock_=judgement_=0;chart_.reset();result_="READY";if(audio_)audio_->start();}
 StudyCompletion completion()const override{return clock_>=beat*RhythmChart::phrase_beats?StudyCompletion::experience_complete:StudyCompletion::playing;}
 const char*help()const override{return "Match each arriving symbol with its controller button on the pulse. Pause to restart or leave.";}
 void handle(const hui::InputFrame&i,hui::ui::Feedback&f)override{
  pending_rumble_=false;
  if(common(i,f,false,true))return;
  if(audio_)clock_=audible_clock();
  if(completion()!=StudyCompletion::playing)return;
  if(chart_.expire(clock_,beat))judgement();
  for(unsigned lane=0;lane<actions.size();++lane)if(i.is_pressed(actions[lane])&&chart_.press(lane,clock_,beat)){
   judgement();flash_=chart_.award? .4f:0;
   // Target sounds are scheduled on the audio sample clock, never as an
   // extra UI-thread beep at the (possibly early/late) button press.
   f.feel(chart_.award?hui::audio::Tactile::confirm:hui::audio::Tactile::error,chart_.award?.13f:.10f,.04f);
  }
 }
 void update(float dt)override{
  if(!active_input_)return;dt=bounded_dt(dt);tick(dt);judgement_=std::max(0.f,judgement_-dt);
  clock_=std::min(audio_?audible_clock():clock_+dt,beat*RhythmChart::phrase_beats);
  if(chart_.expire(clock_,beat))judgement();
 }
 void draw(DrawList&d,hui::ui::Fonts&f,Rect r,Color accent)override{
  Canvas canvas(d,r);
  label(d,f,"SCORE",52,55,19,muted);char score[32];std::snprintf(score,sizeof(score),"%d",chart_.score);label(d,f,score,52,99,36,accent);
  const float phase=clock_/beat-std::floor(clock_/beat),pulse=std::exp(-phase*8);
  // Eight aligned lanes: the receptor row and notes share exactly one icon map.
  for(unsigned lane=0;lane<8;++lane){const float x=245+lane*130.f;
   d.line(x,110,x,545,1,muted.with_alpha(.12f));
   d.rounded_rect({x-43,467,86,86},17,accent.with_alpha(.04f+pulse*.07f));
   icon(d,f,lane,x,510,40,paper.with_alpha(.35f));
  }
  d.line(180,510,1220,510,2,accent.with_alpha(.40f+pulse*.3f));
  for(size_t n=0;n<RhythmChart::notes.size();++n){if(chart_.judged[n])continue;const auto note=RhythmChart::notes[n];
   const float remaining=note.half*beat*.5f-clock_,y=510-remaining*190;
   if(y<125||y>555)continue;const float x=245+note.lane*130.f;
   d.rounded_rect({x-29,y-29,58,58},12,ink);icon(d,f,note.lane,x,y,42,accent);
  }
  if(judgement_>0&&f.regular.font)hui::ui::text(d,f.regular,result_,700,620,34,chart_.award?accent:paper,hui::gfx::Align::center);
  const float progress=std::clamp(clock_/(beat*RhythmChart::phrase_beats),0.f,1.f);
  d.rounded_rect({245,668,910,3},1,muted.with_alpha(.2f));d.rounded_rect({245,668,910*progress,3},1,accent.with_alpha(.7f));
 }
};

class Sequencer final:public Motion {
 friend struct MotionHapticsInspection;
    static constexpr int columns=8,rows=6;
    std::array<unsigned char,columns*rows>tiles_{};int cx_=0,cy_=0,scan_=0,cleared_=0;
    float phase_=0;bool playing_=true;
    static int index(int x,int y){return y*columns+x;}
    void scan(){
        // A square is only erased once the scanner reaches its right edge.
        std::array<bool,columns*rows>erase{};int squares=0;
        if(scan_>0)for(int y=0;y<rows-1;++y){const int a=index(scan_-1,y);const auto tone=tiles_[a];
            if(tone&&tiles_[a+1]==tone&&tiles_[a+columns]==tone&&tiles_[a+columns+1]==tone){
                erase[a]=erase[a+1]=erase[a+columns]=erase[a+columns+1]=true;++squares;}}
        if(squares){cleared_+=squares;for(std::size_t n=0;n<erase.size();++n)if(erase[n])tiles_[n]=0;event(77);}
        else for(int y=0;y<rows;++y)if(tiles_[index(scan_,y)]){sound(notes[static_cast<std::size_t>(rows-1-y)]);break;}
    }
public:
    Sequencer(){reset();}
    void reset()override{clear();tiles_.fill(0);cx_=1;cy_=2;scan_=cleared_=0;phase_=0;playing_=true;
        tiles_[index(1,2)]=tiles_[index(2,2)]=tiles_[index(1,3)]=1;
        tiles_[index(5,1)]=tiles_[index(5,2)]=tiles_[index(6,1)]=2;}
    const char*help()const override{return "D-pad: select a tile   Cross: change colour / erase   Triangle: pause scanner   Square: clear and restart";}
    void handle(const hui::InputFrame&i,hui::ui::Feedback&f)override{
        if(common(i,f))return;
        const int old_x=cx_,old_y=cy_;
        switch(i.nav){case hui::Direction::left:cx_=std::max(0,cx_-1);break;case hui::Direction::right:cx_=std::min(columns-1,cx_+1);break;
            case hui::Direction::up:cy_=std::max(0,cy_-1);break;case hui::Direction::down:cy_=std::min(rows-1,cy_+1);break;default:break;}
        if(old_x!=cx_||old_y!=cy_){motion_haptics_.step(float(cx_-old_x),float(cy_-old_y));motion_haptics_.drain(f,!f.tactile.empty());}
        if(i.is_pressed(Action::confirm)){auto&t=tiles_[index(cx_,cy_)];t=static_cast<unsigned char>((t+1)%3);sound(notes[rows-1-cy_]);f.feel(hui::audio::Tactile::touch,.07f,.035f);}
        if(i.is_pressed(Action::north)){playing_=!playing_;f.feel(playing_?hui::audio::Tactile::confirm:hui::audio::Tactile::back,.07f,.025f);}
    }
    void update(float dt)override{
        if(!active_input_)return;dt=bounded_dt(dt);tick(dt);if(!playing_)return;phase_+=dt;
        while(phase_>=.32f){phase_-=.32f;scan_=(scan_+1)%columns;scan();}
    }
    void draw(DrawList&d,hui::ui::Fonts&f,Rect r,Color accent)override{
        Canvas canvas(d,r);number(d,f,"SQUARES CLEARED %d",cleared_,1050,52,accent);
        constexpr float cell=73,left=408,top=158;
        const Color second=paper;
        for(int y=0;y<rows;++y)for(int x=0;x<columns;++x){const auto t=tiles_[index(x,y)];
            const Rect b{left+x*cell,top+y*cell,cell-5,cell-5};
            d.bordered_rect(b,5,t?(t==1?accent:second):paper.with_alpha(.035f),1,muted.with_alpha(.15f));
            if(t)d.circle(b.cx(),b.cy(),t==1?4.f:9.f,ink.with_alpha(.4f));
            if(x==cx_&&y==cy_)d.bordered_rect({b.x-3,b.y-3,b.w+6,b.h+6},7,Color{0,0,0,0},2,paper);
        }
        const float scanx=left+(scan_+phase_/.32f)*cell;
        d.line(scanx,top-15,scanx,top+rows*cell+4,3,paper.with_alpha(.75f));
        label(d,f,playing_?"PLAYING":"PAUSED",48,650,23,playing_?accent:muted);
    }
};

class Wind final:public Motion {
 friend struct MotionHapticsInspection;
    Point p_{};float vy_=0,breath_=1;int gathered_=0;bool finished_=false,lift_feedback_=false;
    std::array<bool,7>collected_{};
    static constexpr std::array<Point,7>seeds{{{410,340},{790,245},{1170,380},{1550,220},{1930,335},{2310,200},{2690,310}}};
public:
    Wind(){reset();}
    void reset()override{clear();p_={115,370};vy_=0;breath_=1;gathered_=0;finished_=lift_feedback_=false;collected_.fill(false);}
    StudyCompletion completion()const override{return finished_?StudyCompletion::experience_complete:StudyCompletion::playing;}
    const char*help()const override{return "Left stick / D-pad: guide the ribbon   Hold Cross: rise   Rest in an updraft to refill   Square: restart";}
    void handle(const hui::InputFrame&i,hui::ui::Feedback&f)override{if(common(i,f))lift_feedback_=false;}
    void update(float dt)override{
        if(!active_input_)return;dt=bounded_dt(dt);tick(dt);if(finished_)return;const Point before=p_;
        const float updraft=std::max(0.f,std::sin(p_.x*.0052f));
        const bool rising=held_cross_&&breath_>0;
        breath_=std::clamp(breath_+(rising?-.25f:.12f+updraft*.28f)*dt,0.f,1.f);
        vy_+=(input_y_*220+42-updraft*58-(rising?235.f:0.f))*dt;vy_*=std::exp(-2.2f*dt);
        p_.x=std::clamp(p_.x+(110+input_x_*230)*dt,70.f,3150.f);p_.y=std::clamp(p_.y+vy_*dt,155.f,545.f);
        motion_haptics_.record(std::abs(input_x_)>.2f?p_.x-before.x:0,std::abs(input_y_)>.2f?p_.y-before.y:0,std::abs(input_x_)>.2f||std::abs(input_y_)>.2f);
        if(rising!=lift_feedback_&&std::abs(p_.y-before.y)>.0001f){lift_feedback_=rising;pulse(rising?hui::audio::Tactile::rise:hui::audio::Tactile::fall,.08f,.035f);}
        for(std::size_t n=0;n<seeds.size();++n)if(!collected_[n]&&distance(p_,seeds[n])<40){collected_[n]=true;++gathered_;event(notes[n]);}
        if(p_.x>=3060){finished_=true;event(81);}
    }
    void draw(DrawList&d,hui::ui::Fonts&f,Rect r,Color accent)override{
        Canvas canvas(d,r);number(d,f,"LIGHTS %d / 7",gathered_,1150,52,accent);
        const float camera=std::clamp(p_.x-370.f,0.f,1850.f);
        for(int row=0;row<8;++row){float ox=0,oy=0;
            for(int n=0;n<=56;++n){const float x=n*25.f,world=x+camera;
                const float y=190+row*54.f+17*std::sin(world*.005f+row*.51f+time_*.6f);
                if(n)d.line(ox,oy,x,y,1,accent.with_alpha(.06f+.014f*row));ox=x;oy=y;}
        }
        for(int n=0;n<48;++n){float x=std::fmod(n*91.f+time_*43.f-camera*.35f,1400.f);if(x<0)x+=1400;
            const float y=160+std::fmod(n*73.f,430.f)+8*std::sin(time_+n);
            d.line(x,y,x+8,y-2,1,muted.with_alpha(.25f));}
        for(std::size_t n=0;n<seeds.size();++n){const auto b=seeds[n];const float x=b.x-camera;if(x<-60||x>1460)continue;
            d.ring(x,b.y,28+2*std::sin(time_*2+n),1,accent.with_alpha(collected_[n]?.12f:.5f));
            if(!collected_[n])d.circle(x,b.y,6,paper);
        }
        for(int layer=0;layer<3;++layer)for(int n=0;n<40;++n){const float x=n*35.f;
            const float a=590+layer*40.f+18*std::sin((x+camera*(.3f+layer*.2f))*.004f+layer);
            const float b=590+layer*40.f+18*std::sin((x+35+camera*(.3f+layer*.2f))*.004f+layer);
            d.line(x,a,x+35,b,2,muted.with_alpha(.12f));}
        const float x=p_.x-camera;
        for(int n=11;n>=0;--n){const float px=x-n*7.f,py=p_.y+std::sin(time_*6-n*.45f)*n*.7f;
            d.circle(px,py,std::max(1.5f,7.f-n*.45f),accent.with_alpha(1.f-n*.065f));}
        d.circle(x,p_.y,8,paper);d.arc(x,p_.y,20,2,-pi*.5f,2*pi*breath_,accent);
        label(d,f,"LIFT",48,650,22,muted);d.rounded_rect({115,634,180,5},2,muted.with_alpha(.2f));
        d.rounded_rect({115,634,180*breath_,5},2,accent);
        d.ring(3070-camera,310,70,2,accent.with_alpha(.45f));
    }
};
} // namespace

std::unique_ptr<Study> make_study_motion(const std::string&key){
    if(key=="jump")return std::make_unique<Jump>();
    if(key=="dash")return std::make_unique<Dash>();
    if(key=="rhythm")return std::make_unique<Rhythm>();
    if(key=="sequencer")return std::make_unique<Sequencer>();
    if(key=="wind")return std::make_unique<Wind>();
    return {};
}
} // namespace museum
