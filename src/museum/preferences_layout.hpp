// Shared geometry for Options drawing, pointer hitboxes and input checks.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/draw_list.hpp"
namespace museum {
#if defined(MUSEUM_DESKTOP)
inline constexpr float preference_row_pitch=60.f;
inline constexpr int desktop_audio_preference_row=1;
inline constexpr bool has_controller_audio_preferences=false;
inline constexpr const char* audio_preference_label="Audio";
#else
inline constexpr float preference_row_pitch=68.f;
inline constexpr bool has_controller_audio_preferences=true;
inline constexpr const char* audio_preference_label="Volumes";
#endif
inline constexpr float preference_row_baseline(int row){return 240.f+float(row)*preference_row_pitch;}
inline constexpr hui::gfx::Rect preference_row_bounds(float panel_x,int row){return {panel_x+45,preference_row_baseline(row)-35,710,56};}
inline constexpr int audio_slider_count=has_controller_audio_preferences?5:4;
inline constexpr int audio_preference_count=audio_slider_count+int(has_controller_audio_preferences);
inline constexpr float audio_slider_baseline(int row){return 230.f+row*118.f;}
inline constexpr hui::gfx::Rect audio_slider_bounds(float panel_x,int row){return {panel_x+55,audio_slider_baseline(row)-29,675,99};}
}
