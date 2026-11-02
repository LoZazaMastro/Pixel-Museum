// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "core/input.hpp"
#include <SDL3/SDL.h>
#include <array>
namespace museum::desktop {
class Input {
public:
    ~Input();
    hui::InputFrame poll(SDL_Window*,bool text_input,bool& quit,bool& toggle_fullscreen);
    SDL_Gamepad* gamepad(unsigned index=0)const{return index<pads_.size()?pads_[index]:nullptr;}
    void rumble(float strength,float seconds,unsigned index=0);
    bool controller_active() const { return focused_&&style_!=hui::DesktopControllerStyle::keyboard_mouse; }
    void stop_rumble();
private:
    friend struct InputInspection;
    void refresh_gamepads();
    hui::PadSample sample(SDL_Gamepad*,std::uint64_t);
    std::array<SDL_Gamepad*,2> pads_{};
    hui::InputTracker primary_,secondary_;
    bool text_active_=false;
    bool focused_=false;
    bool rumbling_=false;
    hui::DesktopControllerStyle style_=hui::DesktopControllerStyle::keyboard_mouse;
};
}
