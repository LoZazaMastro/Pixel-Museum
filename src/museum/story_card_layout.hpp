// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

#include "gfx/draw_list.hpp"

namespace museum {
inline constexpr float story_card_pitch=1792.f;
inline constexpr hui::gfx::Rect story_card{96,286,1728,620};

inline hui::gfx::Rect story_card_bounds(float distance,float rise){
    return {story_card.x+distance*story_card_pitch,story_card.y+rise,story_card.w,story_card.h};
}
}
