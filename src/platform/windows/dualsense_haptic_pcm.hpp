// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/controller_feedback.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace museum::desktop {
inline constexpr unsigned dualsense_haptic_frames=512;
inline constexpr unsigned dualsense_haptic_group=16;
inline constexpr unsigned dualsense_haptic_payload_bytes=dualsense_haptic_frames/dualsense_haptic_group*2;

inline std::array<std::uint8_t,47> dualsense_pcm_effect(){
    // SDL's DS5EffectsState starts at byte3 in Bluetooth report0x31.
    // Apply only audio/power/filter fields: no rumble-mode, LED, trigger or
    // speaker volume changes. SDL owns the Bluetooth framing and CRC32.
    std::array<std::uint8_t,47> effect{};
    effect[1]=0x02|0x20|0x40;
    effect[39]=0x01;
    return effect;
}

inline void encode_dualsense_haptic_pcm(const float*stereo,std::uint8_t*payload){
    for(unsigned sample=0;sample<dualsense_haptic_frames/dualsense_haptic_group;++sample)
        for(unsigned channel=0;channel<2;++channel){
            float average=0;
            for(unsigned i=0;i<dualsense_haptic_group;++i)
                average+=stereo[(sample*dualsense_haptic_group+i)*2+channel];
            const auto value=std::lround(std::clamp(average/float(dualsense_haptic_group),-1.f,1.f)*127.f);
            payload[sample*2+channel]=std::uint8_t(value);
        }
}

// Bluetooth audio is a clocked stream, including silence between gestures.
// Do not gate sends on amplitude: starving the controller's sample clock makes
// a later short focus cue double as stream restart instead of a complete cue.
template<class Sink>
bool stream_dualsense_haptic_tick(hui::audio::ControllerFeedback&signals,
        std::array<float,dualsense_haptic_frames*2>&pcm,Sink&&sink){
    signals.render_haptics(pcm.data(),dualsense_haptic_frames);
    return sink(pcm.data());
}
}
