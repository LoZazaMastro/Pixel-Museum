// Production screen interaction checks, with a current GL context.
#pragma once
#include "museum/screen.hpp"
#include "museum/general_credits.hpp"
#include "core/save_file.hpp"
#include <cstdio>
namespace museum {
struct ScreenInspection {
    static bool verify_culture_filters(Screen&);
    static void onboarding_structure_state(Screen&s,const char*locale,int step){
        s.language_=locale;s.apply_language();i18n::load(".",locale);
        s.onboarding_=true;s.onboarding_leaving_=false;s.onboarding_complete_=false;s.onboarding_fade_.snap(1);s.language_choice_=step==-2;s.theme_choice_=step==-1||step==-3||step==-4;s.theme_confirming_=step==-3||step==-4;s.theme_confirm_progress_=(step==-3||step==-4)?.5f:0;if(step==-4){s.dark_theme_=true;s.theme_selection_.snap(0);}
        s.onboarding_step_=std::max(0,step);s.onboarding_position_.snap(float(s.onboarding_step_));s.settings_=s.credits_=s.year_guide_=false;s.panel_.snap(0);s.year_panel_.snap(0);s.pin_onboarding_time_=3.8f;s.reduced_=false;
    }
    static bool onboarding_pin_ready(Screen&s){return s.cache_.get("museum-pin:first_pin_3d-colour").texture!=0;}
    static void onboarding_pin_frame(Screen&s,float seconds,bool reduced){onboarding_structure_state(s,"it",3);s.pin_onboarding_time_=seconds;s.reduced_=reduced;}
    static bool verify_onboarding_structure(Screen&s,bool saved){
        const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"Intro structure: %s\n",why);return ok;};
        onboarding_structure_state(s,"en",-1);s.dark_theme_=false;s.theme_selection_.snap(1);
        hui::InputFrame input;input.connected=true;input.pressed=hui::action_bit(hui::Action::confirm);hui::ui::Feedback feedback;s.handle(input,feedback);
        if(!require(s.theme_confirming_&&s.theme_choice_&&s.onboarding_active(),"theme confirmation starts fullscreen expansion"))return false;
        for(int n=0;n<12;++n)s.update(1.f/60);if(!require(s.theme_choice_&&s.theme_confirm_progress_>0&&s.theme_confirm_progress_<1,"theme expansion is visible before advancing"))return false;
        for(int n=0;n<24;++n)s.update(1.f/60);if(!require(!s.theme_choice_&&!s.theme_confirming_&&s.onboarding_step_==0,"completed expansion opens the first intro page"))return false;
        onboarding_structure_state(s,"en",-1);s.reduced_=true;s.handle(input,feedback);if(!require(!s.theme_choice_&&!s.theme_confirming_,"reduced motion confirms without animation delay"))return false;
        onboarding_structure_state(s,"en",5);const auto connection=s.video_.connection();if(!require(connection.saved==saved,"isolated saved-access fixture matches actual backend metadata"))return false;
        s.handle(input,feedback);
        if(saved){if(!require(s.onboarding_step_==6,"saved access X continues without reconnecting"))return false;onboarding_structure_state(s,"en",5);input.pressed=hui::action_bit(hui::Action::west);s.handle(input,feedback);if(!require(s.onboarding_step_==5,"saved access square reconnects without advancing"))return false;}
        else{if(!require(s.onboarding_step_==5,"without saved access X offers connection without skipping"))return false;input.pressed=hui::action_bit(hui::Action::west);s.handle(input,feedback);if(!require(s.onboarding_step_==6,"without saved access square skips"))return false;}
        std::puts("PASS theme expand/snap and explicit saved-access Continue versus Reconnect onboarding semantics.");return true;
    }
    static bool trophy_feedback_image_ready(Screen&s){const auto all=s.trophies_->views(true);return s.cache_.get("museum-pin:"+all[size_t(s.trophy_focus_)].badge+"-colour").texture!=0;}
    static bool actual_native_only_trophy_preview(Screen&s){
        i18n::load(".",s.language_); // Current source UI maps, staged media remains offline.
        s.settings_=s.year_guide_=s.detail_=s.trophy_pin_open_=false;s.year_panel_.snap(0);s.trophy_fallback_queue_.clear();s.trophy_fallback_time_=0;s.trophy_fallback_sound_=false;
        if(!s.trophies_->reset()||!s.trophies_->zoomMaximum())return false;
        s.update_trophies();s.update_trophies();return s.trophy_fallback_time_==0&&s.trophy_fallback_queue_.empty()&&!s.take_trophy_sound();
    }
    static bool actual_native_only_trophy_ready(Screen&s){return s.trophy_fallback_time_==0&&s.trophy_fallback_queue_.empty()&&!s.take_trophy_sound();}
    static bool trophy_feedback_preview(Screen&s,int mode){
        s.onboarding_=s.language_choice_=s.theme_choice_=false;s.boot_time_=5;s.settings_=s.credits_=s.search_page_=false;s.panel_.snap(0);
        s.year_guide_=true;s.guide_trophies_=true;s.guide_experiences_=false;s.year_panel_.snap(1);s.trophy_pin_open_=false;
        s.trophy_curator_preview_=mode!=3;s.trophy_expanded_=mode==2;
        const auto all=s.trophies_->views(true);if(all.empty()||all.size()!=s.trophies_->definitions().size())return false;
        int secret=-1;for(size_t n=0;n<all.size();++n){if(all[n].badge=="secret_09"||all[n].badge=="pin_reverse")return false;if(all[n].secret&&secret<0)secret=int(n);if(all[n].id=="museum_vip_club"&&all[n].target!=all.size()-1)return false;}
        s.trophy_focus_=mode==0?0:mode==4?int(all.size()-1):secret;s.trophy_position_.snap(float(s.trophy_focus_));
        if(mode==5){s.guide_trophies_=false;s.guide_experiences_=true;s.guide_mode_.snap(1);s.experience_focus_=0;s.experience_position_.snap(0);}
        if(mode==6||mode==7){s.year_guide_=false;s.year_panel_.snap(0);s.settings_=mode==6;s.credits_=mode==7;s.panel_.snap(1);s.credits_open_.snap(mode==7?1:0);s.setting_=general_credits_setting;s.focus_line_.snap(240+general_credits_setting*68);s.credits_scroll_.snap(0);}
        if(mode==8){s.year_guide_=false;s.year_panel_.snap(0);s.trophy_fallback_time_=0;s.trophy_fallback_sound_=false;}
        return secret>=0;
    }
    static bool verify_trophy_pin_motion_haptics(Screen&s){
        const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"Pin haptics: %s\n",why);return ok;};
        trophy_feedback_preview(s,1);s.trophies_->zoomMaximum();const auto pins=s.trophies_->views(true);for(size_t n=0;n<pins.size();++n)if(pins[n].unlocked){s.trophy_focus_=int(n);break;}s.trophies_->drainUnlocks();s.trophy_pin_open_=true;s.trophy_pin_yaw_=s.trophy_pin_pitch_=0;s.trophy_pin_zoom_=1;s.trophy_pin_haptic_wait_=0;s.dt_=1.f/60;
        hui::InputFrame i;i.connected=true;hui::ui::Feedback f;
        s.handle(i,f);if(!require(f.tactile.empty(),"rest has no movement pulse"))return false;
        i.stick2_x=.6f;f={};s.handle(i,f);
        if(!require(f.tactile.size()==1&&s.trophy_pin_yaw_>0,"accepted rotation gives one tactile event"))return false;
        f={};s.handle(i,f);if(!require(f.tactile.empty(),"rotation pulse is rate limited"))return false;
        int pulses=0;for(int n=0;n<30;++n){f={};s.handle(i,f);pulses+=int(f.tactile.size());}
        if(!require(pulses>=4&&pulses<=7,"sustained rotation is felt without per-frame vibration"))return false;
        i.stick2_x=0;f={};s.handle(i,f);if(!require(f.tactile.empty(),"release stops pulses"))return false;
        i.trigger_r=.8f;f={};s.handle(i,f);if(!require(f.tactile.size()==1&&s.trophy_pin_zoom_>1,"accepted zoom has immediate feedback"))return false;
        i.trigger_r=1;i.stick2_y=1;s.trophy_pin_zoom_=2.6f;s.trophy_pin_pitch_=1.1f;s.trophy_pin_haptic_wait_=0;
        f={};s.handle(i,f);if(!require(f.tactile.empty(),"held zoom and pitch at clamp have no fictitious movement"))return false;
        i.trigger_r=0;i.stick2_y=0;i.trigger_l=1;f={};s.handle(i,f);
        if(!require(f.tactile.size()==1&&s.trophy_pin_zoom_<2.6f,"reverse zoom moves away from clamp with feedback"))return false;
        i.focus_lost=true;f={};s.handle(i,f);if(!require(f.tactile.empty()&&s.trophy_pin_haptic_wait_==0,"focus loss clears motion feedback"))return false;
        i.focus_lost=false;i.connected=false;f={};s.handle(i,f);if(!require(f.tactile.empty(),"disconnected controller is silent"))return false;
        s.trophy_pin_open_=false;std::puts("PASS actual pin rotation/zoom haptics, rate limit, rest, clamps and focus loss.");return true;
    }
    static bool verify_trophy_awards_feedback(Screen&s){
        const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"Trophy/awards feedback: %s\n",why);return ok;};
        static constexpr const char*months[]={"January","February","March","April","May","June","July","August","September","October","November","December"};
        for(const char*lang:{"en","it","es","fr","de"}){i18n::load(s.root_,lang);for(int month=1;month<=12;++month){s.set_today_date(2026,month,26);std::string expected(i18n::tr(months[month-1]));if(!expected.empty()&&expected[0]>='a'&&expected[0]<='z')expected[0]=char(expected[0]-'a'+'A');if(!require(s.today_date_label().find(expected)!=std::string::npos,"all60 localized month labels retain spelling and uppercase month initial"))return false;}}
        s.language_="it";s.apply_language();
        if(!trophy_feedback_preview(s,1))return require(false,"current definitions, first pin3D replaces pin reverse and ultimate excludes itself");
        const auto private_views=s.trophies_->views();const auto curator=s.trophies_->views(true);
        const std::string reset_path="build/preview-data/trophy-reset-regression.dat";std::remove(reset_path.c_str());std::remove((reset_path+".bak").c_str());
        Trophies reset(reset_path);if(!require(reset.load(),"fresh reset fixture loads"))return false;reset.setDefinitions(s.trophies_->definitions());reset.setEligibleCatalogSnapshot({"one","two"});
        reset.visit("one");reset.musicProgress("first",12);const auto secret_definition=std::find_if(reset.definitions().begin(),reset.definitions().end(),[](const auto&d){return d.secret;});if(secret_definition==reset.definitions().end())return false;reset.card(secret_definition->owner_id,secret_definition->card_index);reset.drainUnlocks();
        if(!require(reset.reset()&&reset.visitedCount()==0&&reset.drainUnlocks().empty(),"atomic reset clears visits, unlocks and pending events"))return false;
        for(const auto&v:reset.views(true)){if(!require(!v.unlocked&&v.current==0,"reset clears all progress"))return false;if(v.id=="all_catalog"&&!require(v.target==2,"eligible snapshot retained"))return false;}
        const auto sic_unlocked=[&](){for(const auto&v:reset.views(true))if(v.badge=="secret_04")return v.unlocked;return false;};
        reset.card("wikipedia-5561698",0);
        if(!require(!sic_unlocked(),"Drake's Fortune no longer awards Sic parvis magna"))return false;
        reset.card("workbook-05-10-uncharted-4-a-thief-s-end",0);
        if(!require(sic_unlocked(),"Uncharted 4 story card one awards Sic parvis magna"))return false;
        if(!require(reset.reset(),"secret-owner test fixture is reset before reload"))return false;
        Trophies reloaded(reset_path);reloaded.load();reloaded.setDefinitions(reset.definitions());if(!require(reloaded.visitedCount()==0&&reloaded.musicProgress("again",12)&&!reloaded.drainUnlocks().empty(),"fresh reset persists and can unlock again"))return false;
        for(size_t n=0;n<curator.size();++n){if(curator[n].title.empty()||curator[n].description.empty())return require(false,"every curator row has actual text");if(curator[n].secret&&!curator[n].unlocked&&!require(private_views[n].title.empty(),"default backend secret redaction preserved"))return false;}
        hui::ui::Feedback f;hui::InputFrame i;i.connected=true;
        for(size_t row=0;row<curator.size();++row){s.trophy_focus_=int(row);s.trophy_expanded_=false;i.pressed=hui::action_bit(hui::Action::confirm);s.handle(i,f);if(!require(s.trophy_expanded_==curator[size_t(row)].secret,"X reveals only secret requirements at every list position"))return false;i.pressed=0;}
        const auto language=s.language_;const bool dark=s.dark_theme_,muted=s.muted_,reduced=s.reduced_;const float volume=s.volume_;
        s.year_guide_=false;s.year_panel_.snap(0);s.settings_=true;s.setting_=reset_trophies_setting;i.pressed=hui::action_bit(hui::Action::confirm);s.handle(i,f);i.pressed=0;
        if(!require(s.trophies_->visitedCount()==0&&s.language_==language&&s.dark_theme_==dark&&s.muted_==muted&&s.reduced_==reduced&&s.volume_==volume,"actual reset row preserves every other preference"))return false;
        s.settings_=false;s.year_guide_=true;s.guide_trophies_=true;s.year_panel_.snap(1);s.trophy_pin_open_=false;s.trophies_->drainUnlocks();
        i.pressed=hui::action_bit(hui::Action::north);s.handle(i,f);i.pressed=0;
        if(!require(!s.trophy_pin_open_&&s.trophies_->drainUnlocks().empty(),"locked pin blocks triangle and does not award 3D inspection"))return false;
        s.trophies_->zoomMaximum();const auto unlocked_pins=s.trophies_->views(true);for(size_t n=0;n<unlocked_pins.size();++n)if(unlocked_pins[n].unlocked){s.trophy_focus_=int(n);break;}s.trophies_->drainUnlocks();
        i.pressed=hui::action_bit(hui::Action::north);s.handle(i,f);i.pressed=0;
        if(!require(s.trophy_pin_open_,"actual triangle opens 3D inspection"))return false;
        const auto first_open=s.trophies_->drainUnlocks();if(!require(first_open.size()==1&&first_open[0].id=="first_pin_3d","first actual 3D opening awards new trophy once"))return false;
        i.pressed=hui::action_bit(hui::Action::north);s.handle(i,f);s.handle(i,f);i.pressed=0;
        if(!require(s.trophy_pin_open_&&s.trophies_->drainUnlocks().empty(),"reopening inspection neither duplicates award nor requires reverse rotation"))return false;
        s.trophy_pin_open_=false;
        // A native API accepting the same unlock without a fallback event must
        // must never create an in-app badge or sound.
        if(!require(s.trophies_->reset(),"native-only regression reset"))return false;
        s.trophy_fallback_queue_.clear();s.trophy_fallback_time_=0;s.trophy_fallback_sound_=false;s.trophy_notifications_.clearPending();
        s.history_focus_=false;s.detail_=false;s.year_guide_=false;s.settings_=false;
        s.trophy_fallback_current_={};
        s.trophies_->zoomMaximum();TrophyUnlock accepted;
        for(const auto&v:s.trophies_->views(true))if(v.unlocked){accepted={v.id,v.title,v.description,v.badge,v.rank,v.unlocked_at};break;}
        setenv("MUSEUM_HOST_TROPHY_NATIVE_ACCEPT","1",1);s.update_trophies();s.update_trophies();
        if(!require(s.trophy_notifications_.pollFallback().empty()&&s.trophy_fallback_queue_.empty()&&s.trophy_fallback_time_==0&&!s.take_trophy_sound(),"native accepted mock does not duplicate a local badge or local sound"))return false;
        unsetenv("MUSEUM_HOST_TROPHY_NATIVE_ACCEPT");
        if(!require(s.trophies_->reset()&&s.trophies_->zoomMaximum(),"fresh persisted unlock after reset"))return false;
        s.trophy_notifications_.clearPending();s.update_trophies();
        s.update_trophies();
        if(!require(s.trophy_fallback_queue_.empty()&&s.trophy_fallback_time_==0&&!s.take_trophy_sound(),"explicit native failure remains log-only without local overlay or audio"))return false;
        if(!require(!s.trophy_notifications_.submit(accepted,"/host.png"),"persisted unlock is submitted to native transport once only"))return false;
        s.trophy_notifications_.clearPending();s.trophy_notifications_.submit(accepted,"/host.png");s.update_trophies();
        if(!require(s.trophy_fallback_queue_.empty()&&s.trophy_fallback_time_==0&&!s.take_trophy_sound(),"late native failures remain log-only without local overlay or audio"))return false;
        s.year_panel_.snap(0);s.settings_=true;s.setting_=reset_trophies_setting;i.pressed=hui::action_bit(hui::Action::confirm);s.handle(i,f);i.pressed=0;
        if(!require(s.trophy_fallback_queue_.empty()&&s.trophy_fallback_time_==0&&!s.take_trophy_sound(),"actual reset cancels queued/current presentation and pending sound"))return false;
        s.settings_=false;
        s.year_guide_=false;s.guide_trophies_=false;s.select("the-game-awards-2024");s.detail_=true;s.prepare_story();
        int annual=0;bool own=false;for(const auto&c:s.story_cards_)if(c.paragraph>=0&&c.feature<0){++annual;if(!require(c.continuation.empty(),"annual award chapters retain their authored boundaries"))return false;if(c.paragraph==1){own=c.image>=0;s.story_focus_=int(&c-s.story_cards_.data());}}
        if(!require(s.current()->body.size()==2&&s.current()->videos.size()==1&&annual==2&&own,"selected2024 edition has its explanation, its illustrated winners and only its own ceremony"))return false;
        std::puts("PASS71 trophies/allrowX semantics/default secret redaction/ultimate70 and selected-edition TGA chapters.");return true;
    }
    static bool verify_main_chapter_boundaries(Screen&s){
        const auto require=[](bool passed,const char*message){if(!passed)std::fprintf(stderr,"Chapter boundary check failed: %s\n",message);return passed;};
        s.onboarding_=false;s.history_focus_=false;s.settings_=false;
        for(const auto&item:std::vector<std::pair<const char*,size_t>>{{"brown-box",6},{"space-invaders",5},{"the-game-awards-2024",2}}){
            s.select(item.first);s.detail_=true;s.prepare_story();
            const auto*entry=s.current();if(!require(entry&&entry->id==item.first&&entry->body.size()>=item.second,"production article meets its chapter minimum"))return false;
            std::vector<int> seen(entry->body.size(),0);
            for(const auto&card:s.story_cards_)if(card.feature<0&&card.paragraph>=0){
                if(!require(size_t(card.paragraph)<seen.size()&&card.continuation.empty(),"each main chapter remains independently navigable"))return false;
                ++seen[size_t(card.paragraph)];
            }
            if(!require(std::all_of(seen.begin(),seen.end(),[](int count){return count==1;}),"no main chapter is hidden, duplicated or merged"))return false;
            std::printf("Chapter boundaries: %s, %zu independent chapters\n",item.first,seen.size());
        }
        return true;
    }
    static bool verify_today_header(Screen&,unsigned,int,int);
    static bool history_preview(Screen&s,bool active,int year=1989){
        s.reduced_=false;s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.year_guide_=false;s.year_panel_.snap(0);s.settings_=s.credits_=false;s.panel_.snap(0);s.preview(0);s.select("game-boy");
        if(s.history_catalog_.entries.empty()){std::fputs("History preview requires the real history catalogue\n",stderr);return false;}
        int nearest=0;for(size_t n=0;n<s.history_catalog_.entries.size();++n)if(std::abs(s.history_catalog_.entries[n].year-year)<std::abs(s.history_catalog_.entries[size_t(nearest)].year-year))nearest=int(n);
        if(active)s.focus_history(true);
        s.history_focus_index_=nearest;s.history_position_.snap(float(nearest));
        s.warm_history();return true;
    }
    static bool verify_history(Screen&s){
        Entry feb,march;feb.year=march.year=1900;feb.month=2;feb.day=28;march.month=3;march.day=1;
        if(chronology_day(march)-chronology_day(feb)!=1)return false;
        feb.year=march.year=2000;if(chronology_day(march)-chronology_day(feb)!=2)return false;
        if(!history_preview(s,false))return false;
        hui::ui::Feedback feedback;hui::InputFrame input;input.connected=true;
        const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"History check failed: %s\n",message);return pass;};
        const std::string game=s.current()->id;const int focus=s.focus_;
        input.nav=hui::Direction::down;s.handle(input,feedback);
        if(!require(!s.detail_,"Down does not open an article"))return false;
        input.nav=hui::Direction::up;s.handle(input,feedback);
        if(!require(s.history_focus_&&s.current()->kind=="history"&&!s.detail_,"Up focuses the separate historical route"))return false;
        const auto&game_entry=s.catalog_.entries[size_t(s.visible_[size_t(focus)])];
        const int game_day=chronology_day(game_entry),history_distance=std::abs(chronology_day(*s.current())-game_day);
        for(const auto&e:s.history_catalog_.entries)if(!require(std::abs(chronology_day(e)-game_day)>=history_distance,"Up chooses the nearest cultural date, including month and day"))return false;
        for(unsigned n=0;n<90;++n)s.update(1.f/60);
        s.open_year_guide();s.guide_experiences_=false;
        if(!require(s.history_focus_&&!s.years_.empty()&&s.years_.front()==1833,"culture year atlas preserves its route and includes pre-gaming years"))return false;
        s.year_focus_=0;input.nav=hui::Direction::none;input.pressed=hui::action_bit(hui::Action::confirm);s.handle(input,feedback);input.pressed=0;
        if(!require(s.history_focus_&&s.current()->year==1833&&s.focus_==focus,"year atlas reaches the first historical event without changing the game"))return false;
        if(!require(s.selected_year()==1833.f,"the ambient soundtrack receives the pre-recording historical year"))return false;
        s.year_panel_.snap(0);for(unsigned n=0;n<90;++n)s.update(1.f/60);
        const int history=s.history_focus_index_;input.nav=history+1<int(s.history_catalog_.entries.size())?hui::Direction::right:hui::Direction::left;s.handle(input,feedback);
        if(!require(s.history_focus_index_!=history&&s.focus_==focus,"historical browsing preserves the game selection"))return false;
        input.nav=hui::Direction::none;input.pressed=hui::action_bit(hui::Action::west);s.handle(input,feedback);
        if(!require(s.gallery_&&s.history_focus_,"Square opens the selected historical image"))return false;
        const int culture_day=chronology_day(*s.current());
        s.gallery_=false;s.gallery_open_.snap(0);input.pressed=0;input.nav=hui::Direction::down;s.handle(input,feedback);
        if(!require(!s.history_focus_&&s.current()->id!=game,"Down from the nineteenth century moves to an early game instead of the old Game Boy selection"))return false;
        const int game_distance=std::abs(chronology_day(*s.current())-culture_day);
        for(int id:s.visible_)if(!require(std::abs(chronology_day(s.catalog_.entries[size_t(id)])-culture_day)>=game_distance,"Down chooses the nearest gaming date"))return false;
        if(!require(s.selected_year()==float(s.current()->year),"returning to play restores the game's musical year"))return false;
        for(unsigned n=0;n<90;++n)s.update(1.f/60);
        input.nav=hui::Direction::none;input.pressed=hui::action_bit(hui::Action::confirm);s.handle(input,feedback);
        if(!require(s.detail_,"X opens the game article"))return false;
        s.preview(0);std::puts("Double timeline: bidirectional nearest-date transfer, independent browsing, Square photo and X article passed");return true;
    }
    static bool verify_startup_compositor(Screen&,unsigned,int,int);
    static bool verify_alpha_images(Screen&,unsigned,int,int);
    static bool verify_photo_feedback(Screen&,unsigned,int,int);
    static bool verify_sayonara_reading(Screen&,unsigned,int,int);
    static bool verify_ninth_scoped(Screen&,unsigned,int,int);
    static bool verify_tenth_scoped(Screen&,unsigned,int,int);
    static bool verify_eleventh_scoped(Screen&,unsigned,int,int);
    static bool verify_twelfth_scoped(Screen&,unsigned,int,int);
    static bool preview_ps1_presentations(Screen&,unsigned,int,int);
    static bool preview_console_cutouts(Screen&,unsigned,int,int,int);
    static bool verify_model_stage_1080(Screen&,unsigned,int,int);
    static bool verify_timeline_pause(Screen&,unsigned,int,int);
    static bool verify_timeline_symbols(Screen&,unsigned,int,int);
    static bool verify_culture_staged(Screen&,unsigned,int,int);
    static bool verify_playlist(Screen&,unsigned,int,int);
    static bool verify_model_transitions(Screen&,unsigned,int,int);
    static bool verify_experiences(Screen&,unsigned,int,int);
    static bool verify_experience_focus(Screen&,unsigned,int,int);
    static bool verify_captions(Screen&,unsigned,int,int);
    static bool verify_feature_cards(Screen&,unsigned,int,int);
    static bool verify_story_scenes(Screen&);
    static bool verify_story_reading(Screen&,unsigned,int,int);
    static bool verify_story_scrollbar(Screen&,unsigned,int,int);
    static bool profile_story_text(Screen&);
    static bool verify_story_distribution(Screen&);
    static bool verify_ui_action_haptics(Screen&);
    static bool verify_timeline_input_today(Screen&);
    static bool verify_arcade_cage_visual(Screen&,unsigned,int,int);
    static bool verify_experience_completion(Screen&,unsigned,int,int);
    static bool verify_ui_locales(Screen&,unsigned,int,int);
    static bool verify_general_credits(Screen&,unsigned,int,int);
    static bool verify_unicode_fonts(Screen&,unsigned,int,int);
    static bool verify_catalog_aliases(Screen&);
    static bool verify_search(Screen&);
    static int illustrated_story_preview(Screen&s,const char*id,int focus){
        // Select a real card directly, with no first-visit sheet covering it.
        s.onboarding_=s.onboarding_leaving_=false;s.language_choice_=s.theme_choice_=false;
        s.settings_=s.credits_=s.connection_panel_=false;s.boot_time_=5;s.boot_note_=13;
        if(!s.current()||s.current()->id!=id)s.select(id);
        s.preview(1);
        const auto*entry=s.current();if(!entry)return -1;
        std::vector<bool> illustrated(entry->body.size(),false);
        std::vector<int> pictures,illustrated_media;
        for(const auto&card:s.story_cards_){
            if(card.kind!=Screen::StoryCard::narrative&&card.kind!=Screen::StoryCard::film)continue;
            // Standalone supplemental films do not own a prose paragraph.
            // They remain capture targets without invalidating body coverage.
            if(card.paragraph<0)continue;
            if(card.image<0)return -1;
            if(std::find(illustrated_media.begin(),illustrated_media.end(),card.image)!=illustrated_media.end())return -1;
            illustrated_media.push_back(card.image);
            if(card.kind==Screen::StoryCard::narrative)pictures.push_back(card.image);
            illustrated[size_t(card.paragraph)]=true;
            for(int paragraph:card.continuation)illustrated[size_t(paragraph)]=true;
        }
        if(std::find(illustrated.begin(),illustrated.end(),false)!=illustrated.end())return -1;
        const int count=int(s.story_cards_.size());
        if(focus<0||focus>=count)return count;
        s.story_focus_=focus;s.story_position_.snap(float(focus));s.story_open_.snap(1);
        std::printf("Illustrated story %s: %zu paragraphs, %zu narrative photographs, %d cards; selected %d\n",id,entry->body.size(),pictures.size(),count,focus);
        return count;
    }
    static bool story_photo_ready(const Screen&s){
        if(s.story_cards_.empty()||!s.current())return false;
        if(s.story_cards_[size_t(s.story_focus_)].kind==Screen::StoryCard::object)
            return s.object_.ready()&&s.object_texture_!=0;
        const int photo=s.story_cards_[size_t(s.story_focus_)].image;
        return photo<0||s.cache_.get(s.current()->images[size_t(photo)].url).texture!=0;
    }
    static bool story_photo_evidence(const Screen&s){
        if(s.story_cards_.empty()||!s.current())return false;
        const auto&card=s.story_cards_[size_t(s.story_focus_)];
        if(card.image<0)return false;
        const auto&image=s.current()->images[size_t(card.image)];
        const auto asset=s.cache_.get(image.url);
        if(!asset.texture||!glIsTexture(asset.texture))return false;
        GLint width=0,height=0;glBindTexture(GL_TEXTURE_2D,asset.texture);
        glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&width);
        glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_HEIGHT,&height);
        const auto error=glGetError();
        std::printf("Story resident evidence: entry=%s card=%d image=%d texture=%u resident=%dx%d asset=%dx%d GL=0x%x URL=%s\n",s.current()->id.c_str(),s.story_focus_,card.image,asset.texture,width,height,asset.width,asset.height,error,image.url.c_str());
        return width>0&&height>0&&width==asset.width&&height==asset.height&&error==GL_NO_ERROR;
    }
    static void search_keyboard_preview(Screen&s){hui::ui::Feedback feedback;s.open_search(feedback);}
    static bool focus_feature(Screen&s,const char*identifier,int paragraph){
        s.preview(1);
        for(size_t n=0;n<s.story_cards_.size();++n){
            const auto&card=s.story_cards_[n];
            if(card.feature>=0&&(card.paragraph==paragraph||std::find(card.continuation.begin(),card.continuation.end(),paragraph)!=card.continuation.end())&&s.current()
                    &&s.current()->editorial_features[size_t(card.feature)].id==identifier){
                s.story_focus_=int(n);s.story_position_.snap(float(n));s.story_open_.snap(1);return true;
            }
        }
        return false;
    }
    static void experience_preview(Screen&,int,int=0);
    static void today(Screen&s){hui::ui::Feedback feedback;s.jump_today(feedback);s.timeline_.snap(float(s.focus_));}
    static void freeze_object(Screen&s){const auto*e=s.current();s.reduced_=true;s.object_angle_=e&&!e->models.empty()?e->models[0].initial_angle:0;}
    static void preview_time(Screen&s,float time){s.time_=time;}
    static bool object_ready(const Screen&s){return s.object_texture_!=0;}
    static void design_year_atlas(Screen&s){s.open_year_guide();s.year_panel_.snap(1);s.year_position_.snap(float(s.year_focus_));}
    static bool design_preview(Screen&s,int mode){
        s.language_choice_=s.theme_choice_=false;s.onboarding_=false;s.onboarding_leaving_=false;s.settings_=s.credits_=s.connection_panel_=false;
        s.year_guide_=false;s.year_panel_.snap(0);s.workshop_active_=false;s.preview(0);s.boot_time_=5;s.boot_note_=13;
        if(mode<3||mode==5||mode==6){s.onboarding_=true;s.onboarding_step_=mode==2?s.onboarding_cards_:mode==5?2:mode==6?4:mode;s.onboarding_position_.snap(float(s.onboarding_step_));s.onboarding_fade_.snap(1);s.boot_time_=0;s.boot_note_=0;return true;}
        s.select("game-boy");
        if(mode==3)return true;
        s.preview(1);
        for(size_t n=0;n<s.story_cards_.size();++n)if(s.story_cards_[n].kind==Screen::StoryCard::interactive){s.story_focus_=int(n);s.story_position_.snap(float(n));s.workshop_active_=true;return true;}
        std::fputs("Design preview requires Game Boy's real interactive study card\n",stderr);return false;
    }
    static int onboarding_card_count(){return Screen::onboarding_cards_;}
    static void reordered_options_preview(Screen&s){
        s.onboarding_=s.onboarding_leaving_=s.language_choice_=s.theme_choice_=false;
        s.connection_panel_=false;s.boot_time_=5;s.boot_note_=13;s.preview(4);s.panel_.snap(1);s.setting_=0;s.focus_line_.snap(240);s.fade_=1;
    }
    static bool localized_onboarding_preview(Screen&s,const char*locale,int step){
        if(step<0||step>s.onboarding_cards_)return false;
        s.language_=locale;s.apply_language();
        if(!design_preview(s,0))return false;
        s.onboarding_step_=step;s.onboarding_position_.snap(float(step));return true;
    }
    static bool verify_scene(Screen&s,unsigned framebuffer,int width,int height);
    static bool verify_first_visit(Screen&s){
        const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"First-visit check failed: %s\n",message);return pass;};
        const auto original_data=s.data_,original_initial=s.initial_exhibit_;
        const bool original_language_choice=s.language_choice_,original_language_chosen=s.language_chosen_,original_theme_choice=s.theme_choice_,original_theme_chosen=s.theme_chosen_,original_dark=s.dark_theme_;
        const auto original_theme_mix=s.theme_mix_;const auto original_language=s.language_;
        const bool original_onboarding=s.onboarding_,original_complete=s.onboarding_complete_,original_leaving=s.onboarding_leaving_,original_dirty=s.dirty_;
        const int original_step=s.onboarding_step_,original_note=s.boot_note_,original_setting=s.setting_;
        const float original_boot=s.boot_time_,original_delay=s.save_delay_;
        const auto original_position=s.onboarding_position_,original_fade=s.onboarding_fade_;
        hui::ui::Feedback feedback;
        const auto press=[&](hui::Action action){hui::InputFrame input;input.connected=true;input.pressed=hui::action_bit(action);s.handle(input,feedback);};
        const auto finish=[&](bool result){s.language_choice_=original_language_choice;s.language_chosen_=original_language_chosen;s.theme_choice_=original_theme_choice;s.theme_chosen_=original_theme_chosen;s.dark_theme_=original_dark;s.theme_mix_=original_theme_mix;s.language_=original_language;s.apply_language();s.data_=original_data;s.initial_exhibit_=original_initial;s.onboarding_=original_onboarding;s.onboarding_complete_=original_complete;s.onboarding_leaving_=original_leaving;s.onboarding_step_=original_step;s.onboarding_position_=original_position;s.onboarding_fade_=original_fade;s.dirty_=original_dirty;s.save_delay_=original_delay;s.boot_time_=original_boot;s.boot_note_=original_note;s.setting_=original_setting;s.settings_=false;return result;};
        // Production persistence is exercised in a separate test directory.
        // Never mark the actual preview or console preferences completed here.
        s.data_=original_data+"/first-visit-check";hui::save::ensure_directory(s.data_);
        s.onboarding_=true;s.onboarding_complete_=false;s.onboarding_leaving_=false;s.onboarding_step_=0;s.onboarding_position_.snap(0);s.onboarding_fade_.snap(1);s.boot_time_=0;s.boot_note_=0;
        s.language_choice_=true;s.language_chosen_=false;s.theme_choice_=true;s.theme_chosen_=false;s.dark_theme_=true;s.theme_mix_.snap(1);s.language_focus_=0;
        if(!require(s.colours().paper.r<.1f,"the first language screen starts dark"))return finish(false);
        press(hui::Action::confirm);
        if(!require(!s.language_choice_&&s.language_chosen_&&s.theme_choice_&&s.onboarding_step_==0,"language selection comes before appearance and the museum tour"))return finish(false);
        hui::InputFrame light;light.connected=true;light.nav=hui::Direction::right;s.handle(light,feedback);
        for(unsigned n=0;n<90;++n)s.update(1.f/60);
        if(!require(!s.dark_theme_&&s.colours().paper.r>.9f,"choosing Light fades the complete palette to light"))return finish(false);
        press(hui::Action::confirm);
        if(!require(s.theme_confirming_||s.reduced_,"appearance confirmation visibly expands the selected button"))return finish(false);
        for(unsigned n=0;n<40;++n)s.update(1.f/60);
        if(!require(!s.theme_choice_&&s.theme_chosen_&&s.onboarding_step_==0,"appearance confirmation starts the first tour card"))return finish(false);
        for(int n=1;n<s.onboarding_cards_;++n){press(hui::Action::confirm);if(!require(s.onboarding_step_==n&&s.onboarding_&&!s.onboarding_complete_,"tour confirmations reach optional YouTube without silently completing it"))return finish(false);}
        press(hui::Action::back);
        if(!require(s.onboarding_step_==s.onboarding_cards_-2,"previous returns from optional YouTube to the tour"))return finish(false);
        press(hui::Action::confirm);press(hui::Action::west);
        if(!require(s.onboarding_step_==s.onboarding_cards_,"dedicated Skip connection advances without authentication"))return finish(false);
        press(hui::Action::confirm);
        if(!require(s.onboarding_step_==s.onboarding_cards_&&s.onboarding_&&!s.onboarding_leaving_,"X cannot bypass the final Options prompt"))return finish(false);
        s.onboarding_step_=0;press(hui::Action::west);
        if(!require(s.onboarding_step_==s.onboarding_cards_-1&&s.onboarding_&&!s.onboarding_complete_&&!s.onboarding_leaving_,"Skip introduction still offers optional YouTube connection"))return finish(false);
        press(hui::Action::west);
        press(hui::Action::menu);
        if(!require(s.onboarding_leaving_&&s.onboarding_&&!s.onboarding_complete_,"Options begins the closing fade"))return finish(false);
        for(unsigned n=0;n<600&&s.onboarding_;++n)s.update(1.f/60);
        if(!require(!s.onboarding_&&s.onboarding_complete_&&s.boot_time_==0&&s.boot_note_==0,"completion starts the M introduction only after the tour fade"))return finish(false);
        s.save_settings();std::string preferences;
        if(!require(hui::save::read_file(s.data_+"/preferences.json",&preferences)&&preferences.find("\"onboarding_complete\":true")!=std::string::npos,"production preferences persist tour completion"))return finish(false);
        s.onboarding_=true;s.onboarding_complete_=false;s.load_settings();
        if(!require(!s.onboarding_&&s.onboarding_complete_&&s.theme_chosen_&&s.language_chosen_&&!s.dark_theme_,"a subsequent preferences load restores language and appearance and skips the completed tour"))return finish(false);
        s.boot_time_=5;s.boot_note_=13;press(hui::Action::menu);
        const std::array<const char*,8> expected_options={"Language","Appearance","Volumes","YouTube connection","Replay introduction","Remove downloaded data","Reset trophies","Credits"};
        if(!require(preference_labels==expected_options,"requested exact option order"))return finish(false);
        s.setting_=0;const auto previous_language=s.language_;press(hui::Action::confirm);
        if(!require(s.language_!=previous_language,"row0 changes language"))return finish(false);
        s.setting_=1;const bool previous_theme=s.dark_theme_;press(hui::Action::confirm);
        if(!require(s.dark_theme_!=previous_theme,"row1 changes appearance"))return finish(false);
        s.setting_=2;press(hui::Action::confirm);
        if(!require(s.volumes_open_,"row2 opens four independent volume sliders"))return finish(false);
        s.volume_focus_=2;const float previous_volume=s.volume_;hui::InputFrame quieter;quieter.connected=true;quieter.nav=hui::Direction::left;s.handle(quieter,feedback);
        if(!require(s.volume_==std::max(0.f,previous_volume-.05f),"ambient slider adjusts music volume"))return finish(false);s.volume_=previous_volume;press(hui::Action::back);
        if(!require(s.settings_&&!s.volumes_open_&&s.setting_==2,"submenu Back returns to Volumes row"))return finish(false);
        s.setting_=3;press(hui::Action::confirm);
        if(!require(s.connection_panel_,"row3 opens existing YouTube connection"))return finish(false);press(hui::Action::back);
        s.setting_=general_credits_setting;press(hui::Action::confirm);
        if(!require(s.credits_&&!s.settings_,"last row opens general credits"))return finish(false);press(hui::Action::back);
        s.setting_=4;press(hui::Action::confirm);
        if(!require(s.onboarding_&&s.onboarding_step_==0&&s.onboarding_complete_&&s.onboarding_fade_.value==0,"Replay introduction begins a fade without forgetting completion"))return finish(false);
        for(unsigned n=0;n<5;++n)s.update(1.f/60);
        if(!require(s.onboarding_fade_.value>0&&s.onboarding_fade_.value<1,"replay has an intermediate opening fade"))return finish(false);
        std::puts("First visit: language, appearance, four tour cards, optional YouTube/Previous/dedicated Skip connection, Skip introduction offers connection, Volumes submenu, persistence and reordered Replay row4 passed");
        return finish(true);
    }
    static bool cover_probe(Screen&s,const char*id){
        s.onboarding_=s.onboarding_leaving_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.connection_panel_=false;s.panel_.snap(0);
        s.select(id);s.preview(0);s.fade_=1;s.entry_snapshot_=false;s.history_transition_=false;
        s.dark_theme_=true;s.theme_mix_.snap(1);
        const auto*e=s.current();if(!e||e->id!=id||e->images.empty())return false;
        std::printf("Actual cover identity: %s / preferred %d / %s\n",e->id.c_str(),e->preferred_image,e->images[size_t(e->preferred_image)].url.c_str());return true;
    }
    static bool cover_probe_ready(Screen&s){const auto*e=s.current();return e&&!e->images.empty()&&s.cache_.get(e->images[size_t(e->preferred_image)].url).texture!=0;}
    static bool refinement_preview(Screen&s,int mode){
        s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=false;s.panel_.snap(0);s.experience_active_=false;s.experience_open_.snap(0);
        const char* music_entry=mode==3?std::getenv("MUSEUM_MUSIC_LAYOUT_ENTRY"):nullptr;
        s.select(music_entry?music_entry:mode==0||mode==4?"the-game-awards-2014":mode==1?"sonic":"journey");s.preview(1);
        const auto kind=mode==1?Screen::StoryCard::experience:mode==2||mode==3?Screen::StoryCard::soundtrack:Screen::StoryCard::narrative;
        for(size_t n=0;n<s.story_cards_.size();++n)if(s.story_cards_[n].kind==kind&&((mode!=0&&mode!=4)||s.story_cards_[n].title.rfind("2025",0)==0)){s.story_focus_=int(n);s.story_position_.snap(float(n));break;}
        s.dark_theme_=mode!=1;s.theme_mix_.snap(s.dark_theme_?1.f:0.f);s.fade_=1;s.story_open_.snap(1);
        if(mode==4){s.video_.close();s.screening_=true;s.fullscreen_=false;s.screening_from_story_=true;s.screening_origin_={958,376,810,456};s.screening_open_.snap(1);s.video_full_.snap(0);s.video_frame_alpha_=0;for(size_t v=0;v<s.current()->videos.size();++v)if(s.current()->videos[v].title.rfind("2025",0)==0)s.video_index_=int(v);}
        if(mode==3){
            // Opt-in actual listening-room visual fixtures: loaded catalogue data,
            // production renderer, no network playback or authoring mutations.
            if(const char* theme=std::getenv("MUSEUM_MUSIC_LAYOUT_THEME")){s.dark_theme_=std::string(theme)!="light";s.theme_mix_.snap(s.dark_theme_?1.f:0.f);}
            const auto* room=s.current_soundtrack();if(!room||room->tracks.empty())return false;
            const int count=int(room->tracks.size());const char* chosen=std::getenv("MUSEUM_MUSIC_LAYOUT_SELECTION");
            const int selected=chosen&&std::string(chosen)=="last"?count-1:chosen?std::clamp(std::atoi(chosen),0,count-1):0;
            s.playlist_music_room_=s.story_cards_[size_t(s.story_focus_)].music_room;
            s.playlist_active_=true;s.playlist_selection_=s.playlist_playing_=selected;s.screening_=s.fullscreen_=true;s.screening_open_.snap(1);s.video_full_.snap(1);
            s.entry_snapshot_=false;s.history_transition_=false;s.video_.close();
            std::printf("Actual music layout: %s / %s / selected %d of %d / %s\n",s.current()->title.c_str(),room->composer.c_str(),selected+1,count,s.dark_theme_?"dark":"light");
        }
        return s.current()!=nullptr;
    }
    static bool verify_model_controls(Screen&s){
        if(!s.object_texture_||!s.current()||s.current()->models.empty()){std::fputs("3D control check requires a loaded exhibit\n",stderr);return false;}
        const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"3D control check failed: %s\n",message);return pass;};
        hui::ui::Feedback feedback;
        const int focus=s.focus_;const auto initial=s.current()->models[0];
        const std::string model_id=s.current()->id;const float expected_zoom=model_id=="xbox-series-x"?1.3f:(model_id=="game-boy"||model_id=="playstation-5")?1.6f:2.f;
        if(!require(s.object_zoom_==expected_zoom,"initial selection uses the reviewed per-console zoom"))return false;
        s.update(1.f/60);
        const float angle=s.object_angle_,tilt=s.object_tilt_offset_,zoom=s.object_zoom_;
        hui::InputFrame input;input.connected=true;input.stick2_x=.75f;input.stick2_y=.6f;s.handle(input,feedback);
        if(!require(s.focus_==focus&&s.object_angle_!=angle&&s.object_tilt_offset_!=tilt,"right stick rotates both axes without moving the timeline"))return false;
        const float held_angle=s.object_angle_;s.update(1.f/60);
        if(!require(s.object_angle_==held_angle,"manual orbit remains still when the stick is released"))return false;
        input={};input.connected=true;input.trigger_r=1;input.pressed=hui::action_bit(hui::Action::jump_next);s.handle(input,feedback);
        if(!require(s.focus_==focus&&s.object_zoom_>zoom,"R2 zooms in without jumping exhibits"))return false;
        const float closer=s.object_zoom_;input={};input.connected=true;input.trigger_l=1;input.pressed=hui::action_bit(hui::Action::jump_prev);s.handle(input,feedback);
        if(!require(s.focus_==focus&&s.object_zoom_<closer,"L2 zooms out without jumping exhibits"))return false;
        input={};input.connected=true;input.pressed=hui::action_bit(hui::Action::r3);s.handle(input,feedback);
        if(!require(s.object_inspect_,"R3 opens fullscreen inspection"))return false;
        input={};input.connected=true;input.stick2_x=-.5f;input.stick2_y=-.5f;s.handle(input,feedback);
        if(!require(s.object_angle_!=held_angle,"right stick also rotates in fullscreen"))return false;
        input={};input.connected=true;input.pressed=hui::action_bit(hui::Action::confirm);s.handle(input,feedback);
        if(!require(s.object_tilt_offset_==0&&s.object_angle_==initial.initial_angle&&s.object_zoom_==expected_zoom,"reset restores the reviewed per-console camera pose"))return false;
        input.pressed=hui::action_bit(hui::Action::back);s.handle(input,feedback);
        if(!require(!s.object_inspect_&&s.focus_==focus,"back preserves the selected exhibit"))return false;
        std::puts("3D controls: right-stick orbit, L2/R2 zoom, manual hold, reset and fullscreen return passed");return true;
    }
    static bool verify(Screen&s){
        const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"Interaction check failed: %s\n",message);return pass;};
        hui::ui::Feedback feedback;
        auto press=[&](hui::Action a){hui::InputFrame i;i.connected=true;i.pressed=hui::action_bit(a);s.handle(i,feedback);};
        if(!verify_first_visit(s))return false;
        s.onboarding_=false;s.onboarding_leaving_=false;s.boot_time_=5;s.boot_note_=13;s.preview(0);s.settings_=s.credits_=false;
        const int focus=s.focus_;hui::InputFrame lost;lost.focus_lost=true;lost.pressed=hui::action_bit(hui::Action::confirm);s.handle(lost,feedback);
        if(!require(!s.detail_&&s.focus_==focus,"controller loss must not open an exhibit"))return false;
        press(hui::Action::confirm);if(!require(s.detail_,"confirm opens the focused exhibit"))return false;
        press(hui::Action::back);if(!require(!s.detail_,"back returns to chronology"))return false;
        press(hui::Action::menu);if(!require(s.settings_,"options opens preferences"))return false;
        s.setting_=2; // Ambient music follows Language and Appearance.
        const bool mute=s.muted_;press(hui::Action::confirm);if(!require(s.muted_!=mute,"soundtrack toggle changes one preference"))return false;
        s.muted_=mute;press(hui::Action::back);
        press(hui::Action::touch);
        if(!require(s.year_guide_&&!s.years_.empty()&&s.focus_==focus,"touchpad opens the Year Atlas without changing the exhibit"))return false;
        const int year_before=s.year_focus_;hui::InputFrame year_nav;year_nav.connected=true;year_nav.nav=year_before+1<int(s.years_.size())?hui::Direction::down:hui::Direction::up;s.handle(year_nav,feedback);
        if(s.years_.size()>1&&!require(s.year_focus_!=year_before&&s.focus_==focus,"year navigation changes the atlas selection, not the chronology"))return false;
        const int decade=s.years_[size_t(s.year_focus_)]/10;press(hui::Action::page_next);
        if(s.years_.back()/10>decade&&!require(s.years_[size_t(s.year_focus_)]/10>decade,"R1 advances the atlas into a later decade"))return false;
        const int target_year=s.years_[size_t(s.year_focus_)];press(hui::Action::confirm);
        if(!require(!s.year_guide_&&s.current()&&s.current()->year==target_year,"atlas confirm selects its chosen year"))return false;
        for(int index:s.visible_){const auto&e=s.catalog_.entries[size_t(index)];if(e.year==target_year){if(!require(s.current()->id==e.id,"atlas jumps to the first exhibit of the year"))return false;break;}}
        s.year_guide_=false;s.year_panel_.snap(.009f);s.settings_=false;s.panel_.snap(0);
        press(hui::Action::menu);
        if(!require(!s.settings_,"Options remains closed while the Year Atlas glass is still closing"))return false;
        s.year_panel_.snap(.0005f);press(hui::Action::menu);
        if(!require(s.settings_,"a fresh Options press opens preferences after the Year Atlas has closed"))return false;
        press(hui::Action::back);
        for(unsigned n=0;n<100;++n)s.update(1.f/60);
        for(const auto*id:{"daily-05-17","daily-08-31","daily-09-09","daily-01-12"}){
            const auto found=std::find_if(s.catalog_.entries.begin(),s.catalog_.entries.end(),[&](const auto&e){return e.id==id;});
            if(found==s.catalog_.entries.end())continue;
            s.select(id);if(!require(s.current()&&s.current()->id==id,"separate public-build/reissue/regional-launch/presentation events remain reachable"))return false;
        }
        const auto saved=s.catalog_.entries.size();if(!require(!s.catalog_.parse("{broken")&&s.catalog_.entries.size()==saved,"malformed catalogue preserves the working collection"))return false;
        unsigned random=17;
        for(unsigned n=0;n<600;++n){random=random*1664525u+1013904223u;hui::InputFrame in;in.connected=true;in.nav=static_cast<hui::Direction>(1+((random>>16)%4));s.handle(in,feedback);s.update(1.f/60);if(!require(s.visible_.empty()||(s.focus_>=0&&s.focus_<int(s.visible_.size())),"navigation remains within collection bounds"))return false;}
        s.select(s.catalog_.entries[0].id);s.preview(0);std::puts("Interaction checks: 600 navigation steps, controller loss, back, preferences and malformed catalogue passed");return true;
    }
};
}
#include "host/scene_checks.hpp"

#include "host/experience_checks.hpp"

#include "host/playlist_checks.hpp"
#include "host/startup_checks.hpp"

#include "host/model_transition_checks.hpp"

#include "host/experience_focus_checks.hpp"

#include "host/story_reading_checks.hpp"
#include "host/story_scrollbar_checks.hpp"

#include "host/alpha_image_checks.hpp"

#include "host/story_text_profile_checks.hpp"
#include "host/unicode_font_checks.hpp"
#include "host/catalog_alias_checks.hpp"

#include "host/photo_feedback_checks.hpp"

#include "host/sayonara_reading_checks.hpp"

#include "host/ninth_scoped_checks.hpp"

#include "host/tenth_scoped_checks.hpp"
#include "host/eleventh_scoped_checks.hpp"
#include "host/twelfth_scoped_checks.hpp"
#include "host/culture_staged_checks.hpp"

#include "host/timeline_pause_checks.hpp"

#include "host/model_stage_1080_checks.hpp"

#include "host/ps1_presentation_checks.hpp"

#include "host/console_presentation_checks.hpp"

#include "host/story_distribution_checks.hpp"
#include "host/ui_action_haptic_checks.hpp"
#include "host/timeline_input_today_checks.hpp"
#include "host/arcade_cage_visual_checks.hpp"
#include "host/experience_completion_checks.hpp"
#include "host/ui_locale_checks.hpp"
#include "host/general_credits_checks.hpp"
