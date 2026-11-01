// First-run integration: no onboarding or media can run ahead of the collection.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/screen.hpp"
#include <cstdio>
#include <atomic>
#include <thread>
#include <chrono>
#include <cstdlib>
namespace museum {
struct CollectionStartupInspection {
    static bool large_inventory(Screen& screen,std::atomic<bool>& entered,std::atomic<bool>& release){
        if(!screen.collection_pending_||screen.collection_media_started_)return false;
        hui::ui::Feedback feedback;
        if(screen.language_choice_){hui::InputFrame choose;choose.connected=true;choose.pressed=hui::action_bit(hui::Action::confirm);screen.handle(choose,feedback);}
        const int step=screen.onboarding_step_;const float boot=screen.boot_time_;
        hui::gfx::Canvas target;if(!target.create(1920,1080,1))return false;
        for(int frame=0;frame<2400&&!entered.load();++frame){screen.update(1.f/60);screen.draw(1920,1080,target.framebuffer());std::this_thread::sleep_for(std::chrono::milliseconds(2));}
        const bool parsed=entered.load()&&screen.collection_installer_.snapshot().phase==CollectionInstaller::Phase::verifying;
        // The worker is stopped at its first missing image, AFTER parsing both
        // unmodified real registries. Exercise drawing while those JSON trees live.
        for(int frame=0;frame<30&&parsed;++frame){screen.update(1.f/60);screen.draw(1920,1080,target.framebuffer());}
        hui::InputFrame pause;pause.connected=true;pause.pressed=hui::action_bit(hui::Action::confirm);screen.handle(pause,feedback);release.store(true);
        for(int frame=0;frame<1000&&screen.collection_installer_.snapshot().phase!=CollectionInstaller::Phase::paused;++frame){screen.update(1.f/60);std::this_thread::sleep_for(std::chrono::milliseconds(2));}
        screen.draw(1920,1080,target.framebuffer());target.destroy();
        const bool passed=parsed&&screen.collection_installer_.snapshot().phase==CollectionInstaller::Phase::paused&&screen.collection_pending_&&!screen.collection_media_started_&&screen.onboarding_step_==step&&screen.boot_time_==boot;
        std::printf("%s: actual Screen and full bundled registries on installer worker, concurrent draw, pause before network, onboarding held.\n",passed?"PASS":"FAIL");return passed;
    }
    static bool existing(Screen& screen){
        const bool passed=!screen.collection_pending_&&screen.collection_media_started_;
        std::printf("%s: existing full collection starts without first-run downloading.\n",passed?"PASS":"FAIL");
        return passed&&(!std::getenv("MUSEUM_TEST_REPLAY_MANIFEST")||replay(screen));
    }
    static bool replay(Screen& screen){
        const char*manifest=std::getenv("MUSEUM_TEST_REPLAY_MANIFEST");
        const char*bundle=std::getenv("MUSEUM_TEST_REPLAY_BUNDLE");
        if(!manifest||!bundle||!screen.collection_installer_.configure(manifest,screen.data_+"/replay-fixture",bundle,true)||!screen.collection_installer_.start())return false;
        for(int frame=0;frame<1000&&!screen.collection_installer_.is_ready();++frame){
            if(screen.collection_installer_.snapshot().phase==CollectionInstaller::Phase::failed)return false;
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        }
        if(!screen.collection_installer_.is_ready())return false;
        screen.onboarding_=false;screen.onboarding_complete_=true;
        screen.language_choice_=screen.theme_choice_=screen.theme_confirming_=false;
        screen.settings_=false;screen.setting_=0;screen.boot_time_=5;
        const auto before=screen.collection_installer_.snapshot();
        const auto cache_root=screen.collection_installer_.cache_root();
        const auto music=screen.volume_,master=screen.master_volume_,culture=screen.culture_volume_;
        hui::ui::Feedback feedback;
        const auto press=[&](hui::Action action){hui::InputFrame input;input.connected=true;input.pressed=hui::action_bit(action);screen.handle(input,feedback);};
        press(hui::Action::menu);
        for(int row=0;row<4;++row){hui::InputFrame input;input.connected=true;input.nav=hui::Direction::down;screen.handle(input,feedback);}
        if(!screen.settings_||screen.setting_!=4)return false;
        press(hui::Action::confirm);
        const bool entered=screen.collection_pending_&&screen.language_choice_&&screen.collection_started_&&screen.onboarding_&&!screen.settings_;
        hui::gfx::Canvas target;if(!target.create(1920,1080,1))return false;
        for(int frame=0;frame<90;++frame)screen.update(1.f/60);
        screen.draw(1920,1080,target.framebuffer());
        const bool visible_language=screen.onboarding_fade_.value>.99f&&screen.language_choice_&&screen.collection_ready_elapsed_==0;
        // Language -> completed collection at100% -> theme. No installer start,
        // cache restart, new network activity or reset of existing preferences.
        press(hui::Action::confirm);
        const auto complete=screen.collection_install_view_state();
        const bool full=complete.phase==CollectionInstallPhase::complete&&complete.progress==1.f;
        screen.draw(1920,1080,target.framebuffer());
        for(int frame=0;frame<60;++frame)screen.update(1.f/60);
        screen.draw(1920,1080,target.framebuffer());target.destroy();
        const auto after=screen.collection_installer_.snapshot();
        const bool resumed=!screen.collection_pending_&&screen.onboarding_&&screen.theme_choice_&&!screen.language_choice_&&screen.collection_media_started_&&screen.onboarding_fade_.value>.99f;
        const bool untouched=before.phase==after.phase&&before.downloaded_bytes==after.downloaded_bytes&&before.installed_bytes==after.installed_bytes&&cache_root==screen.collection_installer_.cache_root()&&music==screen.volume_&&master==screen.master_volume_&&culture==screen.culture_volume_;
        press(hui::Action::confirm);
        for(int frame=0;frame<60;++frame)screen.update(1.f/60);
        const bool advanced=!screen.theme_choice_&&!screen.theme_confirming_&&screen.onboarding_&&screen.onboarding_step_==0;
        const bool passed=entered&&visible_language&&full&&resumed&&untouched&&advanced;
        std::printf("%s: actual Screen Options->Replay->visible language->100%% collection->theme->intro; entered=%d fade=%d full=%d resumed=%d preserved=%d advanced=%d.\n",passed?"PASS":"FAIL",entered,visible_language,full,resumed,untouched,advanced);
        return passed;
    }
    static bool download(Screen& screen,const std::string& manifest,const std::string& data){
        if(!screen.collection_pending_||screen.collection_media_started_||!screen.collection_installer_.configure(manifest,data,screen.root_,true))return false;
        if(screen.language_choice_){hui::InputFrame choose;choose.connected=true;choose.pressed=hui::action_bit(hui::Action::confirm);hui::ui::Feedback feedback;screen.handle(choose,feedback);}
        bool saw_download=false,saw_complete=false;
        for(int frame=0;frame<2000&&screen.collection_pending_;++frame){
            const auto phase=screen.collection_installer_.snapshot().phase;
            if(phase==CollectionInstaller::Phase::failed){std::fprintf(stderr,"FAIL: %s\n",screen.collection_installer_.snapshot().error.c_str());return false;}
            saw_download|=phase==CollectionInstaller::Phase::downloading;
            saw_complete|=phase==CollectionInstaller::Phase::ready;
            screen.update(1.f/60);
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
        bool image_ready=false;
        if(!screen.collection_pending_){
            screen.select("game-boy");const auto*entry=screen.current();
            if(entry&&!entry->images.empty())for(int frame=0;frame<160&&!image_ready;++frame){
                screen.update(1.f/60);const auto photo=screen.cache_.get(screen.image_url(entry->images[entry->preferred_image]));
                image_ready=photo.state==media::State::ready&&photo.texture&&photo.width&&photo.height;
                std::this_thread::sleep_for(std::chrono::milliseconds(5));
            }
        }
        const bool passed=saw_download&&saw_complete&&!screen.collection_pending_&&screen.collection_media_started_&&screen.trophies_&&image_ready;
        std::printf("%s: local HTTP download, verified installation, automatic entry and real image texture from persistent collection.\n",passed?"PASS":"FAIL");return passed;
    }
    static bool check(Screen& screen){
        if(!screen.collection_pending_||screen.collection_media_started_)return false;
        // Keep the installer idle: this test exercises the real first frame and
        // input/update gate; the separate installer harness tests local HTTP.
        screen.collection_started_=true;
        screen.language_choice_=true;screen.language_chosen_=false;
        for(int frame=0;frame<30;++frame)screen.update(1.f/60);
        const bool language_first=screen.collection_pending_&&!screen.collection_media_started_&&screen.collection_installer_.snapshot().phase==CollectionInstaller::Phase::idle;
        hui::ui::Feedback feedback;hui::InputFrame choose;choose.connected=true;choose.pressed=hui::action_bit(hui::Action::confirm);screen.handle(choose,feedback);
        const bool download_second=!screen.language_choice_&&screen.language_chosen_&&screen.collection_pending_&&screen.theme_choice_;
        const float boot=screen.boot_time_,intro=screen.onboarding_position_.value;
        const int step=screen.onboarding_step_,language=screen.language_focus_,focus=screen.focus_;
        hui::InputFrame input;
        input.connected=true;input.nav=hui::Direction::right;
        input.pressed=hui::action_bit(hui::Action::confirm);
        for(int frame=0;frame<30;++frame){screen.handle(input,feedback);screen.update(1.f/60);}
        int pixel=-1;
        const bool held=screen.collection_pending_&&!screen.collection_media_started_&&!screen.trophies_&&
            screen.boot_time_==boot&&screen.onboarding_position_.value==intro&&screen.onboarding_step_==step&&
            screen.language_focus_==language&&screen.focus_==focus&&screen.take_startup_note(&pixel)==-1&&pixel==-1;
        hui::gfx::Canvas target;if(!target.create(1920,1080,1))return false;
        screen.draw(1920,1080,target.framebuffer());target.destroy();
        input={};input.connected=true;input.pressed=hui::action_bit(hui::Action::back);screen.handle(input,feedback);
        const bool passed=language_first&&download_second&&held&&screen.wants_quit();
        std::printf("%s: language first, download second, then remaining onboarding; no early image workers or startup notes; Close remains usable.\n",passed?"PASS":"FAIL");
        return passed;
    }
};
}
