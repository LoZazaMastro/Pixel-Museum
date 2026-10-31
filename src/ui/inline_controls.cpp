// Inline controller symbols share the hint renderer and its measured geometry.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "ui/glyphs.hpp"
#include <algorithm>
namespace hui::ui {
namespace {
struct Symbol{std::string_view token;Button button;std::string_view name;};
constexpr Symbol symbols[]={
 {"{left_stick}",Button::left_stick," (Left stick)"},{"{right_stick}",Button::right_stick," (Right stick)"},
 {"{dpad}",Button::dpad," (D-pad)"},{"{touchpad}",Button::touchpad,""},
 {"{cross}",Button::cross,""},{"{circle}",Button::circle,""},{"{square}",Button::square,""},
 {"{triangle}",Button::triangle,""},{"{l1}",Button::l1,""},{"{r1}",Button::r1,""},
 {"{l2}",Button::l2,""},{"{r2}",Button::r2,""},{"{options}",Button::options,""}
};
template<class Text,class Icon>void spans(std::string_view text,Text ordinary,Icon icon){
 std::size_t start=0,n=0;
 while(n<text.size()){
  const Symbol*found=nullptr;
  if(text[n]=='{')for(const auto&s:symbols)if(text.substr(n,s.token.size())==s.token){found=&s;break;}
  if(!found){++n;continue;}
  if(n>start)ordinary(text.substr(start,n-start));icon(*found);n+=found->token.size();start=n;
 }
 if(start<text.size())ordinary(text.substr(start));
}
float symbol_width(const FontRef&face,const Symbol&s,float size,float tracking){
 return button_width(s.button,size*1.1f)+8+(s.name.empty()?0:face.font->measure(resolve_text(s.name),size,tracking));
}
float measure(const FontRef&face,std::string_view value,float size,float tracking){
 float width=0;spans(value,[&](std::string_view text){width+=face.font->measure(text,size,tracking);},[&](const Symbol&s){width+=symbol_width(face,s,size,tracking);});return width;
}
float draw(gfx::DrawList&list,const FontRef&face,std::string_view value,float x,float y,float size,gfx::Color color,gfx::Align align,float tracking){
 const float width=measure(face,value,size,tracking);float pen=x-(align==gfx::Align::center?width*.5f:align==gfx::Align::right?width:0);
 Fonts fonts;fonts.regular=fonts.semibold=fonts.display=fonts.mono=fonts.pixel=fonts.hand=face;
 const auto style=GlyphStyle::mono(color,gfx::Color::rgb(0,0));
 spans(value,[&](std::string_view text){pen+=list.text(*face.font,face.texture,text,pen,y,size,color,gfx::Align::left,tracking);},[&](const Symbol&s){
  draw_button(list,fonts,style,s.button,pen+4,y-size*.35f,size*1.1f);pen+=button_width(s.button,size*1.1f)+8;
  if(!s.name.empty())pen+=list.text(*face.font,face.texture,resolve_text(s.name),pen,y,size,color,gfx::Align::left,tracking);
 });return width;
}
std::vector<std::string> wrap(const FontRef&face,std::string_view text,float size,float width){
 std::vector<std::string> lines;std::string line;std::size_t start=0;
 const auto flush=[&]{lines.push_back(line);line.clear();};
 while(start<text.size()){
  if(text[start]=='\n'){flush();++start;continue;}
  if(text[start]==' '||text[start]=='\t'||text[start]=='\r'){++start;continue;}
  const auto end=text.find_first_of(" \t\r\n",start);const auto word=text.substr(start,end==std::string_view::npos?text.size()-start:end-start);
  std::string joined=line.empty()?std::string(word):line+" "+std::string(word);
  if(!line.empty()&&measure(face,joined,size,0)>width)flush();
  // Symbols are atomic; ordinary long words retain Font's UTF-8-safe wrapping.
  if(measure(face,word,size,0)>width&&word.find('{')==std::string_view::npos){
   auto parts=face.font->wrap(word,size,width);for(std::size_t n=0;n+1<parts.size();++n)lines.push_back(std::move(parts[n]));if(!parts.empty())line=std::move(parts.back());
  }else{if(!line.empty())line+=' ';line+=word;}
  start=end==std::string_view::npos?text.size():end;
 }
 if(!line.empty()||lines.empty()||(!text.empty()&&text.back()=='\n'))lines.push_back(line);
 return lines;
}
}
void install_inline_controls(){inline_text_renderer={measure,draw,wrap};}
}
