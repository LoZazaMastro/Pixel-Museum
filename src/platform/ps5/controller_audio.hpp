// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "audio/controller_feedback.hpp"
#include <atomic>
#include <pthread.h>
namespace hui::ps5 {
// Separate user-routed PCM ports. Successful API calls are logged, but only a
// physical DualSense test can establish routing, level and tactile sensation.
class ControllerAudio {
public:
    ~ControllerAudio(){stop();}
    bool start(int user,audio::ControllerFeedback&signals);
    void stop();
    bool haptics_ready()const{return haptics_.healthy.load(std::memory_order_acquire);}
    bool speaker_ready()const{return speaker_.healthy.load(std::memory_order_acquire);}
    std::uint64_t speaker_nonzero_blocks()const{return speaker_.nonzero_blocks.load(std::memory_order_relaxed);}
    std::uint64_t haptics_nonzero_blocks()const{return haptics_.nonzero_blocks.load(std::memory_order_relaxed);}
    unsigned speaker_peak()const{return speaker_.peak.load(std::memory_order_relaxed);}
    unsigned haptics_peak()const{return haptics_.peak.load(std::memory_order_relaxed);}
private:
    struct Output {
        int port=-1;bool speaker=false,started=false;
        pthread_t thread{};
        std::atomic<bool> stop{false},healthy{false};
        std::atomic<std::uint64_t> nonzero_blocks{0};
        std::atomic<unsigned> peak{0};
        audio::ControllerFeedback* signals=nullptr;
    };
    Output haptics_,speaker_;
    static bool open(Output&,int user,int type,bool speaker,audio::ControllerFeedback&);
    static void close(Output&);
    static void*run(void*);
};
}
