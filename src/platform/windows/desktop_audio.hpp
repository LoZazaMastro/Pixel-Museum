// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/mixer.hpp"
#include "audio/controller_feedback.hpp"
#include "audio/volume_gain.hpp"
#include <SDL3/SDL.h>
#include <atomic>
namespace museum {class Music;class Screen;}
namespace museum::desktop {
class Audio {
public:
    ~Audio();
    bool start(Music&,Screen&,hui::audio::Mixer&,hui::audio::ControllerFeedback&);
    void stop();
    void refresh_controller(bool dualsense);
    bool controller_audio()const{return controller_ready_.load(std::memory_order_acquire);}
    std::atomic<float> master{1.f};
    std::atomic<bool> culture_pad{false};
private:
    static void SDLCALL mix(void*,SDL_AudioStream*,int,int);
    static void SDLCALL pad_mix(void*,SDL_AudioStream*,int,int);
    Music*music_=nullptr;Screen*screen_=nullptr;hui::audio::Mixer*ui_=nullptr;hui::audio::ControllerFeedback*signals_=nullptr;
    SDL_AudioStream*output_=nullptr,*controller_=nullptr;
    std::atomic<bool> controller_ready_{false};
    hui::audio::VolumeGain gain_;
};
}
