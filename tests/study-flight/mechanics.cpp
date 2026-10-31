#include "museum/study_arcade.cpp"
#include <cassert>
#include <limits>
#include <set>
namespace museum {namespace {
struct FlightInspection {
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){
  {Wireframe s;assert(s.gates_.size()==60);
   for(int n:{0,5,10,59,60}){s.processed_=n;const float expected=n>=10?7.2f:n==5?5.4f:3.6f;assert(std::abs(s.forward_speed()-expected)<.0001f);}
   for(int n=0;n<10;++n){s.processed_=n;const float before=s.forward_speed();s.processed_=n+1;assert(s.forward_speed()>before);}
   for(int n=10;n<60;++n){s.processed_=n;assert(std::abs(s.forward_speed()-7.2f)<.0001f);}
   std::puts("PASS Flight ramp0=3.6/5=5.4/10=7.2/59=7.2/60=7.2; all first10 strictly increase, remaining plateau; unchanged6.2spacing");
  }
  for(int hz:{30,60,120})for(bool sensors:{false,true}){
   Wireframe s;std::set<hui::audio::Tactile>patterns;hui::ui::Feedback feedback;unsigned passages=0;
   if(sensors){auto i=input();i.motion.available=true;for(int n=0;n<hz;++n){s.handle(i,feedback);s.update(1.f/hz);}}
   for(int n=0;n<hz*300&&!s.finished_;++n){
    auto i=input();const auto&g=s.gates_[size_t(s.processed_)];
    const float x=std::clamp((g.x-s.position_.x)*3.f,-1.f,1.f),y=std::clamp((g.y-s.position_.y)*3.f,-1.f,1.f);
    if(sensors){i.motion.available=true;i.motion.angular_velocity[2]=-std::clamp((x-s.gyro_.value()[0])*1.6f,-2.f,2.f);i.motion.angular_velocity[0]=-std::clamp((y-s.gyro_.value()[1])*1.6f,-2.f,2.f);}
    else{i.stick_x=x;i.stick_y=y;}
    feedback.clear();s.handle(i,feedback);for(const auto&v:feedback.tactile){patterns.insert(v.pattern);if(v.pattern==hui::audio::Tactile::passage){++passages;assert(v.strength>=.3f&&v.seconds>=.15f);}}assert(feedback.speaker_cues.empty());s.update(1.f/hz);
   }
   std::fprintf(stderr,"flight%dHz %s passed%d missed%d processed%d done%d\n",hz,sensors?"synthetic gyro":"stick",s.passed_,s.missed_,s.processed_,s.finished_);
   assert(s.finished_&&s.passed_==60&&s.missed_==0);
   s.handle(input(),feedback);for(const auto&v:feedback.tactile)patterns.insert(v.pattern);assert(passages==59&&patterns.contains(hui::audio::Tactile::passage)&&patterns.contains(hui::audio::Tactile::airflow)&&patterns.contains(hui::audio::Tactile::confirm));
   const float time=s.flight_time_,z=s.gates_[59].z;s.update(.04f);assert(s.flight_time_==time&&s.gates_[59].z==z);
   auto replay=input();replay.pressed=hui::action_bit(hui::Action::confirm);s.handle(replay,feedback);assert(s.finished_&&s.processed_==60&&s.completion()==StudyCompletion::playing);
   auto reset_button=input();reset_button.pressed=hui::action_bit(hui::Action::west);s.handle(reset_button,feedback);assert(s.finished_&&s.processed_==60);
   for(int frame=0;frame<hz;++frame)s.update(1.f/hz);
   assert(s.completion()==StudyCompletion::experience_complete);s.handle(replay,feedback);s.handle(reset_button,feedback);assert(s.finished_&&s.processed_==60);
   s.continue_level();assert(!s.finished_&&s.processed_==0&&s.position_.x==0);
  }
  {Wireframe s;hui::ui::Feedback f;auto moving=input();moving.motion.available=true;moving.motion.angular_velocity[2]=.4f;
   const float z=s.gates_[0].z;for(int n=0;n<180;++n){s.handle(moving,f);s.update(1.f/60);}assert(s.flight_time_==0&&s.gates_[0].z==z&&!s.gyro_.calibrated());
   moving.stick_x=.4f;s.handle(moving,f);s.update(.04f);assert(s.flight_time_>0&&s.position_.x>0);
   const auto p=s.position_;const float clock=s.time_,time=s.flight_time_;moving.focus_lost=true;s.handle(moving,f);for(int n=0;n<100;++n)s.update(.04f);assert(s.position_.x==p.x&&s.time_==clock&&s.flight_time_==time);
   moving.focus_lost=false;moving.connected=false;s.handle(moving,f);s.update(.04f);assert(s.flight_time_==time&&!s.gyro_.calibrated());
   auto neutral=input();neutral.motion.available=true;for(int n=0;n<30;++n){s.handle(neutral,f);s.update(.01f);}assert(s.gyro_.calibrated());
   neutral.pressed=hui::action_bit(hui::Action::north);s.handle(neutral,f);assert(!s.gyro_.calibrated()&&!f.tactile.empty());
  }
  {Wireframe s;hui::ui::Feedback f;std::set<hui::audio::Tactile>patterns;
   for(int n=0;n<36000&&!s.finished_;++n){f.clear();s.handle(input(),f);for(auto v:f.tactile)patterns.insert(v.pattern);s.update(1.f/120);}assert(s.finished_&&s.missed_>0&&s.passed_>0&&s.processed_==60&&patterns.contains(hui::audio::Tactile::error));
  }
  {Wireframe s;const auto left=s.project(-Wireframe::half_width,0,Wireframe::near_plane),right=s.project(Wireframe::half_width,0,Wireframe::near_plane);assert(right.x-left.x>1000);}
  {Wireframe s;for(int n=0;n<12000;++n){auto i=input();i.stick_x=std::sin(n*.04f);i.stick_y=std::cos(n*.03f);if(n%947==0)i.pressed=hui::action_bit(hui::Action::west);if(n%311==0)i.stick_x=std::numeric_limits<float>::quiet_NaN();i.focus_lost=n%719<12;hui::ui::Feedback f;s.handle(i,f);s.update(n%101==0?std::numeric_limits<float>::infinity():1.f/120);assert(std::isfinite(s.position_.x)&&std::isfinite(s.position_.y)&&std::isfinite(s.time_));assert(s.processed_<=60&&s.passed_+s.missed_==s.processed_);}}
  std::puts("PASS Flight: 60 input-driven openings at30/60/120Hz via stick and synthetic angular samples; real near-plane crossing; calibration wait/manual override/focus/reconnect; miss feedback, finite finish/replay and12000finiteframes. Physical gyro axes/latency remain unmeasured.");
 }
 static std::unique_ptr<Study> preview(int stage){auto s=std::make_unique<Wireframe>();hui::ui::Feedback f;
  for(int n=0;n<(stage==0?150:stage==1?208:2200)&&!s->finished_;++n){auto i=input();const auto&g=s->gates_[size_t(s->processed_)];i.stick_x=std::clamp((g.x-s->position_.x)*3.f,-1.f,1.f);i.stick_y=std::clamp((g.y-s->position_.y)*3.f,-1.f,1.f);s->handle(i,f);s->update(1.f/120);f.clear();}
  if(stage==2)for(int n=0;n<80;++n)s->update(1.f/120);return s;}
};
}}
void check_flight_mechanics(){museum::FlightInspection::run();}
std::unique_ptr<museum::Study> flight_preview(int stage){return museum::FlightInspection::preview(stage);}
