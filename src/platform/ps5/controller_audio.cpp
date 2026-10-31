// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/ps5/controller_audio.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
extern "C" {
int sceAudioOutInit(void);
int sceAudioOutOpen(int,int,int,unsigned,unsigned,unsigned);
int sceAudioOutOutput(int,const void*);
int sceAudioOutClose(int);
}
namespace hui::ps5 {
namespace {
// Public independent ABI references: AnyPS5 libSceAudioOut/AudioOut.cpp,
// PORT_TYPE_PADSPK=4, PORT_TYPE_VIBRATION=10; S16 mono=0/stereo=1.
// No proprietary SDK headers or platform middleware are included.
constexpr int speaker_port=4,haptics_port=10;
constexpr unsigned grain=256,sample_rate=48000;
}
bool ControllerAudio::open(Output&o,int user,int type,bool speaker,audio::ControllerFeedback&signals){
    o.speaker=speaker;o.signals=&signals;
    o.port=sceAudioOutOpen(user,type,0,grain,sample_rate,speaker?0u:1u);
    sys::log("[Museum] controller PCM %s open user=0x%08x type=%d result=0x%08x",speaker?"speaker":"haptics",unsigned(user),type,unsigned(o.port));
    if(o.port<0)return false;
    o.stop.store(false,std::memory_order_release);o.healthy.store(true,std::memory_order_release);
    pthread_attr_t attr;pthread_attr_init(&attr);pthread_attr_setstacksize(&attr,128u<<10);
    const int result=pthread_create(&o.thread,&attr,&ControllerAudio::run,&o);pthread_attr_destroy(&attr);
    if(result){o.healthy.store(false);sceAudioOutClose(o.port);o.port=-1;return false;}
    o.started=true;return true;
}
bool ControllerAudio::start(int user,audio::ControllerFeedback&signals){
    if(speaker_.started||haptics_.started)return true;
    const int result=sceAudioOutInit();if(result&&result!=static_cast<int>(0x8026000e))return false;
    const bool speaker=open(speaker_,user,speaker_port,true,signals);
    const bool haptics=open(haptics_,user,haptics_port,false,signals);
    return speaker||haptics;
}
void*ControllerAudio::run(void*context){
    auto&o=*static_cast<Output*>(context);alignas(64)std::array<std::int16_t,grain*2>pcm{};
    std::array<float,grain*2>samples{};unsigned errors=0;bool first=true;
    while(!o.stop.load(std::memory_order_acquire)){
        if(o.speaker)o.signals->render_speaker(samples.data(),grain);else o.signals->render_haptics(samples.data(),grain);
        const unsigned count=grain*(o.speaker?1u:2u);
        unsigned peak=0;
        for(unsigned n=0;n<count;++n){pcm[n]=std::int16_t(std::clamp(std::isfinite(samples[n])?samples[n]:0.f,-1.f,1.f)*32767);peak=std::max(peak,unsigned(std::abs(int(pcm[n]))));}
        const int result=sceAudioOutOutput(o.port,pcm.data());
        if(result>=0&&peak){o.nonzero_blocks.fetch_add(1,std::memory_order_relaxed);o.peak.store(std::max(peak,o.peak.load(std::memory_order_relaxed)),std::memory_order_relaxed);}
        if(first||result<0){sys::log("[Museum] controller PCM %s output result=0x%08x",o.speaker?"speaker":"haptics",unsigned(result));first=false;}
        if(result<0){o.healthy.store(false,std::memory_order_release);if(++errors>=3)break;sys::sleep_us(5000);}
        else{errors=0;o.healthy.store(true,std::memory_order_release);}
    }
    o.healthy.store(false,std::memory_order_release);sceAudioOutOutput(o.port,nullptr);return nullptr;
}
void ControllerAudio::close(Output&o){
    if(o.started){o.stop.store(true,std::memory_order_release);pthread_join(o.thread,nullptr);o.started=false;}
    if(o.port>=0)sceAudioOutClose(o.port);o.port=-1;o.healthy.store(false,std::memory_order_release);
}
void ControllerAudio::stop(){close(speaker_);close(haptics_);}
}
