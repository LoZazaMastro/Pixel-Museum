// Pixel Museum - shared icon controls for exhibit cards and fullscreen studies.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "ui/glyphs.hpp"
#include <string>
#include <vector>
#include <algorithm>
namespace museum {
struct StudyControl { hui::ui::Hint hint; bool down=false,up=false; };
inline std::vector<StudyControl> study_controls(const std::string&id,bool navigation=false){
 using B=hui::ui::Button;std::vector<StudyControl> c;
 if(id=="portals"){
  c={{{B::left_stick,"Move"}},{{B::right_stick,"Choose surface"}},{{B::l2,"Blue portal"}},{{B::r2,"Orange portal"}},{{B::cross,"Jump / continue"}},{{B::triangle,"Carry / drop"}},{{B::touchpad,"Choose surface"}}};
  if(navigation){c.push_back({{B::square,"Restart chamber"}});c.push_back({{B::options,"Pause"}});}return c;
 }
 if(id=="city-system"){
  c={{{B::left_stick,"Choose"}},{{B::cross,"Build / continue"}},{{B::triangle,"Road / green"}},{{B::touchpad,"Draw"}}};
  if(navigation){c.push_back({{B::square,"Restart"}});c.push_back({{B::options,"Pause"}});}return c;
 }
 if(id=="cartridge-rules"||id=="pocket-budget"||id=="adaptive-pulse"||id=="jump-lab"){
  if(id=="pocket-budget")c={{{B::dpad,"Choose / tune"}},{{B::cross,"Test brief"}},{{B::touchpad,"Tune"}}};
  else if(id=="cartridge-rules")c={{{B::left_stick,"Move"}},{{B::cross,"Swap program"}},{{B::touchpad,"Move"}}};
  else if(id=="adaptive-pulse")c={{{B::left_stick,"Move"}},{{B::r2,"Run"}},{{B::cross,"Jump"}},{{B::touchpad,"Set pace"}}};
  else c={{{B::left_stick,"Move"}},{{B::cross,"Jump"}},{{B::l1,"Parameter",B::r1}},{{B::dpad,"Tune"}},{{B::touchpad,"Tune"}}};
  if(navigation){c.push_back({{B::square,"Restart"}});c.push_back({{B::options,"Pause"}});}return c;
 }
 if(id!="rhythm")c.push_back({{id=="pixels"||id=="sequencer"?B::dpad:B::left_stick,id=="maze"?"Turn":id=="raycast"?"Move / turn":id=="pixels"?"Choose pixel":id=="sequencer"?"Choose tile":id=="orbit"?"Turn / thrust":id=="dash"?"Move / aim":"Move"}});
 if(id=="wireframe"){c.push_back({{B::triangle,"Recenter"}});c.push_back({{B::cross,"Replay"}});}
 if(id=="jump"||id=="momentum"){c.push_back({{B::cross,"Jump"}});if(id=="jump"){c.push_back({{B::square,"Run"}});c.push_back({{B::dpad,"Crouch"},true});}}
 else if(id=="dash"){c.push_back({{B::cross,"Jump"}});c.push_back({{B::r1,"Dash"}});}
 else if(id=="formation")c.push_back({{B::cross,"Fire"}});
 else if(id=="paddle"||id=="bricks"){c.push_back({{B::cross,"Launch"}});c.push_back({{B::touchpad,"Move / press to launch"}});}
 else if(id=="gravity")c.push_back({{B::cross,"Rotate"}});
 else if(id=="orbit")c.push_back({{B::cross,"Brake"}});
 else if(id=="rhythm"){c.push_back({{B::dpad,"Tap"}});for(auto b:{B::cross,B::circle,B::triangle,B::square})c.push_back({{b,""}});}
 else if(id=="sequencer"||id=="pixels")c.push_back({{B::cross,id=="pixels"?"Draw":"Colour"}});
 if(id=="momentum"){c.push_back({{B::dpad,"Roll"},true});c.push_back({{B::dpad,"Charge",B::cross},true});}
 if(id=="gravity"){c.push_back({{B::dpad,"Fall faster"},true});c.push_back({{B::dpad,"Drop"},false,true});}
 if(id=="sequencer")c.push_back({{B::triangle,"Pause scan"}});
 if(id=="pixels"){c.push_back({{B::circle,"Erase"}});c.push_back({{B::l1,"Colour",B::r1}});}
 if(navigation){if(id!="jump"&&id!="rhythm")c.push_back({{B::square,id=="pixels"?"Grid":"Restart"}});if(id=="pixels")c.push_back({{B::triangle,"Clear canvas"}});c.push_back({{B::options,"Pause"}});}
 return c;
}
inline float draw_study_controls(hui::gfx::DrawList&list,const hui::ui::Fonts&fonts,const std::string&id,hui::gfx::Rect bounds,hui::gfx::Color ink,hui::gfx::Color background,bool navigation=false){
 using namespace hui;const auto controls=study_controls(id,navigation);ui::HintLayout l;l.size=navigation?29.f:23.f;l.text_size=navigation?21.f:18.f;l.item_gap=0;
 const float row=l.size+15,gap=navigation?36.f:24.f;float x=bounds.x,y=bounds.y+row*.5f;const auto style=ui::GlyphStyle::mono(ink,background);
 for(const auto&c:controls){const float w=ui::measure_hints(fonts,&c.hint,1,l);if(x>bounds.x&&x+w>bounds.x+bounds.w){x=bounds.x;y+=row;}l.cy=y;
  ui::draw_hints(list,fonts,style,&c.hint,1,x,false,l);
  if(c.down||c.up){const float size=l.size,cx=x+size*.5f,arm=size*.3f,thick=size*.2f,half=thick*.5f;const auto veil=background.with_alpha(.82f);
   list.rounded_rect({cx-half,c.up?y+half:y-arm,thick,arm-half},0,veil);list.rounded_rect({cx-arm,y-half,arm-half,thick},0,veil);list.rounded_rect({cx+half,y-half,arm-half,thick},0,veil);
  }x+=w+gap;
 }
 return controls.empty()?0:y-bounds.y+row*.5f;
}
}
