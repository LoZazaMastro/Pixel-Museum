// Pixel Museum - One system audio port for the museum and its video exhibits.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <atomic>
#include <pthread.h>
namespace hui::ps5 {
class MuseumAudio {
  public:
    using Render = void (*)(void *context, float *stereo, unsigned frames);
    ~MuseumAudio();
    bool start(Render render, void *context);
    void stop();
  private:
    static void *entry(void *self);
    void run();
    Render render_ = nullptr;
    void *context_ = nullptr;
    int port_ = -1;
    pthread_t thread_{};
    std::atomic<bool> stop_{false};
    bool running_ = false;
};
} // namespace hui::ps5
