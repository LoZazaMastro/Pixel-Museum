// Pixel Museum - Continuous system stereo audio with controller independent playback.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/ps5/museum_audio.hpp"
#include "audio/mixer.hpp"
#include "audio/output_peak_guard.hpp"
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
MuseumAudio::~MuseumAudio() { stop(); }
bool MuseumAudio::start(Render render, void *context) {
    if (running_) return true;
    const int rc=sceAudioOutInit();
    if (rc!=0 && rc!=static_cast<int>(0x8026000e)) return false;
    port_=sceAudioOutOpen(0xff,0,0,256,48000,1); if (port_<0) return false;
    render_=render; context_=context; stop_.store(false);
    pthread_attr_t attr; pthread_attr_init(&attr); pthread_attr_setstacksize(&attr,256u<<10);
    const int created=pthread_create(&thread_,&attr,&MuseumAudio::entry,this); pthread_attr_destroy(&attr);
    if (created!=0) { sceAudioOutClose(port_); port_=-1; return false; }
    running_=true; return true;
}
void *MuseumAudio::entry(void *p) { static_cast<MuseumAudio*>(p)->run(); return nullptr; }
void MuseumAudio::run() {
    alignas(64) std::array<std::int16_t,512> pcm{};
    std::array<float,512> floating{};
    audio::OutputPeakGuard peak_guard;
    while (!stop_.load(std::memory_order_acquire)) {
        floating.fill(0); if (render_) render_(context_,floating.data(),256);
        peak_guard.convert(floating.data(),pcm.data(),256);
        if (sceAudioOutOutput(port_,pcm.data())<0) sys::sleep_us(5000);
    }
    sceAudioOutOutput(port_,nullptr);
}
void MuseumAudio::stop() {
    if (running_) { stop_.store(true); pthread_join(thread_,nullptr); running_=false; }
    if (port_>=0) sceAudioOutClose(port_); port_=-1;
}
} // namespace hui::ps5
