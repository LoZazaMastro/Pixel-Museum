// ps5-homebrew-ui - DualSense input through scePad.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include "core/input.hpp"

#include <cstddef>
#include <span>

namespace hui::ps5
{

// Reads every buffered sample of the initial user's controller each frame
// (scePadRead batches up to 64), so short taps survive long frames. Follows
// ProsperoLight's radio_input.cpp.
class Pad
{
  public:
    Pad() = default;
    Pad(const Pad &) = delete;
    Pad &operator=(const Pad &) = delete;
    ~Pad();

    bool open();
    // Non-blocking discovery among other logged-in users. The primary Pad
    // already owns service initialization; this instance never terminates it.
    bool open_secondary(int primary_user);
    void close();
    // Fills out with the samples read since the last call; returns the count.
    // Returns one disconnected sample if the pad is not open.
    std::size_t read(std::span<PadSample> out);
    bool is_open() const
    {
        return handle_ >= 0;
    }

    // Colours the controller's light bar (for example with the active
    // design's accent). Repeated calls with the same colour do nothing.
    void set_light_bar(std::uint8_t r, std::uint8_t g, std::uint8_t b);
    // Starts a short rumble: strength 0..1, for seconds. tick() stops it.
    void rumble(float strength, float seconds);
    // Call once per frame: ends expired rumble, or cancels immediately off focus.
    void tick(float dt, bool active = true);
    // Explicit opt-in. Export/signature verified against the pinned public SDK
    // and local homebrew reference; physical sensor behaviour is experimental.
    // Repeating a failed request does not spam the service; toggle off/on to retry.
    bool set_motion_enabled(bool enabled);
    int user_id()const{return user_;}
    // Audio waveform haptics opt-in; classic motor calls stay quiet in this mode.
    bool set_advanced_haptics(bool enabled);

  private:
    int handle_ = -1;
    int user_ = -1;
    bool owns_user_service_ = false;
    PadSample initial_sample_{};
    bool initial_sample_pending_=false;
    float rumble_left_ = 0.0f;
    unsigned rumble_reports_ = 0;
    bool last_connected_ = false;
    std::uint32_t light_bar_ = 0xffffffffu;
    bool advanced_requested_ = false;
    bool advanced_enabled_ = false;
    bool advanced_attempted_ = false;
    bool advanced_request_ok_ = false;
    unsigned motion_reports_ = 0;
    bool motion_requested_ = false;
    bool motion_enabled_ = false;
};

} // namespace hui::ps5
