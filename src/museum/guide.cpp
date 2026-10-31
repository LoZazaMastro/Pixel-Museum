// Pixel Museum - a year atlas and a quiet first visit.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/experience_mark.hpp"
#include "museum/study_controls.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
using namespace hui;
using gfx::Color;using gfx::Rect;using gfx::Align;
void Screen::open_search(ui::Feedback&feedback){
    const auto palette=colours();auto theme=ui::default_theme();
    const auto search_accent=Color::rgb(dark_theme_?0xefaa7d:0x9b4c17);
    theme.page=palette.paper;theme.surface=palette.paper;theme.surface_high=gfx::mix(palette.paper,palette.ink,.06f);
    theme.text=palette.ink;theme.text_muted=palette.muted;theme.primary=search_accent;theme.on_primary=palette.paper;
    theme.secondary=theme.surface_high;theme.on_secondary=palette.ink;theme.focus=search_accent;theme.accent=search_accent;
    theme.outline=palette.ink.with_alpha(.18f);theme.style=ui::SurfaceStyle::flat;theme.radius=5;theme.radius_card=8;
    search_prompt_.style.theme=theme;search_prompt_.style.max_length=96;search_prompt_.style.width=1160;
    search_prompt_.style.reduced_motion=reduced_;search_prompt_.style.auto_capital=false;search_prompt_.style.done_label="Search";search_prompt_.style.frosted=false;
    search_prompt_.set_title("Search the museum");search_prompt_.field.set_placeholder("A game, a person, an invention...");
    search_prompt_.keyboard.style.bindings=ui::KeyboardBindings::standard();search_prompt_.keyboard.style.bindings.done=Action::menu;
    search_prompt_.open(feedback,search_query_);
}
bool Screen::handle_search(const InputFrame&i,ui::Feedback&feedback){
    if(search_prompt_.is_open()){
        const auto event=search_prompt_.handle(i,feedback);
        if(event==ui::Event::activated){
            search_query_=search_prompt_.text();search_results_=search_collection(catalog_,history_catalog_all_,search_query_);
            search_focus_=0;search_position_.snap(0);search_page_=true;year_guide_=false;
        }
        return true;
    }
    if(!search_page_)return search_prompt_.visible()||search_open_.value>.001f;
    if(i.is_pressed(Action::touch)){open_search(feedback);return true;}
    if(i.is_pressed(Action::back)){search_page_=false;open_year_guide();feedback.play(audio::Cue::back);return true;}
    const int before=search_focus_;
    if(i.nav==Direction::down)search_focus_=std::min(int(search_results_.size())-1,search_focus_+1);
    if(i.nav==Direction::up)search_focus_=std::max(0,search_focus_-1);
    search_focus_=std::max(0,search_focus_);
    if(before!=search_focus_)feedback.play(audio::Cue::focus,1,0,.4f);
    if(i.is_pressed(Action::confirm)&&!search_results_.empty()){
        const auto result=search_results_[size_t(search_focus_)];search_page_=false;year_guide_=false;detail_=false;
        gallery_=screening_=object_inspect_=false;
        if(result.culture){filter_=culture_filter_=0;rebuild(false);rebuild_history_filter();history_focus_=true;history_focus_index_=result.index;history_position_.snap(float(result.index));changed();warm_history();}
        else{const auto id=catalog_.entries[size_t(result.index)].id;select(id);detail_=true;}
        feedback.play(audio::Cue::select);
    }
    return true;
}
void Screen::draw_search(){
    const auto palette=colours();const float alpha=std::clamp(search_open_.value,0.f,1.f);
    overlay_.push_opacity(alpha);overlay_.rounded_rect({0,0,1920,1080},0,palette.paper);
    logo(overlay_,96,66,34,palette.ink);ui::text(overlay_,fonts_.semibold,"PIXEL MUSEUM",150,93,22,palette.ink,Align::left,2);
    ui::text(overlay_,fonts_.mono,"SEARCH",100,180,18,palette.muted,Align::left,2);
    float size=56;while(size>28&&fonts_.display.font->measure(search_query_,size)>1660)size-=1;
    ui::text(overlay_,fonts_.display,search_query_,96,252,size,palette.ink);
    overlay_.line(96,292,1824,292,1,palette.ink.with_alpha(.15f));
    const float first=std::max(0.f,search_position_.value-3.f);
    overlay_.push_clip({96,312,1728,625});
    for(int n=std::max(0,int(first)-1);n<std::min(int(search_results_.size()),int(first)+9);++n){
        const auto&r=search_results_[size_t(n)];const auto&e=(r.culture?history_catalog_:catalog_).entries[size_t(r.index)];
        const float y=322+(float(n)-first)*86,focus=std::max(0.f,1-std::abs(float(n)-search_position_.value));
        const auto accent=Color::rgb(r.culture?0x91c9e8:0xefaa7d);
        overlay_.rounded_rect({96,y,1728,78},5,palette.ink.with_alpha(.055f*focus));
        overlay_.rounded_rect({116,y+17,5,44},1,accent.with_alpha(.75f+.25f*focus));
        ui::text(overlay_,fonts_.mono,std::to_string(e.year),152,y+49,27,palette.muted);
        float title_size=29;while(title_size>18&&fonts_.semibold.font->measure(e.title,title_size)>1220)title_size-=1;
        ui::text(overlay_,fonts_.semibold,e.title,268,y+49,title_size,palette.ink.with_alpha(.58f+.42f*focus));
        ui::text(overlay_,fonts_.mono,date_label(e,false),1798,y+47,17,palette.muted,Align::right);
        overlay_.line(152,y+78,1824,y+78,1,palette.ink.with_alpha(.07f));
    }
    if(search_results_.empty())ui::paragraph(overlay_,fonts_.regular,"No exhibits match this search. Try a different name or year.",100,410,30,1400,43,palette.muted);
    overlay_.pop_clip();
    const ui::Hint hints[]={{ui::Button::dpad,"Browse"},{ui::Button::cross,"Open"},{ui::Button::touchpad,"Search"},{ui::Button::circle,"Guide"}};
    ui::HintLayout layout;layout.cy=1014;layout.size=30;layout.text_size=22;layout.item_gap=30;
    ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(palette.ink,Color::rgb(0,0)),hints,4,96,false,layout);
    overlay_.pop_opacity();
}
void Screen::draw_trophy_badge(gfx::DrawList& out,const std::string& badge,float cx,float cy,float size,bool colour){
    const auto asset=cache_.request("museum-pin:"+badge+"-colour");
    if(!asset.texture||asset.width<=0||asset.height<=0)return;
    const float factor=size/float(std::max(asset.width,asset.height));
    const float w=asset.width*factor,h=asset.height*factor;
    out.image(asset.texture,{cx-w*.5f,cy-h*.5f,w,h},gfx::kFullUv,Color::rgb(0xffffff),0,colour?1.f:0.f);
}
void Screen::draw_trophy_fallback(){
    if(trophy_fallback_time_<=0)return;
    const auto palette=colours();const float alpha=std::min(1.f,trophy_fallback_time_*3.f);
    overlay_.push_opacity(alpha);
    overlay_.rounded_rect({1160,54,680,138},12,palette.paper);
    overlay_.rounded_rect({1160,54,680,138},12,palette.ink.with_alpha(.045f));
    draw_trophy_badge(overlay_,trophy_fallback_current_.badge,1234,123,106,true);
    ui::text(overlay_,fonts_.mono,"Trophy unlocked",1310,91,16,palette.muted);
    ui::paragraph(overlay_,fonts_.semibold,i18n::tr(trophy_fallback_current_.title),1310,128,27,490,33,palette.ink,2);
    overlay_.pop_opacity();
}
void Screen::draw_trophy_library(){
    const auto palette=colours();const auto ink=palette.ink,quiet=palette.muted;
    const auto all=trophies_?trophies_->views(true):std::vector<TrophyView>{};
    ui::text(overlay_,fonts_.mono,"TROPHIES",64,92,19,quiet,Align::left,2);
    overlay_.push_clip({40,160,680,788});
    const float anchor=470;
    const int first=std::max(0,int(trophy_position_.value)-3),last=std::min(int(all.size())-1,int(trophy_position_.value)+5);
    for(int n=first;n<=last;++n){
        const auto&item=all[size_t(n)];const float d=float(n)-trophy_position_.value,focus=std::clamp(1-std::abs(d),0.f,1.f),y=anchor+d*91;
        const bool concealed=item.secret&&!item.unlocked;
        unsigned colour_key=0;for(unsigned char c:item.badge)colour_key=colour_key*33u+c;
        constexpr unsigned colours[]={0xe0b379,0x85c8b0,0x93b9e0,0xd99fb7,0xb6a5df};
        const auto accent=Color::rgb(colours[colour_key%5]);
        overlay_.rounded_rect({48,y-43,664,83},9,ink.with_alpha(.045f*focus));
        if(focus>.01f)overlay_.rounded_rect({48,y-21,3,40},1,ink.with_alpha(.52f*focus));
        draw_trophy_badge(overlay_,item.badge,104,y-2,66,item.unlocked);
        {
            const std::string title(i18n::tr(concealed&&!trophy_curator_preview_?"Secret trophy":item.title));const float width=fonts_.semibold.measure(title,25),room=506;
            float offset=0;
            if(n==trophy_focus_&&width>room&&trophy_focus_time_>.9f&&!reduced_){
                const float travel=width-room+28,cycle=travel/38.f+2.2f,phase=std::fmod(trophy_focus_time_-.9f,cycle);
                offset=std::min(travel,phase*38.f);
            }
            overlay_.push_clip({158,y-27,room,37});
            ui::text(overlay_,fonts_.semibold,title,158-offset,y+2,25,ink.with_alpha(.48f+.52f*focus));
            overlay_.pop_clip();
            if(item.unlocked){overlay_.circle(164,y+24,2.8f,accent);ui::text(overlay_,fonts_.regular,"Unlocked",177,y+29,15,quiet);}
        }
    }
    overlay_.pop_clip();
    if(all.empty())ui::paragraph(overlay_,fonts_.regular,"Your discoveries will find a home here.",64,420,25,520,36,quiet);
    const bool secret_selected=!all.empty()&&all[size_t(std::clamp(trophy_focus_,0,int(all.size())-1))].secret;
    std::vector<ui::Hint> hints={{ui::Button::square,"Guide"}};
    if(secret_selected)hints.push_back({ui::Button::cross,"Details"});
    if(!all.empty()&&all[size_t(std::clamp(trophy_focus_,0,int(all.size())-1))].unlocked)hints.push_back({ui::Button::triangle,"Pin"});
    ui::HintLayout l;l.cy=1014;l.size=25;l.text_size=18;l.item_gap=24;
    ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),hints.data(),int(hints.size()),64,false,l);
}
void Screen::draw_trophy_detail(){
    const auto all=trophies_?trophies_->views(true):std::vector<TrophyView>{};if(all.empty())return;
    const auto&item=all[size_t(std::clamp(trophy_focus_,0,int(all.size())-1))];
    const auto palette=colours();const auto ink=palette.ink,paper=palette.paper,quiet=palette.muted;
    const bool concealed=item.secret&&!item.unlocked;
    unsigned colour_key=0;for(unsigned char c:item.badge)colour_key=colour_key*33u+c;
    constexpr unsigned colours[]={0xe0b379,0x85c8b0,0x93b9e0,0xd99fb7,0xb6a5df};
    const auto accent=Color::rgb(colours[colour_key%5]);
    overlay_.push_opacity(std::clamp(year_panel_.value,0.f,1.f));
    constexpr float sidebar=736.f,margin=56.f,panel_x=sidebar+margin;
    constexpr float panel_w=1920.f-sidebar-2.f*margin,center=sidebar+(1920.f-sidebar)*.5f;
    constexpr float text_x=panel_x+80.f,text_w=panel_w-160.f,text_right=text_x+text_w;
    overlay_.rounded_rect({panel_x,142,panel_w,796},12,gfx::mix(paper,ink,.035f));
    draw_trophy_badge(overlay_,item.badge,center,(!item.secret||item.unlocked||trophy_expanded_)?337.f:402.f,(!item.secret||item.unlocked||trophy_expanded_)?212.f:282.f,item.unlocked);
    const bool show_requirement=!item.secret||item.unlocked||trophy_expanded_;
    const std::string title(i18n::tr(concealed&&!trophy_curator_preview_&&!trophy_expanded_?"Secret trophy":item.title));float size=46;
    while(size>32&&fonts_.display.measure(title,size)>text_w)size-=1;
    const auto lines=ui::paragraph_lines(fonts_.display,title,size,text_w,3);
    const float title_y=show_requirement?501.f:604.f;
    overlay_.push_clip({text_x-10,title_y-size-6,text_w+20,170});
    ui::paragraph(overlay_,fonts_.display,lines,center,title_y,size,size*1.18f,ink,Align::center);
    overlay_.pop_clip();
    if(show_requirement){
        const float top=title_y+float(lines.lines.size())*size*1.18f+24;
        overlay_.line(text_x,top,text_right,top,1,ink.with_alpha(.12f));
        ui::text(overlay_,fonts_.mono,item.unlocked?"DISCOVERED":"REQUIREMENT",text_x,top+41,15,quiet,Align::left,1.4f);
        overlay_.push_clip({text_x,top+58,text_w,116});
        ui::paragraph(overlay_,fonts_.regular,i18n::tr(item.description),text_x,top+84,25,text_w,35,ink);
        overlay_.pop_clip();
        if(item.target>0){
            const float y=std::min(864.f,top+200),fraction=float(std::min(item.current,item.target))/float(item.target);
            overlay_.rounded_rect({text_x,y,text_w-174,3},1,ink.with_alpha(.11f));
            if(fraction>0)overlay_.rounded_rect({text_x,y,(text_w-174)*fraction,3},1,item.unlocked?accent:ink.with_alpha(.6f));
            ui::text(overlay_,fonts_.mono,std::to_string(std::min(item.current,item.target))+" / "+std::to_string(item.target),text_right,y+7,19,quiet,Align::right);
        }
    }else{
        ui::paragraph(overlay_,fonts_.regular,"Press {cross} to reveal the requirement.",center,title_y+float(lines.lines.size())*size*1.18f+32,23,text_w,34,quiet,99,Align::center);
    }
    overlay_.pop_opacity();
}

void Screen::draw_trophy_pin_viewer(){
    const auto all=trophies_?trophies_->views(true):std::vector<TrophyView>{};if(all.empty())return;
    const auto&item=all[size_t(std::clamp(trophy_focus_,0,int(all.size())-1))];
    const auto palette=colours();const auto ink=palette.ink,paper=palette.paper;
    overlay_.rounded_rect({0,0,1920,1080},0,paper);
    if(!item.unlocked){trophy_pin_open_=false;if(trophy_pin_renderer_)trophy_pin_renderer_(TrophyView{},0,0,0,0,0,0);return;}
    // Only a real mesh renderer supplies this FBO. No rotated flat sprite,
    // invented reverse or 2D lighting trick stands in for the physical pin.
    if(trophy_pin_renderer_){
        const unsigned texture=trophy_pin_renderer_(item,output_width_,output_height_,trophy_pin_yaw_,trophy_pin_pitch_,trophy_pin_zoom_,trophy_pin_pan_y_);
        if(texture)overlay_.image(texture,{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff),0,item.unlocked||trophy_curator_preview_?1.f:0.f);
    }
    if(trophy_curator_preview_||trophy_expanded_||!(item.secret&&!item.unlocked)){
        const auto title=i18n::tr(item.title);float size=30;while(size>20&&fonts_.semibold.measure(title,size)>1690)--size;
        overlay_.push_clip({96,52,1728,52});ui::text(overlay_,fonts_.semibold,title,96,89,size,ink);overlay_.pop_clip();
    }
    const ui::Hint commands[]={{ui::Button::left_stick,"Move",ui::Button::none,false},{ui::Button::right_stick,"Rotate",ui::Button::none,false},{ui::Button::l2,"Zoom out"},{ui::Button::r2,"Zoom in"},{ui::Button::circle,"Back"}};
    ui::HintLayout layout;layout.cy=1014;layout.size=28;layout.text_size=19;layout.item_gap=32;
    ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),commands,5,96,false,layout);
}
void Screen::draw_year_guide(){
    if(guide_trophies_&&trophy_pin_open_){draw_trophy_pin_viewer();return;}
    const float amount=std::clamp(year_panel_.value,0.f,1.f),x=-680*(1-amount);
    const auto palette=colours();const Color ink=palette.ink,paper=palette.paper,quiet=palette.muted;
    overlay_.rounded_rect({0,0,1920,1080},0,ink.with_alpha(.22f*amount));
    const float sidebar=(guide_experiences_||guide_trophies_)?736.f:680.f;
    overlay_.glass(renderer_.glass_texture(),{x,0,sidebar,1080},0,gfx::mix(paper,tone_,.12f).with_alpha(.97f));
    overlay_.rounded_rect({x,0,sidebar,1080},0,gfx::mix(paper,tone_,.08f).with_alpha(.96f));
    overlay_.line(x+sidebar,0,x+sidebar,1080,1,ink.with_alpha(.12f*amount));
    overlay_.push_clip({0,0,sidebar*amount,1080});overlay_.push_transform(1,0,0,x,0);
    if(guide_trophies_){
        draw_trophy_library();
        overlay_.pop_transform();overlay_.pop_clip();
        draw_trophy_detail();return;
    }
    const float library=std::clamp(guide_mode_.value,0.f,1.f);
    if(library>.001f){
        overlay_.push_opacity(library);draw_experience_library(x);
        // The experience renderer is shared elsewhere; replace only this
        // sidebar footer so the next section is correctly announced.
        overlay_.rounded_rect({32,980,680,66},0,gfx::mix(paper,tone_,.08f));
        const ui::Hint next[]={{ui::Button::square,"Trophies"},{ui::Button::triangle,"Exhibit"},{ui::Button::right_stick,"Read"}};
        ui::HintLayout nav;nav.cy=1014;nav.size=25;nav.text_size=18;nav.item_gap=23;
        ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),next,3,64,false,nav);
        overlay_.pop_opacity();
    }
    overlay_.push_opacity(1-library);
    ui::text(overlay_,fonts_.mono,"THE YEAR ATLAS",64,92,19,quiet,Align::left,2);
    ui::paragraph(overlay_,fonts_.semibold,"Find your place\nin the story.",60,167,42,548,51,ink);
    const char*active_filter=active_filter_label();
    ui::text(overlay_,fonts_.mono,"FILTER",64,250,15,quiet,Align::left,1.2f);
    ui::text(overlay_,fonts_.semibold,active_filter,154,255,23,ink);
    overlay_.push_clip({32,292,616,500});
    const float centre=524;
    // A continuous measuring line bends gently around its selected year.
    float last_x=94,last_y=292;
    for(int row=0;row<=80;++row){const float y=292+float(row)*6.25f;const float d=(y-centre)/105;
        const float px=94+25*std::exp(-d*d);
        overlay_.line(last_x,last_y,px,y,1.1f,ink.with_alpha(.19f));last_x=px;last_y=y;
    }
    for(int n=std::max(0,int(year_position_.value)-5);n<std::min(int(years_.size()),int(year_position_.value)+7);++n){
        const float d=float(n)-year_position_.value,focus=std::clamp(1-std::abs(d),0.f,1.f);
        const float y=centre+d*66+(d<0?-38:38)*tween::smoothstep(std::min(1.f,std::abs(d)));
        if(y<278||y>807)continue;
        const float px=94+25*std::exp(-std::pow((y-centre)/105,2));
        const float size=25+49*focus;
        const float baseline=y+size*.32f;
        overlay_.line(px-7,y,px+10+12*focus,y,1+focus,gfx::mix(ink.with_alpha(.23f),ink,focus));
        overlay_.circle(px,y,2+2*focus,gfx::mix(quiet,tone_,focus));
        ui::text(overlay_,fonts_.display,std::to_string(years_[size_t(n)]),157-10*focus,baseline,size,ink.with_alpha(.3f+.7f*focus));
    }
    overlay_.pop_clip();
    if(!years_.empty()){
        overlay_.line(64,815,612,815,1,ink.with_alpha(.15f));
        ui::text(overlay_,fonts_.mono,"FIRST IN THIS YEAR",64,852,16,quiet,Align::left,1.2f);
        for(int n=std::max(0,int(std::floor(year_position_.value)));n<=std::min(int(years_.size())-1,int(std::ceil(year_position_.value)));++n){
            const float alpha=std::max(0.f,1-std::abs(float(n)-year_position_.value));
            const Entry*first=nullptr;if(history_focus_){for(const auto&e:history_catalog_.entries)if(e.year==years_[size_t(n)]){first=&e;break;}}else for(int id:visible_)if(catalog_.entries[size_t(id)].year==years_[size_t(n)]){first=&catalog_.entries[size_t(id)];break;}
            if(first){overlay_.push_opacity(alpha);ui::paragraph(overlay_,fonts_.semibold,first->title,64,893+(1-alpha)*12,28,548,36,ink);overlay_.pop_opacity();}
        }
    }
    std::vector<ui::Hint> buttons={{ui::Button::square,"Experiences"},{ui::Button::touchpad,"Search"}};
    if(!history_focus_)buttons.push_back({ui::Button::triangle,"Filter"});
    ui::HintLayout l;l.cy=1014;l.size=25;l.text_size=16;l.item_gap=15;
    ui::draw_hints(overlay_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),buttons.data(),int(buttons.size()),64,false,l);
    overlay_.pop_opacity();overlay_.pop_transform();overlay_.pop_clip();
    if(library>.001f){
        overlay_.push_opacity(library*amount);
        overlay_.rounded_rect({768,180,1080,782},8,gfx::mix(paper,tone_,.06f));
        draw_study_preview(overlay_,experience_focus_,{796,210,1024,518});
        if(!study_catalog().empty()){const auto&selected=study_catalog()[size_t(std::clamp(experience_focus_,0,int(study_catalog().size())-1))];draw_study_controls(overlay_,fonts_,selected.id,{800,770,1000,170},ink,paper,true);}
        overlay_.pop_opacity();
    }
}
void Screen::draw_onboarding(){
    const auto palette=colours();const Color paper=palette.paper,ink=palette.ink,quiet=palette.muted;
    welcome_.rounded_rect({0,0,1920,1080},0,paper.with_alpha(onboarding_leaving_?1.f:std::clamp(onboarding_fade_.value,0.f,1.f)));
    welcome_.push_opacity(std::clamp(onboarding_fade_.value,0.f,1.f));
    if(language_choice_){
        // Already in the focused language: do not resolve it again through
        // the saved language (which would translate the English preview).
        welcome_.text(*fonts_.display.font,fonts_.display.texture,i18n::language_choice_heading(language_focus_),96,338,68,ink);
        const char*names[]={"English","Italiano","Espa\u00f1ol","Fran\u00e7ais","Deutsch"};
        const float cursor=std::clamp(language_selection_.value,0.f,4.f);
        welcome_.line(100,442+cursor*88,130,442+cursor*88,3,tone_);
        for(int n=0;n<5;++n){const float y=458+float(n)*88;
            const float focus=std::clamp(1.f-std::abs(float(n)-cursor),0.f,1.f);
            ui::text(welcome_,fonts_.semibold,names[n],160+10*focus,y,32+9*focus,ink.with_alpha(.48f+.52f*focus));
        }
        welcome_.pop_opacity();return;
    }
    if(theme_choice_){
        for(int n=0;n<2;++n){
            const float focus=std::clamp(1.f-std::abs(float(n)-theme_selection_.value),0.f,1.f),grow=reduced_?0.f:8.f*focus;
            const auto choice=museum_palette(n==0?1.f:0.f);const float x=300+float(n)*710;
            const Rect card{x-grow,420-grow,610+grow*2,240+grow*2};
            welcome_.shadow(card,16,24+12*focus,ink.with_alpha(.08f+.04f*focus));
            welcome_.bordered_rect(card,16,gfx::mix(choice.paper,tone_,.035f*focus),1+focus,choice.ink.with_alpha(.18f+.3f*focus));
            ui::text(welcome_,fonts_.semibold,n?"Light mode":"Dark mode",card.cx(),card.cy()+15,42,choice.ink,Align::center);
        }
        if(theme_confirming_){
            const float t=tween::smoothstep(theme_confirm_progress_);const auto choice=museum_palette(dark_theme_?1.f:0.f);const float x=dark_theme_?300.f:1010.f;
            const Rect expanded{x*(1-t),420*(1-t),610+(1920-610)*t,240+(1080-240)*t};
            welcome_.rounded_rect(expanded,16*(1-t),choice.paper);
            ui::text(welcome_,fonts_.semibold,dark_theme_?"Dark mode":"Light mode",expanded.cx(),expanded.cy()+15,42,choice.ink.with_alpha(1-t),Align::center);
        }else{
            const ui::Hint buttons[]={{ui::Button::dpad,"Choose"},{ui::Button::cross,"Continue"},{ui::Button::circle,"Previous"}};
            ui::HintLayout l;l.cy=1014;l.size=30;l.text_size=22;l.item_gap=36;
            ui::draw_hints(welcome_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),buttons,3,96,false,l);
        }
        welcome_.pop_opacity();return;
    }
    if(onboarding_position_.value>onboarding_cards_-1){
        const float alpha=std::clamp(onboarding_position_.value-float(onboarding_cards_-1),0.f,1.f);
        welcome_.push_opacity(alpha);
        const float a=fonts_.regular.measure("Press",36),b=fonts_.regular.measure("to begin",36),gap=22,icon=42;
        const float left=960-(a+b+icon+gap*2)/2;
        ui::text(welcome_,fonts_.regular,"Press",left,554,36,ink);
        ui::draw_button(welcome_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),ui::Button::options,left+a+gap,541,icon);
        ui::text(welcome_,fonts_.regular,"to begin",left+a+gap*2+icon,554,36,ink);
        welcome_.pop_opacity();
    }
    welcome_.push_opacity(std::clamp(float(onboarding_cards_)-onboarding_position_.value,0.f,1.f));
    logo(welcome_,96,66,34,ink);ui::text(welcome_,fonts_.semibold,"PIXEL MUSEUM",150,93,22,ink,Align::left,2);
    welcome_.pop_opacity();
    const char*titles[]={"An idea.\nA memory.\nA museum.","Two timelines to discover\nour history.","Look. Listen.\nPlay.","Little discoveries.\nYours to keep.","Take your time.\nMake it yours.","Connect YouTube.\nAccess more content."};
    const char*body[]={
        "Games are more than the things we play. They are people, inventions and places that stay with us. Pixel Museum brings their stories into one collection for you to explore.",
        "The story of play sits beside a wider history of technology, culture and world events. Switching timelines takes you to the closest date, revealing what happened around the same time.",
        "Exhibits unfold through photographs, archive films, music and original interactive experiences. Explore their cards, listen to a score or put an idea into motion. Longer passages can be read in place.",
        "Exploring the museum earns you collectible pins. Some mark your progress; others are secrets hidden in the exhibits. Find them in Trophies in the guide. Press {triangle} to take a closer look in 3D, turn a pin around and discover its golden reverse.",
        "There is no right order and no need to rush. Colour and music follow each decade. Your guide finds a year or an experience; today's discovery takes you straight to a moment in history.",
        "Music cards and films stream from YouTube. Connecting an account is optional. If access is already saved, continue directly or choose Reconnect. Otherwise, choose Connect to follow the instructions on your phone, or skip this step and connect later in Options."
    };
    float title_size=64;
    for(int n=0;n<onboarding_cards_;++n)while(title_size>46&&ui::paragraph_lines(fonts_.semibold,titles[n],title_size,860,999).lines.size()>size_t(n==0?3:2))title_size-=1;
    size_t body_lines=0;for(const auto*text:body)body_lines=std::max(body_lines,ui::paragraph_lines(fonts_.regular,text,27,775,999).lines.size());
    const float title_line=title_size*1.08f,block_height=2*title_line+24+float(body_lines)*39;
    const float title_y=540-block_height*.5f+title_size,body_y=title_y+2*title_line+24;
    for(int n=std::max(0,int(onboarding_position_.value)-1);n<=std::min(onboarding_cards_-1,int(std::ceil(onboarding_position_.value))+1);++n){
        const float d=float(n)-onboarding_position_.value,alpha=std::clamp(1-std::abs(d)*.65f,0.f,1.f);
        welcome_.push_clip({0,150,1920,760});welcome_.push_opacity(alpha*std::clamp(float(onboarding_cards_)-onboarding_position_.value,0.f,1.f));welcome_.push_transform(1,0,0,d*1920,0);
        ui::paragraph(welcome_,fonts_.semibold,titles[n],94,n==0?title_y-title_line:title_y,title_size,860,title_line,ink);
        ui::paragraph(welcome_,fonts_.regular,body[n],100,body_y,27,775,39,quiet);
        const float cx=1394,cy=540;
        if(n==0){
            const int grid[5][5]={{1,0,0,0,1},{1,1,0,1,1},{1,0,1,0,1},{1,0,0,0,1},{1,0,0,0,1}};
            constexpr unsigned palette[]={0xdc9b79,0xc2b179,0xd78a64,0x83b8b0,0xb6a2cf,0x82acc8,0xc8919b,0xb1c098};
            int i=0;for(int row=0;row<5;++row)for(int col=0;col<5;++col)if(grid[row][col]){
                Color colour=Color::rgb(palette[intro_m_colours_[size_t(i)]]);
                if(!reduced_&&i==intro_m_active_)colour=gfx::mix(Color::rgb(palette[intro_m_from_]),Color::rgb(palette[intro_m_to_]),tween::smoothstep(std::clamp(intro_m_fade_/.35f,0.f,1.f)));
                welcome_.rounded_rect({cx-207+float(col)*86,cy-207+float(row)*86,70,70},0,colour);++i;
            }
        }else if(n==1){
            const float travel=reduced_?0.f:.5f-.5f*std::cos(time_*.65f),offset=110*travel;
            welcome_.push_clip({1030,270,770,510});
            for(int route=0;route<2;++route){
                const float y=(route?735.f:225.f)+offset;
                const float active=route?1-travel:travel;
                welcome_.line(1040,y,1800,y,1,ink.with_alpha(.2f));
                for(int k=0;k<5;++k){const float x=1100+float(k)*148;const bool selected=k==2;
                    welcome_.circle(x,y,selected?5.f:2.5f,selected?tone_.with_alpha(.4f+.6f*active):quiet.with_alpha(.4f));
                    ui::text(welcome_,fonts_.display,std::to_string(1985+k*2),x,y-22,selected?32.f:21.f,ink.with_alpha(selected?.6f+.4f*active:.4f),Align::center);
                }
            }
            const float y=360+offset;
            ui::text(welcome_,fonts_.display,"1989",1090,y+34,44,ink);
            welcome_.rounded_rect({1090,y+69,250,13},0,ink.with_alpha(.35f));
            for(int row=0;row<4;++row)welcome_.rounded_rect({1090,y+112+float(row)*25,280-float(row%2)*28,5},0,quiet.with_alpha(.3f));
            welcome_.bordered_rect({1490,y+5,250,230},0,tone_.with_alpha(.13f),1,ink.with_alpha(.22f));
            welcome_.pop_clip();
        }else if(n==2){
            for(int tile=0;tile<4;++tile){
                const float x=cx-285+float(tile%2)*300,y=cy-210+float(tile/2)*225;
                const float breathe=reduced_?0:std::sin(time_*.7f+float(tile)) *9;
                const float top=y+breathe,middle=top+97.5f;
                welcome_.bordered_rect({x,top,270,195},0,tone_.with_alpha(.07f+.025f*tile),1,ink.with_alpha(.2f));
                if(tile==0){
                    const Rect photograph{x+39,middle-63,192,126};
                    welcome_.bordered_rect(photograph,0,tone_.with_alpha(.08f),2,ink.with_alpha(.65f));
                    welcome_.push_clip({photograph.x+3,photograph.y+3,photograph.w-6,photograph.h-6});
                    const float drift=reduced_?0.f:8*std::sin(time_*.8f);
                    welcome_.circle(x+181+drift,middle-29,14,tone_);
                    welcome_.line(x+49,middle+48,x+111,middle-16,2,ink.with_alpha(.7f));
                    welcome_.line(x+111,middle-16,x+171,middle+48,2,ink.with_alpha(.7f));
                    welcome_.line(x+143,middle+48,x+187,middle+4,2,ink.with_alpha(.7f));
                    welcome_.line(x+187,middle+4,x+225,middle+48,2,ink.with_alpha(.7f));
                    welcome_.line(x+49,middle+48,x+225,middle+48,2,ink.with_alpha(.7f));
                    welcome_.pop_clip();
                }
                if(tile==1){const float pulse=reduced_?0.f:7*std::sin(time_*1.1f);welcome_.circle(x+135,middle,37+pulse,ink.with_alpha(.08f));welcome_.triangle({x+121-pulse*.3f,middle-19-pulse*.3f,34+pulse*.6f,38+pulse*.6f},ink,0,1.5708f);}
                if(tile==2)for(int bar=0;bar<18;++bar){const float h=14+37*(.5f+.5f*std::sin(float(bar)*.5f+(reduced_?0.f:time_*1.4f)));const float bx=x+41.5f+bar*11;welcome_.line(bx,middle-h*.5f,bx,middle+h*.5f,2,tone_);}
                if(tile==3){const float travel=reduced_?0.f:std::sin(time_*1.3f);welcome_.rounded_rect({x+32,middle-33+travel*20,7,66},2,ink);welcome_.rounded_rect({x+231,middle-33-travel*20,7,66},2,ink);welcome_.circle(x+135+travel*65,middle+(reduced_?0.f:std::cos(time_*.9f)*40),9,tone_);}
            }
        }else if(n==3){
            // The same physical mesh as the viewer, at one turn per 36 seconds.
            // Reduced motion keeps the actual 3D pin still and facing forward.
            if(trophy_pin_renderer_){
                TrophyView pin;pin.badge="first_pin_3d";pin.unlocked=true;
                const float yaw=reduced_?0.f:pin_onboarding_time_*(6.28318530718f/36.f);
                const float pitch=reduced_?0.f:.10f;
                const int side=std::max(1,output_height_*2/3);
                const unsigned texture=trophy_pin_renderer_(pin,side,side,yaw,pitch,1.f,0.f);
                if(texture)welcome_.image(texture,{cx-340,cy-340,680,680},gfx::kCanvasUv,Color::rgb(0xffffff));
            }
        }else if(n==4){
            constexpr unsigned palette[]={0xdc9b79,0xc2b179,0xd78a64,0x83b8b0,0xb6a2cf,0x82acc8,0xc8919b,0xb1c098};
            for(int k=0;k<8;++k){const float x=1090+float(k)*83;
                const float phase=reduced_?0:time_*.5f+float(k)*.45f;
                for(int p=0;p<42;++p){const float y=cy+std::sin(float(p)*.16f+phase)*(45+float(k)*6);
                    welcome_.circle(x+std::sin(float(p)*.1f)*9,y+float(p-21)*6,2,Color::rgb(palette[k],.75f));}
            }
        }else if(n==5){
            const auto c=video_.connection();
            const auto connection_motion=[&](float center_y){
                const float pulse=reduced_?0.f:4.f*std::sin(time_*1.3f);
                const Rect phone{cx-210,center_y-120+pulse,122,240};
                const Rect screen{cx-15,center_y-89-pulse,260,166};
                welcome_.bordered_rect(phone,12,paper,2,ink.with_alpha(.65f));
                welcome_.rounded_rect({phone.x+11,phone.y+24,100,178},3,tone_.with_alpha(.12f));
                welcome_.line(phone.x+44,phone.y+12,phone.x+78,phone.y+12,2,ink.with_alpha(.55f));
                welcome_.circle(phone.cx(),phone.y+221,5,ink.with_alpha(.55f));
                welcome_.bordered_rect(screen,6,paper,2,ink.with_alpha(.65f));
                welcome_.rounded_rect({screen.x+10,screen.y+10,240,146},2,tone_.with_alpha(.1f));
                welcome_.triangle({screen.cx()-12,screen.cy()-19,34,38},tone_,0,1.5708f);
                welcome_.line(screen.cx(),screen.y+167,screen.cx(),screen.y+187,2,ink.with_alpha(.5f));
                welcome_.line(screen.cx()-46,screen.y+187,screen.cx()+46,screen.y+187,2,ink.with_alpha(.5f));
                for(int dot=0;dot<3;++dot){const float t=reduced_?float(dot+1)*.25f:std::fmod(time_*.38f+float(dot)/3.f,1.f);welcome_.circle(phone.x+phone.w+12+t*58,center_y,3+2*std::sin(t*3.14159265f),tone_.with_alpha(.35f+.65f*std::sin(t*3.14159265f)));}
                return (phone.x+screen.x+screen.w)*.5f;
            };
            if(c.signed_in||c.saved){
                const float illustration_axis=connection_motion(cy-30);
                ui::paragraph(welcome_,fonts_.semibold,c.signed_in?"The museum is connected.":"YouTube access is saved.",illustration_axis,cy+200,30,600,40,ink,3,Align::center);
            }else if(!c.user_code.empty()){
                welcome_.rounded_rect({cx-195,cy-195,390,390},8,Color::rgb(0xffffff));
                if(connection_qr_)welcome_.image(connection_qr_,{cx-175,cy-175,350,350},gfx::kFullUv,Color::rgb(0xffffff));
                ui::text(welcome_,fonts_.mono,c.user_code,cx,cy+268,38,ink,Align::center);
                ui::paragraph(welcome_,fonts_.regular,c.verification_url,cx,cy+320,23,640,32,quiet,2,Align::center);
                for(int dot=0;dot<3;++dot){const float pulse=reduced_?.6f:.4f+.6f*(.5f+.5f*std::sin(time_*2.f-float(dot)*.7f));welcome_.circle(cx-22+dot*22,cy-224,4,tone_.with_alpha(pulse));}
            }else{
                connection_motion(cy);
                if(c.state==media::State::loading)ui::text(welcome_,fonts_.regular,"Contacting YouTube…",cx,730,27,quiet,Align::center);
                if(c.state==media::State::failed)ui::paragraph(welcome_,fonts_.regular,c.error,cx-320,710,23,640,33,quiet,4);
            }
        }
        std::vector<ui::Hint> commands;
        if(n==1)commands={{ui::Button::dpad,"History (D-pad up)"},{ui::Button::dpad,"Games (D-pad down)"}};
        if(n==2)commands={{ui::Button::cross,"Explore"},{ui::Button::right_stick,"Read"},{ui::Button::circle,"Back"}};
        if(n==3)commands={{ui::Button::square,"Trophies"},{ui::Button::triangle,"Pin"}};
        if(n==4)commands={{ui::Button::touchpad,"Guide"},{ui::Button::triangle,"Today"},{ui::Button::options,"Preferences"}};
        if(!commands.empty()){
            ui::HintLayout row;row.cy=890;row.size=29;row.text_size=20;row.item_gap=24;
            while(ui::measure_hints(fonts_,commands.data(),int(commands.size()),row)>790&&row.text_size>17){row.text_size-=1;row.item_gap-=2;}
            ui::draw_hints(welcome_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),commands.data(),int(commands.size()),100,false,row);
        }
        welcome_.pop_transform();welcome_.pop_opacity();welcome_.pop_clip();
    }
    welcome_.push_opacity(std::clamp(float(onboarding_cards_)-onboarding_position_.value,0.f,1.f));
    for(int n=0;n<onboarding_cards_;++n){const float focus=std::max(0.f,1-std::abs(float(n)-onboarding_position_.value));welcome_.rounded_rect({100+float(n)*54,944,42,3+3*focus},0,gfx::mix(quiet.with_alpha(.2f),ink,focus));}
    const auto connection=video_.connection();
    const bool connection_step=onboarding_step_==onboarding_cards_-1;
    std::vector<ui::Hint> buttons={{ui::Button::cross,connection_step&&!connection.signed_in&&!connection.saved?"Connect":"Continue"}};
    buttons.push_back({ui::Button::circle,"Previous"});
    buttons.push_back({ui::Button::square,connection_step?(connection.saved||connection.signed_in?"Reconnect":"Skip connection"):"Skip introduction"});
    ui::HintLayout l;l.cy=1014;l.size=30;l.text_size=22;l.item_gap=36;
    ui::draw_hints(welcome_,fonts_,ui::GlyphStyle::mono(ink,Color::rgb(0,0)),buttons.data(),int(buttons.size()),96,false,l);
    welcome_.pop_opacity();welcome_.pop_opacity();
}
}
