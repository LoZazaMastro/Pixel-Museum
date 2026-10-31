#pragma once
#include "host/behavior.hpp"
namespace museum {
inline bool ScreenInspection::verify_culture_filters(Screen&s){
    const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"Culture filters: %s\n",why);return ok;};
    s.onboarding_=s.language_choice_=s.theme_choice_=s.settings_=s.credits_=s.year_guide_=s.detail_=s.gallery_=s.screening_=s.object_inspect_=s.experience_active_=false;
    s.panel_.snap(0);s.year_panel_.snap(0);s.history_focus_=false;s.filter_=s.culture_filter_=0;s.rebuild_history_filter();s.rebuild(false);
    if(!require(!s.visible_.empty()&&!s.history_catalog_all_.entries.empty(),"both collections loaded"))return false;
    hui::ui::Feedback f;s.change_filter(2,f);const int source_year=s.current()->year;s.focus_history(true);
    if(!require(s.history_focus_&&!s.filter_&&!s.culture_filter_,"switch to culture resets both filters"))return false;
    const bool common=std::any_of(s.history_catalog_.entries.begin(),s.history_catalog_.entries.end(),[&](const Entry&e){return e.year==source_year;});
    if(!require(!common||s.current()->year==source_year,"switch keeps the source year when available"))return false;
    s.boot_time_=5;s.history_transition_=false;s.fade_=1;
    hui::InputFrame input;input.connected=true;s.filter_trigger_down_.fill(false);input.trigger_r=.8f;s.handle(input,f);
    if(!require(s.culture_filter_==1,"R2 changes the culture category"))return false;
    input={};input.connected=true;s.handle(input,f);input.trigger_l=.8f;s.handle(input,f);
    if(!require(s.culture_filter_==0,"L2 returns culture to All"))return false;
    for(int category=1;category<=8;++category){
        s.change_filter(category-s.culture_filter_,f);
        if(!require(!s.history_catalog_.entries.empty(),"each curated category contains stops"))return false;
        const auto expected=s.current()->culture_category;
        if(!require(std::all_of(s.history_catalog_.entries.begin(),s.history_catalog_.entries.end(),[&](const Entry&e){return e.culture_category==expected;}),"filtered view contains one category only"))return false;
        const int before=s.history_focus_index_;s.move_history(1,f);
        if(!require(s.history_focus_index_==std::min(before+1,int(s.history_catalog_.entries.size())-1),"navigation uses the filtered view"))return false;
    }
    const auto id=s.current()->id;const int today_before=s.today_cursor_[1];input={};input.connected=true;input.pressed=hui::action_bit(hui::Action::north);s.handle(input,f);
    if(!require(!s.culture_filter_&&s.current()->id==id&&s.today_cursor_[1]==today_before,"triangle resets All without jumping to Today"))return false;
    const auto dated=std::find_if(s.history_catalog_.entries.begin(),s.history_catalog_.entries.end(),[](const Entry&e){return e.month>0&&e.day>0;});
    if(!require(dated!=s.history_catalog_.entries.end(),"culture contains a dated stop"))return false;
    s.set_today_date(2026,dated->month,dated->day);s.handle(input,f);
    if(!require(s.today_cursor_[1]==0&&s.current()->month==dated->month&&s.current()->day==dated->day,"triangle on All preserves Today cycling"))return false;
    s.change_filter(4,f);const int culture_year=s.current()->year;s.focus_history(false);
    if(!require(!s.history_focus_&&!s.filter_&&!s.culture_filter_,"switch back resets both filters"))return false;
    const bool game_year=std::any_of(s.visible_.begin(),s.visible_.end(),[&](int n){return s.catalog_.entries[size_t(n)].year==culture_year;});
    if(!require(!game_year||s.current()->year==culture_year,"switch back keeps the comparable year"))return false;
    s.history_transition_=false;s.fade_=1;s.change_filter(2,f);const auto game=s.current()->id;s.handle(input,f);
    if(!require(!s.filter_&&s.current()->id==game,"game triangle also resets All at the same stop"))return false;
    for(const auto&pair:std::array<std::pair<const char*,const char*>,5>{{{"en","All"},{"it","Tutto"},{"es","Todo"},{"fr","Tout"},{"de","Alles"}}}){
        i18n::load(s.root_,pair.first);if(!require(std::string(i18n::tr("All"))==pair.second,"All is translated naturally in every UI locale"))return false;
    }
    i18n::load(s.root_,s.language_);std::printf("Culture filters PASS: categories, L2/R2, filtered navigation, both resets, Today, five locales.\n");return true;
}
}
