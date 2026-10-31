// Pixel Museum - relative, calibrated gyro steering for the wireframe study.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "core/input.hpp"
#include <algorithm>
#include <array>
#include <cmath>
namespace museum {
class FlightMotion {
    std::array<float,2> bias_{},sum_{},angle_{},output_{};
    float calibration_=0,missing_=0;bool calibrated_=false;
public:
    void reset(){bias_=sum_=angle_=output_={};calibration_=missing_=0;calibrated_=false;}
    bool calibrated()const{return calibrated_;}
    const std::array<float,2>& value()const{return output_;}
    void update(const hui::MotionData&m,float dt){
        if(!std::isfinite(dt)||dt<=0)return;dt=std::min(dt,.05f);
        if(!m.available){missing_+=dt;if(missing_>.15f)reset();return;}missing_=0;
        // scePad angular-velocity axes: roll about Z, pitch about X. These
        // are relative rotations; no Euler pose is guessed from acceleration.
        const std::array<float,2> rate{-m.angular_velocity[2],-m.angular_velocity[0]};
        for(float r:rate)if(!std::isfinite(r)||std::abs(r)>=100.f){reset();return;}
        if(!calibrated_){
            if(std::abs(rate[0])>.08f||std::abs(rate[1])>.08f){sum_={};calibration_=0;return;}
            for(unsigned n=0;n<2;++n)sum_[n]+=rate[n]*dt;
            calibration_+=dt;if(calibration_>=.2f){for(unsigned n=0;n<2;++n)bias_[n]=sum_[n]/calibration_;calibrated_=true;}return;
        }
        const float smooth=1-std::exp(-dt/.065f);
        for(unsigned n=0;n<2;++n){
            float r=rate[n]-bias_[n];r=std::copysign(std::max(0.f,std::abs(r)-.012f),r);
            angle_[n]=std::clamp(angle_[n]+r*dt,-.70f,.70f);
            const float target=std::copysign(std::clamp((std::abs(angle_[n])-.025f)/.38f,0.f,1.f),angle_[n]);
            output_[n]+=(target-output_[n])*smooth;
        }
    }
};
}
