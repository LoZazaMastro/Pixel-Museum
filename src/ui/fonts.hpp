// ps5-homebrew-ui - The font set every screen draws with.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include "gfx/draw_list.hpp"
#include "gfx/font.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <string>
#include <string_view>
#include <vector>

namespace hui::ui
{

using TextResolver = std::string_view (*)(std::string_view);
inline TextResolver text_resolver=nullptr;
inline std::string_view resolve_text(std::string_view value){return text_resolver?text_resolver(value):value;}
struct FontRef;
struct InlineTextRenderer{
    float (*measure)(const FontRef&,std::string_view,float,float)=nullptr;
    float (*draw)(gfx::DrawList&,const FontRef&,std::string_view,float,float,float,gfx::Color,gfx::Align,float)=nullptr;
    std::vector<std::string> (*wrap)(const FontRef&,std::string_view,float,float)=nullptr;
};
inline InlineTextRenderer inline_text_renderer;
// Resolve the complete sentence before inserting live values. Translating the
// formatted result cannot find an exact source key once a score has changed.
inline const char* format_argument(const char* value){return value?resolve_text(value).data():"";}
template<class T> inline T format_argument(T value){return value;}
template<std::size_t N,class... Args>
inline int format(char (&out)[N],std::string_view pattern,Args... args){
    const std::string translated(resolve_text(pattern));
    if constexpr(sizeof...(Args)==0)return std::snprintf(out,N,"%s",translated.c_str());
    else return std::snprintf(out,N,translated.c_str(),format_argument(args)...);
}
// A loaded font and the GL texture holding its atlas.
struct FontRef
{
    const gfx::Font *font = nullptr;
    std::uint32_t texture = 0;

    float measure(std::string_view text, float size, float tracking = 0.0f) const
    {
        const auto translated=resolve_text(text);
        return inline_text_renderer.measure&&translated.find('{')!=std::string_view::npos?inline_text_renderer.measure(*this,translated,size,tracking):font->measure(translated,size,tracking);
    }
};

struct Fonts
{
    FontRef regular;  // Inter Regular: body text
    FontRef semibold; // Inter SemiBold: titles, labels, buttons
    FontRef display;  // Montserrat Medium: wide geometric headlines
    FontRef mono;     // DejaVu Sans Mono: numbers that must not jump, terminals
    FontRef pixel;    // Press Start 2P: an 8x8 bitmap face (the Pixel theme)
    FontRef hand;     // Patrick Hand: handwriting (the Sketch theme)
};

// Draws one line with its baseline at y; x is the left edge, centre or right
// edge depending on align. Returns the width.
inline float text(gfx::DrawList &list, const FontRef &font, std::string_view value, float x,
                  float baseline, float size, gfx::Color color, gfx::Align align = gfx::Align::left,
                  float tracking = 0.0f)
{
    const auto translated=resolve_text(value);
    if(inline_text_renderer.draw&&translated.find('{')!=std::string_view::npos)return inline_text_renderer.draw(list,font,translated,x,baseline,size,color,align,tracking);
    return list.text(*font.font, font.texture, translated, x, baseline, size, color, align, tracking);
}

// ASCII upper case, for small tracked labels ("CONTINUE PLAYING").
inline std::string upper(std::string_view value)
{
    std::string result(resolve_text(value));
    for (char &c : result)
    {
        if (c >= 'a' && c <= 'z')
            c = static_cast<char>(c - 'a' + 'A');
    }
    return result;
}

// A paragraph as it is drawn: word-wrapped, at most max_lines lines (never
// fewer than one), the last one ending in an ellipsis if text remains. Empty
// text is one empty line. This is the one place that decides it, so what is
// measured and what is drawn cannot disagree.
struct ParagraphLines
{
    std::vector<std::string> lines;
    bool truncated = false; // text remained after max_lines: the last line shows the ellipsis
};

inline ParagraphLines paragraph_lines(const FontRef &font, std::string_view value, float size,
                                      float width, int max_lines = 99)
{
    ParagraphLines result;
    const auto translated=resolve_text(value);
    result.lines = inline_text_renderer.wrap&&translated.find('{')!=std::string_view::npos?inline_text_renderer.wrap(font,translated,size,width):font.font->wrap(translated,size,width);
    const std::size_t cap = static_cast<std::size_t>(std::max(max_lines, 1));
    if (result.lines.size() > cap)
    {
        result.lines.resize(cap);
        result.lines.back() = font.font->fit(result.lines.back() + " \xE2\x80\xA6", size, width);
        result.truncated = true;
    }
    return result;
}

// Draws lines from paragraph_lines() from the first baseline at y. Returns
// the baseline after the last line drawn.
inline float paragraph(gfx::DrawList &list, const FontRef &font, const ParagraphLines &lines,
                       float x, float y, float size, float line_height, gfx::Color color,
                       gfx::Align align = gfx::Align::left)
{
    for (const std::string &line : lines.lines)
    {
        text(list, font, line, x, y, size, color, align);
        y += line_height;
    }
    return y;
}

// Draws word-wrapped text from its first baseline at y, at most max_lines
// lines (the last one ends in an ellipsis if text remains). Returns the
// baseline after the last line drawn.
inline float paragraph(gfx::DrawList &list, const FontRef &font, std::string_view value, float x,
                       float y, float size, float width, float line_height, gfx::Color color,
                       int max_lines = 99, gfx::Align align = gfx::Align::left)
{
    return paragraph(list, font, paragraph_lines(font, value, size, width, max_lines), x, y, size,
                     line_height, color, align);
}

// The space paragraph() will take, measured without drawing. Lay out what
// follows a block of text, or work out how much of a list fits, before
// drawing any of it.
struct ParagraphMetrics
{
    int lines = 0;          // lines paragraph() draws
    float height = 0.0f;    // lines * line_height: how far paragraph() moves y
    float width = 0.0f;     // widest line as drawn, ellipsis included
    bool truncated = false; // text remained after max_lines: the last line shows the ellipsis
};

// Wrapping allocates and measures every word: a screen that measures and then
// draws the same text wraps once with paragraph_lines() and passes the result
// to both.
inline ParagraphMetrics measure_paragraph(const FontRef &font, const ParagraphLines &lines,
                                          float size, float line_height)
{
    ParagraphMetrics m;
    m.lines = static_cast<int>(lines.lines.size());
    m.height = static_cast<float>(m.lines) * line_height;
    for (const std::string &line : lines.lines)
        m.width = std::max(m.width, font.measure(line, size));
    m.truncated = lines.truncated;
    return m;
}

inline ParagraphMetrics measure_paragraph(const FontRef &font, std::string_view value, float size,
                                          float width, float line_height, int max_lines = 99)
{
    return measure_paragraph(font, paragraph_lines(font, value, size, width, max_lines), size,
                             line_height);
}

} // namespace hui::ui
