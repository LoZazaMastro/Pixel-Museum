// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/stream_ring.hpp"
#include <array>
#include <atomic>
#include <cstdint>

namespace hui::audio {
enum class Tactile : std::uint8_t { focus, confirm, back, error, rise, fall, zoom_in, zoom_out, rotate, scroll, touch, impact, airflow, passage, timeline_step };
struct TactileEvent { Tactile pattern=Tactile::focus;float strength=.18f,seconds=.035f,pan=0; };
enum class SpeakerCue : std::uint8_t { ball_hit, coin, ring, charge, portal_open, portal_cross, grow, tool, bonus, startup_pixel, ui_focus, ui_confirm, ui_back, timeline_culture, timeline_games, invader_shot };
struct SpeakerEvent {SpeakerCue cue=SpeakerCue::tool;float pitch=1.f,gain=.12f,seconds=0.f;};

// Main thread posts tactile events; the dedicated controller audio thread owns
// the voices. Speaker PCM has its own single-producer/consumer ring so DDR's
// metronome can come from the same samples as its score, without a second clock.
class ControllerFeedback {
public:
    bool post(TactileEvent event);
    // UI producer -> dedicated controller speaker consumer. Independent of
    // DDR's audio-thread-produced PCM ring, so there are never two producers.
    bool post_speaker(SpeakerEvent event);
    void speaker_volume(float value);
    // Experience PCM already contains its SFX level; apply only master here.
    void speaker_pcm_volume(float value);
    void enabled(bool value){
        const bool before=enabled_.exchange(value,std::memory_order_acq_rel);
        if(before&&!value){generation_.fetch_add(1,std::memory_order_release);speaker_flush_.store(true,std::memory_order_release);}
    }
    void render_haptics(float*stereo,unsigned frames);
    void submit_speaker(const float*mono,unsigned frames);
    void render_speaker(float*mono,unsigned frames);
    std::uint64_t dropped()const{return dropped_.load(std::memory_order_relaxed);}
private:
    static constexpr unsigned queue_size=64;
    struct Voice {TactileEvent event{};unsigned position=0,length=0;};
    struct Queued {TactileEvent event{};unsigned generation=0;};
    struct SpeakerQueued {SpeakerEvent event{};unsigned generation=0;};
    struct SpeakerVoice {SpeakerEvent event{};unsigned position=0,length=0;};
    std::array<Queued,queue_size> events_{};
    std::atomic<unsigned> generation_{0};
    unsigned rendered_generation_=0;
    unsigned speaker_generation_=0;
    std::atomic<bool> speaker_flush_{false};
    std::atomic<float> speaker_volume_{1.f};
    std::atomic<float> speaker_pcm_volume_{1.f};
    float speaker_gain_=1.f;
    float speaker_pcm_gain_=1.f;
    float speaker_peak_gain_=1.f;
    std::atomic<unsigned> head_{0},tail_{0};
    std::atomic<bool> enabled_{false};
    std::atomic<std::uint64_t> dropped_{0};
    std::array<Voice,8> voices_{};
    unsigned next_voice_=0;
    std::array<SpeakerQueued,queue_size> speaker_events_{};
    std::atomic<unsigned> speaker_head_{0},speaker_tail_{0};
    std::array<SpeakerVoice,8> speaker_voices_{};
    unsigned next_speaker_voice_=0;
    StreamRing speaker_{512}; // Two256-frame grains: at most10.7ms of queued DDR PCM.
};
}
