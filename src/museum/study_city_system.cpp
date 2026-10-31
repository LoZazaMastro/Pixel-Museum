// Pixel Museum - original design study, not a recreation of SimCity.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study_city_system.hpp"
#include "museum/haptic_interactions.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
namespace museum {
struct CitySystemInspection;
namespace {
using hui::Action;using hui::Direction;using hui::InputFrame;
using hui::gfx::Color;using hui::gfx::Rect;using hui::gfx::DrawList;using hui::gfx::Align;
using hui::ui::Fonts;using hui::ui::Feedback;
constexpr int width=16,height=10,count=width*height;
constexpr Color paper{.945f,.937f,.906f,1},ink{.12f,.15f,.135f,1};
float sane(float v){return std::isfinite(v)?v:0.f;}
float ease(float t){return t*t*(3-2*t);}
struct Cell {unsigned char kind=0;float road=0,green=0;}; // empty, road, green
struct Route {std::array<int,count>cells{};int size=0;};
struct Board {
 std::array<Cell,count>cells{};std::array<bool,count>blocked{};
 std::array<int,3>homes{};std::array<int,2>jobs{};int clinic=0,budget=58;
 std::array<Route,3>routes{};std::array<int,count>load{};
 int cost=0,work=0,care=0,green=0,peak=0,jobs_connected=0;float mean=0;
};
class CitySystem final:public Study {
 AcceptedMotionHaptics movement_;
 friend struct museum::CitySystemInspection;
 Board board_{},previous_{};std::array<bool,count>stroke_{};
 int brief_=0,brush_=1,cursor_=0,last_touch_=-1,edits_=0;unsigned completed_=0;
 float x_=1,y_=2,visual_x_=1,visual_y_=2,dx_=0,dy_=0,time_=0,blend_=1,stable_=0,rumble_=0,flash_=0;
 bool paused_=false,touching_=false,touch_suppressed_=false,erasing_=false,ready_=false,initialized_=false;
 float touch_start_x_=0,touch_start_y_=0,touch_anchor_x_=0,touch_anchor_y_=0;
 int touch_id_=-1; hui::audio::Tactile pending_pattern_=hui::audio::Tactile::confirm;
 static int at(int x,int y){return y*width+x;}
 static bool node(const Board&b,int n){return n==b.clinic||std::find(b.homes.begin(),b.homes.end(),n)!=b.homes.end()||std::find(b.jobs.begin(),b.jobs.end(),n)!=b.jobs.end();}
 static bool passable(const Board&b,int n){return !b.blocked[size_t(n)]&&(b.cells[size_t(n)].kind==1||node(b,n));}
 static std::array<int,4>neighbors(int n){return {n%width? n-1:-1,n%width+1<width?n+1:-1,n>=width?n-width:-1,n+width<count?n+width:-1};}
 static std::array<int,count> distances(const Board&b,int start,std::array<int,count>&parent){
  std::array<int,count>d{},queue{};d.fill(-1);parent.fill(-1);int head=0,tail=0;queue[size_t(tail++)]=start;d[size_t(start)]=0;
  while(head<tail){const int n=queue[size_t(head++)];for(const int next:neighbors(n))if(next>=0&&d[size_t(next)]<0&&passable(b,next)){d[size_t(next)]=d[size_t(n)]+1;parent[size_t(next)]=n;queue[size_t(tail++)]=next;}}
  return d;
 }
 static void measure(Board&b){
  b.cost=b.work=b.care=b.green=b.peak=b.jobs_connected=0;b.mean=0;b.load.fill(0);b.routes={};std::array<bool,2>linked{};
  for(const auto&c:b.cells)b.cost+=c.kind==1?1:c.kind==2?2:0;
  for(size_t h=0;h<b.homes.size();++h){const int home=b.homes[h];std::array<int,count>parent{};const auto d=distances(b,home,parent);int goal=-1,best=count+1;
   for(size_t j=0;j<b.jobs.size();++j)if(d[size_t(b.jobs[j])]>=0){linked[j]=true;if(d[size_t(b.jobs[j])]<best){best=d[size_t(b.jobs[j])];goal=b.jobs[j];}}
   if(d[size_t(b.clinic)]>=0)++b.care;
   bool green=false;for(int n=0;n<count;++n)if(b.cells[size_t(n)].kind==2&&std::abs(n%width-home%width)+std::abs(n/width-home/width)<=2)green=true;
   if(green)++b.green;
   if(goal>=0){++b.work;b.mean+=float(best);auto&r=b.routes[h];for(int n=goal;n>=0&&r.size<count;n=parent[size_t(n)]){r.cells[size_t(r.size++)]=n;if(n==home)break;}
    std::reverse(r.cells.begin(),r.cells.begin()+r.size);for(int k=0;k<r.size;++k){const int n=r.cells[size_t(k)];if(b.cells[size_t(n)].kind==1)++b.load[size_t(n)];}}
  }
  if(b.work)b.mean/=float(b.work);for(bool v:linked)b.jobs_connected+=int(v);for(int n:b.load)b.peak=std::max(b.peak,n);
 }
 bool fits()const{return board_.work==3&&board_.care==3&&board_.jobs_connected==2&&board_.green==3&&board_.peak<=2&&board_.mean<=float(17+brief_)&&board_.cost<=board_.budget;}
 void event(int n,float strength,hui::audio::Tactile pattern=hui::audio::Tactile::confirm){sound(n);if(strength>=rumble_)pending_pattern_=pattern;rumble_=std::max(rumble_,strength);flash_=.65f;}
 void setup(int stage){
  if(initialized_)previous_=board_;else previous_={};board_={};brief_=stage;board_.budget=40+stage*2;
  if(stage==0){board_.homes={at(1,2),at(1,7),at(5,8)};board_.jobs={at(13,2),at(13,7)};board_.clinic=at(7,4);}
  else if(stage==1){board_.homes={at(1,1),at(1,8),at(4,5)};board_.jobs={at(13,2),at(13,8)};board_.clinic=at(11,5);for(int y=0;y<height;++y)if(y!=2&&y!=7)board_.blocked[size_t(at(7,y))]=true;}
  else{board_.homes={at(1,1),at(2,8),at(6,8)};board_.jobs={at(13,1),at(13,8)};board_.clinic=at(8,3);for(int y=2;y<=5;++y)board_.blocked[size_t(at(6,y))]=true;for(int y=5;y<=8;++y)board_.blocked[size_t(at(9,y))]=true;}
  measure(board_);cursor_=board_.homes[0];x_=float(cursor_%width);y_=float(cursor_/width);stable_=0;ready_=false;blend_=initialized_?0:1;initialized_=true;stroke_.fill(false);last_touch_=-1;touching_=false;dx_=dy_=0;
 }
 bool paint(int n,int kind){
  if(n<0||n>=count||board_.blocked[size_t(n)]||node(board_,n))return false;auto&c=board_.cells[size_t(n)];if(c.kind==kind)return false;
  const int old_cost=c.kind==1?1:c.kind==2?2:0,new_cost=kind==1?1:kind==2?2:0;
  if(board_.cost-old_cost+new_cost>board_.budget){event(49,.035f,hui::audio::Tactile::error);return false;}
  c.kind=static_cast<unsigned char>(kind);++edits_;const int prior=board_.work+board_.care;measure(board_);stable_=0;ready_=false;event(kind==2?67:kind==1?60:55,board_.work+board_.care>prior?.13f:.035f,board_.work+board_.care>prior?hui::audio::Tactile::confirm:kind==0?hui::audio::Tactile::back:kind==2?hui::audio::Tactile::rise:hui::audio::Tactile::touch);return true;
 }
 void contact(int next){
  if(last_touch_<0){erasing_=board_.cells[size_t(next)].kind==brush_;stroke_.fill(false);last_touch_=next;}
  int n=last_touch_;for(int step=0;step<width+height;++step){if(!stroke_[size_t(n)]){paint(n,erasing_?0:brush_);stroke_[size_t(n)]=true;}if(n==next)break;
   if(n%width!=next%width)n+=n%width<next%width?1:-1;else n+=n/width<next/width?width:-width;
  }last_touch_=next;
 }
 static void draw_board(DrawList&l,const Board&b,Color accent,float alpha,float time){
  if(alpha<.001f)return;constexpr float left=55,top=145,unit=34;
  auto px=[](int n){return left+float(n%width)*unit;};auto py=[](int n){return top+float(n/width)*unit;};
  for(int n=0;n<count;++n){const float x=px(n),y=py(n);if(b.blocked[size_t(n)]){l.line(x-8,y-8,x+8,y+8,.7f,ink.with_alpha(.075f*alpha));l.line(x-8,y+8,x+8,y-8,.7f,ink.with_alpha(.075f*alpha));continue;}
   l.circle(x,y,1,ink.with_alpha(.10f*alpha));const auto&c=b.cells[size_t(n)];const float opacity=c.road*alpha;
   if(opacity>.001f){l.circle(x,y,2.1f,accent.with_alpha(opacity*.8f));for(int next:{n%width+1<width?n+1:-1,n+width<count?n+width:-1})if(next>=0&&(b.cells[size_t(next)].road>.001f||node(b,next))){const float fade=node(b,next)?opacity:std::min(opacity,b.cells[size_t(next)].road*alpha);l.line(x,y,px(next),py(next),1.6f,accent.with_alpha(fade*.7f));}
    for(int next:{n%width?n-1:-1,n>=width?n-width:-1})if(next>=0&&node(b,next))l.line(x,y,px(next),py(next),1.6f,accent.with_alpha(opacity*.7f));}
   if(c.green*alpha>.001f){const float opacity=c.green*alpha;l.circle(x,y,8,accent.with_alpha(.10f*opacity));l.line(x,y+6,x,y-6,1.2f,ink.with_alpha(.5f*opacity));l.line(x,y-2,x-4,y-6,1,accent.with_alpha(.8f*opacity));l.line(x,y+1,x+4,y-3,1,accent.with_alpha(.8f*opacity));}
   if(b.load[size_t(n)]>2)l.circle(x,y,5+std::sin(time*2)*1.2f,accent.with_alpha(.12f*alpha));
  }
  for(int h:b.homes){const float x=px(h),y=py(h);l.bordered_rect({x-7,y-6,14,13},2,paper.with_alpha(alpha),1.3f,ink.with_alpha(alpha));l.line(x-8,y-7,x,y-13,1.2f,ink.with_alpha(alpha));l.line(x,y-13,x+8,y-7,1.2f,ink.with_alpha(alpha));}
  for(int j:b.jobs){const float x=px(j),y=py(j);l.bordered_rect({x-8,y-12,16,23},1,paper.with_alpha(alpha),1.3f,ink.with_alpha(alpha));for(int k=0;k<3;++k)l.line(x-4,y-7+k*6.f,x+4,y-7+k*6.f,1,ink.with_alpha(.5f*alpha));}
  const float cx=px(b.clinic),cy=py(b.clinic);l.circle(cx,cy,11,paper.with_alpha(alpha));l.line(cx-6,cy,cx+6,cy,1.6f,ink.with_alpha(alpha));l.line(cx,cy-6,cx,cy+6,1.6f,ink.with_alpha(alpha));
  for(size_t h=0;h<b.routes.size();++h){const auto&r=b.routes[h];if(r.size<2)continue;for(int person=0;person<3;++person){float distance=std::fmod(time*1.9f+float(person)*r.size/3.f+float(h)*.6f,float(2*(r.size-1)));if(distance>r.size-1)distance=2*(r.size-1)-distance;const int k=std::min(r.size-2,int(distance));const float t=distance-float(k);const float x=px(r.cells[size_t(k)])*(1-t)+px(r.cells[size_t(k+1)])*t,y=py(r.cells[size_t(k)])*(1-t)+py(r.cells[size_t(k+1)])*t;l.circle(x,y,2.5f,ink.with_alpha(.8f*alpha));}}
 }
public:
 CitySystem(){reset();}
 void reset()override{movement_.reset();completed_=0;brush_=1;edits_=0;time_=rumble_=flash_=0;note_=-1;paused_=false;touch_suppressed_=false;setup(0);visual_x_=x_;visual_y_=y_;}
 StudyCompletion completion()const override{return !ready_?StudyCompletion::playing:brief_==2?StudyCompletion::experience_complete:StudyCompletion::level_complete;}
 int level_number()const override{return brief_+1;}
 int level_count()const override{return 3;}
 void continue_level()override{if(!ready_)return;if(brief_==2)reset();else setup(brief_+1);}
 const char*help()const override{return "Connect homes to both workplaces and the clinic. Give every home nearby green space. Shorter, separate routes keep travel and congestion low. Complete three briefs within their construction budgets. Choose a road or green-space tool, then draw connections, remove tiles and compare the journeys they create.";}
 void handle(const InputFrame&i,Feedback&f)override{
  dx_=dy_=0;paused_=i.focus_lost||!i.connected;if(paused_){touch_suppressed_=true;last_touch_=-1;touching_=false;rumble_=0;movement_.reset();return;}
  movement_.drain(f,rumble_>0);
  const int previous_cursor=cursor_;
  if(rumble_>0){f.feel(pending_pattern_,rumble_,.035f);rumble_=0;}
  if(i.is_pressed(Action::west)){reset();f.feel(hui::audio::Tactile::back,.07f,.045f);return;}
  if(i.is_pressed(Action::north)){brush_=3-brush_;sound(brush_==1?60:67);f.feel(hui::audio::Tactile::rotate,.045f,.025f,brush_==1?-.45f:.45f);f.speak(hui::audio::SpeakerCue::tool,brush_==1?.9f:1.15f,.1f);last_touch_=-1;touching_=false;}
  const bool contact_now=i.touch.available&&i.touch.count>0;
  if(!contact_now){touch_suppressed_=false;last_touch_=-1;touching_=false;}
  if(contact_now&&!touch_suppressed_){const auto&p=i.touch.points[0];if(std::isfinite(p.x)&&std::isfinite(p.y)){
   if(!touching_||touch_id_!=int(p.id)){touch_start_x_=p.x;touch_start_y_=p.y;touch_anchor_x_=x_;touch_anchor_y_=y_;touch_id_=int(p.id);last_touch_=-1;}
   x_=std::clamp(touch_anchor_x_+(p.x-touch_start_x_)*float(width-1),0.f,float(width-1));y_=std::clamp(touch_anchor_y_+(p.y-touch_start_y_)*float(height-1),0.f,float(height-1));cursor_=at(int(std::round(x_)),int(std::round(y_)));contact(cursor_);touching_=true;}}
  else if(!contact_now){dx_=std::clamp(sane(i.stick_x),-1.f,1.f);dy_=std::clamp(sane(i.stick_y),-1.f,1.f);if(!i.nav_from_stick){if(i.nav==Direction::left)x_-=1;if(i.nav==Direction::right)x_+=1;if(i.nav==Direction::up)y_-=1;if(i.nav==Direction::down)y_+=1;}x_=std::clamp(x_,0.f,float(width-1));y_=std::clamp(y_,0.f,float(height-1));cursor_=at(int(std::round(x_)),int(std::round(y_)));}
  if(cursor_!=previous_cursor){movement_.step(float(cursor_%width-previous_cursor%width),float(cursor_/width-previous_cursor/width));movement_.drain(f,rumble_>0);}
  if(i.is_pressed(Action::confirm)&&!touching_&&!ready_)paint(cursor_,board_.cells[size_t(cursor_)].kind==brush_?0:brush_);
 }
 void update(float dt)override{
  if(paused_)return;dt=std::clamp(sane(dt),0.f,.05f);if(dt<=0)return;movement_.advance(dt);time_+=dt;blend_=std::min(1.f,blend_+dt*2.4f);flash_=std::max(0.f,flash_-dt);
  const int before_cursor=cursor_;
  if(!touching_){x_=std::clamp(x_+dx_*7*dt,0.f,float(width-1));y_=std::clamp(y_+dy_*7*dt,0.f,float(height-1));cursor_=at(int(std::round(x_)),int(std::round(y_)));}
  if(cursor_!=before_cursor)movement_.step(float(cursor_%width-before_cursor%width),float(cursor_/width-before_cursor/width));
  const float smooth=1-std::exp(-dt*15);visual_x_+=(float(cursor_%width)-visual_x_)*smooth;visual_y_+=(float(cursor_/width)-visual_y_)*smooth;
  for(auto&c:board_.cells){c.road+=(float(c.kind==1)-c.road)*smooth;c.green+=(float(c.kind==2)-c.green)*smooth;}
  if(fits()){stable_+=dt;if(stable_>=1.2f&&!ready_){ready_=true;completed_|=1u<<brief_;event(79,.16f);}}else{stable_=0;ready_=false;}
 }
 void draw(DrawList&l,Fonts&f,Rect r,Color a)override{
  if(!std::isfinite(r.x)||!std::isfinite(r.y)||!std::isfinite(r.w)||!std::isfinite(r.h)||r.w<1||r.h<1)return;l.push_clip(r);l.rounded_rect(r,0,paper);const float scale=std::min(r.w/1000.f,r.h/540.f);l.push_transform(scale,0,0,r.x+(r.w-1000*scale)*.5f,r.y+(r.h-540*scale)*.5f);
  char label[100];hui::ui::format(label,"A CITY IS A SYSTEM   /   %d OF 3",brief_+1);hui::ui::text(l,f.mono,label,42,43,12,ink.with_alpha(.55f),Align::left,1);
  hui::ui::text(l,f.semibold,brief_==1?"Two crossings. One network.":brief_==2?"A different route changes the city.":"Draw a connection. Follow its effects.",40,84,27,ink);
  hui::ui::text(l,f.regular,"Connect homes, work and care. Keep green space close and journeys short.",42,112,15,ink.with_alpha(.65f));
  const float blend=ease(blend_);draw_board(l,previous_,a,1-blend,time_);draw_board(l,board_,a,blend,time_);
  l.bordered_rect({55+visual_x_*34-14,145+visual_y_*34-14,28,28},4,a.with_alpha(.045f),1.4f,a.with_alpha(.7f));
  l.line(637,145,637,451,.7f,ink.with_alpha(.14f));
  hui::ui::format(label,"%d / %d",board_.budget-board_.cost,board_.budget);hui::ui::text(l,f.mono,"BUDGET LEFT",681,159,11,ink.with_alpha(.5f),Align::left,1);hui::ui::text(l,f.display,label,678,199,31,a);
  auto metric=[&](const char*name,const char*value,float y){hui::ui::text(l,f.mono,name,681,y,11,ink.with_alpha(.55f));hui::ui::text(l,f.semibold,value,948,y+1,17,ink,Align::right);};
  hui::ui::format(label,"%d / 3",board_.work);metric("HOMES TO WORK",label,240);hui::ui::format(label,"%d / 3",board_.care);metric("HOMES TO CARE",label,275);hui::ui::format(label,"%d / 3",board_.green);metric("NEARBY GREEN",label,310);hui::ui::format(label,"%.1f / %d",board_.mean,17+brief_);metric("MEAN JOURNEY",board_.work?label:"--",345);hui::ui::format(label,"%d / 2",board_.peak);metric("BUSIEST ROAD",label,380);
  const Color road{.68f,.43f,.23f,1},green{.29f,.51f,.31f,1};
  for(int tool=1;tool<=2;++tool){const float x=681+(tool-1)*138.f;const Color color=tool==1?road:green;const bool selected=brush_==tool;l.bordered_rect({x,413,128,35},5,color.with_alpha(selected?.16f:.055f),selected?1.6f:.7f,color.with_alpha(selected?.95f:.4f));hui::ui::text(l,f.semibold,tool==1?"ROAD":"GREEN",x+64,436,12,color,Align::center);}
  const char*message=ready_?(brief_<2?"Brief complete. Continue when you are ready.":"Three briefs complete. Keep experimenting."):board_.jobs_connected<2?"Both workplaces need a connection.":board_.peak>2?"One route carries too much. Build another way through.":board_.green<3?"Each home needs green space within two cells.":board_.care<3?"The clinic needs to reach every home.":board_.mean>17+brief_?"Shorten the paths between homes and work.":"Watch the network settle.";
  l.line(42,473,955,473,.7f,ink.with_alpha(.13f));hui::ui::text(l,f.regular,message,42,505,16,ink.with_alpha(.75f));
  if(flash_>0)l.line(42,473,42+913*std::clamp(flash_/.65f,0.f,1.f),473,1.3f,a.with_alpha(flash_*.45f));l.pop_transform();l.pop_clip();
 }
};
}
std::unique_ptr<Study> make_study_city_system(const std::string&id){if(id=="city-system")return std::make_unique<CitySystem>();return {};}
}
