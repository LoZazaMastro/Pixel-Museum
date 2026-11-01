// Pixel Museum - original workshops, not replicas of commercial games.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study_workshops.hpp"
#include "museum/haptic_interactions.hpp"
#include "museum/pixel_palette.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
namespace museum {
struct WorkshopInspection;
namespace {
using hui::Action;using hui::Direction;using hui::InputFrame;
using hui::gfx::Color;using hui::gfx::Rect;using hui::gfx::DrawList;using hui::gfx::Align;
using hui::ui::Fonts;using hui::ui::Feedback;
constexpr Color paper{.945f,.937f,.906f,1},ink{.10f,.13f,.115f,1},muted{.39f,.42f,.39f,1};
float finite(float n){return std::isfinite(n)?n:0.f;}
float step(float dt){return std::clamp(finite(dt),0.f,.05f);}
float axis(const InputFrame&i){if(std::abs(finite(i.stick_x))>.02f)return std::clamp(i.stick_x,-1.f,1.f);return float(i.is_held(Action::right))-float(i.is_held(Action::left));}
class Workshop:public Study {
protected:
 AcceptedMotionHaptics movement_;
 float time_=0,rumble_=0,flash_=0;bool paused_=false;
 void clean(){movement_.reset();time_=rumble_=flash_=0;paused_=false;note_=-1;}
 bool input(const InputFrame&i,Feedback&f){paused_=i.focus_lost||!i.connected;if(paused_){movement_.reset();rumble_=0;return false;}
  movement_.drain(f,rumble_>0);
  if(rumble_>0){f.feel(hui::audio::Tactile::impact,rumble_,.055f);rumble_=0;}
  if(i.is_pressed(Action::west)){reset();f.feel(hui::audio::Tactile::back,.07f,.04f);return false;}return true;}
 float clock(float dt){if(paused_)return 0;dt=step(dt);movement_.advance(dt);time_+=dt;flash_=std::max(0.f,flash_-dt);return dt;}
 void event(int note,float strength=.10f){sound(note);rumble_=std::max(rumble_,strength);flash_=.5f;}
 bool begin(DrawList&l,Fonts&f,Rect r,Color a,const char*label,const char*title){if(r.w<1||r.h<1)return false;
  l.push_clip(r);l.rounded_rect(r,0,paper);float s=std::min(r.w/1000.f,r.h/540.f);
  l.push_transform(s,0,0,r.x+(r.w-1000*s)*.5f,r.y+(r.h-540*s)*.5f);
  hui::ui::text(l,f.mono,label,40,43,12,muted,Align::left,1.4f);
  hui::ui::text(l,f.display,title,39,86,30,ink);
  l.line(40,108,960,108,.8f,ink.with_alpha(.14f));l.rounded_rect({40,130,640,330},2,ink.with_alpha(.035f));
  if(flash_>0)l.line(40,108,40+920*std::min(1.f,flash_*2),108,1.5f,a.with_alpha(flash_));return true;}
 void end(DrawList&l){l.pop_transform();l.pop_clip();}
 void panel(DrawList&l,Fonts&f,Color a,const char*label,const char*value,const char*body){
  hui::ui::text(l,f.mono,label,732,157,12,muted,Align::left,.8f);hui::ui::text(l,f.display,value,728,209,38,a);
  hui::ui::paragraph(l,f.regular,body,732,248,17,220,22,ink,99);}
 void footer(DrawList&l,Fonts&f,const char*body){hui::ui::paragraph(l,f.regular,body,40,495,16,920,22,muted,2);}
};

// The same objects and controls acquire a different meaning when the program
// changes. Both programs keep their own results while sharing the playfield.
class CartridgeRules final:public Workshop {
 friend struct museum::WorkshopInspection;
 struct Tile{float x=0,y=0;bool active=false;};std::array<Tile,12>tiles_{};
 float player_=320,control_=0,spawn_=0,blend_=0;int mode_=0,serial_=0;
 std::array<int,2>correct_{},mistakes_{};
public:
 CartridgeRules(){reset();}
 void reset()override{clean();tiles_={};player_=320;control_=spawn_=blend_=0;mode_=serial_=0;correct_={};mistakes_={};}
 const char*help()const override{return "Move to catch a light in Collect. In Avoid, let the same light pass. Cross swaps programs; test eight correct decisions in each. Touchpad also moves the catcher. Square restarts.";}
 void handle(const InputFrame&i,Feedback&f)override{control_=0;if(!input(i,f))return;control_=axis(i);
  if(i.touch.available&&i.touch.count){player_=std::clamp(finite(i.touch.points[0].x)*640,22.f,618.f);control_=0;}
  if(i.is_pressed(Action::confirm)){mode_=1-mode_;event(62+mode_*5,.08f);}}
 void update(float dt)override{dt=clock(dt);if(dt<=0)return;blend_+=(float(mode_)-blend_)*std::min(1.f,dt*9);player_=std::clamp(player_+control_*330*dt,22.f,618.f);
  spawn_-=dt;if(spawn_<=0){for(auto&t:tiles_)if(!t.active){const int n=serial_++;t={45.f+float((n*137+79)%550),-10,true};break;}spawn_=.82f;}
  for(auto&t:tiles_)if(t.active){t.y+=(82+float(serial_%3)*9)*dt;if(t.y>=291&&t.y<312&&std::abs(t.x-player_)<29){t.active=false;if(mode_==0){++correct_[0];event(69,.10f);}else{++mistakes_[1];event(48,.17f);}}
   else if(t.y>326){t.active=false;if(mode_==1){++correct_[1];event(65,.06f);}else{++mistakes_[0];event(50,.08f);}}}}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{if(!begin(l,f,r,a,"JERRY LAWSON / PROGRAMS AND RULES","Same machine. A different game."))return;
  l.line(40,436,680,436,1,ink.with_alpha(.2f));for(const auto&t:tiles_)if(t.active){l.circle(40+t.x,130+t.y,7,a.with_alpha(.9f-.25f*blend_));l.circle(40+t.x,130+t.y,13,a.with_alpha(.08f));}
  l.rounded_rect({40+player_-24,424,48,8},3,ink);l.line(40+player_,434,40+player_,447,1,a);
  const char*names[]={"COLLECT","AVOID"};for(int n=0;n<2;++n){const float y=346+n*55.f;const float focus=1-std::abs(float(n)-blend_);
   l.bordered_rect({732,y,220,43},3,a.with_alpha(.04f+.12f*focus),.8f,ink.with_alpha(.2f+.35f*focus));
   hui::ui::text(l,f.mono,names[n],746,y+27,14,ink);char count[24];hui::ui::format(count,"%d / 8",std::min(8,correct_[size_t(n)]));hui::ui::text(l,f.mono,count,938,y+27,14,a,Align::right);}
  char score[32];hui::ui::format(score,"%02d / 08",std::min(8,correct_[size_t(mode_)]));panel(l,f,a,"CURRENT PROGRAM",score,correct_[0]>=8&&correct_[1]>=8?"Both programs passed. Try swapping rules in the middle of a falling pattern.":mode_==0?"Catch each light. Swap programs to make the same contact a mistake.":"Let eight lights pass untouched. Swap back to make contact useful.");
  char results[1024];hui::ui::format(results,"Collect: %d caught, %d missed. Avoid: %d passed, %d contacts. Exchange programs to compare the same movement under a different rule.",correct_[0],mistakes_[0],correct_[1],mistakes_[1]);footer(l,f,results);end(l);}
};

// Costs are explicitly illustrative design units, not measurements or a
// simulated specification of a historical handheld.
class PocketBudget final:public Workshop {
 friend struct museum::WorkshopInspection;
 std::array<int,4>choice_{1,1,1,0};int selected_=0,brief_=0,sound_tick_=-1;unsigned completed_=0;float highlight_=0,cost_display_=0;std::string message_;bool brief_complete_=false;
 int cost()const{constexpr int colours[]={12,24,50},speed[]={10,18,32,50},light[]={6,14,26,42};return colours[choice_[0]]+speed[choice_[1]]+light[choice_[2]]+choice_[3]*12;}
 bool fits()const{return brief_==0?choice_[2]>=2&&choice_[1]>=1&&cost()<=100:brief_==1?choice_[1]>=2&&choice_[0]>=1&&cost()<=100:cost()<=58&&choice_[0]>=1&&choice_[1]>=1;}
 void change(int delta){const int high=selected_==0?2:selected_==3?1:3;int before=choice_[size_t(selected_)];choice_[size_t(selected_)]=std::clamp(before+delta,0,high);if(before!=choice_[size_t(selected_)]){event(60+selected_*2,.035f);message_.clear();}}
public:
 PocketBudget(){reset();}void reset()override{clean();choice_={1,1,1,0};selected_=brief_=0;sound_tick_=-1;completed_=0;highlight_=0;cost_display_=float(cost());message_.clear();brief_complete_=false;}
 StudyCompletion completion()const override{return !brief_complete_?StudyCompletion::playing:brief_==2?StudyCompletion::experience_complete:StudyCompletion::level_complete;}
 int level_number()const override{return brief_+1;}
 int level_count()const override{return 3;}
 void continue_level()override{if(!brief_complete_)return;if(brief_==2)reset();else{++brief_;brief_complete_=false;message_.clear();}}
 const char*help()const override{return "Choose a design decision with Up/Down and change it with Left/Right. Cross tests the current brief. The touchpad selects a row and tunes its value. Complete three briefs inside their budgets. Costs use an illustrative design budget.";}
 void handle(const InputFrame&i,Feedback&f)override{if(!input(i,f))return;
  const int before_selection=selected_;
  if(i.nav==Direction::up)selected_=std::max(0,selected_-1);if(i.nav==Direction::down)selected_=std::min(3,selected_+1);if(i.nav==Direction::left)change(-1);if(i.nav==Direction::right)change(1);
  if(i.touch.available&&i.touch.count){const auto&p=i.touch.points[0];selected_=std::clamp(int(finite(p.y)*4),0,3);int high=selected_==0?2:selected_==3?1:3;const int value=std::clamp(int(std::round(finite(p.x)*high)),0,high);if(choice_[size_t(selected_)]!=value)change(value-choice_[size_t(selected_)]);}
  if(selected_!=before_selection){movement_.step(0,float(selected_-before_selection));movement_.drain(f,rumble_>0);}
  if(i.is_pressed(Action::confirm)){if(fits()){completed_|=1u<<brief_;brief_complete_=true;event(77,.12f);message_="Brief passed. Continue when you are ready.";}else{event(50,.08f);message_="The prototype misses the brief. Compare its requirements with your choices.";}}}
 void update(float dt)override{dt=clock(dt);if(dt<=0)return;highlight_+=(float(selected_)-highlight_)*std::min(1.f,dt*12);cost_display_+=(float(cost())-cost_display_)*std::min(1.f,dt*7);
  const int tick=int(time_/.65f);if(tick!=sound_tick_){sound_tick_=tick;if(choice_[3]){constexpr int notes[]={62,65,69,72};sound(notes[tick%4]);}}}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{if(!begin(l,f,r,a,"GUNPEI YOKOI / DESIGN WITHIN A LIMIT","What does a pocket need?"))return;
  const char*labels[]={"SHADES","MOTION","LIGHT","SOUND"};l.rounded_rect({54,145+highlight_*54,278,45},3,a.with_alpha(.10f));
  for(int n=0;n<4;++n){float y=174+n*54.f;hui::ui::text(l,f.mono,labels[n],67,y,13,ink);int steps=n==0?3:n==3?2:4;for(int k=0;k<steps;++k)l.rounded_rect({189+k*29.f,y-17,20,20},2,k<=choice_[size_t(n)]?a:ink.with_alpha(.09f));}
  l.bordered_rect({365,157,285,214},6,ink.with_alpha(.05f),1,ink.with_alpha(.2f));
  const int shades=choice_[0]==0?2:choice_[0]==1?4:16;const float rate=2+choice_[1]*5.f,t=std::floor(time_*rate)/rate;
  for(int n=0;n<8;++n){float x=390+float(n%4)*63+std::sin(t*.8f+n)*5,y=190+float(n/4)*88;float opacity=(.19f+.7f*float(n%shades)/float(shades))* (.45f+.15f*choice_[2]);
   l.rounded_rect({x,y,34,34},float(n%3)*8,ink.with_alpha(opacity));if(choice_[3])l.circle(x+17,y+51,2+std::sin(time_*2+n),a.with_alpha(.5f));}
  hui::ui::text(l,f.mono,"PROTOTYPE",507,400,12,muted,Align::center,1);l.rounded_rect({365,423,285,9},3,ink.with_alpha(.1f));l.rounded_rect({365,423,285*std::clamp(cost_display_/120,0.f,1.f),9},3,a);
  const char*briefs[]={"OUTSIDE","MOVEMENT","LONG SESSION"};char value[32];hui::ui::format(value,"%d / %d",cost(),brief_==2?58:100);panel(l,f,a,briefs[brief_],value,completed_==7?"Three briefs passed. A useful design balances what it can show with what it can afford.":brief_==0?"Use light level 3 or 4 and motion level 2 or more. Stay within 100 design units.":brief_==1?"Use motion level 3 or 4 and at least four shades. Stay within 100 design units.":"Keep four shades and motion level 2 or more, using no more than 58 design units.");
  for(int n=0;n<3;++n)l.circle(746+n*31.f,431,7,(completed_&(1u<<n))?a:ink.with_alpha(.12f));
  footer(l,f,message_.empty()?"Illustrative design units. Build three prototypes for three different priorities.":message_.c_str());end(l);}
};

class AdaptivePulse final:public Workshop {
 friend struct museum::WorkshopInspection;
 struct Platform{float left,right;};static constexpr std::array<Platform,5>ground_={{{0,330},{420,760},{850,1200},{1320,1650},{1740,2200}}};
 float x_=75,y_=270,vy_=0,move_=0,run_=0,camera_=0,jump_age_=0,jump_buffer_=0,coyote_=0;bool grounded_=true,jump_=false,held_=false;int tick_=-1,pace_=0;
 int density()const{return std::abs(move_)<.05f?4:run_>.3f?1:2;}
public:
 AdaptivePulse(){reset();}void reset()override{clean();x_=75;y_=270;vy_=move_=run_=camera_=jump_age_=jump_buffer_=coyote_=0;grounded_=true;jump_=held_=false;tick_=-1;pace_=0;}
 StudyCompletion completion()const override{return x_>=2110?StudyCompletion::experience_complete:StudyCompletion::playing;}
 const char*help()const override{return "Move along the route and hear the original phrase adapt to rest, walking and running. R2 increases your pace; Cross jumps, and holding it extends the arc. Every gap is reachable at walking speed. Touchpad position can set the pace. Reach the flag. Square restarts.";}
 void handle(const InputFrame&i,Feedback&f)override{move_=run_=0;jump_=held_=false;if(!input(i,f))return;move_=axis(i);run_=std::clamp(finite(i.trigger_r),0.f,1.f);jump_=i.is_pressed(Action::confirm);held_=i.is_held(Action::confirm);
  if(i.touch.available&&i.touch.count)move_=std::clamp((finite(i.touch.points[0].x)-.5f)*2,-1.f,1.f);}
 void update(float dt)override{dt=clock(dt);if(dt<=0)return;const int beat=int(time_/.1875f);if(beat!=tick_){tick_=beat;if(beat%density()==0){constexpr int roots[]={50,58,53,48},notes[]={62,65,69,72,69,65,64,69};sound(beat%4==0?roots[(beat/16)%4]:notes[beat%8]+(density()==1?12:0));}}
  jump_buffer_=jump_?.12f:std::max(0.f,jump_buffer_-dt);coyote_=grounded_?.10f:std::max(0.f,coyote_-dt);
  if(jump_buffer_>0&&coyote_>0){vy_=-390;grounded_=false;jump_age_=0;jump_buffer_=coyote_=0;event(74,.055f);}jump_=false;
  jump_age_+=dt;const float previous=y_,before_x=x_;const bool was_grounded=grounded_;x_=std::clamp(x_+move_*(180+run_*100)*dt,12.f,2160.f);movement_.record(x_-before_x,0,std::abs(move_)>.15f);const int pace=int(run_*3);if(std::abs(x_-before_x)>.0001f&&pace!=pace_){pace_=pace;event(62+pace,.025f);}
  // A short press must still clear the route. Holding extends the arc;
  // running changes its pace, without being a hidden requirement to finish.
  if(!held_&&jump_age_>=.10f&&vy_<-270){vy_=-270;rumble_=std::max(rumble_,.06f);}y_+=vy_*dt+400*dt*dt;vy_+=800*dt;grounded_=false;
  for(const auto&p:ground_)if(x_>=p.left&&x_<=p.right&&previous<=270.5f&&y_>=270&&vy_>=0){y_=270;vy_=0;grounded_=true;break;}
  if(grounded_&&!was_grounded&&vy_==0)event(65,.045f);
  if(y_>420){x_=75;y_=270;vy_=jump_age_=jump_buffer_=coyote_=0;grounded_=true;event(48,.13f);}
  camera_+=(std::clamp(x_-255,0.f,1560.f)-camera_)*std::min(1.f,dt*6);}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{if(!begin(l,f,r,a,"KOJI KONDO / FUNCTIONAL MUSICAL DESIGN","Let movement change the phrase."))return;
  l.push_clip({40,130,640,330});for(const auto&p:ground_){float left=40+p.left-camera_,right=40+p.right-camera_;l.rounded_rect({left,419,right-left,8},2,ink.with_alpha(.38f));}
  float px=40+x_-camera_;l.circle(px,140+y_,9,ink);l.circle(px,140+y_,14,a.with_alpha(.12f));
  l.line(40+2110-camera_,320,40+2110-camera_,419,1.2f,a);l.triangle({40+2110-camera_,320,24,18},a);l.pop_clip();
  for(int n=0;n<16;++n){float x=56+n*38.f;const bool voice=n%density()==0;float pulse=1-std::clamp((time_/.1875f-float(tick_)),0.f,1.f);l.circle(x,164,voice?4+((tick_%16)==n?pulse*5:0):2,voice?a:ink.with_alpha(.15f));}
  panel(l,f,a,"","",x_>=2080?"The route is complete. Rest, walking and running share one continuing musical clock.":density()==4?"Rest: the phrase leaves space. Start walking to add notes without restarting the clock.":density()==2?"Walking adds a second pulse. Run, then jump across the gaps.":"Running adds a quicker subdivision. The phrase follows your action, keeping its place in the bar.");
  footer(l,f,"An original D-minor phrase follows your action, keeping one continuing musical clock.");end(l);}
};

class JumpLab final:public Workshop {
 friend struct museum::WorkshopInspection;
 struct V{float x=0,y=0;};struct Platform{float x,w,y;};static constexpr std::array<Platform,4>platforms_={{{0,170,300},{240,105,190},{410,100,115},{565,75,65}}};
 std::array<float,3>tuning_{.48f,.52f,.65f};float field_=0,x_=72,y_=286,vx_=0,vy_=0,move_=0,trace_clock_=0,takeoff_x_=0,takeoff_y_=0,peak_=0,last_height_=0,last_reach_=0;
 int selected_=0,checkpoint_=0,landings_=0;bool grounded_=true,jump_=false,held_=false,landing_complete_=false;
 std::array<V,120>trace_{},ghost_{};unsigned trace_count_=0,ghost_count_=0;
 float gravity()const{return 560+tuning_[0]*640;}float impulse()const{return 265+tuning_[1]*210;}float speed()const{return 120+tuning_[2]*120;}
 void alter(float amount){tuning_[size_t(selected_)]=std::clamp(tuning_[size_t(selected_)]+amount,0.f,1.f);event(60+selected_*3,.035f);}
public:
 JumpLab(){reset();}void reset()override{clean();tuning_={.48f,.52f,.65f};field_=0;x_=72;y_=286;vx_=vy_=move_=trace_clock_=takeoff_x_=takeoff_y_=peak_=last_height_=last_reach_=0;selected_=checkpoint_=landings_=0;grounded_=true;jump_=held_=landing_complete_=false;trace_count_=ghost_count_=0;}
 StudyCompletion completion()const override{return !landing_complete_?StudyCompletion::playing:checkpoint_==3?StudyCompletion::experience_complete:StudyCompletion::level_complete;}
 int level_number()const override{return std::max(1,checkpoint_);}
 int level_count()const override{return 3;}
 void continue_level()override{if(!landing_complete_)return;if(checkpoint_==3)reset();else{landing_complete_=false;move_=vx_=0;jump_=held_=false;}}
 const char*help()const override{return "Use the left stick to move and Cross to jump; release Cross for a shorter arc. L1/R1 choose a parameter; D-pad Left/Right tunes it. The touchpad tunes the selected parameter. The first ledge is above the default jump: increase lift or reduce gravity. Reach three flags and compare trajectories. Square resets.";}
 void handle(const InputFrame&i,Feedback&f)override{move_=0;jump_=held_=false;if(!input(i,f))return;move_=std::clamp(finite(i.stick_x),-1.f,1.f);jump_=i.is_pressed(Action::confirm);held_=i.is_held(Action::confirm);
  if(i.is_pressed(Action::page_prev)){selected_=(selected_+2)%3;f.feel(hui::audio::Tactile::focus,.07f,.025f,-.5f);}if(i.is_pressed(Action::page_next)){selected_=(selected_+1)%3;f.feel(hui::audio::Tactile::focus,.07f,.025f,.5f);}
  if(!i.nav_from_stick&&i.nav==Direction::left)alter(-.05f);if(!i.nav_from_stick&&i.nav==Direction::right)alter(.05f);
  if(i.touch.available&&i.touch.count){const float n=std::clamp(finite(i.touch.points[0].x),0.f,1.f);if(std::abs(tuning_[size_t(selected_)]-n)>.015f)alter(n-tuning_[size_t(selected_)]);}}
 void update(float dt)override{dt=clock(dt);if(dt<=0)return;field_+=(float(selected_)-field_)*std::min(1.f,dt*10);
  if(jump_&&grounded_){vy_=-impulse();grounded_=false;trace_count_=0;trace_clock_=0;takeoff_x_=x_;takeoff_y_=peak_=y_;event(72,.045f);}jump_=false;
  const float before_x=x_;const float old_y=y_;const bool was_grounded=grounded_;vx_+=(move_*speed()-vx_)*std::min(1.f,dt*(grounded_?18:5+9*tuning_[2]));x_=std::clamp(x_+vx_*dt,10.f,630.f);movement_.record(x_-before_x,0,std::abs(move_)>.15f);
  if(!held_&&vy_<-105){vy_=-105;rumble_=std::max(rumble_,.06f);}vy_+=gravity()*dt;y_+=vy_*dt;if(y_<-8){y_=-8;vy_=std::max(0.f,vy_);rumble_=std::max(rumble_,.09f);}grounded_=false;
  for(unsigned n=0;n<platforms_.size();++n){const auto&p=platforms_[n];if(vy_>=0&&old_y+14<=p.y+.7f&&y_+14>=p.y&&x_+7>=p.x&&x_-7<=p.x+p.w){y_=p.y-14;vy_=0;grounded_=true;
    if(trace_count_>1){ghost_=trace_;ghost_count_=trace_count_;trace_count_=0;last_height_=takeoff_y_-peak_;last_reach_=std::abs(x_-takeoff_x_);event(65,.065f);}else if(!was_grounded)rumble_=std::max(rumble_,.065f);if(int(n)>checkpoint_){checkpoint_=int(n);landings_=checkpoint_;landing_complete_=true;event(77,.13f);}break;}}
  if(!grounded_){peak_=std::min(peak_,y_);trace_clock_+=dt;if(trace_clock_>=.02f&&trace_count_<trace_.size()){trace_clock_=0;trace_[trace_count_++]={x_,y_};}}
  if(y_>420){const auto&p=platforms_[size_t(checkpoint_)];x_=p.x+30;y_=p.y-14;vx_=vy_=0;grounded_=true;trace_count_=0;event(48,.12f);}}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{if(!begin(l,f,r,a,"SHIGERU MIYAMOTO / THE DESIGN OF GAME FEEL","Keep the landing. Change the curve."))return;
  l.push_clip({40,130,640,330});for(unsigned n=1;n<ghost_count_;++n)l.line(40+ghost_[n-1].x,150+ghost_[n-1].y,40+ghost_[n].x,150+ghost_[n].y,1,ink.with_alpha(.15f));
  for(unsigned n=0;n<platforms_.size();++n){const auto&p=platforms_[n];l.rounded_rect({40+p.x,150+p.y,p.w,7},2,ink.with_alpha(.42f));if(n){float x=40+p.x+p.w-13;l.line(x,150+p.y-42,x,150+p.y,1,a.with_alpha(n<=unsigned(checkpoint_)?1:.3f));l.triangle({x,150+p.y-42,16,12},a.with_alpha(n<=unsigned(checkpoint_)?1:.3f));}}
  l.rounded_rect({40+x_-8,150+y_-12,16,25},4,ink);l.pop_clip();
  const char*labels[]={"GRAVITY","LIFT","AIR CONTROL"};l.rounded_rect({722,328+field_*43,237,36},2,a.with_alpha(.10f));
  for(int n=0;n<3;++n){float y=352+n*43.f;hui::ui::text(l,f.mono,labels[n],733,y,12,ink);l.line(855,y-5,943,y-5,2,ink.with_alpha(.16f));l.circle(855+tuning_[size_t(n)]*88,y-5,4,a);}
  char value[24];hui::ui::format(value,"%d / 3",landings_);panel(l,f,a,"LANDINGS",value,landings_==3?"Three flags reached. Compare the pale trace with your next combination of settings.":"Reach three flags. Compare the pale trace of a landing with your next attempt.");
  char summary[1024];if(last_height_>0)hui::ui::format(summary,"Last jump: %.0f units high, %.0f units across. The trace is a comparison, not a prescribed answer.",last_height_,last_reach_);else hui::ui::format(summary,"Try a short tap and a held jump. Tune one property at a time; the pale trace keeps the comparison visible.");footer(l,f,summary);end(l);}
};
// A drawing, not a reproduction of commercial character artwork. The large
// grid and the uninterrupted preview show how a single shade changes an edge.
class PixelDrawing final:public Workshop {
 friend struct museum::WorkshopInspection;
 // The supplied 64-entry NES palette, deduplicated and ordered by hue/lightness.
 // White is reserved for the canvas and eraser, never a selectable brush.
 static constexpr auto palette_=museum::pixel_palette::colours;
 std::array<std::uint16_t,256>cells_{};int x_=0,y_=0,brush_=0;bool grid_=true;float cursor_x_=0,cursor_y_=0;
 int brush_hold_=0;float brush_repeat_=0;
 void paint(int index,int colour){if(cells_[size_t(index)]==colour)return;cells_[size_t(index)]=static_cast<std::uint16_t>(colour);event(60+brush_%12,.025f);}
 int changes()const{int n=0;for(auto c:cells_)n+=c!=0;return n;}
public:
 PixelDrawing(){reset();}
 void reset()override{clean();cells_.fill(0);x_=y_=brush_=0;grid_=true;cursor_x_=cursor_y_=0;brush_hold_=0;brush_repeat_=0;}
 const char*help()const override{return "Start with a white 16-by-16 canvas. Choose a pixel, draw with the selected colour, or erase it to white. Hold L1/R1 to browse the NES-inspired palette; sixteen colours are visible at once. White is available only through the eraser. Triangle clears the canvas. The touchpad is not used.";}
 void handle(const InputFrame&i,Feedback&f)override{
  paused_=i.focus_lost||!i.connected;if(paused_){movement_.reset();rumble_=0;brush_hold_=0;brush_repeat_=0;return;}
  movement_.drain(f,rumble_>0);
  if(rumble_>0){f.feel(hui::audio::Tactile::touch,rumble_,.035f);rumble_=0;}
  if(i.is_pressed(Action::north)){const bool changed=changes()!=0||!grid_||x_||y_||brush_;reset();if(changed)f.feel(hui::audio::Tactile::back,.07f,.025f);return;}
  if(i.is_pressed(Action::west)){grid_=!grid_;event(65,.02f);}
  const int previous_x=x_,previous_y=y_,previous_brush=brush_;
  if(i.nav==Direction::left)x_=std::max(0,x_-1);if(i.nav==Direction::right)x_=std::min(15,x_+1);
  if(i.nav==Direction::up)y_=std::max(0,y_-1);if(i.nav==Direction::down)y_=std::min(15,y_+1);
  const bool previous=i.is_held(Action::page_prev)||i.is_pressed(Action::page_prev);
  const bool next=i.is_held(Action::page_next)||i.is_pressed(Action::page_next);
  const int direction=int(next)-int(previous);
  if(!direction){brush_hold_=0;brush_repeat_=0;}
  else if(direction!=brush_hold_||i.is_pressed(direction>0?Action::page_next:Action::page_prev)){
   brush_=(brush_+direction+int(palette_.size()))%int(palette_.size());brush_hold_=direction;brush_repeat_=.28f;
  }else if(brush_repeat_<=0){brush_=(brush_+direction+int(palette_.size()))%int(palette_.size());brush_repeat_+=.075f;}
  if(previous_brush!=brush_)f.feel(hui::audio::Tactile::focus,.055f,.025f);
  if(i.is_pressed(Action::confirm))paint(y_*16+x_,brush_+1);
  if(i.is_pressed(Action::back))paint(y_*16+x_,0);
  if(x_!=previous_x||y_!=previous_y){movement_.step(float(x_-previous_x),float(y_-previous_y));movement_.drain(f,rumble_>0);}
 }
 void update(float dt)override{dt=clock(dt);if(brush_hold_)brush_repeat_-=dt;cursor_x_+=(float(x_)-cursor_x_)*std::min(1.f,dt*18);cursor_y_+=(float(y_)-cursor_y_)*std::min(1.f,dt*18);}
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(!begin(l,f,r,a,"PIXEL ART / NES-INSPIRED COLOURS","Make one square matter."))return;
  constexpr float preview_centre=524,large_top=148,large_side=160,small_top=354,small_side=64,label_gap=24;
  for(int n=0;n<256;++n){const int colour=cells_[size_t(n)];const Color c=Color::rgb(colour?palette_[size_t(colour-1)]:0xffffff);
   l.rounded_rect({73+float(n%16)*19,143+float(n/16)*19,19,19},0,c);
   l.rounded_rect({preview_centre-large_side*.5f+float(n%16)*10,large_top+float(n/16)*10,10,10},0,c);
   l.rounded_rect({preview_centre-small_side*.5f+float(n%16)*4,small_top+float(n/16)*4,4,4},0,c);
  }
  if(grid_)for(int n=0;n<=16;++n){const float x=73+n*19.f,y=143+n*19.f;
   l.line(x,143,x,447,1.6f,ink.with_alpha(.45f));l.line(73,y,377,y,1.6f,ink.with_alpha(.45f));
   l.line(x,143,x,447,.6f,paper.with_alpha(.8f));l.line(73,y,377,y,.6f,paper.with_alpha(.8f));
  }
  l.bordered_rect({73+cursor_x_*19,143+cursor_y_*19,19,19},0,Color{0,0,0,0},2,a);
  hui::ui::text(l,f.mono,"WITHOUT THE GRID",preview_centre,large_top+large_side+label_gap,10,muted,Align::center,.7f);
  hui::ui::text(l,f.mono,"AT A GLANCE",preview_centre,small_top+small_side+label_gap,10,muted,Align::center,.7f);
  char value[24];hui::ui::format(value,"%d / %d",brush_+1,int(palette_.size()));
  hui::ui::text(l,f.mono,"COLOUR",732,157,12,muted,Align::left,.8f);
  hui::ui::text(l,f.display,value,728,209,38,a);
  const int first=std::min((brush_/16)*16,std::max(0,int(palette_.size())-16));
  for(int n=0;n<16&&first+n<int(palette_.size());++n){const float px=735+(n%4)*52.f,py=240+(n/4)*52.f;l.rounded_rect({px,py,40,40},1,Color::rgb(palette_[size_t(first+n)]));if(brush_==first+n)l.bordered_rect({px-3,py-3,46,46},2,Color{0,0,0,0},2,a);}
  end(l);
 }
};

}
std::unique_ptr<Study> make_study_workshops(const std::string&id){
 if(id=="pixels")return std::make_unique<PixelDrawing>();
 if(id=="cartridge-rules")return std::make_unique<CartridgeRules>();
 if(id=="pocket-budget")return std::make_unique<PocketBudget>();
 if(id=="adaptive-pulse")return std::make_unique<AdaptivePulse>();
 if(id=="jump-lab")return std::make_unique<JumpLab>();
 return {};
}
}
