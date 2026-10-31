// Verifies the actual rhythm oscillator and the clock the study scores against.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/experience_audio.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <algorithm>
#include <vector>
int main(){
    static_assert(museum::ExperienceAudio::phrase_beats>=28);
    museum::ExperienceAudio a;std::array<float,512>pcm{};a.render(pcm.data(),256);for(float v:pcm)assert(v==0);
    a.start();assert(a.time_s()==0);double energy=0;float peak=0;
    FILE*f=std::fopen("build/previews/rhythm-study-extended-loop.wav","wb");assert(f);
    const unsigned frames=48000*44,bytes=frames*4;const unsigned char header[]={ 'R','I','F','F',0,0,0,0,'W','A','V','E','f','m','t',' ',16,0,0,0,1,0,2,0,0x80,0xbb,0,0,0,0xee,2,0,4,0,16,0,'d','a','t','a',0,0,0,0};
    auto write32=[&](unsigned v){for(int b=0;b<4;++b)std::fputc(int((v>>(b*8))&255),f);};
    std::fwrite(header,1,sizeof(header),f);std::fseek(f,4,SEEK_SET);write32(bytes+36);std::fseek(f,40,SEEK_SET);write32(bytes);std::fseek(f,44,SEEK_SET);
    for(unsigned offset=0;offset<frames;offset+=256){const unsigned count=std::min(256u,frames-offset);pcm.fill(0);a.render(pcm.data(),count);
        for(unsigned n=0;n<count*2;++n){assert(std::isfinite(pcm[n]));peak=std::max(peak,std::abs(pcm[n]));energy+=pcm[n]*pcm[n];const auto sample=std::int16_t(std::clamp(pcm[n],-1.f,1.f)*32767);std::fputc(sample&255,f);std::fputc((unsigned(sample)>>8)&255,f);}
    }
    std::fclose(f);assert(energy>100&&peak>.1f&&peak<.7f);assert(std::abs(a.time_s()-44)<.00001);
    // Reset is published as zero immediately, and is sample-accurate on the next callback.
    a.start();assert(a.time_s()==0);pcm.fill(0);a.render(pcm.data(),256);assert(std::abs(a.time_s()-256./48000)<.000001);
    a.stop();for(int n=0;n<80;++n){pcm.fill(0);a.render(pcm.data(),256);}for(float v:pcm)assert(v==0);
    // Focus suspension is a sample-clock freeze, not stop/start or a mute
    // while the judgement clock continues. Mixing remains additive.
    a.start();pcm.fill(0);a.render(pcm.data(),256);const double paused_at=a.time_s();
    a.paused(true);std::array<float,256>speaker{};
    for(int n=0;n<30;++n){pcm.fill(.123f);speaker.fill(1);a.render(pcm.data(),256,speaker.data());for(float v:pcm)assert(v==.123f);for(float v:speaker)assert(v==0);assert(a.time_s()==paused_at);}
    a.paused(false);pcm.fill(0);a.render(pcm.data(),256,speaker.data());assert(std::abs(a.time_s()-paused_at-256./48000)<.000001);
    a.paused(true);a.stop();a.paused(false);for(int n=0;n<80;++n){pcm.fill(0);a.render(pcm.data(),256);}for(float v:pcm)assert(v==0);
    std::puts("PASS focus audio: sample clock frozen, additive HDMI untouched, pad speaker zero, resume same phrase, stop while paused never restarts.");

    // Callback block size must not move either the musical or pad-speaker
    // pulse: a display frame and an audio grain have independent sizes.
    constexpr unsigned count=48000*4;
    const auto render_blocks=[](unsigned block){museum::ExperienceAudio source;source.start();std::vector<float>result(count*3),part(block*2),speaker(block);
        for(unsigned at=0;at<count;at+=block){const unsigned n=std::min(block,count-at);std::fill(part.begin(),part.end(),0);source.render(part.data(),n,speaker.data());
            for(unsigned k=0;k<n;++k){result[(at+k)*3]=part[k*2];result[(at+k)*3+1]=part[k*2+1];result[(at+k)*3+2]=speaker[k];}}
        return result;};
    const auto small=render_blocks(256),large=render_blocks(997);assert(small==large);
    for(unsigned beat=1;beat<=3;++beat){const unsigned at=beat*52800;double on=0,off=0,pad=0;
        for(unsigned k=0;k<1440;++k){on+=small[(at+k)*3]*small[(at+k)*3];off+=small[(at+26400+k)*3]*small[(at+26400+k)*3];pad+=small[(at+k+museum::ExperienceAudio::controller_delay_frames)*3+2]*small[(at+k+museum::ExperienceAudio::controller_delay_frames)*3+2];}
        assert(on>off*1.3&&pad>.01);
        for(unsigned k=4800;k<24000;++k)assert(std::abs(small[(at+k+museum::ExperienceAudio::controller_delay_frames)*3+2])<.001f);
    }
    std::puts("PASS rhythm pulse alignment: main beat dominates offbeat; pad cue compensated by200ms on its sample clock; 256/997-frame renders identical.");
    std::printf("PASS original rhythm audio: 44 seconds including extended loop seam, finite bounded stereo, peak %.3f, exact48kHz clock, restart and silent stop\n",peak);
}
