// Pixel Museum - bounded HTTP retry policy, independent of the frame clock.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <limits>
namespace museum::media::detail {
struct ImageRetry {
    using Milliseconds = std::uint64_t;
    static constexpr Milliseconds never = std::numeric_limits<Milliseconds>::max();
    static constexpr Milliseconds delays[] = {5000, 20000, 60000};
    unsigned failures = 0;
    Milliseconds due = never;
    static bool transient(long status) {
        return status==429 || status==500 || status==502 || status==503 || status==504;
    }
    static Milliseconds after(Milliseconds now, Milliseconds delay) {
        return now < never-delay ? now+delay : never;
    }
    void reset() { failures=0; due=never; }
    void failed(long status, Milliseconds now) {
        if (!transient(status)) { reset(); return; }
        if (failures < 4) ++failures;
        due = failures <= 3 ? after(now, delays[failures-1]) : never;
    }
    bool eligible(bool image, bool visible, Milliseconds now) const {
        return image && visible && due != never && now >= due;
    }
};
} // namespace museum::media::detail
