// Pixel Museum - small, original interactive studies of the medium.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "core/input.hpp"
#include "gfx/draw_list.hpp"
#include "ui/feedback.hpp"
#include "ui/fonts.hpp"
#include <memory>
#include <map>
#include <cstdint>
#include <string>
namespace museum {
class ExperienceAudio;
enum class StudyCompletion { playing, level_complete, experience_complete };
class Study {
public:
    virtual ~Study()=default;
    virtual void reset()=0;
    virtual void handle(const hui::InputFrame&,hui::ui::Feedback&)=0;
    virtual void update(float dt)=0;
    // Draw within the supplied rectangle. Native vectors/original procedural
    // geometry only: these are illustrations, not emulated commercial games.
    virtual void draw(hui::gfx::DrawList&,hui::ui::Fonts&,hui::gfx::Rect,hui::gfx::Color)=0;
    virtual const char*help()const=0;
    virtual void attach_audio(ExperienceAudio*) {}
    virtual bool motion_controls()const{return false;}
    virtual bool local_multiplayer()const{return false;}
    virtual bool flight_settings()const{return false;}
    virtual bool gyro_enabled()const{return false;}
    virtual float gyro_sensitivity()const{return 1.f;}
    virtual void configure_gyro(bool,float) {}
    // A completed stage stays on screen until the shared Continue / Exit sheet
    // accepts an explicit action. Endless creative studies remain playing.
    virtual StudyCompletion completion()const{return StudyCompletion::playing;}
    // Measured current-run bests; the persistent trophy engine retains lifetime bests.
    virtual std::map<std::string,std::uint64_t> trophy_stats()const{return {};}
    virtual int level_number()const{return 1;}
    virtual int level_count()const{return 1;}
    virtual void continue_level(){reset();}
    int take_note(){const int n=note_;note_=-1;return n;}
protected:
    int note_=-1;
    void sound(int note){note_=note;}
};
std::unique_ptr<Study> make_study_arcade(const std::string&);
std::unique_ptr<Study> make_study_motion(const std::string&);
std::unique_ptr<Study> make_study_space(const std::string&);
std::unique_ptr<Study> make_study(const std::string&);
}
