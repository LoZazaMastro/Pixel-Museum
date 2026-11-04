// Original Pixel Museum Windows trophy chime.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include "audio/mixer.hpp"
#include <algorithm>
#include <array>
#include <cmath>

namespace hui::audio::museum_original {
inline const Clip& trophy_chime(){
    static constexpr float duration=.62f;
    static constexpr auto frames=static_cast<std::size_t>(duration*kSampleRate);
    struct Recording {
        std::array<float,frames*2> pcm{};
        Clip clip{pcm.data(),frames};

        Recording(){
            struct Strike {float start,hz,level,decay,pan;};
            constexpr std::array strikes{
                Strike{.000f, 587.33f, .60f, .092f,-.16f},
                Strike{.071f, 880.00f, .49f, .103f, .14f},
                Strike{.135f,1046.50f, .40f, .106f,-.08f},
                Strike{.196f,1174.66f, .55f, .139f, .08f},
                Strike{.196f, 293.66f, .24f, .120f, .00f},
            };
            constexpr float tau=6.28318530718f;
            const auto tone=[](const Strike& note,float time){
                if(time<=0.f)return 0.f;
                const float phase=tau*note.hz*time;
                const float attack=1.f-std::exp(-time/.0024f);
                const float felt=std::sin(phase+.36f*std::sin(phase*2.f)*std::exp(-time/.021f))
                    *std::exp(-time/note.decay);
                const float metal=.23f*std::sin(phase*2.11f)*std::exp(-time/.054f)
                    +.10f*std::sin(phase*3.77f)*std::exp(-time/.027f);
                return note.level*attack*(felt+metal);
            };

            float peak=0.f;
            for(std::size_t n=0;n<frames;++n){
                const float time=float(n)/kSampleRate;
                const float tail=std::clamp((duration-time)/.065f,0.f,1.f);
                for(const auto& note:strikes){
                    const float age=time-note.start;
                    const float dry=tone(note,age);
                    const float reflection=.10f*tone(note,age-.023f);
                    pcm[n*2]+=(dry*(1.f-note.pan)+reflection*(1.f+note.pan))*tail*tail;
                    pcm[n*2+1]+=(dry*(1.f+note.pan)+reflection*(1.f-note.pan))*tail*tail;
                }
                peak=std::max({peak,std::abs(pcm[n*2]),std::abs(pcm[n*2+1])});
            }
            const float gain=.43f/peak;
            for(auto& value:pcm)value*=gain;
            pcm.front()=pcm[1]=pcm[pcm.size()-2]=pcm.back()=0.f;
        }
    };
    // Build once on the calling UI thread. The mixer only sees immutable samples.
    static const Recording recording;
    return recording.clip;
}
}
