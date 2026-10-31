// Causal checks through production Screen::handle, not duplicated UI logic.
#pragma once
namespace museum {
inline bool ScreenInspection::verify_timeline_input_today(Screen&s){
    using hui::Action;using hui::Direction;
    int checks=0;
    const auto require=[&](bool ok,const char*why){++checks;if(!ok)std::fprintf(stderr,"timeline input: %s\n",why);return ok;};
    s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;
    s.settings_=s.credits_=s.connection_panel_=s.experience_active_=s.object_inspect_=false;
    s.gallery_=s.screening_=s.fullscreen_=s.chapters_=s.year_guide_=false;
    s.panel_.snap(0);s.year_panel_.snap(0);s.experience_open_.snap(0);s.experience_pause_open_.snap(0);
    s.detail_=false;s.story_open_.snap(0);s.history_focus_=false;s.history_transition_=false;
    auto entry=[](const char*id,const char*kind,int year){Entry e;e.id=id;e.title=id;e.kind=kind;e.year=year;e.month=9;e.day=11;e.precision="day";e.summary="Input fixture.";e.body={"Input fixture."};return e;};
    s.catalog_.entries={entry("hardware","hardware",1980),entry("game","game",1981),entry("person","person",1982),entry("other","company",1983)};
    auto linked=entry("calendar","game",1981);linked.calendar_only=true;linked.linked_exhibit_id="game";linked.calendar_month=9;linked.calendar_day=11;
    s.catalog_.entries.push_back(linked);linked.id="calendar-again";s.catalog_.entries.push_back(linked);
    s.history_catalog_.entries={entry("culture-one","culture",1900),entry("culture-two","culture",1901)};
    s.filter_=0;s.focus_=1;s.rebuild(false);s.changed();s.set_today_date(2026,9,11);
    const auto send=[&](hui::InputFrame i){i.connected=true;hui::ui::Feedback f;s.handle(i,f);return f;};
    const auto release=[&](){send({});};
    const auto button=[&](Action a){release();hui::InputFrame i;i.pressed=hui::action_bit(a);i.held=i.pressed;return send(i);};
    const auto nav=[&](Direction d){hui::InputFrame i;i.nav=d;return send(i);};
    if(!require(s.today_entries(false)==std::vector<int>({1,0,2,3}),"calendar-linked rows resolve and deduplicate"))return false;
    const auto next_filter=[&](bool right,float value=.8f){hui::InputFrame i;if(right)i.trigger_r=value;else i.trigger_l=value;return send(i);};
    auto f=next_filter(true);if(!require(s.filter_==1&&s.current()->id=="hardware"&&!f.tactile.empty(),"R2 chooses filter with nearest focus and haptics"))return false;
    for(int hz:{30,60,120})for(int frame=0;frame<hz;++frame)next_filter(true);
    if(!require(s.filter_==1,"held R2 never repeats at 30/60/120 samples"))return false;
    next_filter(true,.4f);next_filter(true,.7f);
    if(!require(s.filter_==1,"analogue noise does not rearm"))return false;
    release();next_filter(true);if(!require(s.filter_==2&&s.current()->id=="game","release then repress advances"))return false;
    release();next_filter(false);if(!require(s.filter_==1,"L2 reverses filter"))return false;
    release();next_filter(false);release();next_filter(false);if(!require(s.filter_==4,"filter wraps backwards"))return false;
    release();next_filter(true);if(!require(s.filter_==0&&s.current()->id=="other","filter restores exact focus when still visible"))return false;
    s.settings_=true;release();next_filter(true);s.settings_=false;next_filter(true);
    if(!require(s.filter_==0,"holding trigger across a modal does not leak a press"))return false;
    release();
    hui::InputFrame disconnected;disconnected.focus_lost=true;hui::ui::Feedback ignored;s.handle(disconnected,ignored);next_filter(true);
    if(!require(s.filter_==0,"reconnect while trigger held does not navigate"))return false;
    release();next_filter(true);if(!require(s.filter_==1,"neutral release rearms after focus loss"))return false;
    release();
    const auto today=s.today_entries(false);
    for(size_t n=0;n<today.size()+1;++n){button(Action::north);if(!require(s.visible_[size_t(s.focus_)]==today[n%today.size()],"Triangle cycles each unique gaming entry"))return false;}
    hui::InputFrame held;held.held=hui::action_bit(Action::north);send(held);
    if(!require(s.today_cursor_[0]==0,"held Triangle does not repeat"))return false;
    s.history_focus_=true;s.history_transition_=false;s.history_focus_index_=0;
    button(Action::north);if(!require(s.history_focus_&&s.history_focus_index_==0,"culture Today retains active route"))return false;
    button(Action::north);if(!require(s.history_focus_index_==1,"culture Today cycles second event"))return false;
    s.history_focus_=false;button(Action::north);if(!require(s.today_cursor_[0]==1&&s.today_cursor_[1]==1,"route cursors are independent"))return false;
    s.set_today_date(2027,9,11);if(!require(s.today_cursor_[0]==-1&&s.today_cursor_[1]==-1&&s.today_date_label().find("2027")!=std::string::npos,"year change refreshes label and resets both cursors"))return false;
    s.set_today_date(2027,9,12);if(!require(s.today_entries(false).empty(),"zero-event date has no entries"))return false;
    button(Action::north);if(!require(s.today_cursor_[0]==-1,"zero-event press leaves cursor unchanged"))return false;
    s.set_today_date(2026,12,31);s.today_cursor_.fill(2);s.set_today_date(2027,1,1);
    if(!require(s.date_year_==2027&&s.date_month_==1&&s.date_day_==1&&s.today_cursor_[0]==-1,"midnight year rollover"))return false;
    s.onboarding_=true;s.onboarding_leaving_=false;s.language_choice_=true;s.theme_choice_=true;s.onboarding_step_=0;
    button(Action::back);if(!require(s.language_choice_,"first language page cannot exit"))return false;
    button(Action::confirm);if(!require(!s.language_choice_&&s.theme_choice_,"language advances to theme"))return false;
    button(Action::back);if(!require(s.language_choice_,"theme goes back to language"))return false;
    button(Action::confirm);button(Action::confirm);if(!require(!s.theme_choice_&&s.onboarding_step_==0,"theme advances to first slide"))return false;
    button(Action::back);if(!require(s.theme_choice_,"first slide goes back to theme"))return false;
    button(Action::confirm);button(Action::confirm);if(!require(s.onboarding_step_==1,"slides advance"))return false;
    button(Action::back);if(!require(s.onboarding_step_==0&&!s.theme_choice_,"slides go backwards"))return false;
    s.onboarding_step_=s.onboarding_cards_;button(Action::back);if(!require(s.onboarding_step_==s.onboarding_cards_-1&&!s.onboarding_leaving_,"final page can return without completing onboarding"))return false;
    s.onboarding_=false;s.settings_=true;
    for(int setting=0;setting<8;++setting){s.setting_=setting;const auto language=s.language_;const bool dark=s.dark_theme_,mute=s.muted_,reduced=s.reduced_;const float volume=s.volume_;
        nav(Direction::right);
        if(!require(s.language_==language&&s.dark_theme_==dark&&s.muted_==mute&&s.reduced_==reduced&&s.settings_&&!s.credits_&&!s.connection_panel_&&!s.onboarding_,"Right never activates non-volume option"))return false;
        if(setting==3&&!require(s.volume_>=volume,"volume supports Right"))return false;
        nav(Direction::left);
        if(!require(s.language_==language&&s.dark_theme_==dark&&s.muted_==mute&&s.reduced_==reduced&&s.settings_&&!s.credits_&&!s.connection_panel_&&!s.onboarding_,"Left never activates non-volume option"))return false;
    }
    s.setting_=1;const bool theme=s.dark_theme_;button(Action::confirm);if(!require(s.dark_theme_!=theme,"Cross activates selected option"))return false;
    s.setting_=1;nav(Direction::down);if(!require(s.setting_==2,"Down moves option focus"))return false;
    nav(Direction::up);if(!require(s.setting_==1,"Up moves option focus"))return false;
    std::printf("TIMELINE_INPUT_TODAY_PASS checks=%d GL=0x%x\n",checks,glGetError());return true;
}
}
