#include "platform/ps5/pad.hpp"
#include "platform/ps5/pad_state.hpp"
#include <cassert>
#include <algorithm>
#include <cstdio>
using hui::ps5::detail::RawPadSample;
namespace {int sleeps=0,initializations=0,terminations=0,opened_primary=0,closed_inactive=0,closed_second=0;bool read_error=false,service_error=false;}
namespace hui::sys {void log(const char*,...){}void sleep_us(std::uint32_t){++sleeps;}}
extern "C" {
int sceUserServiceInitialize(const void*){++initializations;return 0;}
int sceUserServiceTerminate(){++terminations;return 0;}
int sceUserServiceGetInitialUser(int*user){*user=10;return 0;}
int sceUserServiceGetLoginUserIdList(int users[4]){if(service_error)return -1;const int ids[]={10,11,12,-1};std::copy_n(ids,4,users);return 0;}
int scePadInit(){return 0;}
int scePadOpen(int user,int,int,const void*){if(user==10)++opened_primary;return 100+user;}
int scePadReadState(int handle,RawPadSample*sample){*sample={};sample->connected=handle==112;sample->left_x=sample->right_x=sample->right_y=128;sample->left_y=255;sample->buttons=hui::pad_bits::kCross;sample->timestamp_us=500;return 0;}
int scePadRead(int,RawPadSample*samples,int){if(read_error)return -1;*samples={};samples->connected=1;samples->left_y=128;samples->timestamp_us=1000;return 1;}
int scePadClose(int handle){if(handle==111)++closed_inactive;if(handle==112)++closed_second;return 0;}
int scePadSetVibrationMode(int,int){return 0;}
int scePadSetVibration(int,const void*){return 0;}
int scePadSetLightBar(int,const void*){return 0;}
int scePadSetMotionSensorState(int,bool){return 0;}
}
int main(){
 hui::ps5::Pad primary,second;assert(primary.open());assert(initializations==1&&sleeps==0);
 assert(second.open_secondary(primary.user_id()));assert(second.user_id()==12);
 assert(opened_primary==1&&closed_inactive==1&&initializations==1&&sleeps==0);
 std::array<hui::PadSample,64> samples;hui::InputTracker tracker;
 auto count=second.read(samples);assert(count==1&&samples[0].timestamp_us==500);
 auto frame=tracker.update(std::span(samples).first(count),500);
 assert(frame.connected&&frame.is_pressed(hui::Action::confirm)&&frame.stick_y>.9f);
 count=second.read(samples);assert(samples[0].timestamp_us==1000);
 read_error=true;count=second.read(samples);frame=tracker.update(std::span(samples).first(count),1500);
 assert(!frame.connected&&frame.focus_lost&&!frame.held&&frame.stick_y==0);
 second.close();assert(closed_second==1&&terminations==0);
 service_error=true;assert(!second.open_secondary(primary.user_id()));assert(sleeps==0);
 primary.close();assert(terminations==1);
 std::puts("PASS second-pad discovery: primary excluded, disconnected users skipped, no sleeps or duplicate service ownership, initial contact preserved, read errors release input, cleanup isolated.");
}
