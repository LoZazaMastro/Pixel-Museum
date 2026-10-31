// Production carousel/input checks. Uses real catalogue cards and a current GL context.
// Film checks validate presentation only; no network request or decoder success is assumed.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
inline bool ScreenInspection::verify_scene(Screen&s,unsigned framebuffer,int width,int height){
    const auto*entry=s.current();
    if(!entry||entry->images.empty()||entry->videos.empty()||s.screening_||s.video_.state()!=media::State::idle){
        std::fputs("Scene checks need an idle exhibit with a photograph and archive film\n",stderr);return false;
    }
    const bool reduced=s.reduced_,manual=s.object_manual_,dirty=s.dirty_,onboarding=s.onboarding_,onboarding_complete=s.onboarding_complete_;
    const float angle=s.object_angle_,tilt=s.object_tilt_offset_,zoom=s.object_zoom_,boot=s.boot_time_,idle=s.idle_,delay=s.save_delay_;
    const int note=s.boot_note_,focus=s.focus_;const std::string exhibit=entry->id;
    const auto gallery_origin=s.gallery_origin_,screening_origin=s.screening_origin_;
    const auto workshop=s.workshop_;const std::string data=s.data_;
    const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"Scene check failed: %s\n",message);return pass;};
    const auto same_rect=[](const hui::gfx::Rect&a,const hui::gfx::Rect&b){return std::abs(a.x-b.x)+std::abs(a.y-b.y)+std::abs(a.w-b.w)+std::abs(a.h-b.h)<.02f;};
    hui::ui::Feedback feedback;
    const auto press=[&](hui::Action action){hui::InputFrame in;in.connected=true;in.pressed=hui::action_bit(action);s.handle(in,feedback);};
    const auto nav=[&](hui::Direction direction){hui::InputFrame in;in.connected=true;in.nav=direction;s.handle(in,feedback);};
    const auto advance=[&](int frames){for(int n=0;n<frames;++n)s.update(1.f/60);};
    const auto draw=[&](){s.draw(width,height,framebuffer);return require(glGetError()==GL_NO_ERROR,"production draw reports no GL error");};
    const auto unchanged=[&](){return s.focus_==focus&&s.current()&&s.current()->id==exhibit;};
    const auto find_card=[&](Screen::StoryCard::Kind kind){const auto it=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&card){return card.kind==kind;});return it==s.story_cards_.end()?-1:int(it-s.story_cards_.begin());};
    const auto choose=[&](int index){s.move_story(index-s.story_focus_,feedback);advance(100);return draw();};
    const auto finish=[&](bool result){
        s.screening_=s.fullscreen_=s.gallery_=s.object_inspect_=s.workshop_active_=false;
        if(!s.current()||s.current()->id!=exhibit)s.select(exhibit);
        s.preview(0);s.scroll_.snap(0);s.story_expanded_=false;s.story_read_.snap(0);s.story_focus_=0;s.story_position_.snap(0);
        s.screening_from_story_=false;s.media_hints_.snap(1);s.seek_first_video_=false;
        s.gallery_origin_=gallery_origin;s.screening_origin_=screening_origin;
        s.workshop_=workshop;s.data_=data;
        s.reduced_=reduced;s.object_manual_=manual;s.object_angle_=angle;s.object_tilt_offset_=tilt;s.object_zoom_=zoom;s.dirty_=dirty;s.save_delay_=delay;s.boot_time_=boot;s.boot_note_=note;s.idle_=idle;s.onboarding_=onboarding;s.onboarding_complete_=onboarding_complete;
        if(result)std::puts("Scene controls: carousel boundaries/animation, complete scrollable original text, active-media isolation, photo/film origin and reverse, retained card, sources, shoulder exhibit navigation, genuine object cards and PixelWorkshop edit/return routing passed; YouTube playback not tested");
        return result;
    };
    s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.reduced_=false;s.object_manual_=true;s.dirty_=false;
    // update() normally persists a changed exhibit. These deterministic scene
    // checks must never rewrite the user's preview or console preferences.
    s.data_.clear();
    s.settings_=s.credits_=s.connection_panel_=false;s.object_inspect_=false;s.fullscreen_=false;s.preview(0);
    if(!draw())return finish(false);
    press(hui::Action::confirm);
    if(!require(s.detail_&&s.story_open_.value==0&&unchanged(),"story opens from the chronology without a snap or exhibit change"))return finish(false);
    advance(5);
    if(!require(s.story_open_.target==1&&s.story_open_.value>0&&s.story_open_.value<1,"story opens through an intermediate animated position"))return finish(false);
    if(!draw())return finish(false);
    advance(100);if(!draw())return finish(false);
    if(!require(s.story_cards_.size()>=3&&s.story_cards_.back().kind!=Screen::StoryCard::sources&&s.story_focus_==0&&unchanged(),"generated story starts on its first scene and has no terminal credits"))return finish(false);
    s.move_story(-999,feedback);
    if(!require(s.story_focus_==0,"previous clamps at first scene"))return finish(false);
    nav(hui::Direction::right);advance(5);
    if(!require(s.story_focus_==1&&s.story_position_.target==1&&s.story_position_.value>0&&s.story_position_.value<1&&unchanged(),"right animates to the next card without changing exhibits"))return finish(false);
    if(!draw())return finish(false);
    advance(100);nav(hui::Direction::left);advance(100);
    if(!require(s.story_focus_==0&&unchanged(),"left returns to the previous card"))return finish(false);
    s.move_story(999,feedback);
    if(!require(s.story_focus_==int(s.story_cards_.size())-1,"next clamps at terminal sources"))return finish(false);
    if(!choose(0))return finish(false);
    int text_card=-1;
    for(size_t n=0;n<s.story_cards_.size();++n)if(s.story_cards_[n].paragraph>=0){text_card=int(n);break;}
    if(!require(text_card>=0,"a scene retains its original narrative reference"))return finish(false);
    if(!choose(text_card))return finish(false);
    if(!require(s.story_cards_[size_t(text_card)].paragraph<int(entry->body.size()),"narrative points to an existing original paragraph"))return finish(false);
    press(hui::Action::r3);advance(100);if(!draw())return finish(false);
    if(!require(s.story_expanded_&&s.story_focus_==text_card,"R3 expands full prose inside the selected card"))return finish(false);
    nav(hui::Direction::down);advance(5);
    if(!require(s.story_expanded_&&s.story_focus_==text_card&&s.story_read_.target>=0&&unchanged(),"down reads expanded prose without advancing the carousel"))return finish(false);
    press(hui::Action::r3);advance(100);
    if(!require(!s.story_expanded_&&s.story_focus_==text_card,"collapse retains the selected scene"))return finish(false);
    int photo_card=-1;
    for(size_t n=0;n<s.story_cards_.size();++n)if(s.story_cards_[n].image>=0&&s.story_cards_[n].kind!=Screen::StoryCard::film){photo_card=int(n);break;}
    if(!require(photo_card>=0,"real catalogue photography creates a media scene"))return finish(false);
    if(!choose(photo_card))return finish(false);
    const int expected_image=s.story_cards_[size_t(photo_card)].image;
    if(!require(s.story_actions_.size()==1&&s.story_actions_[0].image==expected_image&&s.story_actions_[0].video<0,"only the active photo exposes a media action"))return finish(false);
    s.story_action_=0;const auto source=s.story_actions_[0].bounds;
    press(hui::Action::west);
    if(!require(s.gallery_&&s.detail_&&s.image_index_==expected_image&&same_rect(s.gallery_origin_,source)&&s.gallery_open_.value==0,"photo expands from its actual card rectangle"))return finish(false);
    advance(5);if(!draw())return finish(false);
    const auto moving=s.viewer_.bounds();
    if(!require(s.gallery_open_.value>0&&s.gallery_open_.value<1&&moving.w>source.w&&moving.w<1920,"photo has an intermediate expanding rectangle"))return finish(false);
    advance(100);if(!draw())return finish(false);
    if(!require(same_rect(s.viewer_.bounds(),{0,0,1920,1080}),"photo reaches full display bounds"))return finish(false);
    hui::InputFrame zoom_input;zoom_input.connected=true;zoom_input.trigger_r=1;s.handle(zoom_input,feedback);s.update(1.f/60);
    if(!require(s.viewer_.zoom()>1.02f,"R2 zooms the real image viewer"))return finish(false);
    press(hui::Action::back);
    if(!require(s.gallery_&&s.viewer_.mode()==hui::ui::ZoomMode::fit,"first Back exits zoom and retains the gallery"))return finish(false);
    advance(100);
    if(entry->images.size()>1){const int before=s.image_index_;nav(before+1<int(entry->images.size())?hui::Direction::right:hui::Direction::left);if(!require(s.image_index_!=before&&s.story_focus_==photo_card&&unchanged(),"gallery browse preserves scene and chronology"))return finish(false);}
    press(hui::Action::back);
    if(!require(!s.gallery_&&s.detail_&&s.gallery_open_.value>.99f,"gallery Back begins the reverse transition"))return finish(false);
    advance(5);if(!draw())return finish(false);
    if(!require(s.gallery_open_.target==0&&s.gallery_open_.value>0&&s.gallery_open_.value<1,"closing photo retains an intermediate frame"))return finish(false);
    press(hui::Action::back);
    if(!require(s.detail_,"closing photo blocks Back propagation to chronology"))return finish(false);
    advance(100);if(!draw())return finish(false);
    if(!require(s.gallery_open_.value<.001f&&s.detail_&&s.story_focus_==photo_card&&unchanged(),"photo returns to its retained card"))return finish(false);
    const int film_card=find_card(Screen::StoryCard::film);
    if(!require(film_card>=0,"catalogue generates an archive-film scene"))return finish(false);
    if(!choose(film_card))return finish(false);
    if(!require(s.story_actions_.size()==1&&s.story_actions_[0].video==s.story_cards_[size_t(film_card)].video&&s.story_actions_[0].image<0,"only the active film owns its frame"))return finish(false);
    // Open presentation manually; never invoke a YouTube resolver in this deterministic check.
    s.video_index_=s.story_actions_[0].video;s.screening_origin_=s.story_actions_[0].bounds;s.screening_from_story_=true;s.screening_=true;s.fullscreen_=false;
    advance(100);if(!draw())return finish(false);
    if(!require(s.screening_open_.value>.999f&&s.video_full_.value==0&&s.detail_&&s.video_.state()==media::State::idle,"inline presentation retains the card without claiming decode readiness"))return finish(false);
    press(hui::Action::west);advance(5);
    if(!require(s.fullscreen_&&s.video_full_.target==1&&s.video_full_.value>0&&s.video_full_.value<1,"Square animates the frame towards fullscreen"))return finish(false);
    if(!draw())return finish(false);
    advance(100);press(hui::Action::back);advance(5);
    if(!require(!s.fullscreen_&&s.screening_&&s.video_full_.target==0&&s.video_full_.value>0&&s.video_full_.value<1,"fullscreen Back reverses to inline presentation"))return finish(false);
    advance(100);press(hui::Action::back);advance(5);if(!draw())return finish(false);
    if(!require(!s.screening_&&s.detail_&&s.screening_open_.value>0&&s.screening_open_.value<1,"inline Back reverses into the retained story"))return finish(false);
    press(hui::Action::back);
    if(!require(s.detail_,"closing film blocks Back propagation"))return finish(false);
    advance(100);
    if(!require(s.story_focus_==film_card&&unchanged(),"film return preserves card and exhibit"))return finish(false);
    press(hui::Action::north);advance(100);if(!draw())return finish(false);
    if(!require(s.story_focus_==film_card,"Triangle no longer opens per-article credits"))return finish(false);
    press(hui::Action::back);advance(5);if(!draw())return finish(false);
    if(!require(!s.detail_&&s.story_open_.target==0&&s.story_open_.value>0&&s.story_open_.value<1,"story Back reverses its opening transition"))return finish(false);
    advance(100);
    if(!require(s.story_open_.value<.001f&&unchanged(),"story returns to the same chronology selection"))return finish(false);
    if(s.visible_.size()>1){press(hui::Action::confirm);advance(100);const bool forwards=s.focus_+1<int(s.visible_.size());const int expected=s.focus_+(forwards?1:-1);press(forwards?hui::Action::page_next:hui::Action::page_prev);if(!require(s.detail_&&s.focus_==expected&&s.story_focus_==0,"L1/R1 changes one exhibit and resets its scene selection"))return finish(false);s.select(exhibit);s.preview(0);}
    // Full, unabridged prose and last-line reachability without R3 are
    // exercised through the actual Screen by the story-reading regression.
    // Editorial films stay beside their researched chapter rather than being
    // moved to the introduction by the generic card builder.
    {
        auto&fixture=s.catalog_.entries[size_t(s.visible_[size_t(s.focus_)])];
        const Entry original=fixture;
        fixture.models.clear();fixture.videos.resize(1);
        fixture.videos[0].story_paragraph=2;
        fixture.body={"The first chapter introduces the collection.","The second chapter follows its changing tools.","The final chapter introduces the accompanying archival film."};
        fixture.story_headings={"An introduction","Changing tools","Inside the archive"};
        s.prepare_story();
        const int placed=find_card(Screen::StoryCard::film);
        const bool contextual=placed>0&&s.story_cards_[0].kind==Screen::StoryCard::narrative&&s.story_cards_[size_t(placed)].video==0;
        bool chapter_before=false;
        for(int n=0;n<placed;++n){const auto&card=s.story_cards_[size_t(n)];if(card.paragraph==2||std::find(card.continuation.begin(),card.continuation.end(),2)!=card.continuation.end())chapter_before=true;}
        fixture=original;s.prepare_story();
        if(!require(contextual&&chapter_before,"explicit archival film follows its chapter and does not replace the introduction"))return finish(false);
    }
    // Check a genuine model's card generation, not a synthetic texture or procedural stand-in.
    std::string object_exhibit;
    for(const auto&candidate:s.catalog_.entries)if(!candidate.models.empty()){object_exhibit=candidate.id;if(candidate.id=="game-boy")break;}
    if(!object_exhibit.empty()){
        s.select(object_exhibit);
        if(!require(find_card(Screen::StoryCard::object)>=0&&s.current()&&!s.current()->models.empty(),"real bundled model creates an object scene"))return finish(false);
        if(!require(s.story_cards_.back().kind!=Screen::StoryCard::sources,"object-led exhibit has no source credits card"))return finish(false);
        const int study=find_card(Screen::StoryCard::interactive);
        if(!require(object_exhibit!="game-boy"||study>0,"Game Boy includes a real interactive study after its opening scenes"))return finish(false);
        if(study>=0){
            s.preview(1);if(!choose(study))return finish(false);press(hui::Action::confirm);
            if(!require(s.experience_active_&&!s.experience_introduction_&&s.detail_&&s.story_focus_==study,"X enters the actual study directly from its explanatory card"))return finish(false);
            advance(100);
            const int study_exhibit=s.focus_;const std::string study_id=s.current()->id;
            if(!require(s.study_&&study_catalog()[size_t(s.experience_index_)].id=="pixels","pixel insert owns the current drawing study"))return finish(false);
            nav(hui::Direction::right);
            if(!require(s.story_focus_==study&&s.focus_==study_exhibit&&s.current()->id==study_id,"study D-pad input does not move cards or exhibits"))return finish(false);
            s.study_->take_note();
            press(hui::Action::confirm);
            if(!require(s.study_->take_note()>=0&&s.story_focus_==study&&s.focus_==study_exhibit,"study X paints a pixel and emits its sound instead of opening another scene"))return finish(false);
            press(hui::Action::touch);
            if(!require(s.story_focus_==study&&!s.year_guide_,"study input cannot open the Year Atlas"))return finish(false);
            press(hui::Action::back);
            if(!require(!s.experience_active_&&s.detail_&&s.story_focus_==study&&s.focus_==study_exhibit&&s.current()->id==study_id,"study Back returns to its retained card and exhibit"))return finish(false);
            advance(100);nav(hui::Direction::left);advance(100);
            if(!require(!s.experience_active_&&s.story_focus_==study-1&&s.focus_==study_exhibit&&s.current()->id==study_id,"Left resumes normal carousel navigation after leaving the study"))return finish(false);
        }
        s.select(exhibit);
    }
    return finish(true);
}
}
