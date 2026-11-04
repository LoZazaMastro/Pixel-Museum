// Real TextField drawing and editing regression; no window, GPU or user data.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "ui/components/text_field.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iterator>

using namespace hui;
static unsigned inline_calls=0;
static float inline_measure(const ui::FontRef&,std::string_view,float,float){++inline_calls;return 999.f;}
static float inline_draw(gfx::DrawList&,const ui::FontRef&,std::string_view,float,float,float,gfx::Color,gfx::Align,float){++inline_calls;return 999.f;}
static std::string_view translate(std::string_view text){return text=="Play"?std::string_view("Riproduci"):text;}
static std::size_t glyphs(const gfx::DrawList&list,float top,float bottom){
    std::size_t n=0;for(const auto&i:list.instances())if(i.params[3]==float(gfx::Shape::glyph)&&i.rect[1]>=top&&i.rect[1]<bottom)++n;return n;
}
static float caret_x(const gfx::DrawList&list){
    for(const auto&i:list.instances())if(i.params[3]==float(gfx::Shape::rounded_rect)&&std::abs(i.rect[2]-2.5f)<.01f&&std::abs(i.rect[3]-30.f)<.01f)return i.rect[0];
    assert(false&&"No visible caret");return -1;
}
int main(int argc,char**argv){
    const std::string root=argc>1?argv[1]:".";
    std::ifstream file(root+"/assets/fonts/inter-regular.huifont",std::ios::binary);assert(file);
    const std::string bytes{std::istreambuf_iterator<char>(file),{}};gfx::Font font;assert(font.load(bytes));
    ui::Fonts fonts;fonts.regular=fonts.semibold=fonts.mono=fonts.pixel=fonts.hand=fonts.display={&font,1};
    gfx::DrawList list;ui::Canvas canvas{list,fonts};ui::TextField field;
    field.style.theme.label=ui::FontRole::regular;field.style.theme.style=ui::SurfaceStyle::flat;
    field.style.theme.underline_fields=false;field.style.caret_period=0;field.style.counter=false;
    field.set_bounds({100,100,360,120});field.set_active(true);field.update(.1f);
    ui::text_resolver=translate;
    field.set_text("Play");field.set_helper("Play");field.draw(canvas);
    assert(glyphs(list,100,160)==4);assert(glyphs(list,160,250)==9);
    assert(ui::resolve_text("Play")=="Riproduci"&&ui::literal_text_depth==0);
    assert(std::abs(caret_x(list)-(123.f+font.measure("Play",24)))<.01f);

    field.set_helper("");field.set_text("{cross}");list.clear();
    ui::inline_text_renderer.measure=inline_measure;ui::inline_text_renderer.draw=inline_draw;
    field.draw(canvas);assert(glyphs(list,100,160)==7&&inline_calls==0);
    ui::inline_text_renderer={};

    std::string edited="caf\xc3\xa9\xf0\x9f\x99\x82";std::size_t at=3;
    assert(ui::text_entry::insert_bounded(edited,at,"X",96));assert(edited=="cafX\xc3\xa9\xf0\x9f\x99\x82"&&at==4);
    assert(ui::text_entry::erase_next(edited,at));assert(edited=="cafX\xf0\x9f\x99\x82"&&at==4);
    assert(ui::text_entry::erase_previous(edited,at));assert(edited=="caf\xf0\x9f\x99\x82"&&at==3);
    assert(ui::text_entry::next(edited,at)==7&&ui::text_entry::previous(edited,7)==3);
    assert(ui::text_entry::boundary(edited,5)==3);
    std::string full="AB\xc3\xa9";at=1;assert(!ui::text_entry::insert_bounded(full,at,"Z",3));assert(full=="AB\xc3\xa9");
    assert(ui::text_entry::printable("A\n\t\xc3\xa9")=="A\xc3\xa9");

    field.set_text("A\xc3\xa9\xf0\x9f\x99\x82Z");field.set_caret(2);assert(field.caret()==1);
    list.clear();field.draw(canvas);assert(std::abs(caret_x(list)-(123.f+font.measure("A",24)))<.01f);
    ui::Painter paint(list,fonts,field.style.theme);
    assert(field.caret_from_x(paint,caret_x(list))==1);
    const std::string long_text="Play The Legend of Zelda: Link\xe2\x80\x99s Awakening - caf\xc3\xa9 - \xf0\x9f\x99\x82 - A long title with a middle caret";
    field.set_text(long_text);
    for(std::size_t position=0;;position=ui::text_entry::next(long_text,position)){
        field.set_caret(position);list.clear();field.draw(canvas);const float x=caret_x(list);
        assert(x>=123.f-.01f&&x<=field.field_rect().x+field.field_rect().w-20.f);
        assert(field.caret_from_x(paint,x)==position);
        if(position==long_text.size())break;
    }
    field.set_caret(0);list.clear();field.draw(canvas);assert(std::abs(caret_x(list)-123.f)<.01f);
    field.set_caret(long_text.size());list.clear();field.draw(canvas);assert(caret_x(list)>123.f);
    field.set_text(field.text());assert(field.text()==long_text); // aliased input remains intact
    field.backspace();assert(field.caret()==field.text().size());field.clear();assert(field.caret()==0);
    ui::text_resolver=nullptr;
    std::puts("TextField PASS: literal Play/{cross}, localized helper, real caret geometry, UTF-8 insertion/deletion, nearest click, Home/End and stable long-text viewport.");
}
