// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/culture_audio_route.hpp"
#include "audio/controller_feedback.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <vector>
int main(){
    constexpr unsigned frames=2400;
    std::vector<float> input(frames*2),tv(input.size()),pad(frames);
    for(unsigned n=0;n<frames;++n){input[n*2]=.2f;input[n*2+1]=.1f;}
    museum::CultureAudioRoute route;route.snap(true);
    route.process(input.data(),tv.data(),pad.data(),frames,true);
    for(unsigned n=0;n<frames;++n){assert(tv[n*2]==0&&tv[n*2+1]==0);assert(std::abs(pad[n]-.15f)<1e-7f);}
    // On/off does not restart the recording or duplicate its energy.
    std::fill(tv.begin(),tv.end(),0);std::fill(pad.begin(),pad.end(),0);
    route.process(input.data(),tv.data(),pad.data(),frames,false);
    for(unsigned n=0;n<frames;++n){assert(std::abs((tv[n*2]+tv[n*2+1])*.5f+pad[n]-.15f)<1e-6f);if(n>=960)assert(pad[n]==0);}
    // The same audio remains usable on hosts which have no speaker output.
    std::fill(tv.begin(),tv.end(),0);route.snap(false);route.process(input.data(),tv.data(),nullptr,frames,true);assert(tv==input);
    // Protect the physical speaker with one linear block gain, not clipping.
    hui::audio::ControllerFeedback controller;controller.enabled(true);
    std::vector<float> raw(256),output(256);
    for(unsigned n=0;n<256;++n)raw[n]=(n%4==0?.8f:n%4==1?.4f:n%4==2?-.8f:-.4f);
    controller.submit_speaker(raw.data(),256);controller.render_speaker(output.data(),256);
    for(unsigned n=0;n<256;++n)assert(std::abs(output[n]-raw[n]*.375f)<1e-6f);
}
