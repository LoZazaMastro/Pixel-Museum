// Pixel Museum - bounded decoding of the locally documented libScePad state.
// SPDX-FileCopyrightText: 2026 Press5elect
// Layout reference: PSSwanStation ps5/src/ps5/pad_ps5.cpp (Press5elect,
// GPL-3.0-or-later), derived there from PSFlyCast. Physical PS5 motion remains
// unverified; decoding alone is not hardware validation.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "core/input.hpp"
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace hui::ps5::detail {
struct RawTouchPoint {
    std::uint16_t x,y;
    std::uint8_t id,reserved[3];
};
struct RawPadSample {
    std::uint32_t buttons;
    std::uint8_t left_x,left_y,right_x,right_y,l2,r2;
    std::uint8_t reserved0[2];
    float orientation[4];
    float acceleration[3];
    float angular_velocity[3];
    std::uint8_t touch_count,touch_reserved[3];
    std::uint32_t touch_reserved1;
    RawTouchPoint touch[2];
    std::int32_t connected;
    std::uint64_t timestamp_us;
    std::uint8_t extension[16],connected_count,reserved1[15];
};
static_assert(sizeof(RawPadSample)==120);
static_assert(offsetof(RawPadSample,orientation)==0x0c);
static_assert(offsetof(RawPadSample,acceleration)==0x1c);
static_assert(offsetof(RawPadSample,angular_velocity)==0x28);
static_assert(offsetof(RawPadSample,touch_count)==0x34);
static_assert(offsetof(RawPadSample,touch)==0x3c);
static_assert(offsetof(RawPadSample,connected)==0x4c);
static_assert(offsetof(RawPadSample,timestamp_us)==0x50);
static_assert(offsetof(RawPadSample,connected_count)==0x68);

inline PadSample decode_pad_state(const RawPadSample&r,bool motion_enabled){
    PadSample sample;
    sample.buttons=r.buttons;sample.left_x=r.left_x;sample.left_y=r.left_y;
    sample.right_x=r.right_x;sample.right_y=r.right_y;sample.l2=r.l2;sample.r2=r.r2;
    sample.connected=r.connected!=0;sample.timestamp_us=r.timestamp_us;
    if(!sample.connected||(sample.buttons&pad_bits::kIntercepted))return sample;
    if(motion_enabled){
        bool sane=true;float magnitude2=0;
        for(unsigned n=0;n<3;++n){
            sane=sane&&std::isfinite(r.acceleration[n])&&std::abs(r.acceleration[n])<16.f
                &&std::isfinite(r.angular_velocity[n])&&std::abs(r.angular_velocity[n])<100.f;
            magnitude2+=r.acceleration[n]*r.acceleration[n];
        }
        // An all-zero state cannot establish a functioning sensor. No Euler
        // angles or guessed calibration are inferred from the opaque quaternion.
        if(sane&&magnitude2>.000001f){
            sample.motion.available=true;const float magnitude=std::sqrt(magnitude2);
            for(unsigned n=0;n<3;++n){sample.motion.acceleration[n]=r.acceleration[n];
                sample.motion.direction[n]=r.acceleration[n]/magnitude;
                sample.motion.angular_velocity[n]=r.angular_velocity[n];}
        }
    }
    // Local DualSense reference uses the1920x1080 contact grid. Reject values
    // outside it instead of silently turning unrelated bytes into a gesture.
    if(r.touch_count>0&&r.touch_count<=2){
        bool sane=true;for(unsigned n=0;n<r.touch_count;++n)
            sane=sane&&r.touch[n].x<=1919&&r.touch[n].y<=1079;
        if(sane){sample.touch.available=true;sample.touch.count=r.touch_count;
            for(unsigned n=0;n<r.touch_count;++n)sample.touch.points[n]={
                float(r.touch[n].x)/1919.f,float(r.touch[n].y)/1079.f,r.touch[n].id};}
    }
    return sample;
}
}
