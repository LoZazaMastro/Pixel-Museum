// Pixel Museum - an original native listening-room presentation.
// Copyright (C) 2026 Andrea Sgarro. SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/catalog.hpp"
#include "museum/theme.hpp"
#include "ui/fonts.hpp"
#include <string_view>
namespace museum {
// Presentation only. The caller owns navigation, media generation, playback,
// resources and timing. A missing texture never becomes a fabricated still.
void draw_soundtrack_card(hui::gfx::DrawList&,hui::ui::Fonts&,hui::gfx::Rect,
                         hui::gfx::Color accent,const Soundtrack&,int selection,
                         int playing_index,bool paused,float time,float duration,
                         unsigned video_texture,int video_width,int video_height,
                         std::string_view status,float dark=0);
}
