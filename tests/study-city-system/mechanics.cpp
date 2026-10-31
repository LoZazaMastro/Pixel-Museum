#include "museum/study_city_system.cpp"
#include <cassert>
#include <limits>
namespace museum {
struct CitySystemInspection {
 static void solve(CitySystem&s,int stage){
  s.setup(stage);
  const auto line=[&](int x0,int y0,int x1,int y1){int x=x0,y=y0;for(int k=0;k<width+height;++k){s.paint(CitySystem::at(x,y),1);if(x==x1&&y==y1)break;if(x!=x1)x+=x<x1?1:-1;else y+=y<y1?1:-1;}};
  if(stage==0){line(1,2,13,2);line(1,7,13,7);line(5,8,5,7);line(7,2,7,7);for(auto p:std::array<std::array<int,2>,3>{{{1,1},{1,8},{5,9}}})s.paint(CitySystem::at(p[0],p[1]),2);}
  if(stage==1){line(1,2,13,2);line(1,1,1,2);line(1,7,13,7);line(1,8,1,7);line(13,7,13,8);line(4,5,4,7);line(11,2,11,7);for(auto p:std::array<std::array<int,2>,3>{{{1,0},{1,9},{4,4}}})s.paint(CitySystem::at(p[0],p[1]),2);}
  if(stage==2){line(1,1,13,1);line(2,8,8,8);line(8,8,8,9);line(8,9,10,9);line(10,9,10,8);line(10,8,13,8);line(8,1,8,8);for(auto p:std::array<std::array<int,2>,3>{{{1,0},{2,9},{6,9}}})s.paint(CitySystem::at(p[0],p[1]),2);}
 }
 static void run(){
  CitySystem s;assert(!s.fits()&&s.board_.work==0&&s.board_.care==0&&s.board_.green==0);
  hui::InputFrame i;i.connected=true;hui::ui::Feedback feedback;
  s.x_=3;s.y_=0;s.cursor_=3; // Touchdown is relative to the active grid cursor, wherever the finger lands.
  i.touch.available=true;i.touch.count=1;i.touch.points[0]={.2f,.8f,0};s.handle(i,feedback);const int edits=s.edits_;assert(edits==1&&s.cursor_==3);
  for(int n=0;n<100;++n){s.handle(i,feedback);s.update(1.f/120);}assert(s.edits_==edits&&s.board_.cells[3].kind==1);
  i.touch.points[0].x=.7f;s.handle(i,feedback);assert(s.edits_==9);for(int n=3;n<=11;++n)assert(s.board_.cells[size_t(n)].kind==1);
  i.touch.points[0].x=.2f;s.handle(i,feedback);assert(s.edits_==9); // revisiting a cell in the same stroke never toggles it
  i.touch.count=0;s.handle(i,feedback);i.touch.count=1;s.handle(i,feedback);assert(s.board_.cells[3].kind==0&&s.edits_==10); // fresh stroke may erase
  const int before=s.edits_;const float clock=s.time_;i.focus_lost=true;s.handle(i,feedback);s.update(.04f);assert(s.edits_==before&&s.time_==clock);
  i.focus_lost=false;s.handle(i,feedback);assert(s.edits_==before);i.touch.count=0;s.handle(i,feedback);i.touch.count=1;s.handle(i,feedback);assert(s.edits_==before+1);
  i={};i.connected=true;s.handle(i,feedback);
  feedback.clear();i.pressed=hui::action_bit(hui::Action::north);s.handle(i,feedback);assert(s.brush_==2&&feedback.speaker_cues.size()==1&&feedback.speaker_cues[0].cue==hui::audio::SpeakerCue::tool&&!feedback.tactile.empty());i.pressed=0;feedback.clear();s.handle(i,feedback);assert(feedback.speaker_cues.empty());
  for(int stage=0;stage<3;++stage){solve(s,stage);assert(s.fits()&&s.board_.work==3&&s.board_.care==3&&s.board_.green==3&&s.board_.jobs_connected==2);assert(s.board_.peak<=2&&s.board_.cost<=s.board_.budget);
   for(int n=0;n<160;++n){s.handle(i,feedback);s.update(1.f/120);}assert(s.ready_&&(s.completed_&(1u<<stage)));std::printf("City brief%d: cost%d/%d, work%d, care%d, green%d, mean%.2f, peak%d PASS\n",stage+1,s.board_.cost,s.board_.budget,s.board_.work,s.board_.care,s.board_.green,s.board_.mean,s.board_.peak);
   assert(s.completion()==(stage==2?StudyCompletion::experience_complete:StudyCompletion::level_complete));
   if(stage<2){i.pressed=hui::action_bit(hui::Action::confirm);s.handle(i,feedback);assert(s.brief_==stage&&s.ready_);s.continue_level();assert(s.brief_==stage+1&&!s.ready_&&s.board_.cost==0&&s.blend_==0);i.pressed=0;}}
  assert(s.completed_==7);solve(s,0);s.paint(CitySystem::at(12,7),0);assert(s.board_.peak==3&&!s.fits()); // removing a workplace approach sends all three homes through the other route
  solve(s,0);s.paint(CitySystem::at(1,1),0);assert(s.board_.green==2&&!s.fits());
  s.reset();for(int n=0;n<count;++n)s.paint(n,2);assert(s.board_.cost<=s.board_.budget); // cannot overspend
  const int cost=s.board_.cost;i={};i.connected=true;i.nav=hui::Direction::right;s.handle(i,feedback);assert(s.cursor_%width==2&&s.board_.cost==cost); // selection alone does not build
  i.pressed=hui::action_bit(hui::Action::west);s.handle(i,feedback);assert(s.brief_==0&&s.board_.cost==0&&s.completed_==0&&s.edits_==0);
  s.update(std::numeric_limits<float>::quiet_NaN());s.update(-1);assert(std::isfinite(s.time_));i={};i.connected=true;i.touch.available=true;i.touch.count=1;i.touch.points[0]={std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity(),0};s.handle(i,feedback);assert(s.cursor_>=0&&s.cursor_<count);
  std::puts("City touch stroke/release, no repeat commits, focus pause/recovery, real connection/green/congestion/budget causality, three solvable briefs, continue/reset, finite inputs PASS");
 }
 static std::unique_ptr<Study> preview(){auto s=std::make_unique<CitySystem>();solve(*s,0);hui::InputFrame i;i.connected=true;hui::ui::Feedback f;for(int n=0;n<200;++n){s->handle(i,f);s->update(1.f/120);}return s;}
};
}
void check_city_system_mechanics(){museum::CitySystemInspection::run();}
std::unique_ptr<museum::Study> city_system_preview(){return museum::CitySystemInspection::preview();}
