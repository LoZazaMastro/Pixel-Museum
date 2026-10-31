// Pixel Museum - Measure production fonts against the chronology layout.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/catalog.hpp"
#include "core/save_file.hpp"
#include "gfx/font.hpp"
#include "museum/timeline_hero.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <cstdio>
#include <set>
#include <algorithm>
int main(){
    museum::Catalog catalog;if(!catalog.load("build/runtime-preview/content/catalog.json"))return 2;
    hui::gfx::Font regular,bold,cjk;std::string bytes;
    if(!hui::save::read_file("assets/fonts/inter-regular.huifont",&bytes,16u<<20)||!regular.load(bytes))return 3;
    if(!hui::save::read_file("assets/fonts/inter-semibold.huifont",&bytes,16u<<20)||!bold.load(bytes))return 4;
    if(!hui::save::read_file("assets/fonts/cjk-subset.huifont",&bytes,16u<<20)||!cjk.load(bytes))return 6;
    regular.add_fallback(&cjk,1);bold.add_fallback(&cjk,1);
    nlohmann::json report={{"entries",catalog.entries.size()},{"hero_overflow",nlohmann::json::array()},{"rail_clip",nlohmann::json::array()},{"missing_title_glyphs",nlohmann::json::array()},{"missing_body_glyphs",nlohmann::json::array()}};
    report["joint_hero_fits"]=nlohmann::json::array();
    for(const char*field:{"missing_heading_glyphs","paragraph_line_cap","heading_count_mismatch","photo_card_overflow","film_card_overflow"})report[field]=nlohmann::json::array();
    float max_source_height=0;std::string tallest_sources;unsigned paragraphs=0,headings=0,max_heading_lines=0;
    for(const auto&e:catalog.entries){
        const auto hero=museum::timeline_hero_text(bold,regular,e.title,e.summary);
        const float size=hero.title_size;
        const auto titles=bold.wrap(e.title,size,770);
        const auto summary=regular.wrap(e.summary,hero.summary_size,hero.summary_width);
        const float bottom=hero.last_glyph_bottom;
        if(hero.compact)report["joint_hero_fits"].push_back({{"id",e.id},{"title",e.title},{"title_size",size},{"summary_size",hero.summary_size},{"title_baseline",hero.title_baseline},{"summary_baseline",hero.summary_baseline},{"last_glyph_bottom",bottom},{"fits",hero.fits}});
        if(bottom>766)report["hero_overflow"].push_back({{"id",e.id},{"title",e.title},{"title_size",size},{"title_lines",titles.size()},{"summary_lines",summary.size()},{"last_glyph_bottom",bottom}});
        for(int focused=0;focused<=1;++focused)for(int phase=0;phase<=2;++phase){
            const float opened=float(phase)*.5f;
            float reference=26;while(regular.wrap(e.title,reference,450).size()>2&&reference>15)--reference;
            const float label=reference*(focused?1.f:.72f)*(1-.2f*opened);
            const auto lines=regular.wrap(e.title,reference,450);const float baseline=883-714*opened-float(lines.size()-1)*label*1.15f;
            const float top=baseline-regular.ascent(label);
            if(top<814-714*opened)report["rail_clip"].push_back({{"id",e.id},{"title",e.title},{"focused",bool(focused)},{"story_open",opened},{"font_size",label},{"lines",lines.size()},{"first_glyph_top",top}});
        }
        std::size_t i=0;while(i<e.title.size()){auto cp=hui::gfx::next_codepoint(e.title,&i);if(!bold.has_glyph(cp))report["missing_title_glyphs"].push_back({{"id",e.id},{"codepoint",cp},{"title",e.title}});}
        std::set<std::uint32_t> missing;
        for(const auto&p:e.body){i=0;while(i<p.size()){auto cp=hui::gfx::next_codepoint(p,&i);if(cp>32&&!regular.has_glyph(cp))missing.insert(cp);}}
        if(!missing.empty())report["missing_body_glyphs"].push_back({{"id",e.id},{"title",e.title},{"codepoints",missing}});
        if(!e.story_headings.empty()&&e.story_headings.size()!=e.body.size())report["heading_count_mismatch"].push_back({{"id",e.id},{"headings",e.story_headings.size()},{"paragraphs",e.body.size()}});
        for(std::size_t p=0;p<e.body.size();++p){
            ++paragraphs;const float width=p<e.images.size()?850.f:1430.f;
            const auto lines=regular.wrap(e.body[p],28,width);
            if(lines.size()>99)report["paragraph_line_cap"].push_back({{"id",e.id},{"paragraph",p},{"lines",lines.size()}});
            if(p<e.story_headings.size()){
                ++headings;const auto&heading=e.story_headings[p];float font_size=40;
                while(bold.wrap(heading,font_size,width).size()>3&&font_size>28)--font_size;
                max_heading_lines=std::max(max_heading_lines,static_cast<unsigned>(bold.wrap(heading,font_size,width).size()));
                i=0;while(i<heading.size()){const auto cp=hui::gfx::next_codepoint(heading,&i);if(cp>32&&!bold.has_glyph(cp))report["missing_heading_glyphs"].push_back({{"id",e.id},{"paragraph",p},{"codepoint",cp}});}
            }
        }
        const auto height=[&](const std::string&text,float font_size,float width,float line){return float(regular.wrap(text,font_size,width).size())*line;};
        for(std::size_t p=e.body.size();p<e.images.size();++p){
            const auto&image=e.images[p];const auto caption=image.title+" / "+image.credit;
            const float title_height=float(bold.wrap(image.title,36,490).size())*45;
            const float creator_height=height(image.creator,24,490,35);
            const float card=std::max(600.f,std::max(584+height(caption,18,1060,26),192+title_height+creator_height));
            const float caption_ink=546+float(regular.wrap(caption,18,1060).size()-1)*26+regular.descent(18);
            if(caption_ink>card)report["photo_card_overflow"].push_back({{"id",e.id},{"image",p},{"card_height",card},{"caption_ink_bottom",caption_ink}});
        }
        for(const auto&film:e.videos){
            const float title_height=float(bold.wrap(film.title,36,540).size())*44;
            const float description_height=height(film.caption,26,540,38);
            const float card=std::max(650.f,200+title_height+description_height);
            const float creator_ink=171+title_height+description_height+float(regular.wrap(film.creator,21,540).size()-1)*30+regular.descent(21);
            if(creator_ink>card)report["film_card_overflow"].push_back({{"id",e.id},{"title",film.title},{"card_height",card},{"creator_ink_bottom",creator_ink}});
        }
        float source_height=32;
        const auto source_line=[&](const std::string&text,float font_size,float gap){source_height+=height(text,font_size,1600,font_size*1.45f)+gap;};
        if(!e.editorial_credit.empty())source_line(e.editorial_credit,24,26);
        if(!e.factual_note.empty())source_line(e.factual_note,24,26);
        for(const auto&source:e.sources){source_line(source.title,26,8);source_line(source.publisher+" / "+source.url,21,8);if(!source.attribution.empty()||!source.license.empty())source_line(source.attribution+" "+source.license,21,24);else source_height+=20;}
        for(const auto&image:e.images){source_line(image.title+" / "+image.credit+" / "+image.license,22,5);source_line(image.source_page,20,24);}
        for(const auto&model:e.models){source_line(model.title+" / "+model.credit+" / "+model.license,22,5);source_line(model.source_page,20,24);}
        if(source_height>max_source_height){max_source_height=source_height;tallest_sources=e.id;}

    }
    report["measured_paragraphs"]=paragraphs;report["measured_headings"]=headings;report["max_story_heading_lines"]=max_heading_lines;
    report["max_source_accordion"]={{"id",tallest_sources},{"height",max_source_height},{"clip_policy","actual measured content height; no fixed20000px cutoff"}};
    report["hero_font_floors"]={{"title",28},{"summary",20}};
    const auto text=report.dump(2);FILE*f=std::fopen("build/catalog-layout-audit.json","wb");if(!f)return 5;std::fwrite(text.data(),1,text.size(),f);std::fclose(f);
    std::printf("Measured %zu exhibits: %zu hero overflows, %zu rail clips, %zu missing title glyphs, %zu records with missing body glyphs.\n",catalog.entries.size(),report["hero_overflow"].size(),report["rail_clip"].size(),report["missing_title_glyphs"].size(),report["missing_body_glyphs"].size());
    std::printf("Stories: %u paragraphs, %u authored headings, max%u heading lines; sources max%.0fpx (%s). Count mismatches:%zu; paragraph caps:%zu; photo/film overflow:%zu/%zu; missing heading glyphs:%zu.\n",paragraphs,headings,max_heading_lines,max_source_height,tallest_sources.c_str(),report["heading_count_mismatch"].size(),report["paragraph_line_cap"].size(),report["photo_card_overflow"].size(),report["film_card_overflow"].size(),report["missing_heading_glyphs"].size());
    return 0;
}
