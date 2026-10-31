// Pixel Museum - an original native listening-room presentation.
// Copyright (C) 2026 Andrea Sgarro. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/soundtrack_card.hpp"
#include "museum/localization.hpp"
#include "museum/music_waveform.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
namespace {
using hui::gfx::Color;using hui::gfx::Rect;using hui::gfx::Align;
void clock_text(char*out,size_t capacity,float seconds){
 if(!std::isfinite(seconds)||seconds<0){std::snprintf(out,capacity,"--:--");return;}
 const unsigned value=unsigned(std::min(seconds,359999.f));
 if(value>=3600)std::snprintf(out,capacity,"%u:%02u:%02u",value/3600,(value/60)%60,value%60);
 else std::snprintf(out,capacity,"%u:%02u",value/60,value%60);
}
float fitted(const hui::ui::FontRef&font,std::string_view value,float preferred,float width,float minimum){
 const float measured=font.font->measure(value,preferred);return measured>width?std::max(minimum,preferred*width/measured):preferred;
}
}
void draw_soundtrack_card(hui::gfx::DrawList&list,hui::ui::Fonts&fonts,Rect bounds,
                         Color accent,const Soundtrack&playlist,int selection,
                         int playing_index,bool paused,float time,float duration,
                         unsigned video_texture,int video_width,int video_height,
                         std::string_view status,float dark){
 if(!std::isfinite(bounds.w)||!std::isfinite(bounds.h)||bounds.w<1||bounds.h<1)return;
 constexpr float width=1040,height=552;const float scale=std::min(bounds.w/width,bounds.h/height);
 const float left=bounds.x+(bounds.w-width*scale)/2,top=bounds.y+(bounds.h-height*scale)/2;
 const auto palette=museum_palette(dark);const Color ink=palette.ink,quiet=palette.muted,paper=Color::rgb(0xf1efe7);
 (void)video_texture;(void)video_width;(void)video_height;
 const int count=int(playlist.tracks.size());selection=count?std::clamp(selection,0,count-1):-1;
 const bool current=playing_index>=0&&playing_index<count;
 list.push_clip(bounds);list.push_transform(scale,0,0,left,top);
 hui::ui::text(list,fonts.mono,"LISTENING ROOM / SOUNDTRACK",36,31,13,quiet,Align::left,1.1f);
 const std::string title=i18n::music_room_title(playlist.title.empty()?std::string_view("Music from the collection"):std::string_view(playlist.title));
 const float title_size=fitted(fonts.display,title,31,964,21);
 hui::ui::text(list,fonts.display,fonts.display.font->fit(hui::ui::resolve_text(title),title_size,964),34,77,title_size,ink);
 if(!playlist.composer.empty())list.text(*fonts.regular.font,fonts.regular.texture,fonts.regular.font->fit(i18n::music(playlist.composer),19,964),36,107,19,quiet);
 constexpr Rect frame{36,145,480,270};
 list.shadow(frame,0,17,ink.with_alpha(.11f));list.rounded_rect(frame,0,Color::rgb(0x19251f));
 // A soundtrack is an audio presentation. No decoded film or thumbnail is displayed.
 const float cx=frame.cx(),cy=frame.cy()-8;
 draw_music_waveform(list,{frame.x+28,cy-75,frame.w-56,150},paper.with_alpha(.85f),std::isfinite(time)&&time>=0?time*1.4f:0.f);
 hui::ui::text(list,fonts.mono,current?"NOW LISTENING":"SELECT A RECORDING",cx,frame.y+frame.h-23,11,paper.with_alpha(.55f),Align::center,.8f);
 // Only real finite player time produces a progress fill.
 const bool timed=current&&std::isfinite(duration)&&duration>0;
 const float elapsed=std::isfinite(time)&&time>=0?time:0;
 const float progress=timed?std::clamp(elapsed/duration,0.f,1.f):0;
 list.line(36,443,516,443,1,ink.with_alpha(.15f));
 if(progress>0)list.line(36,443,36+480*progress,443,2,accent);
 char elapsed_text[24],duration_text[24];clock_text(elapsed_text,sizeof(elapsed_text),current&&std::isfinite(time)&&time>=0?time:-1);clock_text(duration_text,sizeof(duration_text),timed?duration:-1);
 hui::ui::text(list,fonts.mono,elapsed_text,36,468,14,ink);
 hui::ui::text(list,fonts.mono,duration_text,516,468,14,quiet,Align::right);
 const std::string_view state=status.empty()?(current?(paused?std::string_view("Paused"):std::string_view("Playing")):std::string_view("Choose a recording")):status;
 hui::ui::text(list,fonts.regular,fonts.regular.font->fit(hui::ui::resolve_text(state),15,300),276,468,15,quiet,Align::center);
 constexpr float rx=566,rw=438;
 char collection[96];hui::ui::format(collection,count==1?"%d RECORDING":"%d RECORDINGS",count);
 hui::ui::text(list,fonts.mono,collection,rx,132,12,quiet,Align::left,.7f);
 const int first=count>3?std::clamp(selection-1,0,count-3):0;
 for(int row=0;row<3&&first+row<count;++row){
  const int index=first+row;const auto&track=playlist.tracks[size_t(index)];
  const float y=146+float(row)*88;const bool selected=index==selection,playing=index==playing_index;
  if(selected)list.rounded_rect({rx-12,y,rw+12,78},2,accent.with_alpha(.09f));
  if(selected)list.line(rx-12,y+9,rx-12,y+69,2,accent);
  char number[12];std::snprintf(number,sizeof(number),"%02d",index+1);
  if(playing&&!paused&&status!="Finished")list.triangle({rx,y+22,13,15},accent,0,1.57079633f);
  else if(playing&&paused){list.rounded_rect({rx,y+23,3,13},0,accent);list.rounded_rect({rx+7,y+23,3,13},0,accent);}
  else hui::ui::text(list,fonts.mono,number,rx,y+37,14,quiet);
  // Song titles are proper names. Keep both measurement and drawing outside
  // the interface resolver ("Jump" must not become the controller hint "Salta").
  const std::string_view name=track.title.empty()?i18n::tr("Recording"):std::string_view(track.title);
  const float size=fitted(fonts.semibold,name,23,rw-44,18);
  list.text(*fonts.semibold.font,fonts.semibold.texture,fonts.semibold.font->fit(name,size,rw-44),rx+35,y+35,size,ink);
  if(!track.creator.empty())list.text(*fonts.regular.font,fonts.regular.texture,fonts.regular.font->fit(i18n::music(track.creator),16,rw-44),rx+35,y+60,16,quiet);
  list.line(rx+35,y+87,rx+rw,y+87,.65f,ink.with_alpha(.12f));
 }
 if(!count)hui::ui::paragraph(list,fonts.regular,"No recordings are available for this exhibit.",rx,184,21,rw,30,quiet,3);
 if(count>3){char position[40];std::snprintf(position,sizeof(position),"%d / %d",selection+1,count);hui::ui::text(list,fonts.mono,position,rx+rw,432,12,quiet,Align::right);}
 // Acquisition and verification notes stay with the catalog provenance, away from playback controls.
 hui::ui::text(list,fonts.mono,"RECORDINGS REMAIN WITH THEIR ORIGINAL PUBLISHERS",36,525,10,quiet,Align::left,.5f);
 list.pop_transform();list.pop_clip();
}
} // namespace museum
