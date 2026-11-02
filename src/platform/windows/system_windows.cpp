#if defined(_WIN32)

// Pixel Museum - Native Windows time, logging and process services.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later

#include "platform/windows/system.hpp"

#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

#include <chrono>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <mutex>
#include <thread>

namespace hui::sys
{
namespace
{

bool local_time(std::tm &out)
{
    const std::time_t now = std::time(nullptr);
    return now != static_cast<std::time_t>(-1) && localtime_s(&out, &now) == 0;
}

} // namespace

std::int64_t monotonic_us()
{
    return std::chrono::duration_cast<std::chrono::microseconds>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
}

bool local_clock(int *hour, int *minute, bool *twelve_hour)
{
    if (hour == nullptr || minute == nullptr || twelve_hour == nullptr)
        return false;
    std::tm now{};
    if (!local_time(now))
        return false;
    *hour = now.tm_hour;
    *minute = now.tm_min;
    DWORD twenty_four_hour = 1;
    (void)GetLocaleInfoEx(LOCALE_NAME_USER_DEFAULT, LOCALE_ITIME | LOCALE_RETURN_NUMBER,
                          reinterpret_cast<wchar_t *>(&twenty_four_hour),
                          sizeof(twenty_four_hour) / sizeof(wchar_t));
    *twelve_hour = twenty_four_hour == 0;
    return true;
}

bool local_date(int *weekday, int *month, int *day)
{
    if (weekday == nullptr || month == nullptr || day == nullptr)
        return false;
    std::tm now{};
    if (!local_time(now))
        return false;
    *weekday = now.tm_wday;
    *month = now.tm_mon + 1;
    *day = now.tm_mday;
    return true;
}

void log(const char *format, ...)
{
    if (format == nullptr)
        return;
    char line[2048]{};
    va_list arguments;
    va_start(arguments, format);
    const int length = std::vsnprintf(line, sizeof(line) - 2, format, arguments);
    va_end(arguments);
    if (length < 0)
        return;
    const std::size_t used = std::strlen(line);
    line[used] = '\n';
    line[used + 1] = '\0';
    static std::mutex mutex;
    std::lock_guard<std::mutex> lock(mutex);
    std::fputs(line, stdout);
    std::fflush(stdout);
    OutputDebugStringA(line);
}

bool hide_splash_screen()
{
    // The desktop window presents the app's first frame directly.
    return true;
}

void sleep_us(std::uint32_t microseconds)
{
    std::this_thread::sleep_for(std::chrono::microseconds(microseconds));
}

[[noreturn]] void park()
{
    std::fflush(nullptr);
    for (;;)
        std::this_thread::sleep_for(std::chrono::seconds(1));
}

[[noreturn]] void quit()
{
    log("[HUI] quit requested");
    std::fflush(nullptr);
    std::exit(EXIT_SUCCESS);
}

} // namespace hui::sys

#endif // _WIN32
