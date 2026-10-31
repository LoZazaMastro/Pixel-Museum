// First-run integration: no onboarding or media can run ahead of the collection.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/screen.hpp"
#include <cstdio>
#include <thread>
#include <chrono>
namespace museum {
struct CollectionStartupInspection {
    static bool existing(Screen& screen){
        const bool passed=!screen.collection_pending_&&screen.collection_media_started_;
        std::printf("%s: existing full collection starts without first-run downloading.\n",passed?"PASS":"FAIL");return passed;
    }
    static bool download(Screen& screen,const std::string& manifest,const std::string& data){
        if(!screen.collection_pending_||screen.collection_media_started_||!screen.collection_installer_.configure(manifest,data,screen.root_,true))return false;
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
        const float boot=screen.boot_time_,intro=screen.onboarding_position_.value;
        const int step=screen.onboarding_step_,language=screen.language_focus_,focus=screen.focus_;
        hui::ui::Feedback feedback;hui::InputFrame input;
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
        const bool passed=held&&screen.wants_quit();
        std::printf("%s: first-run download precedes onboarding, navigation, audio notes and image workers; Close remains usable.\n",passed?"PASS":"FAIL");
        return passed;
    }
};
}
