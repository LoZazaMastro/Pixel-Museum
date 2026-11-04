// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/windows/dualsense_haptic_pcm.hpp"
#include "ui/feedback.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>

int main(){
    using namespace hui;
    const auto effect=museum::desktop::dualsense_pcm_effect();
    for(unsigned n=0;n<effect.size();++n)
        assert(effect[n]==(n==1?0x62:n==39?0x01:0x00));
    audio::ControllerFeedback signals;signals.enabled(true);signals.tactile_enabled(true);
    std::array<float,museum::desktop::dualsense_haptic_frames*2> pcm{};
    std::array<std::uint8_t,museum::desktop::dualsense_haptic_payload_bytes> packet{};
    unsigned packets=0,idle_packets=0,heard=0;
    const auto tick=[&](){
        bool nonzero=false;
        assert(museum::desktop::stream_dualsense_haptic_tick(signals,pcm,[&](const float*block){
            museum::desktop::encode_dualsense_haptic_pcm(block,packet.data());
            nonzero=std::any_of(packet.begin(),packet.end(),[](auto v){return v!=0;});
            ++packets;if(!nonzero)++idle_packets;return true;
        }));
        return nonzero;
    };
    // Six real authored UI actions, alternating timeline detents and menu
    // focus cues, with enough silence to exceed the old four-tick tail.
    for(unsigned action=0;action<6;++action){
        for(unsigned n=0;n<24;++n)assert(!tick());
        ui::Feedback feedback;
        if(action%2==0)feedback.timeline_step(action%4? -1:1);
        else feedback.play(audio::Cue::focus);
        for(const auto&e:feedback.tactile)assert(signals.post(e));
        bool delivered=false;
        for(unsigned n=0;n<12;++n)delivered|=tick();
        assert(delivered);++heard;
    }
    assert(heard==6&&packets==6*(24+12)&&idle_packets>6*24&&signals.dropped()==0);
    // Input-device cancellation still flushes queued/current voices, while
    // the radio receives correctly clocked silence rather than stopping.
    assert(signals.post({audio::Tactile::confirm,.22f,.065f,0}));
    signals.tactile_enabled(false);
    for(unsigned n=0;n<8;++n)assert(!tick());
    signals.tactile_enabled(true);assert(signals.post({audio::Tactile::focus,.13f,.022f,0}));assert(tick());
    std::puts("PASS Bluetooth PCM cadence: 6/6 spaced timeline/menu actions encoded, every idle tick transmitted, no queue drops; input-device cancellation remains silent.");
}
