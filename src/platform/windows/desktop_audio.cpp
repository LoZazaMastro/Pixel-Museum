#if defined(_WIN32)
// Museum sound plays on the PC; a DualSense can receive dedicated PCM haptics.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/windows/desktop_audio.hpp"
#include "museum/screen.hpp"
#include "museum/music.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <array>
#include <cctype>
#include <string>
namespace museum::desktop {
namespace {
bool controller_endpoint(const char* name){
    std::string value=name?name:"";
    std::transform(value.begin(),value.end(),value.begin(),[](unsigned char c){return char(std::tolower(c));});
    return value.find("dualsense")!=std::string::npos||value.find("wireless controller")!=std::string::npos||
        value.find("controller wireless")!=std::string::npos;
}
}
Audio::~Audio(){stop();}
bool Audio::start(Music&music,Screen&screen,hui::audio::Mixer&ui,hui::audio::ControllerFeedback&signals){
    music_=&music;screen_=&screen;ui_=&ui;signals_=&signals;
    refresh_controller(nullptr);
    return output_!=nullptr;
}
void Audio::stop(){
    if(output_){SDL_DestroyAudioStream(output_);output_=nullptr;}
    output_device_=0;
    bluetooth_.stop();
    close_controller();
}
void Audio::refresh_output(const SDL_AudioDeviceID* devices,int count){
    const char* raw=SDL_GetAudioDeviceName(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK);
    const std::string default_name=raw?raw:"";
    SDL_AudioDeviceID target=0;
    for(int i=0;i<count;++i){
        const char*name=SDL_GetAudioDeviceName(devices[i]);
        if(!name||controller_endpoint(name))continue;
        if(!target)target=devices[i];
        if(default_name==name){target=devices[i];break;}
    }
    if(output_&&output_device_==target)return;
    if(output_){SDL_DestroyAudioStream(output_);output_=nullptr;}
    output_device_=0;
    if(!target)return;
    const SDL_AudioSpec spec{SDL_AUDIO_F32,2,48000};
    output_=SDL_OpenAudioDeviceStream(target,&spec,mix,this);
    if(!output_||!SDL_ResumeAudioStreamDevice(output_)){
        hui::sys::log("[Windows] audio output: %s",SDL_GetError());
        if(output_){SDL_DestroyAudioStream(output_);output_=nullptr;}
        return;
    }
    output_device_=target;
}
void Audio::close_controller(){
    if(controller_){SDL_DestroyAudioStream(controller_);controller_=nullptr;}
    controller_device_=0;
}
void Audio::refresh_controller(SDL_Gamepad* dualsense){
    int count=0;
    auto*devices=SDL_GetAudioPlaybackDevices(&count);
    refresh_output(devices,count);
    const auto transport=dualsense?SDL_GetGamepadConnectionState(dualsense):SDL_JOYSTICK_CONNECTION_INVALID;
    const auto id=dualsense?SDL_GetGamepadID(dualsense):0;
    const auto wired=transport==SDL_JOYSTICK_CONNECTION_WIRED?id:0;
    const auto wireless=transport==SDL_JOYSTICK_CONNECTION_WIRELESS?id:0;
    if(bluetooth_pad_!=wireless){bluetooth_.stop();bluetooth_pad_=wireless;}
    if(controller_pad_!=wired){close_controller();controller_pad_=wired;}
    if(wireless&&!bluetooth_.ready()&&bluetooth_.start(dualsense,*signals_))
        hui::sys::log("[Windows] DualSense Bluetooth PCM haptics active");
    if(wired){
        SDL_AudioDeviceID quad=0;
        for(int i=0;i<count;++i){
            const char* name=SDL_GetAudioDeviceName(devices[i]);
            SDL_AudioSpec format{};
            if(controller_endpoint(name)&&SDL_GetAudioDeviceFormat(devices[i],&format,nullptr)&&format.channels==4){
                quad=devices[i];
                break;
            }
        }
        if(controller_device_!=quad)close_controller();
        if(quad&&!controller_){
            const SDL_AudioSpec spec{SDL_AUDIO_F32,4,48000};
            controller_=SDL_OpenAudioDeviceStream(quad,&spec,pad_mix,this);
            if(controller_&&SDL_ResumeAudioStreamDevice(controller_))controller_device_=quad;
            else close_controller();
        }
    }
    SDL_free(devices);
}
void SDLCALL Audio::mix(void*owner,SDL_AudioStream*stream,int needed,int){
    auto&a=*static_cast<Audio*>(owner);
    std::array<float,512>out{},speaker{},mono{};std::array<std::int16_t,512>ui{};
    int remaining=(needed+7)/8;
    while(remaining>0){const unsigned n=unsigned(std::min(256,remaining));
        a.music_->render(out.data(),n);std::fill(speaker.begin(),speaker.end(),0);
        a.screen_->mix_experience(out.data(),n);
        a.screen_->mix_video(out.data(),n,speaker.data(),false);
        a.signals_->render_speaker(mono.data(),n);
        for(unsigned j=0;j<n;++j){out[j*2]+=speaker[j]+mono[j];out[j*2+1]+=speaker[j]+mono[j];}
        a.ui_->render(ui.data(),int(n));for(unsigned j=0;j<n*2;++j)out[j]+=float(ui[j])/32768.f;
        a.gain_.process(out.data(),n,a.master.load(std::memory_order_relaxed));
        for(unsigned j=0;j<n*2;++j)out[j]=std::clamp(out[j],-1.f,1.f);
        SDL_PutAudioStreamData(stream,out.data(),int(n*2*sizeof(float)));remaining-=int(n);
    }
}
void SDLCALL Audio::pad_mix(void*owner,SDL_AudioStream*stream,int needed,int){
    auto&a=*static_cast<Audio*>(owner);
    std::array<float,512>haptic{};
    std::array<float,1024>out{};
    constexpr int frame_size=4*int(sizeof(float));
    int remaining=(needed+frame_size-1)/frame_size;
    while(remaining>0){
        const unsigned n=unsigned(std::min(256,remaining));
        a.signals_->render_haptics(haptic.data(),n);
        // Front channels feed the controller speaker. Leave both silent.
        for(unsigned j=0;j<n;++j){out[j*4+2]=haptic[j*2];out[j*4+3]=haptic[j*2+1];}
        SDL_PutAudioStreamData(stream,out.data(),int(n)*frame_size);
        remaining-=int(n);
    }
}
}

#endif // _WIN32
