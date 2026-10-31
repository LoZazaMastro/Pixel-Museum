// Pixel Museum - synchronized original decade soundtrack.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <string>
#include <vector>

namespace museum {

// Initialize before the audio callback starts. Setters are safe from the UI
// thread; render belongs exclusively to the audio thread. Destruction and init
// require the output thread to have stopped. This object is not movable.
class Music {
public:
    static constexpr unsigned kOutputRate = 48000;
    static constexpr unsigned kSourceRate = 24000;
    static constexpr unsigned kSeconds = 64;
    static constexpr unsigned kEraCount = 8;
    static constexpr unsigned kCrossfadeFrames = kOutputRate / 5; // 200 ms
    static constexpr unsigned kTechnologyCount = 7;

    // Directory and culture/ each contain 1950.ogg through 2020.ogg;
    // onboarding/intro.ogg is the dedicated sustained entrance bed.
    // All-or-nothing loading:
    // failure releases decoded audio and render produces silence. Callers can
    // still start the museum and show a nonfatal diagnostic from error().
    bool init(const std::string &directory);
    const std::string &error() const { return error_; }
    bool ready() const { return ready_; }
    std::size_t pcm_bytes() const;

    void select_year(float year);
    // Both timeline compositions share the same continuously advancing clock.
    // Selection changes only their crossfade, never their playback positions.
    void select_timeline(bool culture) { culture_.store(culture, std::memory_order_relaxed); }
    void onboarding_active(bool active) { onboarding_.store(active, std::memory_order_relaxed); }
    void archival_ambient_gain(float gain);
    void volume(float gain);
    void muted(bool value) { mute_.store(value, std::memory_order_relaxed); }
    void video_active(bool value) { video_.store(value, std::memory_order_relaxed); }
    void listening_room(bool value) { listening_.store(value, std::memory_order_relaxed); }

    // Always fills frames * 2 stereo floats. No I/O, locks or allocations.
    // All sixteen arrangements and the entrance bed share one playhead.
    // The selected decade crossfades in 200 ms, in sample time, never resets
    // loop position when navigating. Recording technology follows historical
    // milestones independently of arrangements, with its own 200 ms crossfade.
    // Profiles are artistic approximations, not physical equipment emulations.
    // Quiet 0.42 default volume, -30 dB film duck. A listening room fades
    // ambience to silence until it relinquishes ownership, including pause.
    void render(float *out, unsigned frames);

private:
    friend struct MusicInspection;
    std::array<std::vector<std::int16_t>, kEraCount> pcm_;
    std::array<std::vector<std::int16_t>, kEraCount> culture_pcm_;
    std::vector<std::int16_t> onboarding_pcm_;
    std::atomic<bool> onboarding_{false};
    float onboarding_mix_=0;
    bool composition_started_=false;
    std::atomic<bool> culture_{false};
    float culture_mix_=0;
    std::atomic<float> year_{1980.0f};
    std::atomic<float> volume_{0.42f};
    std::atomic<float> archival_gain_{1.f};
    float archival_mix_=1.f;
    std::atomic<bool> mute_{false}, video_{false}, listening_{false};
    std::array<float, kEraCount> weights_{};
    std::array<float, kEraCount> fade_from_{};
    unsigned target_era_ = kEraCount;
    unsigned fade_remaining_ = 0;
    std::uint32_t frame_ = 0;
    float gain_ = 0.0f;
    std::array<float, kTechnologyCount> technology_weights_{}, technology_from_{};
    unsigned target_technology_ = kTechnologyCount, technology_remaining_ = 0;
    // Parallel, continuously warm filter banks prevent a switched filter from
    // starting with empty history. No sample hold or few-bit quantization.
    struct FilterState { std::array<float,2> low1{}, low2{}, dc{}; };
    std::array<FilterState, kTechnologyCount> filters_{};
    bool ready_ = false;
    std::string error_;
};
} // namespace museum
