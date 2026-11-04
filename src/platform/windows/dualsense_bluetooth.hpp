// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include <SDL3/SDL_gamepad.h>
#include <atomic>
#include <thread>

namespace hui::audio { class ControllerFeedback; }

namespace museum::desktop {
class DualSenseBluetooth {
public:
    ~DualSenseBluetooth();
    bool start(SDL_Gamepad*,hui::audio::ControllerFeedback&);
    void stop();
    bool ready()const{return ready_.load(std::memory_order_acquire);}

private:
    std::atomic<bool> ready_{false};
    std::jthread worker_;
};
}
