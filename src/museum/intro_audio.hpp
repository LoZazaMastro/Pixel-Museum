// Thirteen soft notes share the D minor / F major colour of the museum score.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/mixer.hpp"
#include "audio/controller_feedback.hpp"
#include "audio/museum_pixel.hpp"
#include <cmath>
namespace museum {
inline void play_startup_note(hui::audio::Mixer& mixer,int note){
    if(note<0)return;
    hui::audio::Tone tone;tone.wave=hui::audio::Wave::sine;
    tone.start_hz=tone.end_hz=440.f*std::exp2(float(note-69)/12);
    tone.seconds=note==86?.75f:.38f;tone.attack=.012f;tone.release=note==86?.60f:.27f;
    hui::audio::PlayParams parameters;parameters.gain=note>=77?.035f:.055f;
    parameters.pan=float(note%3-1)*.22f;parameters.bus=hui::audio::Bus::sfx;
    mixer.play_tone(tone,parameters);
}
enum class StartupRoute { silent, television, television_and_controller };
inline void prepare_startup_sounds(){(void)hui::audio::museum_original::pixel_bank();}
inline void play_original_pixel(hui::audio::Mixer& mixer,int note){
    const auto* clip=hui::audio::museum_original::pixel_clip(note);
    if(!clip)return;
    hui::audio::PlayParams p;p.bus=hui::audio::Bus::sfx;
    p.gain=note>=77?.085f:.105f;p.pan=float(note%3-1)*.22f;
    mixer.play_clip(clip,p);
}
// Boot ignition ordinal is independent of the shuffled cell coordinates.
// Workshop notes have ordinal -1 and retain their existing TV-only route.
inline StartupRoute route_startup_note(hui::audio::Mixer& mixer,hui::audio::ControllerFeedback& controller,int note,int pixel_ordinal,bool speaker_ready){
    if(note<0)return StartupRoute::silent;
    if(pixel_ordinal>=0)play_original_pixel(mixer,note);
    else play_startup_note(mixer,note);
    if(pixel_ordinal>=0&&speaker_ready){
        const float pitch=std::exp2(float(note-69)/12.f);
        if(controller.post_speaker({hui::audio::SpeakerCue::startup_pixel,pitch,note>=77?.07f:.10f,note==86?.75f:.38f}))return StartupRoute::television_and_controller;
    }
    return StartupRoute::television;
}
}
