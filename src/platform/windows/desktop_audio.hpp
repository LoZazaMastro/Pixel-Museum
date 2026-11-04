// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/mixer.hpp"
#include "audio/controller_feedback.hpp"
#include "audio/volume_gain.hpp"
#include "platform/windows/dualsense_bluetooth.hpp"
#include <SDL3/SDL.h>
#include <atomic>
namespace museum {class Music;class Screen;}
namespace museum::desktop {
class Audio {
public:
    ~Audio();
    bool start(Music&,Screen&,hui::audio::Mixer&,hui::audio::ControllerFeedback&);
    void stop();
    void refresh_controller(SDL_Gamepad* dualsense);
    bool controller_haptics()const{return bluetooth_.ready()||controller_!=nullptr;}
    std::atomic<float> master{1.f};
private:
    void refresh_output(const SDL_AudioDeviceID*,int);
    void close_controller();
    static void SDLCALL mix(void*,SDL_AudioStream*,int,int);
    static void SDLCALL pad_mix(void*,SDL_AudioStream*,int,int);
    Music*music_=nullptr;Screen*screen_=nullptr;hui::audio::Mixer*ui_=nullptr;hui::audio::ControllerFeedback*signals_=nullptr;
    SDL_AudioStream*output_=nullptr,*controller_=nullptr;
    SDL_JoystickID controller_pad_=0;
    SDL_JoystickID bluetooth_pad_=0;
    DualSenseBluetooth bluetooth_;
    SDL_AudioDeviceID output_device_=0,controller_device_=0;
    hui::audio::VolumeGain gain_;
};
}
