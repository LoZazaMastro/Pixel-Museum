// Shared geometry for Options drawing, pointer hitboxes and input checks.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/draw_list.hpp"
namespace museum {
#if defined(MUSEUM_DESKTOP)
inline constexpr float preference_row_pitch=60.f;
#else
inline constexpr float preference_row_pitch=68.f;
#endif
inline constexpr float preference_row_baseline(int row){return 240.f+float(row)*preference_row_pitch;}
inline constexpr hui::gfx::Rect preference_row_bounds(float panel_x,int row){return {panel_x+45,preference_row_baseline(row)-35,710,56};}
}
