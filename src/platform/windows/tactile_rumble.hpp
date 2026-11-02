#pragma once
#if defined(_WIN32)
#include "ui/feedback.hpp"
#include <algorithm>
#include <cmath>

namespace hui::windows
{
struct RumblePulse { float strength = 0.f, seconds = 0.f; };

// Merge rather than add: Feedback::feel already mirrors most PCM gestures
// into classic rumble. Preserve its amplitude and retain longer weak events.
inline RumblePulse conventional_feedback(const ui::Feedback &feedback)
{
    const auto finite = [](float value) { return std::isfinite(value) ? value : 0.f; };
    RumblePulse pulse;
    const auto merge = [&](float strength, float seconds) {
        if (strength <= 0.f || seconds <= 0.f) return;
        pulse.strength = std::max(pulse.strength, strength);
        pulse.seconds = std::max(pulse.seconds, seconds);
    };
    merge(std::clamp(finite(feedback.rumble_strength), 0.f, 1.f),
          std::clamp(finite(feedback.rumble_seconds), 0.f, 2.f));
    for (const auto &event : feedback.tactile)
    {
        float seconds = std::clamp(finite(event.seconds), .025f, .3f);
        if (event.pattern == audio::Tactile::impact) seconds = std::max(seconds, .055f);
        merge(std::clamp(finite(event.strength), 0.f, .65f), seconds);
    }
    return pulse;
}

// PC UI feedback is input-aware. Conventional motors are deliberately quiet
// while browsing/rotating; real panel or timeline transitions get one short tap.
inline RumblePulse desktop_feedback(const ui::Feedback &feedback, bool controller_active,
                                    bool generic_pad, bool experience_active,
                                    bool navigation_changed)
{
    if(!controller_active)return {};
    if(generic_pad&&!experience_active)return navigation_changed?RumblePulse{.10f,.025f}:RumblePulse{};
    return conventional_feedback(feedback);
}

// Original boot notes have a controller-speaker route, independent of
// Feedback. Give ordinary pads one soft pulse per ignition note only.
inline RumblePulse conventional_startup_note(int note, int pixel_ordinal)
{
    if (note < 0 || pixel_ordinal < 0) return {};
    return note == 86 ? RumblePulse{.12f, .055f} : RumblePulse{.08f, .028f};
}
}
#endif
