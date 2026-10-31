// Pixel Museum - a picture, one pixel at a time.
// Copyright (C) 2026 Andrea Sgarro. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/pixel_workshop.hpp"
#include "ui/glyphs.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
namespace {
using hui::gfx::Color;using hui::gfx::Rect;using hui::gfx::Align;
constexpr std::array<std::uint8_t,64> kDrawing={
 0,0,0,0,0,0,0,0,
 0,3,0,0,0,0,3,0,
 0,3,3,0,0,3,3,0,
 0,3,2,3,3,2,3,0,
 0,3,1,2,2,1,3,0,
 0,3,0,0,0,0,3,0,
 0,3,0,0,0,0,3,0,
 0,0,0,0,0,0,0,0};
constexpr std::array<std::uint32_t,4> kShades={0xf4f1e7,0xc9c9bd,0x858b80,0x29322c};
Color shade_color(float value){const float shade=std::clamp(value,0.f,3.f);const auto low=static_cast<unsigned>(shade);return hui::gfx::mix(Color::rgb(kShades[low]),Color::rgb(kShades[std::min(3u,low+1)]),shade-float(low));}
}
PixelWorkshop::PixelWorkshop(){reset();}
void PixelWorkshop::set_cursor(unsigned x,unsigned y){
 x_=std::min(x,7u);y_=std::min(y,7u);
 cursor_x_.target=float(x_);cursor_y_.target=float(y_);
}
void PixelWorkshop::reset(){pixels_=kDrawing;for(unsigned i=0;i<64;++i)appearance_[i]=float(pixels_[i]);x_=y_=1;grid_=true;cursor_x_.snap(1);cursor_y_.snap(1);focus_.snap(0);grid_opacity_.snap(1);edit_flash_=0;}
bool PixelWorkshop::handle(const hui::InputFrame&input,hui::ui::Feedback&feedback){
 using hui::Action;using hui::Direction;using hui::audio::Cue;
 if(input.is_pressed(Action::back)){feedback.play(Cue::back);return true;}
 // An intercepted/disconnected controller must never edit the picture.
 if(input.focus_lost||!input.connected)return false;
 const unsigned previous_x=x_,previous_y=y_;
 switch(input.nav){case Direction::left:if(x_)--x_;break;case Direction::right:if(x_<7)++x_;break;case Direction::up:if(y_)--y_;break;case Direction::down:if(y_<7)++y_;break;default:break;}
 if(previous_x!=x_||previous_y!=y_){cursor_x_.target=float(x_);cursor_y_.target=float(y_);feedback.play(Cue::focus,1.f,0,.55f);}
 if(input.is_pressed(Action::confirm)){auto&pixel=pixels_[y_*8+x_];pixel=static_cast<std::uint8_t>((pixel+1)%4);edit_flash_=1;feedback.play(Cue::select,1.f,0,.65f);}
 if(input.is_pressed(Action::west)){grid_=!grid_;grid_opacity_.target=grid_?1.f:0.f;feedback.play(Cue::toggle,1.f,0,.55f);}
 if(input.is_pressed(Action::north)&&(pixels_!=kDrawing||x_!=1||y_!=1||!grid_)){const auto previous=appearance_;const float focus=focus_.value,cursor_x=cursor_x_.value,cursor_y=cursor_y_.value,grid=grid_opacity_.value;reset();appearance_=previous;cursor_x_.snap(cursor_x);cursor_y_.snap(cursor_y);cursor_x_.target=cursor_y_.target=1;grid_opacity_.snap(grid);grid_opacity_.target=1;focus_.snap(focus);focus_.target=active_?1.f:0.f;edit_flash_=1;feedback.play(Cue::restart,1.f,0,.65f);}
 return false;
}
void PixelWorkshop::update(float dt){
 if(!std::isfinite(dt)||dt<=0)return;dt=std::min(dt,.05f);
 cursor_x_.update(dt,24);cursor_y_.update(dt,24);focus_.target=active_?1.f:0.f;focus_.update(dt,14);grid_opacity_.update(dt,15);
 const float blend=1-std::exp(-18.f*dt);for(unsigned i=0;i<64;++i)appearance_[i]+=(float(pixels_[i])-appearance_[i])*blend;edit_flash_=std::max(0.f,edit_flash_-dt*3.5f);
}
void PixelWorkshop::draw(hui::gfx::DrawList&list,hui::ui::Fonts&fonts,Rect bounds,Color accent,bool active){
 active_=active;if(bounds.w<1||bounds.h<1)return;
 constexpr float width=1040,height=552;const float scale=std::min(bounds.w/width,bounds.h/height);const float left=bounds.x+(bounds.w-width*scale)/2,top=bounds.y+(bounds.h-height*scale)/2;
 const Color ink=Color::rgb(0x27302a),quiet=Color::rgb(0x697068),paper=Color::rgb(0xf1efe7);
 list.push_clip(bounds);list.rounded_rect(bounds,0,paper);list.push_transform(scale,0,0,left,top);
 // Whole image at left: deliberate, crisp squares instead of a scaled photograph.
 constexpr float gx=56,gy=130,cell=39,side=312;
 list.shadow({gx,gy,side,side},0,15,Color::rgb(0x18241a,.10f));
 for(unsigned y=0;y<8;++y)for(unsigned x=0;x<8;++x)list.rounded_rect({gx+float(x)*cell,gy+float(y)*cell,cell,cell},0,shade_color(appearance_[y*8+x]));
 const float grid=std::clamp(grid_opacity_.value,0.f,1.f);for(unsigned i=0;i<=8;++i){list.line(gx+float(i)*cell,gy,gx+float(i)*cell,gy+side,.65f,ink.with_alpha(.16f*grid));list.line(gx,gy+float(i)*cell,gx+side,gy+float(i)*cell,.65f,ink.with_alpha(.16f*grid));}
 const float focus=std::clamp(focus_.value,0.f,1.f),lift=2.3f*focus;
 if(focus>.001f){const Rect selected{gx+cursor_x_.value*cell-lift,gy+cursor_y_.value*cell-lift,cell+lift*2,cell+lift*2};list.shadow(selected,0,9,ink.with_alpha(.20f*focus));list.bordered_rect(selected,0,shade_color(appearance_[y_*8+x_]),1.5f,accent.with_alpha(focus));list.bordered_rect(selected.inset(-3),0,Color::rgb(0,0),.7f,paper.with_alpha(.9f*focus));}
 hui::ui::text(list,fonts.mono,"8 x 8",gx,472,17,quiet);
 hui::ui::text(list,fonts.mono,"64 PIXELS",gx+side,472,17,quiet,Align::right);
 list.line(430,126,430,448,.7f,ink.with_alpha(.16f));
 // The enlarged active pixel and its four choices connect the small tile to
 // its underlying values, without imitating a web settings form.
 const float pulse=edit_flash_*.035f;list.bordered_rect({482-64*pulse,132-64*pulse,64*(1+2*pulse),64*(1+2*pulse)},0,shade_color(appearance_[y_*8+x_]),.7f,ink.with_alpha(.22f));
 char position[40];hui::ui::format(position,"COLUMN %u / ROW %u",x_+1,y_+1);hui::ui::text(list,fonts.mono,position,572,145,15,quiet);
 for(unsigned i=0;i<4;++i){const Rect swatch{574+float(i)*48,164,32,32};list.rounded_rect(swatch,0,Color::rgb(kShades[i]));if(i==pixels_[y_*8+x_])list.bordered_rect(swatch.inset(-4),0,Color::rgb(0,0),1.5f,accent);}
 hui::ui::text(list,fonts.mono,"64 PIXELS x 2 BITS = 16 BYTES",482,397,17,ink);
 list.pop_transform();list.pop_clip();
}
} // namespace museum
