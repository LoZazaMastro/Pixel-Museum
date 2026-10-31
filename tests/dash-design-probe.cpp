#include "museum/study_motion.cpp"
#include <cstdio>
namespace museum { namespace {
struct DashInspection {
 static void run(){for(int room:{3,4}){Dash s;s.enter(room);int phase=0;hui::ui::Feedback f;
  for(int n=0;n<60*20&&!s.room_complete_;++n){float x=1,y=0;bool jump=false,burst=false;
   if(room==3){
    if(phase==0&&s.grounded_&&s.p_.x>290){jump=true;phase=1;}
    else if(phase==1&&s.p_.x>350&&s.p_.y<450){x=1;y=-1;burst=true;phase=2;}
    else if(phase==2&&s.gem_taken_&&s.dash_<=0){burst=true;phase=3;}
    else if(phase==3&&s.grounded_){phase=4;}
    else if(phase==4&&s.p_.x>1090){jump=true;phase=5;}
   }else{
    if(phase==0&&s.grounded_&&s.p_.x>290){jump=true;phase=1;}
    else if(phase==1&&s.p_.x>360&&s.p_.y<460){burst=true;phase=2;}
    else if(phase==2&&s.p_.x>600){x=0;if(s.grounded_)phase=3;}
    else if(phase==3){x=-1;if(s.p_.x<555){jump=true;phase=4;}}
    else if(phase==4){x=-1;if(s.p_.x<440&&s.p_.y<420){x=0;y=-1;burst=true;phase=5;}}
    else if(phase==5){if(s.p_.y<260)x=1;else x=0;if(s.grounded_)phase=6;}
    else if(phase==6&&s.p_.x>700){jump=true;phase=7;}
    else if(phase==7&&s.p_.x>780&&s.p_.y>125&&s.vy_>=0){burst=true;phase=8;}
    else if(phase==8&&s.gem_taken_&&s.dash_<=0){burst=true;phase=9;}
   }
   hui::InputFrame i;i.connected=true;i.stick_x=x;i.stick_y=y;if(jump)i.pressed=hui::action_bit(Action::confirm);if(burst)i.pressed|=hui::action_bit(Action::page_next);if(jump||s.vy_<0)i.held=hui::action_bit(Action::confirm);s.handle(i,f);s.update(1.f/60);
   if(n%12==0||jump||burst)std::printf("room%d n%d ph%d x%.1f y%.1f vx%.0f vy%.0f ground%d gem%d charge%d dash%.2f falls%u\n",room,n,phase,s.p_.x,s.p_.y,s.vx_,s.vy_,s.grounded_,s.gem_taken_,s.charged_,s.dash_,s.falls_);
   if(s.falls_)break;
  }std::printf("END room%d phase%d done%d falls%u\n",room,phase,s.room_complete_,s.falls_);
 }}
};}}
int main(){museum::DashInspection::run();}
