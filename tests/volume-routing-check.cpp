// SPDX-License-Identifier: GPL-3.0-or-later
#include "audio/volume_gain.hpp"
#include "audio/controller_feedback.hpp"
#include <cassert>
#include <cmath>
#include <limits>
#include <vector>

int main(){
    using hui::audio::VolumeGain;
    std::vector<float> input(4096*2),whole,split;
    // The master scales the complete mixed TV output with one stereo gain.
    for(unsigned n=0;n<4096;++n){input[n*2]=.8f;input[n*2+1]=-.4f;}
    VolumeGain a,b;whole=input;split=input;
    a.process(whole.data(),4096,0.f);
    for(unsigned at=0;at<4096;){const unsigned n=std::min(137u,4096-at);b.process(split.data()+at*2,n,0.f);at+=n;}
    assert(whole==split);
    for(unsigned n=0;n<4096;++n){assert(std::abs(whole[n*2]+2*whole[n*2+1])<1e-7f);if(n>=960)assert(whole[n*2]==0&&whole[n*2+1]==0);}
    // Saved mute is silent from the first sample, not after an initial ramp.
    a.snap(0);whole=input;a.process(whole.data(),4096,0);for(float v:whole)assert(v==0);
    a.snap(.5f);whole=input;a.process(whole.data(),4096,.5f);for(unsigned n=0;n<4096;++n)assert(whole[n*2]==.4f&&whole[n*2+1]==-.2f);
    a.snap(std::numeric_limits<float>::quiet_NaN());whole=input;a.process(whole.data(),4096,0);for(float v:whole)assert(v==0);
    // The physical controller speaker follows master*SFX, while haptics remain independent.
    hui::audio::ControllerFeedback controller;controller.enabled(true);
    controller.speaker_volume(0);
    std::vector<float> pcm(2048);controller.render_speaker(pcm.data(),2048);
    assert(controller.post_speaker({hui::audio::SpeakerCue::ui_confirm,1,.1f,.04f}));
    controller.render_speaker(pcm.data(),2048);for(float v:pcm)assert(v==0);
    controller.speaker_volume(1);controller.render_speaker(pcm.data(),2048);
    assert(controller.post_speaker({hui::audio::SpeakerCue::ui_confirm,1,.1f,.04f}));
    controller.render_speaker(pcm.data(),2048);bool audible=false;for(float v:pcm)audible|=std::abs(v)>.00001f;assert(audible);
    hui::audio::ControllerFeedback experience;experience.enabled(true);
    experience.speaker_volume(.25f);experience.speaker_pcm_volume(.5f);
    experience.render_speaker(pcm.data(),2048);
    // PCM already scaled by SFX=.5 receives MASTER=.5 exactly once.
    std::vector<float> already_scaled(256,.05f);experience.submit_speaker(already_scaled.data(),256);
    experience.render_speaker(pcm.data(),256);
    for(unsigned n=0;n<256;++n)assert(std::abs(pcm[n]-.025f)<1e-6f);
}
