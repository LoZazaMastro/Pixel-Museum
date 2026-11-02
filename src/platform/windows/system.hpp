// Pixel Museum - Native Windows system services.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include <cstdint>

namespace hui::sys
{

std::int64_t monotonic_us();
#if defined(__GNUC__) || defined(__clang__)
void log(const char *format, ...) __attribute__((format(printf, 1, 2)));
#else
void log(const char *format, ...);
#endif
bool hide_splash_screen();
void sleep_us(std::uint32_t microseconds);
bool local_clock(int *hour, int *minute, bool *twelve_hour);
bool local_date(int *weekday, int *month, int *day);
[[noreturn]] void park();
[[noreturn]] void quit();

} // namespace hui::sys
