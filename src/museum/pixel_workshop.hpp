// Pixel Museum - an original, bounded interactive illustration.
// Copyright (C) 2026 Andrea Sgarro. SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "core/input.hpp"
#include "core/tween.hpp"
#include "gfx/draw_list.hpp"
#include "ui/feedback.hpp"
#include "ui/fonts.hpp"
#include <array>
#include <cstdint>
namespace museum {
// Generic four-shade illustration, not an emulated console or historical game.
// No media, allocation, networking or GL resource ownership in the component.
class PixelWorkshop {
public:
    PixelWorkshop();
    bool handle(const hui::InputFrame&,hui::ui::Feedback&); // true means Back/exit
    void update(float);
    void draw(hui::gfx::DrawList&,hui::ui::Fonts&,hui::gfx::Rect,hui::gfx::Color accent,bool active);
    void reset();
    // A pointer contact selects its exact tile before a simultaneous click.
    // Preserve the drawing and animate the visible cursor towards that tile.
    void set_cursor(unsigned x,unsigned y);
    unsigned cursor_x()const{return x_;}
    unsigned cursor_y()const{return y_;}
    unsigned shade(unsigned x,unsigned y)const{return x<8&&y<8?pixels_[y*8+x]:0;}
    bool grid_visible()const{return grid_;}
private:
    std::array<std::uint8_t,64> pixels_{};
    std::array<float,64> appearance_{};
    unsigned x_=1,y_=1;
    bool grid_=true,active_=false;
    hui::tween::Spring cursor_x_,cursor_y_,focus_,grid_opacity_;
    float edit_flash_=0;
};
} // namespace museum
