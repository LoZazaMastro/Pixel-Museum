// Exercises real relative gyro filter and the native pad sensor decoder.
#include "museum/flight_motion.hpp"
#include "platform/ps5/pad_state.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
hui::MotionData motion(float x=0,float z=0){hui::MotionData m;m.available=true;m.angular_velocity={x,0,z};return m;}
void calibrate(museum::FlightMotion&f,float bias=0){for(int n=0;n<30;++n)f.update(motion(bias,bias),.01f);assert(f.calibrated());}
int main(){
 museum::FlightMotion f;f.update({},.01f);assert(!f.calibrated());
 for(int n=0;n<100;++n)f.update(motion(.4f,0),.01f);assert(!f.calibrated());
 calibrate(f,.02f);for(int n=0;n<6000;++n)f.update(motion(.025f,.015f),1.f/120);assert(std::abs(f.value()[0])<.0001f&&std::abs(f.value()[1])<.0001f);
 for(int n=0;n<120;++n)f.update(motion(.52f,.52f),1.f/120);assert(f.value()[0]<-.95f&&f.value()[1]<-.95f);
 f.reset();calibrate(f);for(int n=0;n<120;++n)f.update(motion(-1,-1),1.f/120);assert(f.value()[0]>.99f&&f.value()[1]>.99f);
 auto before=f.value();f.update(motion(1,1),std::numeric_limits<float>::quiet_NaN());assert(f.value()==before);
 f.update(motion(std::numeric_limits<float>::quiet_NaN(),0),.01f);assert(!f.calibrated()&&f.value()[0]==0);
 calibrate(f);f.update({},.01f);assert(f.calibrated());for(int n=0;n<20;++n)f.update({},.01f);assert(!f.calibrated()&&f.value()[0]==0);calibrate(f);
 museum::FlightMotion a,b;calibrate(a);calibrate(b);for(int n=0;n<30;++n)a.update(motion(.3f,.2f),1.f/30);for(int n=0;n<120;++n)b.update(motion(.3f,.2f),1.f/120);for(unsigned n=0;n<2;++n)assert(std::abs(a.value()[n]-b.value()[n])<.012f);
 hui::ps5::detail::RawPadSample raw{};raw.connected=1;raw.acceleration[1]=1;raw.angular_velocity[2]=.4f;auto sample=hui::ps5::detail::decode_pad_state(raw,true);assert(sample.motion.available&&sample.motion.angular_velocity[2]==.4f);assert(!hui::ps5::detail::decode_pad_state(raw,false).motion.available);raw.buttons=hui::pad_bits::kIntercepted;assert(!hui::ps5::detail::decode_pad_state(raw,true).motion.available);raw.buttons=0;raw.connected=0;assert(!hui::ps5::detail::decode_pad_state(raw,true).motion.available);
 std::puts("PASS gyro: native enabled-only decode, calibration, moving-pose rejection, bias+angle deadzones, bounded tilt, 30/120Hz time consistency, invalid samples/dt and reconnect recalibration. Physical PS5 axes pending.");
}
