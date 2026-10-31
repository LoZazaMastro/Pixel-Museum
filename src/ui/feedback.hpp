// ps5-homebrew-ui - Feedback: the sounds and rumble a screen asks for this frame.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include "audio/cues.hpp"
#include "audio/controller_feedback.hpp"

#include <vector>

namespace hui::ui
{

// What a screen or a component asks the platform to do this frame besides
// drawing. The owner of the frame loop plays the cues and starts the rumble.
struct Feedback
{
    std::vector<audio::CueEvent> cues;
    std::vector<audio::TactileEvent> tactile;
    std::vector<audio::SpeakerEvent> speaker_cues;
    float rumble_strength = 0.0f;
    float rumble_seconds = 0.0f;

    void play(audio::Cue cue, float pitch = 1.0f, float pan = 0.0f, float gain = 1.0f)
    {
        cues.push_back({cue, pitch, pan, gain, audio::SoundSet::count});
        const auto pattern=cue==audio::Cue::error||cue==audio::Cue::invalid?audio::Tactile::error:
            cue==audio::Cue::back||cue==audio::Cue::modal_close?audio::Tactile::back:
            cue==audio::Cue::focus||cue==audio::Cue::tick||cue==audio::Cue::slider?audio::Tactile::focus:audio::Tactile::confirm;
        feel(pattern,pattern==audio::Tactile::focus?.13f:.22f,pattern==audio::Tactile::focus?.022f:.065f,pan);
    }
    void feel(audio::Tactile pattern,float strength,float seconds,float pan=0.f){
        tactile.push_back({pattern,strength,seconds,pan});
        if(strength>=rumble_strength){rumble_strength=strength;rumble_seconds=seconds;}
    }
    // Semantic action sounds; ordinary focus navigation remains on the TV.
    // The explicit timeline route switch below also uses a short pad motif.
    void speak(audio::SpeakerCue cue,float pitch=1.f,float gain=.12f){
        speaker_cues.push_back({cue,pitch,gain});
    }
    // Called only after a timeline index actually changes, never a held input
    // at a boundary. TV focus audio stays separate from controller PCM.
    void timeline_step(int direction){
        if(direction==0)return;
        const float pan=direction<0?-.55f:.55f;
        cues.push_back({audio::Cue::focus,1.f,pan,.6f,audio::SoundSet::count});
        feel(audio::Tactile::timeline_step,.34f,.055f,pan);
    }
    void timeline_route(bool culture){
        tactile.clear();
        feel(culture?audio::Tactile::rise:audio::Tactile::fall,.38f,.17f);
        speak(culture?audio::SpeakerCue::timeline_culture:audio::SpeakerCue::timeline_games,1.f,.14f);
    }
    // strength 0..1; keep UI rumbles short (0.04-0.15 s).
    void rumble(float strength, float seconds)
    {
        feel(audio::Tactile::impact,strength,seconds);
    }
    void clear()
    {
        cues.clear();
        tactile.clear();
        speaker_cues.clear();
        rumble_strength = 0.0f;
        rumble_seconds = 0.0f;
    }
};

} // namespace hui::ui
