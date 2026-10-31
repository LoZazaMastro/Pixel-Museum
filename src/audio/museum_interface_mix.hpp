// Pixel Museum interface-only gain contract. Gameplay buses stay unchanged.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/cues.hpp"
namespace hui::audio::museum_original {
inline bool interface_cue(Cue cue){
    switch(cue){
        case Cue::focus:case Cue::select:case Cue::back:case Cue::tab:
        case Cue::open:case Cue::modal_open:case Cue::modal_close:case Cue::toggle:
        case Cue::slider:case Cue::error:case Cue::notify:case Cue::launch:
        case Cue::favorite_on:case Cue::favorite_off:case Cue::saved:
        case Cue::welcome:case Cue::resume:case Cue::type:case Cue::erase:case Cue::tick:
            return true;
        default:return false;
    }
}
inline float interface_gain(Cue cue,float requested){
    if(requested<=0.f||!interface_cue(cue))return requested;
    // The keyboard's default1 and timeline's .4/.6 share one reference.
    constexpr float audible_gain=1.8f;
    return audible_gain*(cue==Cue::focus||cue==Cue::slider||cue==Cue::tick?.6f:1.f);
}
}
