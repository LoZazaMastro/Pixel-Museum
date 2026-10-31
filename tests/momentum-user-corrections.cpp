#include "museum/study_motion.cpp"
#include <cassert>
#include <cstdio>
namespace museum {namespace {
struct MomentumLoopInspection {
 static void run(){
  for(int hz:{30,60,120}){
   hui::ui::Feedback f;hui::InputFrame neutral,opposite;neutral.connected=opposite.connected=true;opposite.stick_x=-1;
   Momentum coast,brake;coast.v_=brake.v_=600;
   for(int n=0;n<hz/4;++n){coast.handle(neutral,f);coast.update(1.f/hz);brake.handle(opposite,f);brake.update(1.f/hz);}
   assert(coast.v_>550&&brake.v_>0&&brake.v_<coast.v_*.6f);
   for(int n=0;n<hz/2;++n){brake.handle(opposite,f);brake.update(1.f/hz);}assert(brake.v_<0);
   Momentum left;left.x_=500;left.v_=-600;opposite.stick_x=1;
   for(int n=0;n<hz/4;++n){left.handle(opposite,f);left.update(1.f/hz);}assert(left.v_<0&&left.v_>-300);
   for(float height:{100.f,300.f,484.f}){
    Momentum end;end.x_=Momentum::finish_x-8;end.y_=height;end.v_=600;end.vy_=-80;end.grounded_=height==484;
    for(int n=0;n<hz/5&&!end.finished_;++n){end.handle(neutral,f);end.update(1.f/hz);}
    assert(end.finished_&&end.x_>=Momentum::finish_x&&end.completion()==StudyCompletion::playing);
    if(height<484){const float before=end.y_;end.update(1.f/hz);assert(end.y_<484&&std::abs(end.y_-before)<30);}
    for(int n=0;n<hz*2;++n)end.update(1.f/hz);assert(end.completion()==StudyCompletion::experience_complete&&end.grounded_&&end.y_==484);
   }
   Momentum approach;approach.x_=Momentum::finish_x-20;approach.y_=300;approach.grounded_=false;approach.v_=0;approach.handle(neutral,f);approach.update(1.f/hz);assert(!approach.finished_);
   Momentum reverse;reverse.x_=Momentum::finish_x+5;reverse.y_=300;reverse.grounded_=false;reverse.v_=-600;reverse.handle(neutral,f);reverse.update(1.f/hz);assert(!reverse.finished_);
   std::printf("Momentum %dHz: opposite-stick brake stronger, symmetric reversal; X-crossing finish at three heights, physical landing and single delayed completion PASS\n",hz);
  }
  // Keep the previously failing complete first-gap/checkpoint regression.
  Momentum gap;gap.x_=1120;gap.y_=Momentum::ground(1120)-26;gap.v_=680;hui::ui::Feedback f;hui::InputFrame i;i.connected=true;i.stick_x=1;i.held=i.pressed=hui::action_bit(Action::confirm);gap.handle(i,f);i.pressed=0;
  for(int n=0;n<150;++n){gap.handle(i,f);gap.update(1.f/120);}
  std::fprintf(stderr,"First-gap regression x%.2f y%.2f speed%.2f falls%d checkpoint%d\n",gap.x_,gap.y_,gap.v_,gap.falls_,gap.checkpoint_);
  assert(gap.x_>1470&&gap.falls_==0&&gap.checkpoint_);
  assert(Momentum::spikes_left>gap.x_&&Momentum::spikes_left>Momentum::ledges[1].x);
  std::printf("Original first-gap assertion preserved: x%.2f falls%d checkpoint%d; ground hazard now beyond landing runway PASS\n",gap.x_,gap.falls_,gap.checkpoint_);
 }
};
}}
int main(){museum::MomentumLoopInspection::run();}
