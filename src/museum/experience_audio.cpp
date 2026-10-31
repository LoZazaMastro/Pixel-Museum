// Pixel Museum - original experience scores and the rhythm experiment's groove.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/experience_audio.hpp"
#include "museum/rhythm_chart.hpp"
#include <algorithm>
#include <cmath>
namespace museum {
namespace {
constexpr double tau=6.2831853071795864769;
float sine(double phase){return std::sin(float(phase));}
float envelope(double phase,double attack,double release){return float(std::min(1.0,phase/attack)*std::exp(-phase/release));}
// Original, deliberately small arrangements in the museum's D-minor palette.
// Each experience has its own written phrase, harmony, pace and articulation.
// DDR retains its existing score and exact clock; Kondo retains its interactive
// phrase in the study itself, so neither receives a second background score.
struct Score {
    std::string_view id;
    float bpm, pulse, brightness, pad;
    int melody[8];
    unsigned roots[4];
};
constexpr Score scores[]={
 {"paddle",80,.018f,.10f,.012f,{0,-1,4,-1,2,-1,6,-1},{0,3,5,4}},
 {"bricks",88,.025f,.28f,.009f,{0,4,7,4,2,6,9,6},{0,5,2,4}},
 {"formation",72,.030f,.20f,.007f,{0,0,3,-1,4,4,2,-1},{0,0,5,4}},
 {"maze",96,.021f,.34f,.008f,{0,2,4,2,1,3,5,3},{0,3,4,0}},
 {"gravity",72,.015f,.16f,.014f,{0,4,2,5,1,4,3,6},{0,5,3,4}},
 {"orbit",64,.009f,.08f,.019f,{0,-1,7,-1,5,-1,4,-1},{0,5,2,3}},
 {"wireframe",68,.012f,.18f,.015f,{0,3,6,3,2,5,9,5},{0,2,5,3}},
 {"jump",92,.020f,.24f,.009f,{0,2,4,7,6,4,2,-1},{0,3,5,4}},
 {"momentum",104,.024f,.22f,.008f,{0,4,2,7,4,9,6,4},{0,5,3,0}},
 {"dash",84,.012f,.30f,.016f,{7,-1,4,6,9,-1,7,4},{0,2,5,4}},
 {"sequencer",80,.010f,.16f,.010f,{0,-1,4,6,2,-1,5,7},{0,3,2,5}},
 {"raycast",76,.026f,.12f,.009f,{0,-1,0,3,2,-1,1,4},{0,0,3,4}},
 {"scale",90,.017f,.32f,.011f,{0,4,5,2,7,6,4,2},{0,5,3,5}},
 {"portals",66,.008f,.28f,.017f,{0,-1,6,4,2,-1,7,5},{0,2,4,5}},
 {"pocket-budget",62,.009f,.12f,.012f,{0,2,-1,4,3,1,-1,5},{0,3,5,2}},
 {"jump-lab",70,.011f,.22f,.013f,{0,1,3,6,4,2,5,-1},{0,4,3,5}},
 {"city-system",64,.010f,.15f,.016f,{0,4,-1,2,5,7,-1,3},{0,3,2,4}},
 {"pixels",60,.006f,.27f,.014f,{0,-1,2,4,-1,3,5,7},{0,5,2,0}},
};
constexpr float notes[]={146.8324f,164.8138f,174.6141f,195.9977f,220.f,233.0819f,261.6256f,293.6648f,329.6276f,349.2282f};
float note_envelope(double phase,double length,double decay){
    const double tail=std::clamp((length-phase)/(length*.12),0.0,1.0);
    return envelope(phase,.012,decay)*float(tail*tail*(3-2*tail));
}
}
void ExperienceAudio::start(std::string_view experience){
    if(experience=="adaptive-pulse"){stop();return;}
    unsigned score=0;
    if(experience!="rhythm"){
        for(unsigned n=0;n<sizeof(scores)/sizeof(scores[0]);++n)if(scores[n].id==experience){score=n+1;break;}
        // An unknown study must not accidentally start DDR's beat or pad cue.
        if(!score){stop();return;}
    }
    selected_score_.store(score,std::memory_order_relaxed);
    published_frames_.store(0,std::memory_order_release);generation_.fetch_add(1,std::memory_order_release);wanted_.store(true,std::memory_order_release);
}
void ExperienceAudio::stop(){wanted_.store(false,std::memory_order_release);}
void ExperienceAudio::paused(bool value){paused_.store(value,std::memory_order_release);}
void ExperienceAudio::volume(float level){volume_.store(std::isfinite(level)?std::clamp(level,0.f,1.f):0.f,std::memory_order_relaxed);}
double ExperienceAudio::time_s()const{if(published_generation_.load(std::memory_order_acquire)!=generation_.load(std::memory_order_acquire))return 0;return double(published_frames_.load(std::memory_order_acquire))/sample_rate;}
void ExperienceAudio::render(float*out,unsigned frames,float*controller_speaker){
    if(controller_speaker)std::fill_n(controller_speaker,frames,0.f);
    if(!out||!frames)return;
    const unsigned generation=generation_.load(std::memory_order_acquire);
    if(generation!=audio_generation_){audio_generation_=generation;audio_score_=selected_score_.load(std::memory_order_relaxed);rendered_frames_=0;noise_=0x31415926u;gain_=0;rhythm_speaker_delay_.fill(0);rhythm_speaker_at_=0;}
    // Mixing is additive: a paused experience must leave another source's
    // stereo buffer untouched and explicitly silence its own speaker bus.
    // Retain oscillator/noise/sample phase; resume fades in at that same cue.
    if(paused_.load(std::memory_order_acquire)){gain_=0;return;}
    const bool requested=wanted_.load(std::memory_order_acquire);
    const float volume=volume_.load(std::memory_order_relaxed);
    if(!requested&&gain_<.0001f)return;
    if(audio_score_){
        const auto&score=scores[audio_score_-1];
        const double beat=60.0/score.bpm,slot=beat*.5,end=beat*32;
        // Integer loop cycles make the pad phases continuous at the seam.
        // Compute these few constants once per audio grain, never per sample.
        float roots[4],thirds[4],fifths[4];
        for(unsigned c=0;c<4;++c){
            const float hz=notes[score.roots[c]];
            roots[c]=float(std::round(hz*end)/end);
            thirds[c]=float(std::round(hz*1.189207115*end)/end);
            fifths[c]=float(std::round(hz*1.5*end)/end);
        }
        for(unsigned n=0;n<frames;++n){
            const double t=std::fmod(double(rendered_frames_)/sample_rate,end);
            const unsigned beat_index=unsigned(t/beat),section=(beat_index/8)%4;
            const unsigned step=unsigned(t/slot)%8;
            const double sub=std::fmod(t,slot),pulse=std::fmod(t,beat);
            gain_+=((requested?1.f:0.f)-gain_)*.0014f;
            if(gain_<.0001f&&!requested)break;
            const int degree=score.melody[step];
            float pluck=0;
            if(degree>=0){
                const float hz=notes[degree];
                pluck=(sine(tau*hz*sub)+score.brightness*sine(tau*hz*2*sub))*note_envelope(sub,slot,.17)*.031f;
            }
            const float bass=sine(tau*roots[section]*.5*pulse)*note_envelope(pulse,beat,.24)*.027f;
            const float tap=sine(tau*(52*pulse+2.4*(1-std::exp(-pulse*30))))*note_envelope(pulse,beat,.065)*score.pulse;
            const unsigned previous=(section+3)%4;
            const float transition=float(std::clamp(std::fmod(t,8*beat)/(.65*beat),0.0,1.0));
            const float blend=transition*transition*(3-2*transition);
            const auto chord=[&](unsigned c){return sine(tau*roots[c]*t)+.5f*sine(tau*thirds[c]*t)+.4f*sine(tau*fifths[c]*t);};
            const float pad=(chord(previous)*(1-blend)+chord(section)*blend)*score.pad;
            const float signal=(pluck+bass+tap+pad)*gain_*volume;
            const float pan=sine(tau*t/end)*.10f;
            out[n*2]+=signal*(1-pan);out[n*2+1]+=signal*(1+pan);
            ++rendered_frames_;
        }
        published_frames_.store(rendered_frames_,std::memory_order_release);published_generation_.store(audio_generation_,std::memory_order_release);
        return;
    }
    constexpr double beat=double(beat_seconds),half=beat*.5,eighth=beat*.25,end=beat*phrase_beats;
    static constexpr auto chart_cues=[](){std::array<bool,phrase_beats*2> slots{};for(const auto&note:RhythmChart::notes)slots[note.half]=true;return slots;}();
    constexpr float roots[]={73.4162f,58.2705f,87.3071f,65.4064f};
    constexpr float melody[]={293.6648f,349.2282f,440.f,523.2511f,440.f,349.2282f,261.6256f,329.6276f};
    for(unsigned n=0;n<frames;++n){
        const double t=std::fmod(double(rendered_frames_)/sample_rate,end);
        const float target=requested?1.f:0.f;
        gain_+=(target-gain_)*.0014f;
        if(gain_<.0001f&&target==0){published_frames_.store(rendered_frames_,std::memory_order_release);break;}
        const int half_index=int(t/half),beat_index=int(t/beat),section=(std::max(0,beat_index-2)/4)%4;
        const double pulse=std::fmod(t,beat),sub=std::fmod(t,half),hat=std::fmod(t,eighth);
        noise_=noise_*1664525u+1013904223u;
        const float noise=float(noise_>>8)*(2.f/16777216.f)-1;
        // The strong pulse is exactly the centre crossing used by the study.
        const float kick=sine(tau*(47*pulse+5.2*(1-std::exp(-pulse*32))))*envelope(pulse,.001,.095)*.18f;
        const float snare=beat_index%2?noise*envelope(pulse,.001,.035)*.085f:0;
        const float hats=noise*envelope(hat,.0005,.012)*.024f;
        const float count=beat_index<2?sine(tau*880*pulse)*envelope(pulse,.002,.055)*.055f:0;
        const float root=roots[section];
        const float bass=sine(tau*root*t)*envelope(sub,.006,.18)*.065f;
        const int step=std::max(0,half_index-4)%8;
        const float phrase=beat_index>=2?1.f:.26f;
        const float pluck=(sine(tau*melody[step]*t)+.18f*sine(tau*melody[step]*2*t))*envelope(sub,.008,.16)*.025f*phrase;
        const auto chord=[&](float hz){return sine(tau*hz*4*t)+sine(tau*hz*5.994f*t)+sine(tau*hz*7.128f*t);};
        const float previous_root=beat_index<6?roots[0]:roots[(section+3)%4];
        const float blend=float(std::min(1.0,std::fmod(std::max(0.0,t-2*beat),4*beat)/.14));
        const float pad=(chord(previous_root)*(1-blend)+chord(root)*blend)*.008f*phrase;
        const float edge=float(std::min({1.0,t/.02,(end-t)/.02}));
        const float seam=.5f-.5f*std::cos(float(tau*.5)*std::clamp(edge,0.f,1.f));
        const float amplitude=gain_*volume*seam;
        // The actual chart, including its late half-beat notes, owns these
        // audible targets. A whole-beat metronome omitted those targets on
        // the controller and made the denser section contradict its cues.
        const bool count_in=beat_index<2;
        const bool target_note=half_index<int(chart_cues.size())&&chart_cues[size_t(half_index)];
        const double cue_phase=count_in?pulse:sub;
        const float target_cue=(count_in||target_note)?sine(tau*(count_in?980:720)*cue_phase)*envelope(cue_phase,.001,.020):0.f;
        const float delayed_target=rhythm_speaker_delay_[rhythm_speaker_at_];
        rhythm_speaker_delay_[rhythm_speaker_at_]=target_cue*.13f*seam;
        if(++rhythm_speaker_at_==rhythm_speaker_delay_.size())rhythm_speaker_at_=0;
        if(controller_speaker)controller_speaker[n]=delayed_target*gain_*volume;
        const float signal=(kick+snare+hats+count+bass+pluck+pad+target_cue*.065f)*amplitude;
        out[n*2]+=signal;out[n*2+1]+=signal+(sine(tau*root*4.004*t)-sine(tau*root*4*t))*.004f*amplitude;
        ++rendered_frames_;
    }
    published_frames_.store(rendered_frames_,std::memory_order_release);published_generation_.store(audio_generation_,std::memory_order_release);
}
}
