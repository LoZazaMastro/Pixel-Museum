// Production compositor regression: no software-blit entry, faithful GPU snapshots.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "host/perf_hooks.hpp"
#include <array>
#include <cmath>
namespace museum {
inline bool ScreenInspection::verify_startup_compositor(Screen&s,unsigned framebuffer,int width,int height){
    using hui::gfx::Color;
    const auto require=[](bool ok,const char*message){if(!ok)std::fprintf(stderr,"Compositor check failed: %s\n",message);return ok;};
    const auto id=s.current()?s.current()->id:std::string{},data=s.data_;
    const bool onboarding=s.onboarding_,complete=s.onboarding_complete_,reduced=s.reduced_;
    s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.reduced_=true;
    auto finish=[&](bool ok){host::count_transfers(false);s.experience_active_=false;s.experience_open_.snap(0);s.study_.reset();s.year_guide_=s.guide_experiences_=false;s.year_panel_.snap(0);s.settings_=s.credits_=s.connection_panel_=false;s.panel_.snap(0);s.select(id);s.preview(0);s.onboarding_=onboarding;s.onboarding_complete_=complete;s.reduced_=reduced;s.data_=data;return ok;};
    auto clean=[&](const char*label){const auto c=host::transfers();if(c.blits||c.read_pixels||c.get_texture){std::fprintf(stderr,"%s unexpectedly used %llu framebuffer blits / %llu pixel reads / %llu texture reads\n",label,(unsigned long long)c.blits,(unsigned long long)c.read_pixels,(unsigned long long)c.get_texture);return false;}return require(glGetError()==GL_NO_ERROR,label);};
    auto render=[&](const char*label){host::reset_transfers();host::count_transfers(true);s.draw(width,height,framebuffer);host::count_transfers(false);return clean(label);};
    auto pixel=[&](unsigned target,int x,int y){std::array<unsigned char,4> p{};host::count_transfers(false);glBindFramebuffer(GL_FRAMEBUFFER,target);glReadPixels(x,height-1-y,1,1,GL_RGBA,GL_UNSIGNED_BYTE,p.data());return p;};
    auto equal=[](const auto&a,const auto&b,int tolerance=1){for(unsigned c=0;c<4;++c)if(std::abs(int(a[c])-int(b[c]))>tolerance)return false;return true;};
    s.onboarding_=true;s.onboarding_leaving_=false;s.onboarding_step_=0;s.onboarding_position_.snap(0);s.onboarding_fade_.snap(1);
    if(!render("first-visit welcome page"))return finish(false);
    s.onboarding_=false;
    if(!render("first chronology page"))return finish(false);
    s.fade_=1;s.entry_snapshot_=false;
    if(!render("settled chronology page"))return finish(false);
    for(int y:{height/8,height/2,height*7/8})for(int x:{width/8,width/2,width*7/8}){
        const auto source=pixel(s.composed_.framebuffer(),x,y),output=pixel(framebuffer,x,y);
        if(!require(equal(source,output)&&source[3]==255,"GPU output preserves canvas orientation, colour and opaque alpha"))return finish(false);
    }
    // Asymmetric native draw-list colours detect both vertical flips and stale
    // target blending. Test reads are outside the production-call counter.
    const std::array<unsigned,4> colours={0xe12b37,0x1baf62,0x264de0,0xe7bc29};
    hui::gfx::DrawList quadrants;
    for(unsigned n=0;n<4;++n)quadrants.rounded_rect({float(n%2)*960,float(n/2)*540,960,540},0,Color::rgb(colours[n]));
    s.renderer_.begin();s.renderer_.draw(quadrants);s.renderer_.present(s.composed_.framebuffer(),width,height);s.entry_snapshot_=false;s.fade_=1;
    host::reset_transfers();host::count_transfers(true);s.snapshot_current();host::count_transfers(false);
    if(!clean("first GPU snapshot"))return finish(false);
    for(unsigned n=0;n<4;++n){const auto p=pixel(s.previous_entry_.framebuffer(),int(n%2)*width/2+width/4,int(n/2)*height/2+height/4);const auto c=colours[n];const std::array<unsigned char,4> expected={static_cast<unsigned char>(c>>16),static_cast<unsigned char>(c>>8),static_cast<unsigned char>(c),255};if(!require(equal(p,expected),"snapshot preserves four distinct upright corner colours"))return finish(false);}
    hui::gfx::DrawList blue;blue.rounded_rect({0,0,1920,1080},0,Color::rgb(0x204060));s.renderer_.begin();s.renderer_.draw(blue);s.renderer_.present(s.composed_.framebuffer(),width,height);s.fade_=.5f;
    host::reset_transfers();host::count_transfers(true);s.snapshot_current();host::count_transfers(false);
    if(!clean("interrupted GPU dissolve snapshot"))return finish(false);
    for(unsigned n=0;n<4;++n){const auto p=pixel(s.previous_entry_.framebuffer(),int(n%2)*width/2+width/4,int(n/2)*height/2+height/4);const auto c=colours[n];const std::array<unsigned char,4> expected={static_cast<unsigned char>((((c>>16)&255)+32)/2),static_cast<unsigned char>((((c>>8)&255)+64)/2),static_cast<unsigned char>(((c&255)+96)/2),255};if(!require(equal(p,expected,2),"rapid second navigation snapshots the visible half-dissolve, not a raw new layer"))return finish(false);}
    s.select("pong");s.preview(0);s.fade_=.4f;
    if(!render("chronology entry dissolve"))return finish(false);
    hui::ui::Feedback feedback;
    for(int step=0;step<3;++step){host::reset_transfers();host::count_transfers(true);s.move(1,feedback);s.update(1.f/60);s.draw(width,height,framebuffer);host::count_transfers(false);if(!clean("rapid chronology navigation"))return finish(false);}
    if(!s.history_catalog_.entries.empty()){
        s.fade_=1;s.entry_snapshot_=false;
        if(!render("gaming before culture transition"))return finish(false);
        std::array<std::array<unsigned char,4>,12> brand{};
        for(unsigned n=0;n<brand.size();++n)brand[n]=pixel(framebuffer,int((96+n*18)*width/1920.f),int(81*height/1080.f));
        s.focus_history(true);
        for(float phase:{.2f,.5f,.8f}){
            s.fade_=phase;
            if(!render("culture transition has no software framebuffer transfer"))return finish(false);
            for(unsigned n=0;n<brand.size();++n)if(!require(equal(brand[n],pixel(framebuffer,int((96+n*18)*width/1920.f),int(81*height/1080.f))),"museum brand remains fixed throughout the vertical route transition"))return finish(false);
        }
        s.fade_=1;s.focus_history(false);s.fade_=.5f;
        if(!render("return to gaming has no software framebuffer transfer"))return finish(false);
        s.fade_=1;s.entry_snapshot_=false;s.history_transition_=false;
    }
    s.fade_=1;s.settings_=true;s.panel_.snap(1);
    if(!render("Options glass panel"))return finish(false);
    s.settings_=false;s.panel_.snap(0);s.open_year_guide();s.year_panel_.snap(1);
    if(!render("Year Atlas glass panel"))return finish(false);
    experience_preview(s,1,8);
    s.experience_open_.snap(.5f);
    if(!render("partially opened study over the library"))return finish(false);
    s.experience_open_.snap(1);
    if(!render("study introduction"))return finish(false);
    s.experience_introduction_=false;s.experience_intro_.snap(0);
    if(!render("opaque study activity"))return finish(false);
    std::puts("Compositor: zero production framebuffer blits/readbacks across first page, entry fade, rapid navigation, both timeline directions, both panels and study; fixed brand, upright colours, opaque alpha and interrupted dissolve snapshots passed.");
    return finish(true);
}
}
