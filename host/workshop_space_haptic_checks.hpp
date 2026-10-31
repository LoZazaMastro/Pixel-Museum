#pragma once
#include "museum/study.hpp"
#include "museum/haptic_interactions.hpp"
#include <cstdio>
namespace museum {
inline bool verify_workshop_space_haptics(){
 const auto require=[](bool ok,const char*note){if(!ok)std::fprintf(stderr,"Haptic workshop/space FAILED: %s\n",note);return ok;};
 for(int hz:{30,60,120}){
  for(const char*id:{"pocket-budget","adaptive-pulse","jump-lab","pixels","city-system","raycast","scale","portals"}){
   auto study=make_study(id);if(!require(bool(study),id))return false;
   hui::InputFrame input;input.connected=true;hui::ui::Feedback f;
   study->handle(input,f);study->update(1.f/hz);if(!require(f.tactile.empty(),"neutral initialization has no phantom pulse"))return false;
   const std::string name=id;
   if(name=="pocket-budget"){input.nav=hui::Direction::down;study->handle(input,f);}
   else if(name=="pixels"){input.nav=hui::Direction::right;study->handle(input,f);}
   else {input.stick_x=1;for(int n=0;n<hz/3;++n){study->handle(input,f);study->update(1.f/hz);}}
   if(!require(!f.tactile.empty(),id))return false;
   f.clear();input.focus_lost=true;study->handle(input,f);study->update(1.f/hz);
   if(!require(f.tactile.empty(),"focus loss clears pending tactile"))return false;
   input={};input.connected=true;study->handle(input,f);if(!require(f.tactile.empty(),"neutral resume does not replay movement"))return false;
   std::printf("PASS semantic accepted action/focus/neutral resume %s %dHz\n",id,hz);
  }
  for(const char*id:{"raycast","scale"}){auto study=make_study(id);hui::InputFrame i;i.connected=true;i.pressed=hui::action_bit(hui::Action::confirm);hui::ui::Feedback f;study->handle(i,f);if(!require(f.tactile.empty(),"ignored confirm has no global pulse"))return false;}
  auto pixel=make_study("pixels");hui::InputFrame i;i.connected=true;i.nav=hui::Direction::left;hui::ui::Feedback f;pixel->handle(i,f);if(!require(f.tactile.empty(),"clamped pixel cursor silent"))return false;
  i.nav=hui::Direction::none;i.pressed=hui::action_bit(hui::Action::north);pixel->handle(i,f);if(!require(f.tactile.empty(),"unchanged restore silent"))return false;
  AcceptedMotionHaptics helper;unsigned events=0;
  for(int n=0;n<hz;++n){helper.advance(1.f/hz);helper.step(1,0);f.clear();helper.drain(f);events+=unsigned(f.tactile.size());}
  if(!require(events>=8&&events<=13,"accepted cursor rate cap independent of frame rate"))return false;
  helper.reset();f.clear();helper.record(0,0,true);helper.drain(f);if(!require(f.tactile.empty(),"zero accepted displacement silent"))return false;
 }
 return true;
}
}
