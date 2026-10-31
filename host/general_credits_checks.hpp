// Actual production settings route and five-language credits layout.
#pragma once
#include "museum/general_credits.hpp"
#include "museum/feature_resources.hpp"
#include <cctype>
namespace museum {
inline bool ScreenInspection::verify_general_credits(Screen&s,unsigned fb,int width,int height){
    const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"General credits: %s\n",why);return ok;};
    const auto compact=[](std::string_view value){std::string out;for(unsigned char c:value)if(!std::isspace(c))out+=char(c);return out;};
    const auto capture=[&](const std::string&name){s.draw(width,height,fb);std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,fb);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/general-credits-"+name+".png").c_str(),width,height,4,pixels.data(),width*4)&&glGetError()==GL_NO_ERROR;};
    s.data_.clear();s.onboarding_=s.onboarding_leaving_=s.language_choice_=s.theme_choice_=false;
    s.boot_time_=5;s.boot_note_=13;s.gallery_=s.screening_=s.fullscreen_=s.year_guide_=s.chapters_=false;
    s.experience_active_=false;s.experience_open_.snap(0);s.experience_pause_open_.snap(0);s.detail_=false;s.story_open_.snap(0);s.year_panel_.snap(0);
    s.connection_panel_=false;s.fade_=1;s.dt_=1.f/60;
    const auto saved_visible=s.visible_;const int saved_focus=s.focus_,saved_history=s.history_focus_index_;const bool saved_history_focus=s.history_focus_;
    unsigned examined=0,features=0;
    for(bool culture:{false,true}){
        s.history_focus_=culture;
        const auto count=culture?s.history_catalog_.entries.size():s.catalog_.entries.size();
        for(size_t n=0;n<count;++n){
            if(culture)s.history_focus_index_=int(n);else{s.visible_={int(n)};s.focus_=0;}
            s.prepare_story();
            features+=unsigned(s.current()->editorial_features.size());
            if(!require(!s.story_cards_.empty(),"every article retains content cards"))return false;
            for(const auto&card:s.story_cards_)if(!require(card.kind!=Screen::StoryCard::sources,"gaming, culture and feature stories contain no credits card"))return false;
            hui::ui::Feedback feedback;s.move_story(int(s.story_cards_.size())+1,feedback);
            if(!require(s.story_focus_==int(s.story_cards_.size())-1,"navigation clamps to the last remaining content card"))return false;
            ++examined;
        }
    }
    s.visible_=saved_visible;s.focus_=saved_focus;s.history_focus_index_=saved_history;s.history_focus_=saved_history_focus;s.prepare_story();
    s.detail_=true;s.story_open_.snap(1);s.story_position_.snap(0);
    hui::InputFrame triangle;triangle.connected=true;triangle.pressed=hui::action_bit(hui::Action::north);hui::ui::Feedback ignored;s.handle(triangle,ignored);
    if(!require(s.story_focus_==0,"Triangle cannot open article credits or jump to the final card"))return false;
    s.detail_=false;s.story_open_.snap(0);
    std::printf("Global resources: %u authentic sites; %u gaming/culture articles including %u nested features have no credits cards and valid navigation ends.\n",feature_resources_site_count,examined,features);
    for(const char*lang:{"en","it","es","fr","de"}){
        if(!require(i18n::load(".",lang),"complete language dictionary loads"))return false;s.language_=lang;
        const auto translated=general_credits_body();
        if(!require(std::string_view(lang)=="en"||translated!=general_credits_text,"body has an actual translation"))return false;
        if(!require(translated.find("Andrea Sgarro")!=std::string_view::npos&&translated.find("LoZazaMastro")==std::string_view::npos,"requested personal attribution"))return false;
        const auto lines=hui::ui::paragraph_lines(s.fonts_.regular,translated,24,665,999);
        std::string joined;int empty=0;for(const auto&line:lines.lines){joined+=line;if(line.empty())++empty;if(!require(s.fonts_.regular.measure(line,24)<=665.1f,"every full line stays inside reading column"))return false;}
        if(!require(!lines.truncated&&compact(joined)==compact(translated)&&empty==5,"all text and all five paragraph separations retained without ellipsis"))return false;
        if(!require(s.fonts_.semibold.measure(hui::ui::resolve_text(preference_labels.back()),25)<600,"last settings label fits before arrow"))return false;
        s.settings_=true;s.credits_=false;s.panel_.snap(1);s.credits_open_.snap(0);s.setting_=0;
        hui::InputFrame i;i.connected=true;i.nav=hui::Direction::down;hui::ui::Feedback feedback;
        for(int n=0;n<8;++n)s.handle(i,feedback);
        if(!require(s.setting_==general_credits_setting,"navigation ends at Credits"))return false;
        i.nav=hui::Direction::up;s.handle(i,feedback);if(!require(s.setting_==reset_trophies_setting,"reset trophies is immediately before Credits"))return false;
        i.nav=hui::Direction::down;s.handle(i,feedback);
        s.focus_line_.snap(240+float(s.setting_)*68);
        if(!capture(std::string(lang)+"-settings-last"))return false;
        i.nav=hui::Direction::none;i.pressed=hui::action_bit(hui::Action::confirm);s.handle(i,feedback);
        if(!require(s.credits_&&!s.settings_&&s.credits_scroll_.target==0,"last-row confirmation opens credits from the beginning"))return false;
        s.credits_open_.snap(1);
        if(!capture(std::string(lang)+"-start"))return false;
        std::string resource_text;for(const auto&line:s.feature_resources_lines_){resource_text+=line;if(!require(s.fonts_.regular.measure(line,21)<=665.1f,"every site name remains inside the reading column"))return false;}
        if(!require(compact(resource_text)==compact(feature_resources_sites),"complete global site list retained without omitted domains"))return false;
        const float body_end=265+float(lines.lines.size())*35;
        i.pressed=0;i.nav=hui::Direction::none;i.stick2_y=1;s.dt_=1.f/60;
        for(int n=0;n<2000&&s.credits_scroll_.target<std::max(0.f,body_end-780);++n)s.handle(i,feedback);
        s.credits_scroll_.snap(s.credits_scroll_.target);
        if(!require(s.credits_scroll_.value>=std::max(0.f,body_end-780),"reading input reaches the final requested paragraph"))return false;
        if(!capture(std::string(lang)+"-full-text-end"))return false;
        for(int n=0;n<2000;++n)s.handle(i,feedback);
        if(!require(s.credits_scroll_.target==s.credits_scroll_max_&&s.credits_scroll_max_>body_end-900,"retained sources and licences remain scrollable after new text"))return false;
        i.nav=hui::Direction::none;i.stick2_y=0;i.pressed=hui::action_bit(hui::Action::back);s.handle(i,feedback);
        if(!require(s.settings_&&!s.credits_,"back returns to settings"))return false;
        std::printf("General credits %s: %zu full lines, five blank lines, bodyEnd %.0f, totalScroll %.0f; actual last-row route PASS, 3 PNG GL0\n",lang,lines.lines.size(),body_end,s.credits_scroll_max_);
    }
    return true;
}
}
