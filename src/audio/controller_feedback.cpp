// SPDX-License-Identifier: GPL-3.0-or-later
#include "audio/controller_feedback.hpp"
#include "audio/museum_interface_pcm.hpp"
#include "audio/museum_pixel.hpp"
#include <algorithm>
#include <cmath>
namespace hui::audio {
namespace {
constexpr float tau=6.2831853071795864769f;
float finite(float v){return std::isfinite(v)?v:0.f;}
float speaker_seconds(SpeakerCue cue){
    const auto original=museum_original::gesture(cue);
    if(original.frames)return float(original.frames)/48000.f;
    switch(cue){
        case SpeakerCue::ball_hit:return .055f;
        case SpeakerCue::coin:return .13f;
        case SpeakerCue::ring:return .16f;
        case SpeakerCue::charge:return .14f;
        case SpeakerCue::portal_open:return .20f;
        case SpeakerCue::portal_cross:return .11f;
        case SpeakerCue::grow:return .09f;
        case SpeakerCue::tool:return .05f;
        case SpeakerCue::bonus:return .24f;
        case SpeakerCue::startup_pixel:return .38f;
        case SpeakerCue::ui_focus:return .035f;
        case SpeakerCue::ui_confirm:return .075f;
        case SpeakerCue::ui_back:return .065f;
        case SpeakerCue::timeline_culture:case SpeakerCue::timeline_games:return .09f;
        case SpeakerCue::invader_shot:return .115f;
    }
    return 0.f;
}
// Original, small procedural gestures, not recordings or game-song samples.
float speaker_sample(SpeakerEvent event,unsigned position,unsigned length){
    const auto original=museum_original::gesture(event.cue);
    if(original.frames){
        const bool interface=event.cue==SpeakerCue::ui_focus||event.cue==SpeakerCue::ui_confirm||event.cue==SpeakerCue::ui_back||event.cue==SpeakerCue::timeline_culture||event.cue==SpeakerCue::timeline_games;
        return museum_original::read(original,position,event.pitch)*event.gain*(interface?1.35f:1.f);
    }
    if(event.cue==SpeakerCue::startup_pixel)return museum_original::pixel_sample(event.pitch,float(position)/48000.f,float(length)/48000.f)*event.gain;
    const float t=float(position)/48000.f,p=float(position)/float(length-1);
    const float duration=float(length)/48000.f;
    float hz=300.f,sweep=0.f,second=0.f;
    float envelope=std::sin(3.141592653589793f*p);
    switch(event.cue){
        case SpeakerCue::ball_hit:hz=310;second=.3f;envelope*=std::exp(-p*5);break;
        case SpeakerCue::coin:hz=1200;sweep=800;second=.12f;envelope*=std::exp(-p*3);break;
        case SpeakerCue::ring:hz=1480;sweep=-100;second=.22f;envelope*=std::exp(-p*3);break;
        case SpeakerCue::charge:hz=220;sweep=800;envelope*=p;break;
        case SpeakerCue::portal_open:hz=420;sweep=-180;second=.12f;break;
        case SpeakerCue::portal_cross:hz=180;sweep=540;second=.18f;break;
        case SpeakerCue::grow:hz=180;sweep=260;envelope*=std::exp(-p*2);break;
        case SpeakerCue::tool:hz=1100;sweep=-500;second=.25f;envelope*=std::exp(-p*5);break;
        case SpeakerCue::bonus:hz=660;sweep=900;second=.15f;break;
        case SpeakerCue::startup_pixel:
            hz=440;
            envelope=std::min(1.f,t/.012f)*std::min(1.f,(duration-t)/(duration>.5f?.60f:.27f));
            break;
        case SpeakerCue::ui_focus:hz=880;envelope*=std::exp(-p*4);break;
        case SpeakerCue::ui_confirm:hz=660;sweep=330;break;
        case SpeakerCue::ui_back:hz=660;sweep=-220;break;
        case SpeakerCue::timeline_culture:hz=620;sweep=480;envelope*=std::exp(-p);break;
        case SpeakerCue::timeline_games:hz=1100;sweep=-480;envelope*=std::exp(-p);break;
        case SpeakerCue::invader_shot:hz=1700;sweep=-1595;second=.18f;envelope*=std::exp(-p*4);break;
    }
    const float phase=tau*event.pitch*(hz*t+.5f*sweep*t*t/duration);
    return (std::sin(phase)+second*std::sin(phase*1.503f))*envelope*event.gain;
}
}
bool ControllerFeedback::post(TactileEvent event){
    event.strength=std::clamp(finite(event.strength),0.f,.65f);
    event.seconds=std::clamp(finite(event.seconds),.008f,.3f);event.pan=std::clamp(finite(event.pan),-1.f,1.f);
    // A low-frequency collision needs several actuator cycles; the old
    // 18–35ms authored gestures could decay before a useful impact developed.
    if(event.pattern==Tactile::impact)event.seconds=std::max(event.seconds,.055f);
    if(event.strength==0||!enabled_.load(std::memory_order_acquire))return false;
    const unsigned head=head_.load(std::memory_order_relaxed),tail=tail_.load(std::memory_order_acquire);
    if(head-tail>=queue_size){dropped_.fetch_add(1,std::memory_order_relaxed);return false;}
    events_[head%queue_size]={event,generation_.load(std::memory_order_acquire)};head_.store(head+1,std::memory_order_release);return true;
}
bool ControllerFeedback::post_speaker(SpeakerEvent event){
    if(speaker_seconds(event.cue)==0.f||!enabled_.load(std::memory_order_acquire))return false;
    event.pitch=std::clamp(finite(event.pitch),.25f,4.f);
    event.gain=std::clamp(finite(event.gain),0.f,.22f);
    event.seconds=event.seconds>0.f?std::clamp(finite(event.seconds),.008f,.8f):speaker_seconds(event.cue);
    if(event.gain==0.f)return false;
    const unsigned head=speaker_head_.load(std::memory_order_relaxed),tail=speaker_tail_.load(std::memory_order_acquire);
    if(head-tail>=queue_size){dropped_.fetch_add(1,std::memory_order_relaxed);return false;}
    speaker_events_[head%queue_size]={event,generation_.load(std::memory_order_acquire)};
    speaker_head_.store(head+1,std::memory_order_release);return true;
}
void ControllerFeedback::render_haptics(float*out,unsigned frames){
    if(!out)return;std::fill_n(out,frames*2,0.f);
    const unsigned head=head_.load(std::memory_order_acquire);unsigned tail=tail_.load(std::memory_order_relaxed);
    const bool active=enabled_.load(std::memory_order_acquire);
    const unsigned generation=generation_.load(std::memory_order_acquire);
    if(generation!=rendered_generation_){for(auto&v:voices_)v.length=0;rendered_generation_=generation;}
    if(!active){for(auto&v:voices_)v.length=0;tail_.store(head,std::memory_order_release);return;}
    while(tail!=head){const auto&q=events_[tail%queue_size];if(q.generation==generation){
        // The flight bed owns one background voice; repeated airflow can never
        // replace a passage, collision or other accepted-action gesture.
        const auto voice=q.event.pattern==Tactile::airflow?0u:1u+next_voice_++%unsigned(voices_.size()-1);
        auto&v=voices_[voice];v.event=q.event;v.position=0;v.length=std::max(2u,unsigned(v.event.seconds*48000));}++tail;}
    tail_.store(tail,std::memory_order_release);
    for(unsigned n=0;n<frames;++n){float left=0,right=0;
        for(auto&v:voices_){if(v.position>=v.length)continue;
            const float t=float(v.position)/48000.f,p=float(v.position)/float(v.length-1),duration=float(v.length)/48000.f;
            float hz=180,sweep=0,pan=v.event.pan,envelope=std::sin(3.141592653589793f*p);
            switch(v.event.pattern){
                case Tactile::focus:hz=235;envelope*=std::exp(-p*4);break;
                case Tactile::timeline_step:
                    hz=185;sweep=40;
                    // A firm detent: 5ms attack, short body, 30ms release.
                    // Longer than the old 22ms heavily attenuated focus click.
                    envelope=std::min(1.f,t/.005f)*std::min(1.f,(duration-t)/.030f);
                    break;
                case Tactile::confirm:hz=145;sweep=140;envelope*=std::exp(-p*2);break;
                case Tactile::back:hz=230;sweep=-120;envelope*=std::exp(-p*2);break;
                case Tactile::error:hz=95;envelope*=.45f+.55f*std::pow(std::sin(tau*p*2),2);break;
                case Tactile::rise:hz=65;sweep=210;pan=-.65f+1.3f*p;break;
                case Tactile::fall:hz=275;sweep=-210;pan=.65f-1.3f*p;break;
                case Tactile::zoom_in:hz=100;sweep=150;pan*=1-p;break;
                case Tactile::zoom_out:hz=250;sweep=-150;pan*=p;break;
                case Tactile::rotate:hz=165;pan=std::clamp(pan+.2f*std::sin(tau*p),-1.f,1.f);break;
                case Tactile::scroll:hz=210;envelope*=.65f+.35f*std::cos(tau*p*2);break;
                case Tactile::touch:hz=260;envelope*=std::exp(-p*3);break;
                case Tactile::impact:hz=70;sweep=-25;envelope*=std::exp(-p*3);break;
                case Tactile::airflow:
                    hz=115;sweep=35;
                    envelope=std::min(1.f,p*8)*std::min(1.f,(1-p)*8)*(.72f+.28f*std::sin(tau*t*17));
                    break;
                case Tactile::passage:
                    hz=125;sweep=115;
                    envelope=std::sin(3.141592653589793f*p)*(.65f+.35f*std::pow(std::cos(tau*p),2));
                    break;
            }
            const float phase=tau*(hz*t+.5f*sweep*t*t/duration);
            const float sample=(std::sin(phase)+.12f*std::sin(phase*2))*envelope*v.event.strength;
            left+=sample*(.7f-.3f*pan);right+=sample*(.7f+.3f*pan);++v.position;
        }
        // Short gesture envelopes and the stereo distribution attenuate the
        // authored strength considerably. Restore useful low-level drive,
        // while soft-limiting stacked impacts to the existing output ceiling.
        out[n*2]=.7f*std::tanh(left*3.5f/.7f);out[n*2+1]=.7f*std::tanh(right*3.5f/.7f);
    }
}
void ControllerFeedback::submit_speaker(const float*mono,unsigned frames){
    if(!mono)return;
    if(!enabled_.load(std::memory_order_acquire)){speaker_flush_.store(true,std::memory_order_release);return;}
    std::array<float,512> stereo{};
    for(unsigned pos=0;pos<frames;){const unsigned count=std::min(256u,frames-pos);
        for(unsigned n=0;n<count;++n)stereo[n*2]=stereo[n*2+1]=std::clamp(finite(mono[pos+n]),-8.f,8.f);
        // Never reclaim slots while the consumer may be copying them. A
        // stalled output requests a consumer-owned flush and drops this new
        // block instead; two256-frame grains bound queued DDR audio to10.7ms.
        if(speaker_.space()<count){speaker_flush_.store(true,std::memory_order_release);dropped_.fetch_add(count,std::memory_order_relaxed);}
        else speaker_.write(stereo.data(),count);pos+=count;
    }
}
void ControllerFeedback::speaker_volume(float value){speaker_volume_.store(std::isfinite(value)?std::clamp(value,0.f,1.f):0.f,std::memory_order_relaxed);}
void ControllerFeedback::speaker_pcm_volume(float value){speaker_pcm_volume_.store(std::isfinite(value)?std::clamp(value,0.f,1.f):0.f,std::memory_order_relaxed);}
void ControllerFeedback::render_speaker(float*out,unsigned frames){
    if(!out)return;std::fill_n(out,frames,0.f);std::array<float,512> stereo{};
    // Only this consumer can flush and then reuse slots without racing a
    // read in progress. Even a disable/re-enable between callbacks discards
    // the previous context rather than replaying its count-in.
    if(speaker_flush_.exchange(false,std::memory_order_acq_rel))speaker_.drain();
    const unsigned head=speaker_head_.load(std::memory_order_acquire);
    unsigned tail=speaker_tail_.load(std::memory_order_relaxed);
    const unsigned generation=generation_.load(std::memory_order_acquire);
    if(generation!=speaker_generation_){for(auto&v:speaker_voices_)v.length=0;speaker_generation_=generation;}
    if(!enabled_.load(std::memory_order_acquire)){
        speaker_.drain();speaker_tail_.store(head,std::memory_order_release);
        for(auto&v:speaker_voices_)v.length=0;return;
    }
    while(tail!=head){const auto&q=speaker_events_[tail%queue_size];
        if(q.generation==generation){auto&v=speaker_voices_[next_speaker_voice_++%speaker_voices_.size()];
            v.event=q.event;v.position=0;v.length=std::max(2u,unsigned(q.event.seconds*48000));}
        ++tail;
    }
    speaker_tail_.store(tail,std::memory_order_release);
    for(unsigned pos=0;pos<frames;){const unsigned count=std::min(256u,frames-pos),read=unsigned(speaker_.read(stereo.data(),count));
        for(unsigned n=0;n<read;++n)out[pos+n]=(stereo[n*2]+stereo[n*2+1])*.5f;pos+=count;
    }
    // Preserve DDR PCM sample values and timing when no semantic cue is active.
    // Mixing happens only on the controller consumer, never on the TV bus.
    const float volume=speaker_volume_.load(std::memory_order_relaxed);
    const float pcm_volume=speaker_pcm_volume_.load(std::memory_order_relaxed);
    float peak=0;
    for(unsigned n=0;n<frames;++n){float cues=0;
        for(auto&v:speaker_voices_)if(v.position<v.length){cues+=speaker_sample(v.event,v.position,v.length)*1.3f;++v.position;}
        speaker_gain_+=std::clamp(volume-speaker_gain_,-1.f/960.f,1.f/960.f);
        speaker_pcm_gain_+=std::clamp(pcm_volume-speaker_pcm_gain_,-1.f/960.f,1.f/960.f);
        out[n]=out[n]*speaker_pcm_gain_+cues*speaker_gain_;
        peak=std::max(peak,std::abs(out[n]));
    }
    // Long archival recordings retain their waveform on the small speaker;
    // attenuate a whole overloaded block instead of flattening its peaks.
    speaker_peak_gain_=std::min(speaker_peak_gain_,peak>.3f?.3f/peak:1.f);
    for(unsigned n=0;n<frames;++n)out[n]*=speaker_peak_gain_;
    speaker_peak_gain_+=(1.f-speaker_peak_gain_)*(1.f-std::exp(-float(frames)/(48000.f*.15f)));
}
}
