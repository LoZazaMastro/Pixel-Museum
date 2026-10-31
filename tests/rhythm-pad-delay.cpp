// Focused regression: delayed rhythm cues follow the current audio clock/state.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/experience_audio.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
using museum::ExperienceAudio;
namespace {
struct Grain {
    std::vector<float> tv,pad;
    explicit Grain(unsigned frames,float initial=0):tv(frames*2,initial),pad(frames,initial){}
};
Grain render(ExperienceAudio& source,unsigned frames,bool speaker=true,float initial=0){
    Grain out(frames,initial);source.render(out.tv.data(),frames,speaker?out.pad.data():nullptr);return out;
}
bool silent(const std::vector<float>& samples){return std::all_of(samples.begin(),samples.end(),[](float v){return v==0;});}
double energy(const std::vector<float>& samples){double sum=0;for(float v:samples)sum+=double(v)*v;return sum;}
void prime(ExperienceAudio& source){source.start();render(source,4800);}
}
int main(){
    static_assert(ExperienceAudio::controller_delay_frames==9600);
    // A restart must discard a populated ring, rather than emit the previous
    // run's cue before the new 200 ms delay has elapsed.
    ExperienceAudio restarted,fresh;prime(restarted);restarted.start();fresh.start();
    auto reset_silence=render(restarted,9600);auto fresh_silence=render(fresh,9600);
    assert(silent(reset_silence.pad)&&reset_silence.pad==fresh_silence.pad);
    auto after_reset=render(restarted,4800);auto after_fresh=render(fresh,4800);
    assert(after_reset.pad==after_fresh.pad&&energy(after_reset.pad)>1e-5);
    // Pause freezes both the song clock and its delay ring. A longer wall-clock
    // pause must produce exactly the same resumed samples as a short pause.
    ExperienceAudio paused,reference;prime(paused);prime(reference);
    const double paused_at=paused.time_s();paused.paused(true);reference.paused(true);
    auto gap=render(paused,24000,true,.125f);render(reference,1,true,.125f);
    assert(silent(gap.pad)&&paused.time_s()==paused_at);
    for(float v:gap.tv)assert(v==.125f);
    paused.paused(false);reference.paused(false);
    auto resumed=render(paused,12000);auto expected=render(reference,12000);
    assert(resumed.pad==expected.pad&&resumed.tv==expected.tv&&energy(resumed.pad)>1e-5);
    // The ring stores the dry cue, not a previously applied volume: zero must
    // silence even queued samples, and restoring volume must not replay them.
    ExperienceAudio muted,unmuted;prime(muted);prime(unmuted);muted.volume(0);
    auto mute_grain=render(muted,12000);render(unmuted,12000);
    assert(silent(mute_grain.pad)&&silent(mute_grain.tv));
    muted.volume(1);auto audible=render(muted,48000);auto continuous=render(unmuted,48000);
    assert(audible.pad==continuous.pad&&audible.tv==continuous.tv&&energy(audible.pad)>1e-5);
    // Absence of a destination buffer must still consume the ring in song
    // time; reattaching the pad must never drain a backlog of old cues.
    ExperienceAudio detached,attached;prime(detached);prime(attached);
    render(detached,60000,false);render(attached,60000);
    auto returned=render(detached,12000);auto live=render(attached,12000);
    assert(returned.pad==live.pad&&returned.tv==live.tv);
    assert(detached.time_s()==attached.time_s());
    std::puts("PASS DDR delay: restart clears 9600 frames; pause freezes queue/clock; current volume mutes queued cues; missing pad buffer consumes without backlog.");
}
