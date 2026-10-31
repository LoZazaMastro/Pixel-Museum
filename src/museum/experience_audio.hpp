// Pixel Museum - Original rhythm-study music with one sample-accurate clock.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <string_view>
namespace museum {
// Owned by Screen for its entire audio-callback lifetime. The UI never touches
// oscillator state; the callback never touches a Study pointer or allocates.
class ExperienceAudio {
public:
    static constexpr unsigned sample_rate=48000;
    // Match the measured TV/visual presentation offset in the rhythm study.
    static constexpr unsigned controller_delay_frames=sample_rate/5;
    static constexpr float beat_seconds=1.1f;
    static constexpr unsigned phrase_beats=38;
    // Select an original score before restarting its sample clock. The no-arg
    // form belongs to the rhythm study, whose judgement uses this clock.
    void start(std::string_view experience="rhythm");
    void stop();
    // Freeze the sample clock without restarting the phrase on resume.
    void paused(bool value);
    void volume(float level);
    double time_s()const;
    void render(float*stereo,unsigned frames,float*controller_speaker=nullptr);
private:
    std::atomic<unsigned> generation_{0};
    std::atomic<unsigned> selected_score_{0};
    std::atomic<bool> wanted_{false};
    std::atomic<bool> paused_{false};
    std::atomic<float> volume_{1.f};
    std::atomic<std::uint64_t> published_frames_{0};
    std::atomic<unsigned> published_generation_{0};
    unsigned audio_generation_=0;
    unsigned audio_score_=0;
    std::uint64_t rendered_frames_=0;
    std::uint32_t noise_=0x31415926u;
    float gain_=0;
    std::array<float,controller_delay_frames> rhythm_speaker_delay_{};
    unsigned rhythm_speaker_at_=0;
};
}
