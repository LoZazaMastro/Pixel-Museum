// Pixel Museum - transparent stereo PCM output, limiting only actual overload.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
namespace hui::audio {
class OutputPeakGuard {
public:
    void convert(const float* input,std::int16_t* output,std::size_t frames){
        float peak=0;
        for(std::size_t i=0;i<frames*2;++i)if(std::isfinite(input[i]))peak=std::max(peak,std::fabs(input[i]));
        // A normal full-scale stream stays linear, including peaks above the
        // old 0.7 waveshaper knee. One gain for both channels preserves stereo.
        const float required=peak>1.f?1.f/peak:1.f;
        gain_=std::min(gain_,required);
        for(std::size_t i=0;i<frames*2;++i){
            const float sample=std::isfinite(input[i])?std::clamp(input[i]*gain_,-1.f,1.f):0.f;
            output[i]=static_cast<std::int16_t>(std::lrint(sample*32767.f));
        }
        // Slow release after overlapping sounds overload the output. Never
        // compress or reshape an otherwise valid music waveform sample-wise.
        gain_+=(1.f-gain_)*(1.f-std::exp(-float(frames)/(48000.f*.15f)));
    }
private:
    float gain_=1.f;
};
}
