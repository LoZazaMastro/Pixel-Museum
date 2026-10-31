// Production Experiences navigation, repeated introductions and source retention.
#pragma once
namespace museum {
inline bool ScreenInspection::verify_experiences(Screen&s,unsigned framebuffer,int width,int height){
    const auto require=[](bool value,const char*message){if(!value)std::fprintf(stderr,"Experiences check failed: %s\n",message);return value;};
    const std::string data=s.data_,id=s.current()?s.current()->id:"pong";s.data_.clear();
    s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=false;s.panel_.snap(0);s.preview(0);s.select("pong");
    hui::ui::Feedback feedback;
    auto press=[&](hui::Action a){hui::InputFrame i;i.connected=true;i.pressed=hui::action_bit(a);s.handle(i,feedback);};
    auto advance=[&](int n){for(int k=0;k<n;++k)s.update(1.f/60);};
    auto finish=[&](bool result){s.experience_active_=false;s.experience_open_.snap(0);s.study_.reset();s.year_guide_=s.guide_experiences_=false;s.year_panel_.snap(0);s.select(id);s.preview(0);s.data_=data;return result;};
    press(hui::Action::touch);press(hui::Action::west);advance(90);
    if(!require(s.year_guide_&&s.guide_experiences_,"Square switches the left guide to Experiences"))return finish(false);
    const auto&all=study_catalog();if(!require(all.size()==21,"all21 reviewed studies are collected"))return finish(false);
    const auto*source=s.current();const std::string source_id=source?source->id:"";
    for(size_t n=0;n<all.size();++n){
        const auto&info=all[n];
        if(!require(!info.explanation.empty()&&!info.discipline.empty(),"each experience has a design/art/music explanation"))return finish(false);
        if(!require(std::any_of(s.catalog_.entries.begin(),s.catalog_.entries.end(),[&](const auto&e){return e.id==info.entry_id;}),"every experience links to a real historical exhibit"))return finish(false);
        s.experience_focus_=int(n);press(hui::Action::confirm);
        if(!require(s.experience_active_&&!s.experience_introduction_&&s.experience_intro_.value==0,"every library launch enters the activity directly"))return finish(false);
        press(hui::Action::confirm);if(!require(s.experience_active_,"opening animation keeps ownership of input"))return finish(false);
        advance(90);s.draw(width,height,framebuffer);if(!require(glGetError()==GL_NO_ERROR,"direct fullscreen activity renders through production screen"))return finish(false);
        press(hui::Action::confirm);advance(60);if(!require(!s.experience_introduction_&&s.experience_intro_.value<.01f,"the experience remains directly playable without an extra introduction"))return finish(false);
        s.draw(width,height,framebuffer);if(!require(glGetError()==GL_NO_ERROR,"activity renders through production screen"))return finish(false);
        if(info.id=="pixels"){
            if(!require(bool(s.study_),"pixel library launches the drawing study"))return finish(false);
            s.study_->take_note();hui::InputFrame touch;touch.connected=true;touch.touch.available=true;touch.touch.count=1;touch.touch.points[0].x=1;touch.touch.points[0].y=0;s.handle(touch,feedback);
            if(!require(s.study_->take_note()>=0,"touch input paints through the active pixel study and emits feedback"))return finish(false);
        }
        if(!require(s.motion_controls()==(info.id=="wireframe"),"only the explicitly implemented flight study requests calibrated sensor controls"))return finish(false);
        press(hui::Action::menu);if(!require(!s.settings_,"experience owns its controls without opening settings"))return finish(false);
        press(hui::Action::back);advance(90);if(!require(!s.experience_active_&&s.year_guide_&&s.current()&&s.current()->id==source_id,"Back restores the library without navigating the historical exhibit"))return finish(false);
        press(hui::Action::confirm);advance(90);if(!require(!s.experience_introduction_&&s.experience_intro_.value<.001f,"reopening goes straight to the activity"))return finish(false);
        press(hui::Action::back);advance(90);
    }
    s.year_guide_=false;s.year_panel_.snap(0);
    for(size_t n=0;n<all.size();++n){if(all[n].id=="pixels")continue;s.select(all[n].entry_id);s.preview(1);
        const auto found=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&c){return c.kind==Screen::StoryCard::experience&&c.study_index==int(n);});
        if(!require(found!=s.story_cards_.end(),"the same experience is inserted into its game's story"))return finish(false);
        s.story_focus_=int(found-s.story_cards_.begin());s.story_position_.snap(float(s.story_focus_));press(hui::Action::confirm);advance(90);
        if(!require(s.experience_active_&&!s.experience_introduction_,"story insert also launches directly"))return finish(false);
        press(hui::Action::back);advance(90);
        if(!require(s.detail_&&s.story_focus_==int(found-s.story_cards_.begin()),"story return retains its source card"))return finish(false);
    }
    std::puts("Experiences: reviewed library entries, conceptual explanations on cards, direct fullscreen launch, source-card return and actual GL rendering passed");return finish(true);
}
inline void ScreenInspection::experience_preview(Screen&s,int mode,int index){
    s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=false;s.panel_.snap(0);s.select("pong");s.preview(0);
    s.open_year_guide();s.guide_experiences_=true;s.experience_focus_=index;s.experience_position_.snap(float(index));s.year_panel_.snap(1);
    s.experience_active_=false;s.experience_open_.snap(0);
    if(mode){s.open_experience(index,{64,350,548,370});s.experience_open_.snap(1);if(mode==2){s.experience_introduction_=false;s.experience_intro_.snap(0);}}
}
}
