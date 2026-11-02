// Shared optical alignment for the museum's settings rows.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "ui/fonts.hpp"

namespace museum {
inline float menu_text_center(const hui::ui::FontRef& font,std::string_view label,float baseline,float size){
    std::vector<hui::gfx::GlyphQuad> glyphs;
    font.font->layout(hui::ui::resolve_text(label),0,baseline,size,hui::gfx::Align::left,glyphs);
    if(glyphs.empty())return baseline+(font.font->descent(size)-font.font->ascent(size))*.5f;
    float top=glyphs.front().y0,bottom=glyphs.front().y1;
    for(const auto& glyph:glyphs){top=std::min(top,glyph.y0);bottom=std::max(bottom,glyph.y1);}
    return (top+bottom)*.5f;
}
inline float menu_text_baseline(const hui::ui::FontRef& font,std::string_view label,float center,float size){
    return center-menu_text_center(font,label,0,size);
}
}
