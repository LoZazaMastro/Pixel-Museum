// Selective archival recollections, separate from article/player content.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <array>
#include <atomic>
#include <string>
#include <cstdint>
#include <memory>
#include <vector>
#include "museum/culture_level.hpp"
namespace museum {
class CultureAmbience {
 static_assert(std::atomic<std::uint64_t>::is_always_lock_free);
 static_assert(std::atomic<const void*>::is_always_lock_free);
public:
 struct LocalAudio {std::vector<std::int16_t> samples;};
 struct Cue {std::string entry_id,youtube_id,kind,evidence,local_audio_path;const LocalAudio*local_audio=nullptr;double start=0,end=0;bool reverb=false;float gain=1;bool normalize_level=true;};
 struct Context {std::string entry_id;bool eligible=false;float volume=0;};
 struct Playback {bool ready=false,ended=false,failed=false;double position=0;};
 struct Command {enum Kind{none,open,close}kind=none;const Cue*cue=nullptr;};
 bool load(const std::string&path);
 // UI thread only. A stop is consumed once even if unavailable or interrupted.
 Command update(const Context&,const Playback&,float dt);
 bool owns_player()const{return owns_;}
 bool using_local_audio()const{return owns_&&active_&&active_->local_audio;}
 bool rendering_local_audio()const{return local_render_.load(std::memory_order_acquire)!=nullptr;}
 float ambient_gain()const{return volume_.load(std::memory_order_relaxed)>.001f&&owns_&&ready_&&closing_==0&&active_?entry_bed_gain_.load(std::memory_order_relaxed):1.f;}
 void relinquish(); // Before an explicit player takes over, without fading it.
 bool rendering()const{return render_.load(std::memory_order_acquire);}
 // Audio thread only: stream input is borrowed from the SINGLE Video service;
 // a local cue instead reads immutable preloaded PCM. Null input is silence.
 // No allocation, I/O or locks. Adds the original-dynamics foreground layer.
 void process(const float*input,float*output,unsigned frames);
 const std::vector<Cue>&cues()const{return cues_;}
private:
 // Buffers remain alive across table reloads until the audio engine is stopped
 // before destruction. No last-reference destruction or allocation in process().
 std::vector<std::unique_ptr<LocalAudio>>local_storage_;
 std::atomic<const LocalAudio*>local_render_{nullptr};
 std::atomic<std::uint64_t>local_progress_{0};unsigned local_audio_frame_=0;
 std::vector<Cue>cues_;std::string stop_;float dwell_=0,closing_=0;bool fired_=false,owns_=false,ready_=false;
 const Cue*active_=nullptr;
 std::atomic<bool>render_{false},audible_{false},voice_reverb_{false};
 std::atomic<bool>normalize_level_{true};
 CultureLevel level_;
 std::atomic<float>volume_{0},cue_gain_{1},remaining_{0};
 std::atomic<float>bed_target_{1},entry_bed_gain_{1};
 std::atomic<unsigned>revision_{0};unsigned audio_revision_=0;
 float envelope_=0,energy_=0,normal_gain_=0,user_gain_=0;bool audio_started_=false;
 float audio_remaining_=0,last_remaining_=-1;
 unsigned entry_frames_=0;
 std::array<float,3840*2>delay_{};unsigned delay_at_=0;
};
}
