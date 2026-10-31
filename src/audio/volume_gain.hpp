// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cmath>

namespace hui::audio {
// Audio-thread-owned, sample-clock ramp shared by both stereo channels.
class VolumeGain {
public:
    void snap(float value) { gain_=valid(value); }
    void process(float* stereo,unsigned frames,float target) {
        target=valid(target);
        constexpr float step=1.f/(48000.f*.020f);
        for(unsigned n=0;n<frames;++n){
            gain_+=std::clamp(target-gain_,-step,step);
            stereo[n*2]*=gain_;stereo[n*2+1]*=gain_;
        }
    }
private:
    static float valid(float value){return std::isfinite(value)?std::clamp(value,0.f,1.f):0.f;}
    float gain_=1.f;
};
}
