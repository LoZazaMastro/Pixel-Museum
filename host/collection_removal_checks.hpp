// Real Screen regression using only a caller-owned temporary collection.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/screen.hpp"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <thread>

namespace museum {
struct CollectionRemovalInspection {
    static bool check(Screen& screen) {
        namespace fs=std::filesystem;
        const auto require=[](bool value,const char*step){if(!value)std::printf("FAIL: collection removal Screen / %s\n",step);return value;};
        const char*owned=std::getenv("MUSEUM_TEST_REMOVAL_DATA");
        if(!require(owned&&screen.data_==owned&&screen.data_.rfind("/tmp/pm-screen-collection-removal-",0)==0,"isolated temporary root required"))return false;
        const auto sentinel=screen.data_+"/trophy-preservation-sentinel.bin";
        const auto collection=screen.data_+"/collection";
        if(!require(fs::exists(collection)&&fs::exists(sentinel),"fixture exists"))return false;
        if(!require(screen.collection_installer_.start(),"validate existing fixture"))return false;
        for(int frame=0;frame<1500&&!screen.collection_installer_.is_ready();++frame){
            if(screen.collection_installer_.snapshot().phase==CollectionInstaller::Phase::failed)return require(false,"existing fixture readiness");
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        }
        if(!require(screen.collection_installer_.is_ready(),"existing fixture ready"))return false;
        screen.collection_pending_=false;screen.collection_started_=true;
        screen.onboarding_=screen.language_choice_=screen.theme_choice_=screen.theme_confirming_=false;
        screen.onboarding_complete_=screen.language_chosen_=true;
        screen.boot_time_=5;
        if(!require(screen.start_collection_media(),"actual image/video readers started"))return false;
        const auto music=screen.volume_,master=screen.master_volume_,culture=screen.culture_volume_;
        hui::ui::Feedback feedback;
        const auto press=[&](hui::Action action){hui::InputFrame input;input.connected=true;input.pressed=hui::action_bit(action);screen.handle(input,feedback);};
        const auto nav=[&](hui::Direction direction){hui::InputFrame input;input.connected=true;input.nav=direction;screen.handle(input,feedback);};
        press(hui::Action::menu);
        for(int row=0;row<5;++row)nav(hui::Direction::down);
        if(!require(screen.settings_&&screen.setting_==5,"option immediately after Replay"))return false;
        hui::gfx::Canvas target;if(!target.create(1920,1080,1))return false;
        const auto capture=[&](const char*name){
            std::vector<unsigned char>pixels(1920u*1080u*4u);
            glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());glReadPixels(0,0,1920,1080,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
            for(unsigned y=0;y<540;++y)for(unsigned x=0;x<1920u*4u;++x)std::swap(pixels[y*1920u*4u+x],pixels[(1079u-y)*1920u*4u+x]);
            const auto path=std::string("build/research/collection-removal-0.1.4/")+name+".png";
            return stbi_write_png(path.c_str(),1920,1080,4,pixels.data(),1920*4)!=0;
        };
        press(hui::Action::confirm);for(int frame=0;frame<30;++frame)screen.update(1.f/60);screen.draw(1920,1080,target.framebuffer());
        if(!require(capture("confirmation"),"confirmation preview"))return false;
        if(!require(screen.collection_remove_dialog_&&screen.collection_remove_focus_==0&&!screen.collection_removal_active()&&fs::exists(collection),"opening defaults to Cancel without deletion"))return false;
        press(hui::Action::confirm);
        if(!require(!screen.collection_remove_dialog_&&screen.settings_&&fs::exists(collection)&&screen.collection_installer_.is_ready(),"Cancel preserves ready collection"))return false;
        press(hui::Action::confirm);press(hui::Action::back);
        if(!require(!screen.collection_remove_dialog_&&fs::exists(collection),"Circle cancels"))return false;
        press(hui::Action::confirm);press(hui::Action::menu);
        if(!require(!screen.collection_remove_dialog_&&fs::exists(collection),"Options cancels"))return false;
        press(hui::Action::confirm);nav(hui::Direction::right);press(hui::Action::confirm);
        if(!require(!screen.collection_remove_dialog_&&screen.collection_removal_active()&&!screen.onboarding_complete_&&!screen.language_chosen_&&fs::exists(collection),"explicit Remove starts reader shutdown before deleting"))return false;
        screen.draw(1920,1080,target.framebuffer());if(!require(capture("removing"),"removal preview"))return false;
        // These are the real Screen update/draw gates while the media readers
        // stop and the separate filesystem worker removes the collection.
        for(int frame=0;frame<1500&&screen.collection_removal_active();++frame){
            screen.update(1.f/60);screen.draw(1920,1080,target.framebuffer());
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        }
        screen.draw(1920,1080,target.framebuffer());
        if(!require(capture("language"),"language preview"))return false;
        const bool language=!screen.collection_removal_active()&&screen.onboarding_&&screen.language_choice_&&screen.onboarding_fade_.value>.99f&&screen.collection_pending_&&!screen.collection_started_&&!screen.settings_;
        if(!require(language&&!fs::exists(collection)&&fs::exists(sentinel)&&!screen.collection_media_started_,"completed removal shows visible language page; trophy file preserved"))return false;
        std::ifstream trophy_file(sentinel);std::string trophy_bytes;std::getline(trophy_file,trophy_bytes);
        if(!require(trophy_bytes=="trophies-preserved"&&music==screen.volume_&&master==screen.master_volume_&&culture==screen.culture_volume_,"trophies and volume preferences preserved"))return false;
        const int previous=screen.language_focus_;nav(hui::Direction::right);
        if(!require(screen.language_focus_==previous+1,"language selection receives input"))return false;
        press(hui::Action::confirm);
        if(!require(!screen.language_choice_&&screen.language_chosen_&&!screen.collection_started_,"language confirmation precedes fresh installer"))return false;
        screen.update(1.f/60);screen.draw(1920,1080,target.framebuffer());
        const bool fresh=screen.collection_started_&&screen.collection_pending_&&!screen.collection_media_started_&&!screen.collection_installer_.is_ready();
        screen.collection_installer_.shutdown();target.destroy();
        if(!require(fresh,"fresh installation starts after language confirmation"))return false;
        std::puts("PASS: actual Screen confirmation/Cancel/Circle/Options, reader shutdown, asynchronous deletion, visible interactive language page, preserved trophies/volumes and fresh installation restart.");
        return true;
    }
};
}
