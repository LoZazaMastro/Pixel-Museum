#pragma once
#include <algorithm>
#include <cmath>
namespace museum {
// Learn one gain from the first 1.25 seconds of audible PCM, then retain it.
// Silence and tiny signals pass through; they never train the measurement.
// No gate, limiter, compressor, per-block gain, or continuously rising AGC.
class CultureLevel {
    double window_energy_=0,audible_energy_=0;
    unsigned window_frames_=0,audible_frames_=0;
    float window_peak_=0,peak_=0,gain_=1,target_=1;
    bool enabled_=true,calibrated_=false;
public:
    void reset(bool enabled=true){*this=CultureLevel{};enabled_=enabled;}
    bool calibrated()const{return calibrated_;}
    float target_gain()const{return target_;}
    float gain()const{return gain_;}
    float process(float left,float right){
        if(!enabled_)return 1.f;
        if(!calibrated_){
            window_energy_+=double(left)*left+double(right)*right;
            window_peak_=std::max({window_peak_,std::abs(left),std::abs(right)});
            if(++window_frames_==2400){
                const double rms=std::sqrt(window_energy_/(2.*window_frames_));
                if(rms>=.001){audible_energy_+=window_energy_;audible_frames_+=window_frames_;peak_=std::max(peak_,window_peak_);}
                window_energy_=0;window_frames_=0;window_peak_=0;
                if(audible_frames_>=60000){
                    const float rms=float(std::sqrt(audible_energy_/(2.*audible_frames_)));
                    // Existing cultural trim is0.8:0.15 gives approximately
                    //0.12 RMS at full user volume before explicit curator gain.
                    target_=std::min({16.f,.15f/std::max(rms,.001f),.85f/std::max(peak_,.001f)});
                    calibrated_=true;
                }
            }
        }
        // Sample-clock smoothing is invariant under decoder block splitting.
        constexpr float blend=.0002975748f; //70ms time constant at48kHz.
        gain_+=(target_-gain_)*blend;
        return gain_;
    }
};
}
