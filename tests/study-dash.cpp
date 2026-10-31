// Exercise the actual authored platform route without teleporting the player.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study_motion.cpp"
#include <cassert>
#include <limits>
#include <set>
namespace museum { namespace {
struct DashInspection {
 static void route(int fps,bool digital){
  Dash s;hui::ui::Feedback f;std::set<hui::audio::Tactile> patterns;unsigned gems=0,landings=0,last_room=0;std::array<unsigned,5> room_gems{},room_landings{};bool previous_ground=true;int phase=0;
  std::array<std::vector<hui::InputFrame>,2> traces;
  for(int frame=0;frame<fps*50&&!s.finished_;++frame){
   hui::InputFrame i;i.connected=true;float x=1,y=0;bool jump=false,burst=false;
   if(s.room_>=3){
    if(s.room_==3){
     if(phase==0&&s.grounded_&&s.p_.x>205){jump=true;phase=1;}
     else if(phase==1){x=s.p_.x>330?0:1;if(s.grounded_)phase=2;}
     else if(phase==2&&s.p_.x>365){jump=true;phase=3;}
     else if(phase==3){x=s.p_.x>500?0:1;if(s.grounded_)phase=4;}
     else if(phase==4&&s.p_.x>545){jump=true;phase=5;}
     else if(phase==5){x=s.p_.x>665?0:1;if(s.grounded_)phase=6;}
     else if(phase==6&&s.p_.x>695){jump=true;phase=7;}
     else if(phase==7&&s.p_.x>755&&s.p_.y<335){y=-1;burst=true;phase=8;}
     else if(phase==8&&s.gem_taken_&&s.dash_<=0){burst=true;phase=9;}
     else if(phase==9){x=s.p_.x>1180?0:1;if(s.grounded_)phase=10;}
     else if(phase==10&&s.p_.x>1190){jump=true;phase=11;}
    }else{
     if(phase==0&&s.grounded_&&s.p_.x>205){jump=true;phase=1;}
     else if(phase==1){x=s.p_.x>350?0:1;if(s.grounded_)phase=2;}
     else if(phase==2&&s.p_.x>405){jump=true;phase=3;}
     else if(phase==3){x=s.p_.x>590?0:1;if(s.grounded_)phase=4;}
     else if(phase==4){x=0;jump=true;phase=5;}
     else if(phase==5){x=0;if(s.p_.y<310){x=-1;y=-1;burst=true;phase=6;}}
     else if(phase==6){x=0;if(s.grounded_)phase=7;}
     else if(phase==7&&s.p_.x>495){jump=true;phase=8;}
     else if(phase==8&&s.p_.x>605&&s.p_.y<195){burst=true;phase=9;}
     else if(phase==9&&s.gem_taken_&&s.dash_<=0){burst=true;phase=10;}
     else if(phase==10){x=s.p_.x>1160?0:1;if(s.grounded_)phase=11;}
     else if(phase==11&&s.p_.x>1190){jump=true;phase=12;}
    }
   }else if(s.grounded_){
    jump=s.room_==0?s.p_.x>360:s.room_==1?s.p_.x>245:s.room_==2?(s.p_.x<400?s.p_.x>245:s.p_.x>600&&s.p_.x<900):s.room_==3?(s.p_.x<500?s.p_.x>335:s.p_.x>870&&s.p_.x<1000):(s.p_.x<400?s.p_.x>300:s.p_.x<740?s.p_.x>610:s.p_.x>910&&s.p_.x<1050);
   }else if(s.dash_<=0){
    if(s.room_==0&&s.charged_&&s.p_.x>470)burst=true;
    if(s.room_==1&&s.charged_){
     if(!s.gem_taken_&&s.p_.x>320&&s.p_.y<450){x=.85f;y=-.52f;burst=true;}
     else if(s.gem_taken_){burst=true;}
    }
    if(s.room_==2){
     if(s.p_.x<470&&s.charged_&&s.p_.x>340){x=.75f;y=-.66f;burst=true;}
     else if(s.p_.x>540&&s.p_.x<740&&s.vy_>=0)x=0;
     else if(s.p_.x>690&&s.charged_&&!s.gem_taken_){x=.72f;y=-.69f;burst=true;}
     else if(s.gem_taken_&&s.charged_)burst=true;
    }
   }
   if(digital){if(x>.1f)i.held|=hui::action_bit(Action::right);if(x<-.1f)i.held|=hui::action_bit(Action::left);if(y<-.1f)i.held|=hui::action_bit(Action::up);if(y>.1f)i.held|=hui::action_bit(Action::down);}
   else{i.stick_x=x;i.stick_y=y;}
   if(jump)i.pressed|=hui::action_bit(Action::confirm);
   if(jump||(!s.grounded_&&s.vy_<0))i.held|=hui::action_bit(Action::confirm);
   if(burst)i.pressed|=hui::action_bit(Action::page_next);
   if(s.room_>=3)traces[s.room_-3].push_back(i);
   f.clear();s.handle(i,f);for(const auto&t:f.tactile)patterns.insert(t.pattern);
   const bool taken=s.gem_taken_,was_grounded=s.grounded_;s.update(1.f/fps);
   if(!was_grounded&&s.grounded_){++room_landings[s.room_];assert(s.charged_);
    if(s.room_>=3&&!s.room_complete_){Dash rest=s;hui::InputFrame neutral;neutral.connected=true;hui::ui::Feedback ignored;for(int n=0;n<fps/2;++n){rest.handle(neutral,ignored);rest.update(1.f/fps);}if(!rest.grounded_||!rest.charged_||rest.falls_)std::fprintf(stderr,"REST room%u phase%d from %.1f,%.1f to %.1f,%.1f falls%u\n",s.room_+1,phase,s.p_.x,s.p_.y,rest.p_.x,rest.p_.y,rest.falls_);assert(rest.grounded_&&rest.charged_&&rest.falls_==0);}
   }
   if(!taken&&s.gem_taken_){++gems;++room_gems[s.room_];}
   if(s.completion()==StudyCompletion::level_complete){
    const auto p=s.p_;const auto room=s.room_;
    for(int n=0;n<10;++n)s.update(1.f/fps);
    assert(s.room_==room&&s.p_.x==p.x&&s.p_.y==p.y); // No silent room transition.
    s.continue_level();phase=0;assert(s.room_==room+1);
   }
   if(!previous_ground&&s.grounded_)++landings;previous_ground=s.grounded_;
   if(s.room_!=last_room){std::fprintf(stderr,"dash %dHz %s room %u completed falls%u\n",fps,digital?"digital":"stick",last_room+1,s.falls_);last_room=s.room_;}
   assert(std::isfinite(s.p_.x)&&std::isfinite(s.p_.y));
  }
  std::fprintf(stderr,"dash %dHz %s x%.1f y%.1f room%u gem%d falls%u done%d\n",fps,digital?"digital":"stick",s.p_.x,s.p_.y,s.room_,s.gem_taken_,s.falls_,s.finished_);
  assert(s.finished_&&s.room_==4&&gems>=1&&landings>=3&&s.falls_==0);
  assert(room_gems[3]&&room_gems[4]&&room_landings[3]>=5&&room_landings[4]>=5);
  assert(s.completion()==StudyCompletion::experience_complete&&s.level_number()==5&&s.level_count()==5);
  for(unsigned room=3;room<=4;++room){
   // Replay exactly the successful physical input stream with one mechanic
   // removed. No auto-pilot branch can hide a rejected second dash.
   for(bool disable_refill:{false,true}){
    Dash negative;negative.enter(room);if(disable_refill)negative.gem_taken_=true;
    bool rejected=false;hui::ui::Feedback ignored;
    for(auto input:traces[room-3]){
     if(!disable_refill)input.pressed&=~hui::action_bit(Action::page_next);
     else if(input.is_pressed(Action::page_next)&&!negative.charged_)rejected=true;
     negative.handle(input,ignored);negative.update(1.f/fps);
     if(negative.falls_)break;
    }
    for(int n=0;n<fps*2&&!negative.falls_&&!negative.room_complete_;++n){hui::InputFrame input;input.connected=true;input.stick_x=1;negative.handle(input,ignored);negative.update(1.f/fps);}
    std::fprintf(stderr,"negative room%u refill-disabled%d done%d falls%u rejected%d\n",room+1,disable_refill,negative.room_complete_,negative.falls_,rejected);
    assert(!negative.room_complete_&&negative.falls_>0);
    if(disable_refill)assert(rejected);
   }
   // Repeated rightward jumps never solve either authored final room.
   Dash right;right.enter(room);hui::ui::Feedback ignored;
   for(int n=0;n<fps*12;++n){hui::InputFrame input;input.connected=true;input.stick_x=1;input.held=hui::action_bit(Action::confirm);if(right.grounded_)input.pressed=input.held;right.handle(input,ignored);right.update(1.f/fps);}
   assert(!right.room_complete_&&right.falls_>0);
  }
  s.continue_level();assert(s.room_==0&&s.completion()==StudyCompletion::playing&&!s.finished_);
  assert(patterns.contains(hui::audio::Tactile::rise)&&patterns.contains(hui::audio::Tactile::impact)&&patterns.contains(hui::audio::Tactile::touch));
 }
 static void safety(){
  for(int fps:{30,60,120}){
   Dash ceiling;ceiling.enter(4);ceiling.p_={800,180};ceiling.grounded_=false;ceiling.direction_={0,-1};ceiling.dash_=.2f;
   for(int n=0;n<fps/10;++n)ceiling.update(1.f/fps);assert(ceiling.p_.y>=139&&ceiling.dash_==0);
   Dash left;left.enter(4);left.p_={920,400};left.grounded_=false;left.direction_={1,0};left.dash_=.2f;
   for(int n=0;n<fps/10;++n)left.update(1.f/fps);assert(left.p_.x<=947.01f&&left.dash_==0);
   Dash right;right.enter(4);right.p_={1090,400};right.grounded_=false;right.direction_={-1,0};right.dash_=.2f;
   for(int n=0;n<fps/10;++n)right.update(1.f/fps);assert(right.p_.x>=1062.99f&&right.dash_==0);
   Dash spike;spike.enter(4);spike.p_={990,260};spike.grounded_=false;spike.vy_=300;
   for(int n=0;n<fps/5;++n)spike.update(1.f/fps);assert(spike.falls_==1);
  }
  Dash once;once.enter(3);once.p_=Dash::rooms[3].crystal;once.grounded_=false;once.charged_=false;once.update(.001f);assert(once.gem_taken_&&once.charged_);once.charged_=false;once.update(.001f);assert(!once.charged_);
  Dash wrong_floor;wrong_floor.enter(4);wrong_floor.p_={1250,535};wrong_floor.update(.001f);assert(!wrong_floor.room_complete_);
  Dash s;hui::ui::Feedback f;hui::InputFrame i;i.connected=true;i.pressed=hui::action_bit(Action::confirm);s.handle(i,f);s.update(.08f);assert(!s.grounded_&&s.p_.y<535);
  i.pressed=hui::action_bit(Action::page_next);i.stick_x=1;s.handle(i,f);assert(!s.charged_&&s.air_dashes_==1);s.handle(i,f);assert(s.air_dashes_==1);
  i={};i.connected=true;i.focus_lost=true;i.pressed=hui::action_bit(Action::west)|hui::action_bit(Action::page_next);auto before=s.p_;s.handle(i,f);assert(s.p_.x==before.x&&s.p_.y==before.y&&s.air_dashes_==1);
  const float clock=s.time_,dash=s.dash_;for(int n=0;n<60;++n)s.update(1.f/60);assert(s.p_.x==before.x&&s.p_.y==before.y&&s.time_==clock&&s.dash_==dash);
  i.focus_lost=false;i.connected=false;s.handle(i,f);s.update(.1f);assert(s.time_==clock&&s.p_.y==before.y);
  i={};i.connected=true;s.handle(i,f);s.update(.01f);assert(s.time_>clock);
  i={};i.connected=true;i.stick_x=std::numeric_limits<float>::quiet_NaN();i.stick_y=std::numeric_limits<float>::infinity();s.handle(i,f);s.update(std::numeric_limits<float>::quiet_NaN());assert(std::isfinite(s.p_.x)&&std::isfinite(s.p_.y));
  s.enter(1);s.p_.y=800;s.update(.01f);assert(s.room_==1&&s.falls_==1&&s.charged_&&s.grounded_);
  i={};i.connected=true;i.pressed=hui::action_bit(Action::west);s.handle(i,f);assert(s.room_==0&&s.falls_==0&&s.p_.x==115&&s.charged_);
  hui::gfx::DrawList d;hui::ui::Fonts fonts;s.draw(d,fonts,{0,0,1920,1080},{.7f,.5f,.4f,1});assert(d.instances().size()<150);
  for(const auto&v:d.instances())for(float x:v.rect)assert(std::isfinite(x));
 }
 static void run(){for(int fps:{30,60,120}){route(fps,false);route(fps,true);}safety();std::puts("PASS Dash: five real platform rooms at30/60/120Hz, analogue/Dpad, midair recharge, landing, distinct haptics, no-spam, checkpoint/focus/NaN/reset.");}
};
}}
int main(){museum::DashInspection::run();}
