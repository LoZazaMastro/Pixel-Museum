// Pixel Museum - desktop trophy presentation and sound routing.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/museum_trophy_chime.hpp"
#include <algorithm>

namespace museum::desktop_trophy {
inline constexpr float duration=6.f;
inline float opacity(float remaining){
    return std::min(std::clamp((duration-remaining)/.2f,0.f,1.f),std::clamp(remaining/.25f,0.f,1.f));
}
// One pass, with a pause at either end, exposes the complete subtitle during
// this notification's lifetime without resetting when the underlying page moves.
inline float text_offset(float measured,float room,float remaining,bool reduced){
    if(reduced||measured<=room)return 0;
    const float progress=std::clamp((duration-remaining-.8f)/(duration-1.6f),0.f,1.f);
    return (measured-room)*progress;
}
inline void play_sound(hui::audio::Mixer&mixer,float master,float sfx){
    // The mixer and Windows output already apply these levels. Do not bypass
    // either mute or multiply the configured gain for a second time.
    if(!(master>0.f&&sfx>0.f))return;
    mixer.play_clip(&hui::audio::museum_original::trophy_chime(),
        {1.f,1.f,0.f,hui::audio::Bus::sfx});
}
}
