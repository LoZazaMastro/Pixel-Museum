// Pixel Museum - Legible film captions, independent of transient controls.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "ui/fonts.hpp"
#include <algorithm>
#include <string_view>
namespace museum {
struct CaptionLayout {
    std::vector<std::string> lines;
    hui::gfx::Rect backing{};
    float size=0,line_height=0,first_baseline=0;
};
inline CaptionLayout film_caption_layout(const hui::ui::FontRef& font,std::string_view cue,
                                        hui::gfx::Rect picture,float controls) {
    CaptionLayout out;
    if(cue.empty()||picture.w<160||picture.h<100)return out;
    const float width=picture.w*.88f;
    out.size=std::clamp(picture.w/55.f,18.f,34.f);
    // Caption text is supplied by YouTube, not an interface localisation key.
    // Wrap and draw the actual words without passing through the UI resolver.
    for(;;){
        out.lines=font.font->wrap(cue,out.size,width);
        out.line_height=out.size*1.3f;
        if((out.lines.size()<=4&&out.lines.size()*out.line_height<=picture.h*.48f)||out.size<=12.f)break;
        out.size-=1.f;
    }
    float widest=0;for(const auto&line:out.lines)widest=std::max(widest,font.font->measure(line,out.size));
    const float pad=out.size*.38f,height=float(out.lines.size())*out.line_height;
    const float bottom=picture.y+picture.h-std::clamp(picture.h*.065f,14.f,64.f)-std::clamp(controls,0.f,1.f)*80.f;
    const float top=std::max(picture.y+pad,bottom-height-pad*2);
    out.backing={picture.cx()-widest/2-pad,top,widest+pad*2,height+pad*2};
    out.first_baseline=top+pad+out.size;
    return out;
}
inline void draw_film_captions(hui::gfx::DrawList& list,const hui::ui::FontRef& font,
                              std::string_view cue,hui::gfx::Rect picture,float controls) {
    const auto layout=film_caption_layout(font,cue,picture,controls);
    if(layout.lines.empty())return;
    list.push_clip(picture);
    list.rounded_rect(layout.backing,3,hui::gfx::Color::rgb(0,.82f));
    float baseline=layout.first_baseline;
    for(const auto&line:layout.lines){
        list.text(*font.font,font.texture,line,picture.cx(),baseline,layout.size,
                  hui::gfx::Color::rgb(0xffffff),hui::gfx::Align::center);
        baseline+=layout.line_height;
    }
    list.pop_clip();
}
} // namespace museum
