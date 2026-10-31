#include "museum/study_motion.cpp"
#include <cstdio>
#include <cassert>
namespace museum {namespace {struct MotionInspection {
 static int run(int hz){Momentum s;hui::ui::Feedback f;float jump_delay=0,stuck=0,lastx=s.x_,charge_time=0;int milestone=0,prepare=0,taps=0,tube_mask=0;
  for(int frame=0;frame<hz*90;++frame){hui::InputFrame i;i.connected=true;i.stick_x=1;if(s.x_/1.6f>2100&&s.x_/1.6f<2600&&s.grounded_&&std::abs(s.v_)>300)i.stick_y=1;jump_delay-=1.f/hz;bool jump=false;
   if(s.grounded_&&jump_delay<=0){const float look=std::max(50.f,std::abs(s.v_)*.14f);const float floor=Momentum::land_floor(s.x_+look,s.y_+26,50,55);
    if(floor>1e7f||floor<s.y_+26-15||stuck>.18f)jump=true;
    for(unsigned n=0;n<22;++n)if(!s.enemy_down_[n]){const auto e=s.enemy(n);if(e.x>s.x_&&e.x-s.x_<look+55&&std::abs(e.y-s.y_)<75)jump=true;}
    for(const auto&p:s.native_spikes)if(p.x*1.6f>s.x_&&p.x*1.6f-s.x_<look+70&&std::abs(p.y*1.6f-s.y_)<80)jump=true;
    if(s.x_>320&&s.x_<480)jump=true;
   }
   if(s.x_/1.6f>3400&&s.x_/1.6f<3700){jump=false;if(s.v_>380)i.stick_x=-1;}
   if(s.x_/1.6f>5200&&s.x_/1.6f<5660){jump=false;i.stick_y=1;}
   if((s.x_/1.6f>6080&&s.x_/1.6f<6420)||(s.x_/1.6f>6600&&s.x_/1.6f<6930)){jump=false;i.stick_y=1;}
   if(!prepare&&s.x_/1.6f>5100&&s.x_/1.6f<5400&&s.grounded_&&s.v_<650)prepare=1;
   if(prepare==1){jump=false;i.stick_y=0;i.stick_x=s.v_>10?-1:0;if(std::abs(s.v_)<15)prepare=2;}
   if(prepare==2){jump=false;i.stick_y=1;i.stick_x=0;charge_time+=1.f/hz;if(charge_time>.11f){i.pressed=i.held=hui::action_bit(Action::confirm);charge_time=0;if(++taps>=5)prepare=3;}}
   else if(prepare==3){jump=false;i.stick_y=0;i.stick_x=1;prepare=4;}
   if(jump){i.pressed=i.held=hui::action_bit(Action::confirm);jump_delay=.3f;}
   const float before_x=s.x_,before_y=s.y_;const int before_falls=s.falls_,before_rings=s.rings_;
   s.handle(i,f);s.update(1.f/hz);if(std::abs(s.x_-lastx)<.1f)stuck+=1.f/hz;else stuck=0;lastx=s.x_;
   assert(std::isfinite(s.x_)&&std::isfinite(s.y_)&&std::isfinite(s.v_)&&std::isfinite(s.vy_));
   if(s.tube_distance_>=0)tube_mask|=1<<s.tube_number_;
   if(s.falls_>before_falls)printf("DEATH %dHz native x%.1f y%.1f rings%d time%.2f\n",hz,before_x/1.6f,before_y/1.6f,before_rings,s.time_);
   if(s.x_/1.6f>milestone*256){printf("%dHz %.2fs x%.0f y%.0f v%.0f grounded%d ring%d falls%d\n",hz,s.time_,s.x_/1.6f,s.y_/1.6f,s.v_,s.grounded_,s.rings_,s.falls_);++milestone;}
   if(s.finished_){printf("FINISH %dHz %.2fs rings%d falls%d loop%d tubes%d\n",hz,s.time_,s.rings_,s.falls_,s.loop_done_,tube_mask);assert(s.loop_done_&&tube_mask==3);return s.falls_;}
  }printf("STOP %dHz x%.1f y%.1f v%.1f floor%.1f falls%d\n",hz,s.x_/1.6f,s.y_/1.6f,s.v_,s.land_floor(s.x_+40,s.y_+26,100,100)/1.6f,s.falls_);return 99;
 }
};}}
int main(){for(int hz:{30,60,120})if(museum::MotionInspection::run(hz)!=0)return 1;}
