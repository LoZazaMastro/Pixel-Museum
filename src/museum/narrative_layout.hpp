// Full source paragraphs, wrapped once and painted inside the reading window.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "ui/fonts.hpp"
#include <algorithm>
#include <limits>
#include <vector>
namespace museum {
class NarrativeLayout {
public:
 struct Row {std::string text;float baseline=0,size=0;bool heading=false;};
 bool ready=false;
 float title_size=0,title_height=0,bottom=0;
 hui::ui::ParagraphLines title;
 const std::vector<Row>&rows()const{return rows_;}
 void append(const hui::ui::FontRef&font,const std::string&text,float size,float width,float line,bool heading=false){
  auto wrapped=hui::ui::paragraph_lines(font,text,size,width,std::numeric_limits<int>::max());
  for(auto&value:wrapped.lines){rows_.push_back({std::move(value),bottom,size,heading});bottom+=line;}
 }
 void gap(float amount){bottom+=amount;}
 float content_bottom(const hui::ui::FontRef&regular,const hui::ui::FontRef&semibold)const{
  if(rows_.empty())return 0;
  const auto&last=rows_.back();const auto&font=last.heading?semibold:regular;
  return last.baseline+std::max(0.f,font.font->descent(last.size));
 }
 unsigned draw(hui::gfx::DrawList&out,const hui::ui::FontRef&regular,const hui::ui::FontRef&semibold,
               float x,float top,float scroll,float lower,float upper,hui::gfx::Color ink,hui::gfx::Color quiet)const{
  // Include a whole font-size guard for ascenders, descenders and fallback
  // glyphs. The existing reading clip remains the final authority at its edges.
  constexpr float padding=64;
  const float low=lower-top+scroll-padding,high=upper-top+scroll+padding;
  auto row=std::lower_bound(rows_.begin(),rows_.end(),low,[](const Row&r,float y){return r.baseline<y;});
  unsigned count=0;
  for(;row!=rows_.end()&&row->baseline<=high;++row){
   hui::ui::text(out,row->heading?semibold:regular,row->text,x,top+row->baseline,row->size,row->heading?ink:quiet);++count;
  }
  return count;
 }
private:
 std::vector<Row>rows_;
};
}
