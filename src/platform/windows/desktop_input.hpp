// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "core/input.hpp"
#include <SDL3/SDL.h>
#include <array>
namespace museum::desktop {
class Input {
public:
    ~Input();
    hui::InputFrame poll(SDL_Window*,bool text_input,bool& quit,bool& toggle_fullscreen,
                         bool keep_player_order=false,bool motion_controls=false);
    SDL_Gamepad* gamepad(unsigned index=0)const{return index<pads_.size()?pads_[index]:nullptr;}
    void rumble(float strength,float seconds,unsigned index=0);
    bool controller_active() const { return focused_&&style_!=hui::DesktopControllerStyle::keyboard_mouse; }
    bool hide_system_cursor(bool mouse_in_window,const hui::PointerInput&) const;
    void stop_rumble();
    static bool is_dualsense(SDL_Gamepad*);
private:
    friend struct InputInspection;
    bool pointer_available(bool mouse_in_window) const { return focused_&&mouse_in_window&&mouse_active_; }
    void refresh_gamepads();
    hui::PadSample sample(SDL_Gamepad*,std::uint64_t);
    std::array<SDL_Gamepad*,2> pads_{};
    hui::InputTracker primary_,secondary_;
    bool text_active_=false;
    bool focused_=false;
    std::array<bool,2> rumbling_{};
    // Keyboard prompts and pointer visibility are independent: only using the
    // mouse restores a pointer hidden by controller input.
    bool mouse_active_=true;
    float canvas_left_=0;
    hui::DesktopControllerStyle style_=hui::DesktopControllerStyle::keyboard_mouse;
};
}
