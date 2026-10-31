// Actual Screen model selection, cancellation and framebuffer lifetime checks.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/gl_program.hpp"
#include <chrono>
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_model_transitions(Screen&s,unsigned framebuffer,int width,int height){
    const auto require=[](bool value,const char*message){if(!value)std::fprintf(stderr,"Model transition check failed: %s\n",message);return value;};
    if(!require(s.prepared_programs_ready_,"active and both prepared scene programs were initialized before navigation"))return false;
    // A genuine shader compilation failure in a prepared scene must disable
    // background caching, release the partial programs, and leave the active
    // scene available. No test-only failure branch enters production code.
    for(auto&prepared:s.prepared_objects_)prepared.release();
    hui::gfx::set_glsl_prefix("#version 450 core\n#error intentional_prepared_program_failure\n");
    const bool unexpectedly_ready=s.initialize_object_programs();
    hui::gfx::set_glsl_prefix("#version 450 core\n");
    if(!require(!unexpectedly_ready&&!s.prepared_programs_ready_&&s.warm_objects(),"prepared shader failure disables only background model caching")||!require(glGetError()==GL_NO_ERROR,"failed compile/cleanup leaves GL state valid"))return false;
    if(!require(s.initialize_object_programs(),"all three owned scenes can initialize after failed prepared programs are cleaned"))return false;
    std::puts("PASS startup model programs: all3 initialized, real prepared-shader failure disables background caching, cleanup/reinitialize GL0.");
    const auto saved_data=s.data_;s.data_.clear();
    s.onboarding_=false;s.onboarding_leaving_=false;s.boot_time_=5;s.boot_note_=13;
    s.year_guide_=false;s.year_panel_.snap(0);s.settings_=s.credits_=s.experience_active_=false;
    s.panel_.snap(0);s.experience_open_.snap(0);s.reduced_=true;s.preview(0);
    s.draw(width,height,framebuffer);
    auto finish=[&](bool result){s.data_=saved_data;return result;};
    auto wait=[&](const char*id){
        const auto started=std::chrono::steady_clock::now(),deadline=started+std::chrono::seconds(60);
        while(!s.object_texture_&&std::chrono::steady_clock::now()<deadline){
            s.update(1.f/120);std::this_thread::sleep_for(std::chrono::milliseconds(2));
            const auto active=s.object_.timings();
            if(active.planned_gpu_bytes>(512u<<20)&&active.uploaded_bytes){
                std::size_t prepared_bytes=0;for(const auto&prepared:s.prepared_objects_)prepared_bytes+=prepared.timings().estimated_gpu_bytes;
                if(!require(prepared_bytes==0,"large active upload waits until all prepared model allocation bytes, including retired bytes, drain"))return false;
            }
            if(!s.object_.error().empty()){std::fprintf(stderr,"%s: %s\n",id,s.object_.error().c_str());return false;}
        }
        if(!require(s.object_texture_&&s.object_.ready(),"selected model finishes actual Screen upload/render"))return false;
        s.draw(width,height,framebuffer);
        const auto t=s.object_.timings();
        std::printf("Screen model %s: ready %.2fms, target %dx%d, model+target %.2fMiB, target allocation %.2fms\n",id,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count(),t.render_width,t.render_height,double(t.estimated_gpu_bytes)/(1u<<20),t.target_allocation_ms);
        return require(glGetError()==GL_NO_ERROR,"production upload/draw leaves GL error clear");
    };
    s.select("playstation-3");
    if(!require(s.current()&&s.current()->id=="playstation-3","PS3 exists in current production catalogue")||!wait("playstation-3"))return finish(false);
    const auto target=s.object_texture_;const auto first=s.object_.timings();
    constexpr char target_label[]="museum-model-transition-target";
    glObjectLabel(GL_TEXTURE,target,-1,target_label);
    const auto plane=static_cast<std::size_t>(first.render_width)*static_cast<std::size_t>(first.render_height)*12;
    if(!require(first.estimated_gpu_bytes>plane+(352u<<20),"real PS3 exceeds neighbour cache admission"))return finish(false);
    for(const char*id:{"playstation-4","playstation-3"}){
        s.select(id);
        if(!require(!s.object_texture_&&glIsTexture(target),"selection hides old console while preserving its full-resolution framebuffer"))return finish(false);
        for(const auto&path:s.prepared_paths_)if(!require(path.find("playstation-3-clean")==std::string::npos&&path.find("playstation-4-clean")==std::string::npos,"large originals never enter the neighbour GPU cache"))return finish(false);
        if(!wait(id))return finish(false);
        if(!require(s.object_texture_==target&&s.object_.timings().target_allocation_ms==0,"PS3/PS4 reuses the original target without allocating another framebuffer"))return finish(false);
    }
    // A real queued request is superseded before it can present. Retirement
    // still drains through normal Screen updates; no test-only upload path.
    s.select("playstation-4");
    for(int n=0;n<12;++n){s.update(1.f/120);std::this_thread::sleep_for(std::chrono::milliseconds(2));}
    s.select("playstation-3");
    if(!require(glIsTexture(target),"cancel/re-request preserves target lifetime")||!wait("playstation-3 after cancelled PS4"))return finish(false);
    if(!require(s.object_texture_==target&&s.object_.timings().target_allocation_ms==0,"cancelled request cannot retire or replace the selected target"))return finish(false);
    for(const char*asset:{"models/wii-u-gamepad.glb","models/playstation-5.glb"}){
        std::string id;for(const auto&e:s.catalog_.entries)for(const auto&m:e.models)if(m.asset_file==asset){id=e.id;break;}
        if(!require(!id.empty(),"actual GamePad/PS5 source model is attached to a current canonical exhibit"))return finish(false);
        s.select(id);if(!wait(id.c_str()))return finish(false);
        std::size_t prepared_bytes=0;for(const auto&prepared:s.prepared_objects_)prepared_bytes+=prepared.timings().estimated_gpu_bytes;
        if(!require(prepared_bytes==0,"large GamePad/PS5 readiness retains no prepared/retired neighbour allocation bytes"))return finish(false);
        std::printf("PASS actualScreen large-memory gate %s: active+target%.2fMiB prepared+retired0MiB; photos/fonts/UI remain separately bounded, no physicalpool guarantee.\n",id.c_str(),double(s.object_.timings().estimated_gpu_bytes)/(1u<<20));
    }
    s.select("nintendo-3ds");if(!require(s.current()&&s.current()->id=="nintendo-3ds","small fixture is a real catalogue exhibit")||!wait("nintendo-3ds"))return finish(false);
    if(!require(s.object_texture_==target,"small selected console can reuse the active target too"))return finish(false);
    s.select("pong");
    bool small_cached=false;
    for(std::size_t n=0;n<s.prepared_paths_.size();++n)if(s.prepared_paths_[n].find("nintendo-3ds.glb")!=std::string::npos){
        small_cached=true;const auto cached=s.prepared_objects_[n].timings();
        if(!require(s.prepared_objects_[n].ready()&&cached.render_width==0&&cached.render_height==0,"small neighbour cache keeps artwork but releases its framebuffer"))return finish(false);
    }
    if(!require(small_cached,"real small console is admitted to the unchanged neighbour cache"))return finish(false);
    for(int n=0;n<12;++n)s.update(1.f/120);
    // Names can be reused by normal photo uploads after deletion. A newly
    // generated texture has no label, so distinguish that from a leaked FBO.
    char remaining_label[64]{};GLsizei label_length=0;
    if(glIsTexture(target))glGetObjectLabel(GL_TEXTURE,target,sizeof(remaining_label),&label_length,remaining_label);
    if(!require(std::string(remaining_label,std::size_t(label_length))!=target_label,"unused small-console framebuffer is actually retired by normal Screen maintenance"))return finish(false);
    s.draw(width,height,framebuffer);
    if(!require(glGetError()==GL_NO_ERROR,"final transition and retirement leave GL clear"))return finish(false);
    std::printf("Actual Screen model transitions PASS: PS3 -> PS4 -> PS3; interrupted PS4 -> PS3; original %dx%d framebuffer retained without repeated allocation; small Nintendo 3DS -> Pong retires it, GL=0x%x\n",first.render_width,first.render_height,glGetError());
    return finish(true);
}
}
