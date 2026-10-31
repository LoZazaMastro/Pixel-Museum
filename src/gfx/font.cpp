// ps5-homebrew-ui - Baked SDF font: loading, measuring and glyph layout.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#include "gfx/font.hpp"

#include <algorithm>
#include <cstring>
#include <cmath>

namespace hui::gfx
{

namespace ff = font_format;

std::uint32_t next_codepoint(std::string_view text, std::size_t *index)
{
    const auto byte = [&](std::size_t at) { return static_cast<unsigned char>(text[at]); };
    const std::size_t i = *index;
    const unsigned char lead = byte(i);
    int length = 1;
    std::uint32_t value = lead;
    if (lead >= 0xf0 && lead < 0xf8)
    {
        length = 4;
        value = lead & 0x07u;
    }
    else if (lead >= 0xe0)
    {
        length = 3;
        value = lead & 0x0fu;
    }
    else if (lead >= 0xc0)
    {
        length = 2;
        value = lead & 0x1fu;
    }
    else if (lead >= 0x80)
    {
        *index = i + 1;
        return 0xfffd;
    }
    if (i + static_cast<std::size_t>(length) > text.size())
    {
        *index = text.size();
        return 0xfffd;
    }
    for (int k = 1; k < length; ++k)
    {
        const unsigned char continuation = byte(i + static_cast<std::size_t>(k));
        if ((continuation & 0xc0u) != 0x80u)
        {
            *index = i + 1;
            return 0xfffd;
        }
        value = (value << 6) | (continuation & 0x3fu);
    }
    *index = i + static_cast<std::size_t>(length);
    return value;
}

bool Font::load(std::string_view data)
{
    error_.clear();
    if (data.size() < sizeof(ff::Header))
    {
        error_ = "font too small";
        return false;
    }
    std::memcpy(&header_, data.data(), sizeof(header_));
    if (header_.magic != ff::kMagic || (header_.version != ff::kVersion && header_.version != ff::kClusterVersion) ||
        header_.pixel_size <= 0.0f)
    {
        error_ = "not a supported huifont";
        return false;
    }
    const std::size_t glyph_bytes =
        static_cast<std::size_t>(header_.glyph_count) * sizeof(ff::Glyph);
    const std::size_t kern_bytes = static_cast<std::size_t>(header_.kern_count) * sizeof(ff::Kern);
    const std::size_t atlas_bytes = static_cast<std::size_t>(header_.atlas_width) *
                                    static_cast<std::size_t>(header_.atlas_height);
    const auto base_size=sizeof(ff::Header)+glyph_bytes+kern_bytes+atlas_bytes;
    if ((header_.version==ff::kVersion&&data.size()!=base_size) || data.size()<base_size)
    {
        error_ = "font size mismatch";
        return false;
    }
    const char *cursor = data.data() + sizeof(ff::Header);
    // A font may have no glyphs or (monospaced faces) no kerning pairs.
    glyphs_.resize(header_.glyph_count);
    if (glyph_bytes != 0)
        std::memcpy(glyphs_.data(), cursor, glyph_bytes);
    cursor += glyph_bytes;
    kerns_.resize(header_.kern_count);
    if (kern_bytes != 0)
        std::memcpy(kerns_.data(), cursor, kern_bytes);
    cursor += kern_bytes;
    atlas_.assign(reinterpret_cast<const std::uint8_t *>(cursor),
                  reinterpret_cast<const std::uint8_t *>(cursor) + atlas_bytes);
    for (const ff::Glyph &glyph : glyphs_)
    {
        if (glyph.x + glyph.w > header_.atlas_width || glyph.y + glyph.h > header_.atlas_height)
        {
            error_ = "glyph outside atlas";
            return false;
        }
    }
    shaped_runs_.clear();
    if(header_.version==ff::kClusterVersion){
        std::size_t at=base_size;std::uint32_t tag=0,count=0;
        const auto integer=[&](std::uint32_t&value){if(at>data.size()||data.size()-at<4)return false;std::memcpy(&value,data.data()+at,4);at+=4;return true;};
        if(data.size()-base_size>(256u<<10)||!integer(tag)||tag!=ff::kClusterTag||!integer(count)||count>512){error_="invalid shaped font trailer";return false;}
        std::vector<ShapedRun> runs;runs.reserve(count);
        for(std::uint32_t n=0;n<count;++n){
            std::uint32_t glyph=0,length=0;if(!integer(glyph)||!integer(length)||length==0||length>1024||at>data.size()||length>data.size()-at){error_="invalid shaped font run";return false;}
            std::string text(data.substr(at,length));at+=length;const auto*target=find(glyph);
            if(glyph<0xf0000||glyph>0xffffd||!target||!std::isfinite(target->advance)||target->advance<=0){error_="invalid shaped font glyph";return false;}
            bool script=false;for(std::size_t p=0;p<text.size();){const auto cp=next_codepoint(text,&p);if(cp>=0x590&&cp<=0xdff)script=true;else if(cp!=' '&&cp!=0xa0){error_="invalid shaped font source text";return false;}}
            if(!script||static_cast<unsigned char>(text.front())<0xc0||text.back()==' '){error_="invalid shaped font source boundary";return false;}
            if(std::any_of(runs.begin(),runs.end(),[&](const auto&run){return run.text==text;})){error_="duplicate shaped font run";return false;}
            runs.push_back({std::move(text),glyph});
        }
        if(at!=data.size()){error_="trailing shaped font bytes";return false;}
        std::sort(runs.begin(),runs.end(),[](const auto&a,const auto&b){return a.text.size()!=b.text.size()?a.text.size()>b.text.size():a.text<b.text;});shaped_runs_=std::move(runs);
    }
    return true;
}

namespace {
bool complex_script(std::uint32_t cp){return (cp>=0x590&&cp<=0xeff)||(cp>=0x1780&&cp<=0x17ff)||(cp>=0xfb1d&&cp<=0xfdff)||(cp>=0xfe70&&cp<0xfeff);}
}
std::uint32_t Font::next_unit(std::string_view text,std::size_t*index,bool words_only)const{
    const auto start=*index;
    // Ordinary Latin and most UI strings take the original fast path.
    if(static_cast<unsigned char>(text[start])>=0xc0){
        bool boundary=true;
        if(start){std::size_t previous=start-1;while(previous&&((static_cast<unsigned char>(text[previous])&0xc0)==0x80))--previous;boundary=!complex_script(next_codepoint(text,&previous));}
        if(boundary){
            const auto match=[&](const Font*face)->std::uint32_t{
                for(const auto&run:face->shaped_runs_){if(words_only&&run.text.find(' ')!=std::string::npos)continue;if(text.size()-start<run.text.size()||text.compare(start,run.text.size(),run.text)!=0)continue;
                    const auto end=start+run.text.size();if(end<text.size()){auto following=end;if(complex_script(next_codepoint(text,&following)))continue;}
                    *index=end;return run.glyph;
                }return 0;
            };
            if(const auto cp=match(this))return cp;
            for(const auto&fallback:fallbacks_)if(const auto cp=match(fallback.face))return cp;
        }
    }
    return next_codepoint(text,index);
}
bool Font::has_text(std::string_view text)const{
    for(std::size_t index=0;index<text.size();){const auto cp=next_unit(text,&index);if(cp=='\n'||cp=='\r'||cp=='\t')continue;if(complex_script(cp)||!has_glyph(cp))return false;}return true;
}

const ff::Glyph *Font::find(std::uint32_t codepoint) const
{
    const auto it =
        std::lower_bound(glyphs_.begin(), glyphs_.end(), codepoint,
                         [](const ff::Glyph &g, std::uint32_t c) { return g.codepoint < c; });
    return it != glyphs_.end() && it->codepoint == codepoint ? &*it : nullptr;
}

float Font::kern(std::uint32_t first, std::uint32_t second) const
{
    const auto it = std::lower_bound(
        kerns_.begin(), kerns_.end(), std::make_pair(first, second),
        [](const ff::Kern &k, const std::pair<std::uint32_t, std::uint32_t> &key)
        { return k.first != key.first ? k.first < key.first : k.second < key.second; });
    return it != kerns_.end() && it->first == first && it->second == second ? it->amount : 0.0f;
}

std::string Font::fit(std::string_view text, float size, float max_width, float tracking) const
{
    if (measure(text, size, tracking) <= max_width)
        return std::string(text);
    constexpr std::string_view kEllipsis = "\xE2\x80\xA6";
    const std::string_view mark = has_glyph(0x2026) ? kEllipsis : std::string_view("...");
    std::string best;
    for (std::size_t index = 0; index < text.size();)
    {
        const std::size_t start = index;
        next_unit(text, &index,true);
        std::string candidate(text.substr(0, start));
        while (!candidate.empty() && candidate.back() == ' ')
            candidate.pop_back();
        candidate.append(mark);
        if (measure(candidate, size, tracking) > max_width)
            break;
        best = std::move(candidate);
    }
    return best;
}

bool Font::has_glyph(std::uint32_t codepoint) const
{
    if (find(codepoint) != nullptr)
        return true;
    for (const Fallback &fallback : fallbacks_)
    {
        if (fallback.face->find(codepoint) != nullptr)
            return true;
    }
    return false;
}

Font::Resolved Font::resolve(std::uint32_t *codepoint) const
{
    if (const ff::Glyph *glyph = find(*codepoint))
        return {this, glyph, 0};
    for (const Fallback &fallback : fallbacks_)
    {
        if (const ff::Glyph *glyph = fallback.face->find(*codepoint))
            return {fallback.face, glyph, fallback.texture};
    }
    *codepoint = '?';
    return {this, find('?'), 0};
}

float Font::measure(std::string_view text, float size, float tracking) const
{
    float width = 0.0f;
    std::uint32_t previous = 0;
    const Font *previous_face = nullptr;
    int glyphs = 0;
    for (std::size_t index = 0; index < text.size();)
    {
        std::uint32_t codepoint = next_unit(text, &index);
        const Resolved resolved = resolve(&codepoint);
        if (resolved.glyph == nullptr)
            continue;
        // Each face has metrics of its own; pairs are kerned within one face.
        const float scale = size / resolved.face->header_.pixel_size;
        if (previous != 0 && previous_face == resolved.face)
            width += resolved.face->kern(previous, codepoint) * scale;
        width += resolved.glyph->advance * scale;
        previous = codepoint;
        previous_face = resolved.face;
        ++glyphs;
    }
    return glyphs > 1 ? width + tracking * static_cast<float>(glyphs - 1) : width;
}

float Font::layout(std::string_view text, float x, float y, float size, Align align,
                   std::vector<GlyphQuad> &quads, float tracking) const
{
    const float width = measure(text, size, tracking);
    float pen = x;
    if (align == Align::center)
        pen -= width * 0.5f;
    else if (align == Align::right)
        pen -= width;
    std::uint32_t previous = 0;
    const Font *previous_face = nullptr;
    for (std::size_t index = 0; index < text.size();)
    {
        std::uint32_t codepoint = next_unit(text, &index);
        const Resolved resolved = resolve(&codepoint);
        const ff::Glyph *glyph = resolved.glyph;
        if (glyph == nullptr)
            continue;
        const ff::Header &face = resolved.face->header_;
        const float scale = size / face.pixel_size;
        if (previous != 0 && previous_face == resolved.face)
            pen += resolved.face->kern(previous, codepoint) * scale;
        if (glyph->w > 0 && glyph->h > 0)
        {
            const float inverse_w = 1.0f / static_cast<float>(face.atlas_width);
            const float inverse_h = 1.0f / static_cast<float>(face.atlas_height);
            GlyphQuad quad;
            quad.x0 = pen + glyph->offset_x * scale;
            quad.y0 = y + glyph->offset_y * scale;
            quad.x1 = quad.x0 + static_cast<float>(glyph->w) * scale;
            quad.y1 = quad.y0 + static_cast<float>(glyph->h) * scale;
            quad.u0 = static_cast<float>(glyph->x) * inverse_w;
            quad.v0 = static_cast<float>(glyph->y) * inverse_h;
            quad.u1 = static_cast<float>(glyph->x + glyph->w) * inverse_w;
            quad.v1 = static_cast<float>(glyph->y + glyph->h) * inverse_h;
            quad.texture = resolved.texture;
            quad.range = resolved.face->sdf_range(size);
            quads.push_back(quad);
        }
        pen += glyph->advance * scale + tracking;
        previous = codepoint;
        previous_face = resolved.face;
    }
    return width;
}

std::vector<std::string> Font::wrap(std::string_view text, float size, float max_width) const
{
    std::vector<std::string> lines;
    std::string line;
    std::size_t index = 0;
    while (index <= text.size())
    {
        const std::size_t newline = text.find('\n', index);
        const std::string_view paragraph = text.substr(
            index, newline == std::string_view::npos ? std::string_view::npos : newline - index);
        std::size_t word_start = 0;
        line.clear();
        while (word_start <= paragraph.size())
        {
            std::size_t word_end = paragraph.find(' ', word_start);
            if (word_end == std::string_view::npos)
                word_end = paragraph.size();
            const std::string_view word = paragraph.substr(word_start, word_end - word_start);
            std::string candidate =
                line.empty() ? std::string(word) : line + " " + std::string(word);
            if (measure(candidate, size) <= max_width)
            {
                line = std::move(candidate);
            }
            else
            {
                if (!line.empty())
                    lines.push_back(line);
                // The word starts a line of its own. One wider than the line
                // gives up as many code points as fit, line after line.
                std::size_t start = 0;
                while (measure(word.substr(start), size) > max_width)
                {
                    std::size_t end = start;
                    next_unit(word, &end,true);
                    for (std::size_t next = end; next < word.size(); end = next)
                    {
                        next_unit(word, &next,true);
                        if (measure(word.substr(start, next - start), size) > max_width)
                            break;
                    }
                    if (end >= word.size())
                        break;
                    lines.emplace_back(word.substr(start, end - start));
                    start = end;
                }
                line.assign(word.substr(start));
            }
            word_start = word_end + 1;
        }
        lines.push_back(line);
        if (newline == std::string_view::npos)
            break;
        index = newline + 1;
    }
    return lines;
}

} // namespace hui::gfx
