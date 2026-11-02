#if defined(_WIN32)
// Original museum mix, with USB DualSense PCM and audible fallback on ordinary PC audio.
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
Audio::~Audio(){stop();}
bool Audio::start(Music&music,Screen&screen,hui::audio::Mixer&ui,hui::audio::ControllerFeedback&signals){
    music_=&music;screen_=&screen;ui_=&ui;signals_=&signals;
    SDL_AudioSpec spec{SDL_AUDIO_F32,2,48000};
    output_=SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,&spec,mix,this);
    if(!output_){hui::sys::log("[Windows] audio: %s",SDL_GetError());return false;}
    SDL_ResumeAudioStreamDevice(output_);return true;
}
void Audio::stop(){
    if(output_){SDL_DestroyAudioStream(output_);output_=nullptr;}
    if(controller_){SDL_DestroyAudioStream(controller_);controller_=nullptr;}
    controller_ready_.store(false,std::memory_order_release);
}
void Audio::refresh_controller(bool dualsense){
    if(!dualsense){if(controller_){
        if(output_)SDL_LockAudioStream(output_);
        SDL_DestroyAudioStream(controller_);controller_=nullptr;controller_ready_.store(false,std::memory_order_release);
        if(output_)SDL_UnlockAudioStream(output_);
    }return;}
    if(controller_)return;
    int count=0;auto*devices=SDL_GetAudioPlaybackDevices(&count);
    for(int i=0;i<count;++i){const char*raw=SDL_GetAudioDeviceName(devices[i]);std::string name=raw?raw:"";
        std::transform(name.begin(),name.end(),name.begin(),[](unsigned char c){return char(std::tolower(c));});
        if(name.find("dualsense")==std::string::npos&&name.find("wireless controller")==std::string::npos)continue;
        SDL_AudioSpec physical{};if(!SDL_GetAudioDeviceFormat(devices[i],&physical,nullptr)||physical.channels!=4||physical.freq!=48000)continue;
        SDL_AudioSpec spec{SDL_AUDIO_F32,4,48000};controller_=SDL_OpenAudioDeviceStream(devices[i],&spec,pad_mix,this);
        if(controller_){
            if(output_)SDL_LockAudioStream(output_);
            controller_ready_.store(true,std::memory_order_release);SDL_ResumeAudioStreamDevice(controller_);
            if(output_)SDL_UnlockAudioStream(output_);
            hui::sys::log("[Windows] USB DualSense four-channel audio: %s",raw);break;
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
        a.screen_->mix_experience(out.data(),n,speaker.data());
        a.screen_->mix_video(out.data(),n,speaker.data(),a.culture_pad.load(std::memory_order_relaxed));
        if(a.controller_ready_.load(std::memory_order_acquire)){a.signals_->submit_speaker(speaker.data(),n);}
        else{
            // An ordinary controller has no speaker. Preserve these sounds on
            // the PC output so gameplay cues and cultural recordings stay audible.
            a.signals_->render_speaker(mono.data(),n);
            for(unsigned j=0;j<n;++j)out[j*2]+=speaker[j]+mono[j],out[j*2+1]+=speaker[j]+mono[j];
        }
        a.ui_->render(ui.data(),int(n));for(unsigned j=0;j<n*2;++j)out[j]+=float(ui[j])/32768.f;
        a.gain_.process(out.data(),n,a.master.load(std::memory_order_relaxed));
        for(unsigned j=0;j<n*2;++j)out[j]=std::clamp(out[j],-1.f,1.f);
        SDL_PutAudioStreamData(stream,out.data(),int(n*2*sizeof(float)));remaining-=int(n);
    }
}
void SDLCALL Audio::pad_mix(void*owner,SDL_AudioStream*stream,int needed,int){
    auto&a=*static_cast<Audio*>(owner);std::array<float,256>speaker{};std::array<float,512>haptic{};std::array<float,1024>out{};
    int remaining=(needed+15)/16;while(remaining>0){const unsigned n=unsigned(std::min(256,remaining));
        a.signals_->render_speaker(speaker.data(),n);a.signals_->render_haptics(haptic.data(),n);
        for(unsigned j=0;j<n;++j){out[j*4]=out[j*4+1]=speaker[j];out[j*4+2]=haptic[j*2];out[j*4+3]=haptic[j*2+1];}
        SDL_PutAudioStreamData(stream,out.data(),int(n*4*sizeof(float)));remaining-=int(n);
    }
}
}

#endif // _WIN32
