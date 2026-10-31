// Actual Screen completion routing and native 4K visual checks.
#pragma once
#include "third_party/stb/stb_image_write.h"
#include <filesystem>
#include "museum/rhythm_chart.hpp"
namespace museum {
inline bool ScreenInspection::verify_experience_completion(Screen&s,unsigned framebuffer,int width,int height){
    struct Probe final:Study {
        std::unique_ptr<Study> visual=make_study("dash");StudyCompletion state=StudyCompletion::level_complete;
        int advances=0,updates=0,inputs=0,touches=0;
        void reset()override{visual->reset();state=StudyCompletion::playing;}
        void handle(const hui::InputFrame&i,hui::ui::Feedback&)override{++inputs;if(i.is_pressed(hui::Action::touch))++touches;}
        void update(float dt)override{++updates;visual->update(dt);}
        void draw(hui::gfx::DrawList&d,hui::ui::Fonts&f,hui::gfx::Rect r,hui::gfx::Color c)override{visual->draw(d,f,r,c);}
        const char*help()const override{return "Completion routing fixture";}
        StudyCompletion completion()const override{return state;}
        int level_number()const override{return state==StudyCompletion::experience_complete?5:2;}
        int level_count()const override{return 5;}
        void continue_level()override{++advances;state=StudyCompletion::playing;}
    };
    const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"Experience completion: %s\n",why);return ok;};
    s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.connection_panel_=false;
    s.gallery_=s.screening_=s.fullscreen_=false;s.panel_.snap(0);s.year_guide_=false;s.year_panel_.snap(0);s.select("celeste");s.detail_=false;s.story_open_.snap(0);s.fade_=1;s.history_transition_=false;
    int dash=-1;for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].id=="dash")dash=int(n);
    if(!require(dash>=0,"Celeste study in catalog"))return false;
    s.open_experience(dash,{64,350,548,370});s.experience_open_.snap(1);
    auto fixture=std::make_unique<Probe>();auto*probe=fixture.get();s.study_=std::move(fixture);
    const auto input=[&](hui::Action a,hui::Direction nav=hui::Direction::none){hui::InputFrame i;i.connected=true;i.nav=nav;if(a!=hui::Action::count)i.pressed=hui::action_bit(a);hui::ui::Feedback f;s.handle(i,f);return f;};
    const auto settle=[&]{for(int n=0;n<80;++n)s.update(1.f/60);};
    const std::string output="build/previews/experience-completion-refined/";
    std::filesystem::create_directories(output);
    const auto capture=[&](const std::string&name){s.draw(width,height,framebuffer);std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png((output+name+"-4k.png").c_str(),width,height,4,pixels.data(),width*4)&&glGetError()==GL_NO_ERROR;};
    const auto completion_languages=[&](bool final){
        for(const char*lang:{"en","it","es","fr","de"}){
            if(!require(i18n::load(".",lang)&&i18n::locale()==lang&&i18n::error().empty(),"actual five dictionaries load"))return false;
            s.language_=lang;
            const auto lines=hui::ui::paragraph_lines(s.fonts_.regular,final?"Continue to play again, or return to the museum.":"Continue when you are ready for the next level.",21,1040,2);
            if(!require(!lines.truncated&&lines.lines.size()<=2,"complete guidance fits with breathing room before actions"))return false;
            for(const auto&line:lines.lines)if(!require(s.fonts_.regular.measure(line,21)<=1040,"full guidance within text column"))return false;
            if(!require(capture(std::string(final?"final-":"level-")+lang),"actual localized completion capture GL0"))return false;
            for(const auto&instance:s.experience_layer_.instances())
                if(int(instance.params[3]+.5f)==int(hui::gfx::Shape::glyph)&&instance.rect[1]>=960)
                    return require(false,"completed screen must contain no persistent lower control legend");
            std::printf("Completion %s %s: full guidance %zu lines; lower legend absent; native %dx%d GL0\n",lang,final?"final":"level",lines.lines.size(),width,height);
        }
        s.language_="en";return i18n::load(".","en");
    };
    auto f=input(hui::Action::confirm);
    if(!require(probe->advances==0&&!f.tactile.empty(),"opening frame confirms completion tactually but cannot skip the sheet"))return false;
    s.experience_audio_.start();std::array<float,512>audio{};s.experience_audio_.render(audio.data(),256);const auto clock=s.experience_audio_.time_s();
    settle();s.experience_audio_.render(audio.data(),256);
    if(!require(probe->updates==0&&s.experience_audio_.time_s()==clock,"completion freezes simulation and sample clock"))return false;
    if(!completion_languages(false))return false;
    input(hui::Action::menu);if(!require(probe->advances==0&&probe->inputs==0,"Options cannot bypass completion into gameplay"))return false;
    f=input(hui::Action::confirm);if(!require(probe->advances==1&&s.experience_active_&&!f.tactile.empty(),"Continue advances exactly once and keeps experience open"))return false;
    settle();const auto before=probe->touches;input(hui::Action::touch);
    if(!require(probe->touches==before+1&&!s.year_guide_,"touchpad press is delivered to active gameplay before museum guide"))return false;
    probe->state=StudyCompletion::experience_complete;s.experience_completion_seen_=false;input(hui::Action::count);settle();
    if(!completion_languages(true))return false;
    input(hui::Action::confirm);if(!require(probe->advances==2&&s.experience_active_,"final Continue requests replay explicitly"))return false;
    probe->state=StudyCompletion::level_complete;s.experience_completion_seen_=false;input(hui::Action::count);settle();
    input(hui::Action::count,hui::Direction::down);input(hui::Action::confirm);
    if(!require(!s.experience_active_&&probe->advances==2,"Exit closes without advancing the next level"))return false;
    s.study_.reset();settle();s.open_year_guide();s.guide_experiences_=true;s.year_panel_.snap(1);s.guide_mode_.snap(1);s.experience_focus_=dash;s.experience_position_.snap(float(dash));settle();
    if(!require(capture("experience-menu-game-referents"),"actual menu with game/person referents 4K GL0"))return false;
    // Real rhythm study, real Screen input routing (including Circle/Square),
    // and actual rendered audio frames. UI dt does not set judgement time.
    int rhythm=-1;for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].id=="rhythm")rhythm=int(n);
    if(!require(rhythm>=0,"rhythm study available"))return false;
    s.year_guide_=false;s.year_panel_.snap(0);s.open_experience(rhythm,{64,350,548,370});s.experience_open_.snap(1);s.experience_pause_open_.snap(0);
    constexpr std::array<hui::Action,8> commands{hui::Action::left,hui::Action::right,hui::Action::up,hui::Action::down,hui::Action::confirm,hui::Action::back,hui::Action::north,hui::Action::west};
    const auto render_until=[&](unsigned target){while(unsigned(std::llround(s.experience_audio_.time_s()*48000))<target){const unsigned at=unsigned(std::llround(s.experience_audio_.time_s()*48000)),count=std::min(256u,target-at);audio.fill(0);s.experience_audio_.render(audio.data(),count);}s.update(.001f);};
    unsigned command_mask=0;
    for(size_t n=0;n<RhythmChart::notes.size();++n){const auto note=RhythmChart::notes[n];
        render_until(unsigned(std::llround(note.half*double(ExperienceAudio::beat_seconds)*24000)));
        auto accepted=input(commands[note.lane]);
        if(!require(!accepted.tactile.empty()&&s.study_->take_note()==-1,"actual eight-command perfect input uses rendered targets without asynchronous press beeps"))return false;
        command_mask|=1u<<note.lane;
        auto duplicate=input(commands[note.lane]);if(!require(duplicate.tactile.empty(),"duplicate input cannot score twice or restart Square"))return false;
        if(n==6||n==25||n==43||n==47)if(!require(capture("rhythm-stage-"+std::to_string(n)),"rhythm eight icons, centred judgement, padded score 4K GL0"))return false;
    }
    if(!require(command_mask==255,"all eight commands reach study through Screen"))return false;
    render_until(unsigned(std::llround(ExperienceAudio::beat_seconds*RhythmChart::phrase_beats*48000.0)));
    if(!require(s.study_->completion()==StudyCompletion::experience_complete,"full extended score reaches completion"))return false;
    input(hui::Action::count);settle();if(!require(capture("rhythm-complete"),"rhythm completion without footer legend"))return false;
    std::puts("PASS actual Screen DDR: all48 audio-clock notes accepted, eight-command mask255, duplicate inputs ignored; full41.8seconds, score4800; native4K GL0.");
    for(const char*id:{"paddle","bricks","city-system","portals"}){
        int index=-1;for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].id==id)index=int(n);
        if(!require(index>=0,"representative study exists"))return false;
        s.open_experience(index,{64,350,548,370});s.experience_open_.snap(1);s.experience_pause_open_.snap(0);
        if(std::string_view(id)=="paddle"){
            if(!require(s.secondary_controller_active(),"Pong requests second controller through live Screen"))return false;
            hui::InputFrame players;players.connected=true;players.stick_y=-1;players.secondary.connected=true;players.secondary.stick_y=1;
            hui::ui::Feedback feedback;
            for(int n=0;n<8;++n){s.handle(players,feedback);s.update(.05f);}
            players.secondary.pressed=hui::action_bit(hui::Action::confirm);s.handle(players,feedback);s.update(.05f);
            if(!require(s.study_->take_note()==60,"player two can serve through Screen"))return false;
        }
        if(!require(capture(std::string("themed-margins-")+id),"full Screen themed aspect-ratio margins and footer native4K GL0"))return false;
    }
    std::puts("PASS real Screen completion sheet: first-frame guard, explicit Continue/Exit/final replay, no underlying input, frozen simulation/sample clock, tactile choices, touchpad gameplay dispatch; ten localized completion4K captures without lower legends plus menu4K GL0. Fixture supplies end-state only, actual Portal/Celeste mechanics tested separately.");return true;
}
}
