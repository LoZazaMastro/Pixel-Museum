// Exercises the real pad driver through documented compatible-vibration calls.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/ps5/pad.hpp"
#include "platform/ps5/pad_state.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
namespace {unsigned commands=0,modes=0;bool fail_once=false,connected=true,fail_mode_once=false;unsigned last_mode=0;unsigned left=0,right=0;}
namespace hui::sys {void log(const char*,...){} void sleep_us(unsigned){} }
extern "C" {
int sceUserServiceInitialize(const void*){return 0;}int sceUserServiceTerminate(){return 0;}int sceUserServiceGetInitialUser(int*u){*u=1;return 0;}
int scePadInit(){return 0;}int scePadOpen(int,int,int,const void*){return 7;}int scePadClose(int){return 0;}
int scePadSetVibrationMode(int,int mode){assert(mode==1||mode==2);last_mode=unsigned(mode);++modes;if(fail_mode_once){fail_mode_once=false;return -1;}return 0;}
int scePadSetVibration(int,const void*raw){++commands;const auto*b=static_cast<const unsigned char*>(raw);left=b[0];right=b[1];if(fail_once){fail_once=false;return -1;}return 0;}
int scePadSetLightBar(int,const void*){return 0;}int scePadSetMotionSensorState(int,bool){return 0;}
int scePadRead(int,hui::ps5::detail::RawPadSample*out,int){out[0]={};out[0].connected=connected?1:0;return 1;}
}
int main(){
 hui::ps5::Pad pad;assert(pad.open());pad.rumble(.10f,.04f);assert(left>50&&right>80);pad.tick(.06f);assert(left==0&&right==0);
 pad.rumble(.3f,.3f);assert(left>0&&right>0);const auto in_flight=commands;pad.tick(.0001f,false);assert(commands==in_flight+1&&left==0&&right==0);const auto cancelled=commands;pad.tick(.0001f,false);pad.tick(.001f);assert(commands==cancelled);
 const auto before=commands;pad.rumble(std::numeric_limits<float>::quiet_NaN(),.1f);assert(commands==before);
 fail_once=true;pad.rumble(.2f,.06f);assert(modes>=2&&left>90&&right>100);
 std::array<hui::PadSample,2>samples;pad.read(samples);const auto first=modes;connected=false;pad.read(samples);connected=true;pad.read(samples);assert(modes==first+1);
 assert(pad.user_id()==1);assert(pad.set_advanced_haptics(true));assert(last_mode==1);const auto advanced_commands=commands;pad.rumble(.4f,.1f);pad.tick(.001f,false);assert(commands==advanced_commands);
 connected=false;pad.read(samples);connected=true;pad.read(samples);assert(last_mode==1);assert(pad.set_advanced_haptics(false));assert(last_mode==2);pad.rumble(.4f,.05f);assert(left>0);
 fail_mode_once=true;assert(!pad.set_advanced_haptics(true));assert(last_mode==2);const auto failed=modes;assert(!pad.set_advanced_haptics(true));assert(modes==failed);pad.rumble(.4f,.05f);assert(left>0);assert(pad.set_advanced_haptics(false));
 pad.close();assert(left==0&&right==0);std::puts("PASS compatible DualSense feedback: both motors, timed stop, failure recovery, advanced mode handoff/quiet motors/reconnect/failure fallback, and invalid input");
}
