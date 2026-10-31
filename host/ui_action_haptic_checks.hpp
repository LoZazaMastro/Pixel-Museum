// Exercise actual Screen input routing, including early-return branches.
#pragma once
namespace museum {
inline bool ScreenInspection::verify_ui_action_haptics(Screen&s){
    using hui::Action;using hui::Direction;using hui::audio::Tactile;
    const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"UI tactile: %s\n",why);return ok;};
    s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;
    s.settings_=s.credits_=s.connection_panel_=s.experience_active_=s.object_inspect_=false;
    s.gallery_=s.screening_=s.fullscreen_=false;s.panel_.snap(0);s.year_guide_=false;s.year_panel_.snap(0);
    s.experience_open_.snap(0);s.experience_pause_open_.snap(0);s.history_focus_=false;
    s.select("game-boy");s.detail_=false;s.story_open_.snap(0);s.fade_=1;s.history_transition_=false;
    const auto settle=[&](){for(int n=0;n<80;++n)s.update(1.f/60);};
    const auto input=[&](Action action,Direction direction=Direction::none){hui::InputFrame i;i.connected=true;i.nav=direction;if(action!=Action::count)i.pressed=hui::action_bit(action);hui::ui::Feedback f;s.handle(i,f);return f;};
    const auto tactile=[&](const hui::ui::Feedback&f,const char*why){return require(!f.tactile.empty(),why);};
    auto f=input(Action::count,Direction::right);if(!tactile(f,"main timeline navigation"))return false;
    if(!require(f.tactile.back().pattern==Tactile::timeline_step&&f.tactile.back().strength>=.34f&&f.tactile.back().pan>0,"accepted gaming step has firm right detent"))return false;
    f=input(Action::count,Direction::left);if(!require(!f.tactile.empty()&&f.tactile.back().pattern==Tactile::timeline_step&&f.tactile.back().pan<0,"gaming left detent direction"))return false;
    f=input(Action::confirm);if(!require(s.detail_,"article opens")||!tactile(f,"article confirmation"))return false;
    if(!require(s.story_cards_.size()>1,"article fixture has multiple cards"))return false;
    const int first_card=s.story_focus_;
    s.scroll_.snap(200);
    f=input(Action::count,Direction::right);
    if(!require(s.story_focus_==first_card+1&&!f.tactile.empty()&&f.tactile.back().pattern==Tactile::timeline_step&&f.tactile.back().strength>=.34f&&f.tactile.back().pan>0,"right card change has perceptible directional detent"))return false;
    f=input(Action::count,Direction::left);
    if(!require(s.story_focus_==first_card&&!f.tactile.empty()&&f.tactile.back().pattern==Tactile::timeline_step&&f.tactile.back().strength>=.34f&&f.tactile.back().pan<0,"left card change has perceptible directional detent"))return false;
    f=input(Action::back);if(!require(!s.detail_,"article returns")||!tactile(f,"article return"))return false;
    settle();f=input(Action::count,Direction::up);
    if(!require(s.history_focus_,"culture route opens")||!require(!f.tactile.empty()&&f.tactile.back().pattern==Tactile::rise,"culture transition rises across the actuators"))return false;
    if(!require(f.speaker_cues.size()==1&&f.speaker_cues.front().cue==hui::audio::SpeakerCue::timeline_culture,"accepted culture transition has ascending speaker motif"))return false;
    settle();f=input(Action::count,Direction::right);
    if(!require(!f.tactile.empty()&&f.tactile.back().pattern==Tactile::timeline_step&&f.tactile.back().pan>0&&f.speaker_cues.empty(),"culture browse uses right detent without replaying route motif"))return false;
    settle();f=input(Action::count,Direction::down);
    if(!require(!s.history_focus_,"gaming route returns")||!require(!f.tactile.empty()&&f.tactile.back().pattern==Tactile::fall,"gaming transition has its descending tactile"))return false;
    if(!require(f.speaker_cues.size()==1&&f.speaker_cues.front().cue==hui::audio::SpeakerCue::timeline_games,"accepted gaming return has descending speaker motif"))return false;
    settle();f=input(Action::touch);if(!require(s.year_guide_,"guide opens")||!tactile(f,"guide opening"))return false;
    f=input(Action::count,Direction::down);if(!tactile(f,"guide year navigation"))return false;
    f=input(Action::west);if(!require(s.guide_experiences_,"experience collection opens")||!tactile(f,"guide collection switch"))return false;
    f=input(Action::count,Direction::down);if(!tactile(f,"experience collection navigation"))return false;
    f=input(Action::back);if(!require(!s.year_guide_,"guide returns")||!tactile(f,"guide return"))return false;
    settle();f=input(Action::menu);if(!require(s.settings_,"settings opens")||!tactile(f,"settings opening"))return false;
    s.setting_=0;f=input(Action::count,Direction::down);if(!require(s.setting_==1,"settings item changes")||!tactile(f,"silent settings focus has tactile"))return false;
    f=input(Action::confirm);if(!tactile(f,"settings edit confirmation"))return false;
    f=input(Action::back);if(!require(!s.settings_,"settings closes")||!tactile(f,"settings return"))return false;
    const auto& studies=study_catalog();int flight=-1;
    for(size_t n=0;n<studies.size();++n)if(studies[n].id=="wireframe")flight=int(n);
    if(!require(flight>=0,"flight study exists"))return false;
    s.open_experience(flight,{0,0,1920,1080});s.experience_open_.snap(1);
    f=input(Action::menu);if(!require(s.experience_paused_,"flight pauses")||!tactile(f,"flight pause"))return false;
    f=input(Action::count,Direction::down);if(!require(s.experience_pause_selection_==1,"gyro row")||!tactile(f,"flight pause focus"))return false;
    const bool gyro=s.study_->gyro_enabled();f=input(Action::confirm);
    if(!require(s.study_->gyro_enabled()!=gyro&&!s.study_->motion_controls(),"disabled gyro stops sensor request")||!tactile(f,"gyro toggle"))return false;
    f=input(Action::count,Direction::down);if(!require(s.experience_pause_selection_==2,"sensitivity row")||!tactile(f,"sensitivity focus"))return false;
    const float sensitivity=s.study_->gyro_sensitivity();f=input(Action::count,Direction::right);
    if(!require(s.study_->gyro_sensitivity()>sensitivity,"sensitivity increases")||!tactile(f,"sensitivity adjustment"))return false;
    f=input(Action::confirm);if(!require(s.study_->gyro_sensitivity()==1.f,"sensitivity reset")||!tactile(f,"sensitivity reset"))return false;
    f=input(Action::back);if(!require(!s.experience_paused_,"flight resumes")||!tactile(f,"flight resume"))return false;
    f=input(Action::menu);input(Action::count,Direction::down);input(Action::count,Direction::down);input(Action::count,Direction::down);
    f=input(Action::confirm);if(!require(!s.experience_active_,"fourth pause row exits")||!tactile(f,"flight exit"))return false;
    s.experience_open_.snap(0);s.experience_pause_open_.snap(0);
    // The onboarding uses exactly the same input path as a real first visit.
    s.onboarding_=true;s.onboarding_leaving_=false;s.language_choice_=true;s.language_focus_=0;s.onboarding_step_=0;
    const auto onboarding=[&](const hui::ui::Feedback&feedback,const char*why){return tactile(feedback,why)&&require(!feedback.speaker_cues.empty(),"onboarding accepted action also reaches controller speaker");};
    f=input(Action::count,Direction::right);if(!onboarding(f,"language navigation"))return false;
    f=input(Action::count,Direction::left);if(!onboarding(f,"language return"))return false;
    f=input(Action::confirm);if(!require(!s.language_choice_&&s.theme_choice_,"language accepted")||!onboarding(f,"language confirmation"))return false;
    s.dark_theme_=true;f=input(Action::count,Direction::left);if(!require(!s.dark_theme_,"theme changes")||!onboarding(f,"appearance choice"))return false;
    f=input(Action::confirm);if(!require(!s.theme_choice_,"theme accepted")||!onboarding(f,"appearance confirmation"))return false;
    f=input(Action::confirm);if(!require(s.onboarding_step_==1,"onboarding next page")||!onboarding(f,"onboarding next"))return false;
    f=input(Action::back);if(!require(s.onboarding_step_==0,"onboarding previous page")||!onboarding(f,"onboarding back"))return false;
    f=input(Action::west);if(!require(s.onboarding_step_==s.onboarding_cards_-1,"skip reaches optional connection page")||!onboarding(f,"onboarding skip"))return false;
    f=input(Action::west);if(!require(s.onboarding_step_==s.onboarding_cards_,"skip connection reaches start prompt")||!onboarding(f,"optional connection skip"))return false;
    f=input(Action::menu);if(!require(s.onboarding_leaving_,"start accepted")||!onboarding(f,"museum entrance confirmation"))return false;
    hui::InputFrame neutral;neutral.connected=true;hui::ui::Feedback quiet;s.handle(neutral,quiet);
    if(!require(quiet.tactile.empty()&&quiet.speaker_cues.empty(),"no haptic or speaker event without a new accepted action"))return false;
    std::puts("PASS actual UI tactile: timeline/culture directions, article, guide, experience collection, settings and every onboarding action; neutral remains quiet. Physical DualSense output is a separate console check.");return true;
}
}
