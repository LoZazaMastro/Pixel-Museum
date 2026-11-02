// Pixel Museum - an optional invitation to support the free museum.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/general_credits.hpp"
#include "museum/menu_row.hpp"
#include "yt/qr.hpp"
#include <algorithm>

namespace museum {
using namespace hui;
using gfx::Rect;using gfx::Color;using gfx::Align;
void Screen::open_support(ui::Feedback& feedback){
    support_dialog_=true;support_focus_=0;support_open_.snap(0);
    if(!support_qr_){
        yt::QrImage qr;
        if(yt::make_qr(museum_support_url,8,&qr)&&qr.valid())support_qr_=renderer_.batch().create_texture(qr.width,qr.height,qr.rgba.data());
    }
    feedback.play(audio::Cue::modal_open);
}
int Screen::support_action_count()const{
#if defined(MUSEUM_DESKTOP)
    return 2;
#else
    return 1;
#endif
}
const char* Screen::support_action_label(int action)const{return action?"Open Ko-fi":"Close";}
Rect Screen::support_action_bounds(int action)const{
    const float rise=(1-std::clamp(support_open_.value,0.f,1.f))*18;
    return {support_action_count()==1?722.5f:470+action*505.f,737+rise,475,72};
}
bool Screen::handle_support(const InputFrame& input,ui::Feedback& feedback){
    if(!support_dialog_)return support_open_.value>.001f;
    if(input.focus_lost||!input.connected)return true;
    if(input.is_pressed(Action::back)||input.is_pressed(Action::menu)){support_dialog_=false;feedback.play(audio::Cue::back);return true;}
    const int before=support_focus_;
    if(input.nav==Direction::left||input.nav==Direction::up)support_focus_=0;
    if(input.nav==Direction::right||input.nav==Direction::down)support_focus_=support_action_count()-1;
    if(before!=support_focus_)feedback.play(audio::Cue::focus);
    if(!input.is_pressed(Action::confirm))return true;
#if defined(MUSEUM_DESKTOP)
    if(support_focus_==1){desktop_url_request_=museum_support_url;feedback.play(audio::Cue::select);return true;}
#endif
    support_dialog_=false;feedback.play(audio::Cue::back);return true;
}
void Screen::draw_support(){
    const float alpha=std::clamp(support_open_.value,0.f,1.f);if(alpha<=0)return;
    const auto p=colours();const float rise=(1-alpha)*18;
    overlay_.push_opacity(alpha);
    overlay_.rounded_rect({0,0,1920,1080},0,Color::rgb(0,.44f));
    overlay_.bordered_rect({410,225+rise,1100,630},0,p.paper,1,p.rule);
    ui::text(overlay_,fonts_.mono,"PIXEL MUSEUM",470,282+rise,18,p.muted,Align::left,1.8f);
    ui::text(overlay_,fonts_.semibold,"Support the museum",470,343+rise,38,p.ink);
    ui::paragraph(overlay_,fonts_.regular,"Pixel Museum is a free project, created through months of research and work. If you would like to support it, even a small donation is appreciated. Thank you.",470,415+rise,26,570,39,p.muted,7);
    overlay_.line(1080,382+rise,1080,695+rise,1,p.rule);
    const Rect code{1144,382+rise,286,286};
    if(support_qr_)overlay_.image(support_qr_,code,gfx::kFullUv,Color::rgb(0xffffff));
    for(int action=0;action<support_action_count();++action){
        const auto button=support_action_bounds(action);const bool selected=action==support_focus_;
        overlay_.bordered_rect(button,0,selected?p.ink:p.paper,1,selected?p.ink:p.rule);
        ui::text(overlay_,fonts_.semibold,support_action_label(action),button.cx(),menu_text_baseline(fonts_.semibold,support_action_label(action),button.cy(),25),25,selected?p.paper:p.ink,Align::center);
    }
#if !defined(MUSEUM_DESKTOP)
    ui::Hint controls[]={{ui::Button::circle,"Close"},{ui::Button::cross,"Close"}};
    ui::HintLayout layout;layout.cy=1015;layout.size=28;layout.text_size=22;
    ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(p.ink,Color::rgb(0,0)),controls,2,96,false,layout);
#endif
    overlay_.pop_opacity();
}
}
