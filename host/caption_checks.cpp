// Production caption layout and renderer checks, without a network request.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "host/behavior.hpp"
#include "museum/caption_overlay.hpp"
#include <array>
#include <cmath>
#include <cstdio>
namespace museum {
bool ScreenInspection::verify_captions(Screen&s,unsigned framebuffer,int width,int height){
    using hui::gfx::Rect;using hui::gfx::Color;
    // The actual player input route owns this shortcut, so it must never
    // invoke the timeline's Today action or leave fullscreen playback.
    s.onboarding_=false;s.boot_time_=5;s.settings_=s.credits_=s.year_guide_=false;
    s.connection_panel_=s.experience_active_=s.gallery_=s.object_inspect_=false;
    s.panel_.snap(0);s.screening_=true;s.playlist_active_=false;
    s.film_captions_enabled_=true;
    for(const bool fullscreen:{false,true}){
        s.fullscreen_=fullscreen;
        for(const bool expected:{false,true}){
            hui::InputFrame input;input.connected=true;input.pressed=hui::action_bit(hui::Action::north);
            hui::ui::Feedback feedback;const auto before=s.current();s.handle(input,feedback);
            if(s.film_captions_enabled_!=expected||s.fullscreen_!=fullscreen||!s.screening_||s.current()!=before||feedback.tactile.empty()){
                std::fputs("Caption toggle failed: player route, fullscreen, timeline selection or tactile feedback changed incorrectly\n",stderr);return false;
            }
        }
    }
    s.screening_=s.fullscreen_=false;
    const std::array<std::string_view,5> cues={
        "Il design cambia il modo in cui attraversiamo questo mondo.",
        "La m\xC3\xBA" "sica y los espacios cuentan una historia compartida.",
        "Les images et les sons donnent au joueur une autre fa\xC3\xA7on de comprendre le monde.",
        "Die Gestaltung der Spielwelt ver\xC3\xA4ndert, wie wir uns durch ihre R\xC3\xA4ume bewegen und miteinander spielen.",
        "Continue"};
    const auto resolver=hui::ui::text_resolver;
    hui::ui::text_resolver=+[](std::string_view text)->std::string_view{return text=="Continue"?"WRONG UI TRANSLATION":text;};
    unsigned checks=0;
    for(const auto picture:{Rect{0,0,1920,1080},Rect{950,220,826,465},Rect{180,80,1200,900}}){
        for(float controls:{0.f,1.f})for(const auto cue:cues){
            const auto layout=film_caption_layout(s.fonts_.regular,cue,picture,controls);
            if(layout.lines.empty()||layout.backing.x<picture.x||layout.backing.y<picture.y||
               layout.backing.x+layout.backing.w>picture.x+picture.w||
               layout.backing.y+layout.backing.h>picture.y+picture.h){
                std::fputs("Caption check failed: text backing escapes the actual video picture\n",stderr);hui::ui::text_resolver=resolver;return false;
            }
            if(cue=="Continue"&&(layout.lines.size()!=1||layout.lines[0]!="Continue")){
                std::fputs("Caption check failed: remote dialogue passed through interface localisation\n",stderr);hui::ui::text_resolver=resolver;return false;
            }
            ++checks;
        }
    }
    if(!film_caption_layout(s.fonts_.regular,"",{0,0,1920,1080},0).lines.empty())return false;
    hui::gfx::DrawList list;list.rounded_rect({0,0,1920,1080},0,Color::rgb(0x40534e));
    draw_film_captions(list,s.fonts_.regular,cues[0],{0,0,1920,1080},0);
    draw_film_captions(list,s.fonts_.regular,cues[3],{950,220,826,465},1);
    s.renderer_.begin();s.renderer_.draw(list);s.renderer_.present(framebuffer,width,height);
    hui::ui::text_resolver=resolver;
    const auto error=glGetError();
    if(error){std::fprintf(stderr,"Caption renderer GL error0x%x\n",error);return false;}
    std::printf("Captions: %u multilingual picture-bound cases; controls-hidden text and literal dialogue passed; rendered %dx%d GL=0\n",checks,width,height);
    return true;
}
}
