// Pixel Museum - one palette across the collection and its first visit.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/draw_list.hpp"
#include <algorithm>
namespace museum {
struct MuseumPalette {
    hui::gfx::Color paper,ink,muted,rule,surface;
};
inline MuseumPalette museum_palette(float dark){
    using hui::gfx::Color;using hui::gfx::mix;
    const float t=std::clamp(dark,0.f,1.f);
    const Color ink=mix(Color::rgb(0x202521),Color::rgb(0xf1efe7),t);
    return {mix(Color::rgb(0xf1efe7),Color::rgb(0x0b100e),t),ink,
            mix(Color::rgb(0x656a63),Color::rgb(0xa3aaa2),t),ink.with_alpha(.16f),
            mix(Color::rgb(0xe5e2d7),Color::rgb(0x18201b),t)};
}
}
