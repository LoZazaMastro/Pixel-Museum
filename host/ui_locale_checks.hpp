// Actual Screen routes, localized drawing and manual full-description reading.
#pragma once
#include "third_party/stb/stb_image_write.h"
namespace museum {
inline bool ScreenInspection::verify_ui_locales(Screen&s,unsigned fb,int width,int height){
    const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"UI locale: %s\n",why);return ok;};
    struct Finished final:Study{
        std::unique_ptr<Study> visual=make_study("dash");
        void reset()override{}void handle(const hui::InputFrame&,hui::ui::Feedback&)override{}void update(float)override{}
        void draw(hui::gfx::DrawList&l,hui::ui::Fonts&f,hui::gfx::Rect r,hui::gfx::Color a)override{visual->draw(l,f,r,a);}
        const char*help()const override{return "UI completion fixture";}
        StudyCompletion completion()const override{return StudyCompletion::experience_complete;}
        int level_number()const override{return 5;}int level_count()const override{return 5;}
    };
    s.data_.clear();s.onboarding_=s.onboarding_leaving_=s.language_choice_=s.theme_choice_=false;
    s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.connection_panel_=false;
    s.gallery_=s.screening_=s.fullscreen_=false;s.panel_.snap(0);s.fade_=1;s.history_transition_=false;s.dt_=1.f/60;
    const auto capture=[&](const std::string&name){s.draw(width,height,fb);std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,fb);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/ui-"+name+"-4k.png").c_str(),width,height,4,pixels.data(),width*4)&&glGetError()==GL_NO_ERROR;};
    int portal=-1,pocket=-1,dash=-1;
    for(size_t n=0;n<study_catalog().size();++n){const auto&id=study_catalog()[n].id;if(id=="portals")portal=int(n);if(id=="pocket-budget")pocket=int(n);if(id=="dash")dash=int(n);}
    if(!require(portal>=0&&pocket>=0&&dash>=0,"studies present"))return false;
    for(const char*lang:{"it","es","fr","de"}){
        if(!require(i18n::load(".",lang),"current source dictionary loads"))return false;s.language_=lang;
        s.experience_active_=false;s.experience_open_.snap(0);s.experience_pause_open_.snap(0);s.detail_=false;s.story_open_.snap(0);
        s.open_year_guide();s.guide_experiences_=true;s.year_panel_.snap(1);s.guide_mode_.snap(1);
        s.experience_focus_=portal;s.experience_position_.snap(float(portal));s.experience_description_scroll_=0;
        s.draw(width,height,fb);if(!require(s.experience_description_max_>200,"full translated description extends beyond viewport"))return false;
        hui::InputFrame i;i.connected=true;i.stick2_y=1;hui::ui::Feedback f;
        s.tactile_repeat_=0;s.handle(i,f);if(!require(!f.tactile.empty()&&f.tactile.back().pattern==hui::audio::Tactile::scroll,"accepted reading motion emits paced scroll texture"))return false;
        for(int n=0;n<180;++n)s.handle(i,f);
        if(!require(s.experience_description_scroll_==s.experience_description_max_,"right stick reaches last full line"))return false;
        f.clear();s.tactile_repeat_=0;s.handle(i,f);if(!require(f.tactile.empty(),"reading boundary emits no false scroll"))return false;
        if(!capture(std::string(lang)+"-library-end"))return false;
        i.stick2_y=0;i.nav=hui::Direction::up;s.handle(i,f);
        if(!require(s.experience_description_scroll_==0,"new selected study resets reading position"))return false;
        s.year_guide_=false;s.year_panel_.snap(0);s.open_experience(pocket,{64,350,548,370});s.experience_open_.snap(1);
        if(!capture(std::string(lang)+"-workshop"))return false;
        s.open_experience(dash,{64,350,548,370});s.study_=std::make_unique<Finished>();s.experience_completion_seen_=true;s.experience_open_.snap(1);s.experience_pause_open_.snap(1);
        if(!capture(std::string(lang)+"-completed"))return false;
        const hui::ui::Hint hints[]={{hui::ui::Button::square,"Years"},{hui::ui::Button::triangle,"Exhibit"},{hui::ui::Button::right_stick,"Read"}};
        hui::ui::HintLayout layout;layout.size=25;layout.text_size=18;layout.item_gap=23;
        const float hints_width=hui::ui::measure_hints(s.fonts_,hints,3,layout);std::printf("UI %s hints %.1fpx; description %.1fpx; 3 native4K captures GL0\n",lang,hints_width,s.experience_description_max_);
        if(!require(hints_width<=572,"library glyph controls stay inside column"))return false;
    }
    return true;
}
}
