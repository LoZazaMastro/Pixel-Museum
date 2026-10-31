// Original input regressions: no controller service or network is used.
#include "core/input.hpp"
#include "platform/ps5/pad_state.hpp"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <array>
#include <cstdio>
using hui::ps5::detail::RawPadSample;
using hui::ps5::detail::decode_pad_state;
int main(){
    // Byte offsets are exercised independently of C++ member assignment.
    std::array<std::uint8_t,120>bytes{};
    const auto put=[&](unsigned offset,const auto&value){std::memcpy(bytes.data()+offset,&value,sizeof(value));};
    put(0x4c,std::int32_t(1));put(0x50,std::uint64_t(123456));
    put(0x1c,.0f);put(0x20,.6f);put(0x24,.8f);put(0x28,.25f);
    put(0x34,std::uint8_t(2));put(0x3c,std::uint16_t(1919));put(0x3e,std::uint16_t(1079));put(0x40,std::uint8_t(7));
    put(0x44,std::uint16_t(0));put(0x46,std::uint16_t(0));put(0x48,std::uint8_t(9));
    RawPadSample raw{};std::memcpy(&raw,bytes.data(),bytes.size());
    auto off=decode_pad_state(raw,false);assert(off.connected&&!off.motion.available&&off.touch.count==2);
    assert(off.touch.points[0].x==1&&off.touch.points[0].y==1&&off.touch.points[0].id==7);
    assert(off.touch.points[1].x==0&&off.touch.points[1].y==0&&off.touch.points[1].id==9);
    auto sample=decode_pad_state(raw,true);assert(sample.motion.available&&sample.timestamp_us==123456);
    assert(std::abs(sample.motion.direction[1]-.6f)<.0001f&&std::abs(sample.motion.direction[2]-.8f)<.0001f);
    assert(sample.motion.angular_velocity[0]==.25f);
    auto invalid=raw;invalid.touch_count=3;assert(!decode_pad_state(invalid,true).touch.available);
    invalid=raw;invalid.touch[0].x=1920;assert(!decode_pad_state(invalid,true).touch.available);
    invalid=raw;invalid.acceleration[0]=std::numeric_limits<float>::quiet_NaN();assert(!decode_pad_state(invalid,true).motion.available);
    invalid=raw;invalid.angular_velocity[2]=1000;assert(!decode_pad_state(invalid,true).motion.available);
    invalid=raw;invalid.acceleration[0]=invalid.acceleration[1]=invalid.acceleration[2]=0;assert(!decode_pad_state(invalid,true).motion.available);
    invalid=raw;invalid.buttons=hui::pad_bits::kIntercepted;assert(!decode_pad_state(invalid,true).motion.available&&!decode_pad_state(invalid,true).touch.available);
    invalid=raw;invalid.connected=0;assert(!decode_pad_state(invalid,true).motion.available&&!decode_pad_state(invalid,true).touch.available);
    hui::InputTracker tracker;
    auto frame=tracker.update(std::span(&sample,1),123456);assert(frame.motion.available&&frame.touch.count==2);
    frame=tracker.update({},123457);assert(!frame.motion.available&&!frame.touch.available&&frame.touch.count==0);
    sample.buttons=hui::pad_bits::kIntercepted;sample.left_x=255;
    frame=tracker.update(std::span(&sample,1),123458);assert(frame.focus_lost&&!frame.motion.available&&!frame.touch.available&&frame.nav==hui::Direction::none);
    sample.buttons=0;sample.left_x=128;sample.left_y=128;
    frame=tracker.update(std::span(&sample,1),123459);assert(frame.motion.available&&frame.touch.count==2);
    sample.connected=false;frame=tracker.update(std::span(&sample,1),123460);assert(frame.focus_lost&&!frame.motion.available&&!frame.touch.available);
    // A contact that ends within one buffered batch is not kept as a drag.
    sample.connected=true;auto end=sample;end.touch={};std::array batch{sample,end};
    frame=tracker.update(batch,123461);assert(frame.motion.available&&!frame.touch.available);
    // Future platform adapters cannot smuggle non-finite coordinates through.
    sample.touch.points[0].x=std::numeric_limits<float>::quiet_NaN();
    frame=tracker.update(std::span(&sample,1),123462);assert(!frame.touch.available);
    sample.motion.acceleration[1]=std::numeric_limits<float>::infinity();
    frame=tracker.update(std::span(&sample,1),123463);assert(!frame.motion.available);
    std::puts("Optional controller decoding passed: byte offsets, default-off motion, finite direction, two normalized contacts, invalid data rejection, fresh-sample gating, interception/disconnect clearing and no retained drag.");
}
