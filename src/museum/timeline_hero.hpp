// Joint, source-complete typography for the timeline's existing hero region.
#pragma once
#include "gfx/font.hpp"
#include <algorithm>
#include <string_view>

namespace museum {
struct TimelineHeroText {
    float title_size=46,summary_size=24;
    float title_baseline=381,summary_baseline=0,summary_width=710;
    float last_glyph_bottom=0;
    bool fits=false,compact=false;
};
inline TimelineHeroText timeline_hero_text(const hui::gfx::Font& title_font,
                                         const hui::gfx::Font& body_font,
                                         std::string_view title,std::string_view summary,float title_baseline=381){
    constexpr float bottom=744; // 22px clear of the actual y=766 hero clip.
    TimelineHeroText legacy;legacy.title_baseline=title_baseline;
    while(title_font.wrap(title,legacy.title_size,770).size()>2&&legacy.title_size>28)legacy.title_size-=2;
    const auto title_count=title_font.wrap(title,legacy.title_size,770).size();
    const float after=title_baseline+float(title_count)*legacy.title_size*1.15f;
    while(after+16+float(body_font.wrap(summary,legacy.summary_size,710).size())*legacy.summary_size*1.4f>719&&legacy.summary_size>20)--legacy.summary_size;
    legacy.summary_baseline=after+16;
    const auto lines=body_font.wrap(summary,legacy.summary_size,710).size();
    legacy.last_glyph_bottom=lines?legacy.summary_baseline+float(lines-1)*legacy.summary_size*1.4f+body_font.descent(legacy.summary_size):after;
    legacy.fits=legacy.last_glyph_bottom<=bottom;
    if(legacy.fits)return legacy;

    // Retain the title's ink-top, not a baseline that leaves a growing empty
    // band when its size changes. The date and large year never move.
    const float title_top=title_baseline-title_font.ascent(46);
    TimelineHeroText result=legacy;result.compact=true;result.summary_width=770;
    const auto measure=[&](float title_size,float summary_size){
        TimelineHeroText fit;fit.compact=true;fit.title_size=title_size;fit.summary_size=summary_size;fit.summary_width=770;
        fit.title_baseline=title_top+title_font.ascent(title_size);
        const auto titles=title_font.wrap(title,title_size,770).size();
        const float title_bottom=fit.title_baseline+float(titles?titles-1:0)*title_size*1.15f+title_font.descent(title_size);
        fit.summary_baseline=title_bottom+16+body_font.ascent(summary_size);
        const auto summaries=body_font.wrap(summary,summary_size,770).size();
        fit.last_glyph_bottom=summaries?fit.summary_baseline+float(summaries-1)*summary_size*1.4f+body_font.descent(summary_size):title_bottom;
        fit.fits=fit.last_glyph_bottom<=bottom;
        return fit;
    };
    // Prefer readable summary text with a substantial heading. Only if that
    // cannot fit do we visit the old 28px heading floor. Text is never cut.
    for(float floor:{38.f,28.f})
        for(float body=24;body>=20;--body)
            for(float heading=46;heading>=floor;heading-=2){
                if(title_font.wrap(title,heading,770).size()>2)continue;
                result=measure(heading,body);
                if(result.fits)return result;
            }
    return measure(28,20); // An explicit !fits remains visible to the audit.
}
}
