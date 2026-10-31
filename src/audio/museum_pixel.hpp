// Original Pixel Museum felt/FM ignition. No samples or borrowed melodies.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/mixer.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <vector>
namespace hui::audio::museum_original {
inline float pixel_sample(float pitch,float t,float duration){
    constexpr float tau=6.2831853071795864769f;
    const float phase=tau*440.f*pitch*t;
    const float body=std::sin(phase+.28f*std::exp(-t/.018f)*std::sin(phase*2.f))
        +.06f*std::sin(phase*3.f)*std::exp(-t/.020f);
    const float attack=1.f-std::exp(-t/.0025f);
    const float decay=std::exp(-t/(duration>.5f?.19f:.095f));
    const float release=std::clamp((duration-t)/.018f,0.f,1.f);
    return body*attack*decay*release*release*.40f;
}
struct PixelBank {
    inline static constexpr std::array<int,13> notes{50,57,60,62,64,65,69,72,74,76,77,81,86};
    std::array<std::vector<float>,13> samples;
    std::array<Clip,13> clips;
    PixelBank(){
        for(unsigned i=0;i<notes.size();++i){
            const float seconds=notes[i]==86?.75f:.38f;
            const auto frames=unsigned(seconds*48000.f);
            auto& pcm=samples[i];pcm.resize(frames*2);
            const float pitch=std::exp2(float(notes[i]-69)/12.f);
            for(unsigned n=0;n<frames;++n){
                const float value=pixel_sample(pitch,float(n)/48000.f,seconds)*.70710678f;
                pcm[n*2]=pcm[n*2+1]=value;
            }
            pcm[0]=pcm[1]=pcm[pcm.size()-2]=pcm.back()=0;
            clips[i]={pcm.data(),frames};
        }
    }
};
// Construct on the UI thread before starting audio; the callback only reads.
inline PixelBank& pixel_bank(){static PixelBank bank;return bank;}
inline const Clip* pixel_clip(int note){
    auto&bank=pixel_bank();
    for(unsigned i=0;i<PixelBank::notes.size();++i)if(PixelBank::notes[i]==note)return &bank.clips[i];
    return nullptr;
}
}
