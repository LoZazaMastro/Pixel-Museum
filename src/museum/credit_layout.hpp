// Full provenance, wrapped once and painted only inside the visible window.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "ui/fonts.hpp"
#include <algorithm>
#include <limits>
#include <vector>
namespace museum {
class CreditLayout {
public:
 struct Row {std::string text;float baseline=0,size=0;bool quiet=false;};
 void clear(){rows_.clear();cursor_=486;ready_=false;}
 bool ready()const{return ready_;}
 float bottom()const{return cursor_;}
 const std::vector<Row>&rows()const{return rows_;}
 void append(const hui::ui::FontRef&font,const std::string&text,float size,bool quiet){
  if(text.empty())return;
  auto wrapped=hui::ui::paragraph_lines(font,text,size,1510,std::numeric_limits<int>::max());
  for(auto&value:wrapped.lines){rows_.push_back({std::move(value),cursor_,size,quiet});cursor_+=size*1.45f;}
  cursor_+=18;
 }
 void gap(float amount){cursor_+=amount;}
 void finish(){ready_=true;}
 unsigned draw(hui::gfx::DrawList&out,const hui::ui::FontRef&font,float scroll,hui::gfx::Color ink,hui::gfx::Color quiet)const{
  // A whole font-size margin includes descenders and tall fallback glyphs.
  // Rows remain in source order, with no scroll-height approximation.
  constexpr float padding=32;
  const float low=448+scroll-padding,high=848+scroll+padding;
  auto first=std::lower_bound(rows_.begin(),rows_.end(),low,[](const Row&r,float y){return r.baseline<y;});
  unsigned count=0;
  for(auto row=first;row!=rows_.end()&&row->baseline<=high;++row){hui::ui::text(out,font,row->text,184,row->baseline,row->size,row->quiet?quiet:ink);++count;}
  return count;
 }
private:
 std::vector<Row>rows_;
 float cursor_=486;
 bool ready_=false;
};
}
