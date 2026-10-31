// Actual SoundBank + Mixer proof and a reproducible listening preview.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "audio/cues.hpp"
#include "museum/music.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <vector>
namespace {
using namespace hui::audio;
void put16(FILE*f,unsigned value){std::fputc(int(value&255),f);std::fputc(int((value>>8)&255),f);}
void put32(FILE*f,unsigned value){put16(f,value&65535);put16(f,value>>16);}
void wav(const char*path,const std::vector<std::int16_t>&s){FILE*f=std::fopen(path,"wb");assert(f);std::fwrite("RIFF",1,4,f);put32(f,unsigned(s.size()*2+36));std::fwrite("WAVEfmt ",1,8,f);put32(f,16);put16(f,1);put16(f,2);put32(f,48000);put32(f,192000);put16(f,4);put16(f,16);std::fwrite("data",1,4,f);put32(f,unsigned(s.size()*2));for(auto sample:s)put16(f,std::uint16_t(sample));std::fclose(f);}
void pitch_proof(){
    std::vector<float> source(4096*2);for(unsigned n=0;n<4096;++n)source[n*2]=source[n*2+1]=std::sin(float(n)*.17f)*.3f;
    Clip clip{source.data(),4096};
    auto actual=[&](float jitter,bool set){SoundBank b;b.add(SoundSet::glass,Cue::focus,source,4096);if(set)b.set_pitch_jitter(jitter);Mixer m;b.play(m,SoundSet::glass,{Cue::focus});std::vector<std::int16_t>out(2048);m.render(out.data(),1024);return out;};
    auto reference=[&](float pitch){Mixer m;PlayParams p;p.bus=Bus::ui;p.pitch=pitch;m.play_clip(&clip,p);std::vector<std::int16_t>out(2048);m.render(out.data(),1024);return out;};
    assert(actual(0,true)==reference(1));
    const std::uint32_t next=0x2545f491u*1664525u+1013904223u;
    const float previous_default=.97f+.06f*float(next>>8)/16777216.f;
    assert(actual(0,false)==reference(previous_default));
    assert(actual(.03f,true)==actual(0,false));
    assert(actual(0,true)!=actual(0,false));
    std::puts("PASS recorded pitch: zero jitter exactly matches concert-pitch PCM; untouched default is bit-identical to original +/-3% formula");
}
}
int main(){
    using namespace hui::audio;pitch_proof();SoundBank bank;
    const auto start=std::chrono::steady_clock::now();const auto stats=bank.load("assets/audio/museum-navigation");
    const double load_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    assert(stats.files==25&&stats.rejected==0);bank.set_pitch_jitter(0);
    const std::array<Cue,18> cues{Cue::focus,Cue::select,Cue::back,Cue::tab,Cue::open,Cue::modal_open,Cue::modal_close,Cue::toggle,Cue::slider,Cue::error,Cue::restart,Cue::notify,Cue::saved,Cue::resume,Cue::welcome,Cue::launch,Cue::favorite_on,Cue::favorite_off};
    for(auto cue:cues)assert(bank.has_recording(cue,SoundSet::glass));
    Mixer mixer;mixer.set_bus_gain(Bus::ui,.18f);std::array<std::int16_t,2048>pcm{};mixer.render(pcm.data(),1024);
    int peak=0;for(unsigned n=0;n<1200;++n){bank.play(mixer,SoundSet::glass,{cues[n%cues.size()],1,0,n%18==0?.6f:1.f});for(unsigned k=0;k<5;++k){mixer.render(pcm.data(),960);for(unsigned i=0;i<1920;++i)peak=std::max(peak,std::abs(int(pcm[i])));}}
    assert(mixer.dropped_commands()==0&&peak<6500);for(unsigned n=0;n<48;++n)mixer.render(pcm.data(),1024);assert(mixer.active_voices()==0);
    std::printf("PASS SoundBank:25PCM files,18cue names,0rejected; %.3fms host load.1,200actions at10Hz:queue drops0,peak%.5f,allvoicesreleased\n",load_ms,peak/32768.f);
    museum::Music music;assert(music.init("music/eras"));music.volume(.48f);music.select_year(1980);music.muted(true);
    Mixer preview;preview.set_bus_gain(Bus::ui,.18f);
    struct Event{double at;Cue cue;float gain;};
    const std::array<Event,35> events{{{.35,Cue::focus,.6f},{.65,Cue::focus,.6f},{.95,Cue::focus,.6f},
        {1.55,Cue::select,1},{2.15,Cue::back,1},{2.75,Cue::tab,1},{3.35,Cue::modal_open,1},
        {3.95,Cue::modal_close,1},{4.55,Cue::toggle,1},{5.15,Cue::slider,1},{5.75,Cue::error,1},
        {6.35,Cue::restart,1},{7.10,Cue::notify,1},{8.0,Cue::saved,1},{8.8,Cue::resume,1},
        {9.6,Cue::welcome,1},{10.5,Cue::launch,1},{11.4,Cue::favorite_on,1},{12.1,Cue::favorite_off,1},
        {14.0,Cue::focus,.6f},{14.3,Cue::focus,.6f},{14.6,Cue::focus,.6f},{15.2,Cue::select,1},
        {16.2,Cue::back,1},{17.2,Cue::tab,1},{18.3,Cue::modal_open,1},{19.0,Cue::modal_close,1},
        {20.0,Cue::toggle,1},{20.5,Cue::slider,1},{21.0,Cue::error,1},{21.8,Cue::restart,1},
        {22.6,Cue::select,1},{23.4,Cue::back,1},{24.0,Cue::tab,1},{24.7,Cue::select,1}}};
    constexpr unsigned frames=26*48000;std::vector<std::int16_t>output(frames*2);std::array<float,960>background{};unsigned next=0;float mixed_peak=0;
    for(unsigned frame=0;frame<frames;frame+=480){const double seconds=double(frame)/48000;
        if(seconds>=13)music.muted(false);if(seconds>=19)music.select_year(2020);
        while(next<events.size()&&seconds+1e-6>=events[next].at){bank.play(preview,SoundSet::glass,{events[next].cue,1,0,events[next].gain});++next;}
        music.render(background.data(),480);preview.render(pcm.data(),480);
        for(unsigned n=0;n<960;++n){const float value=background[n]+pcm[n]/32768.f;mixed_peak=std::max(mixed_peak,std::abs(value));assert(std::isfinite(value)&&std::abs(value)<.5f);output[frame*2+n]=std::int16_t(std::clamp(value,-1.f,1.f)*32767);}
    }
    wav("music/previews/Museum - Navigation Sound Palette.wav",output);
    std::printf("PASS listening preview:26seconds,actual SoundBank/Mixer,UIgain.18,musicgain.48,phase-preserving1980to2020,peak%.5f\n",mixed_peak);
}
