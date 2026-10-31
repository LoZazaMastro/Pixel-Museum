// Pixel Museum - same-renderer GLB tests. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#if defined(__clang__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Weverything"
#else
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
#endif
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#if defined(__clang__)
#pragma clang diagnostic pop
#else
#pragma GCC diagnostic pop
#endif
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <thread>
#include <sys/resource.h>
#include <vector>

int main(int argc,char **argv) {
    if(argc<2)return 1;
    std::vector<std::string> groups;bool validate_only=false,z_up=false,adaptive_upload=false,pin_studio=false;float tilt=.13f,yaw=0,zoom=1;int width=768,height=768,expected_dedup=-1,expected_textures=-1,expected_cache_hits=-1;
    for(int arg=2;arg<argc;++arg) {
        std::string value=argv[arg];if(value=="--adaptive-upload"){adaptive_upload=true;continue;}if(value=="--validate"){validate_only=true;continue;}
        if(value=="--pin-studio"){pin_studio=true;continue;}
        if(value.rfind("--cache-hits=",0)==0){expected_cache_hits=std::atoi(value.c_str()+13);continue;}
        if(value.rfind("--dedup=",0)==0){expected_dedup=std::atoi(value.c_str()+8);continue;}
        if(value.rfind("--textures=",0)==0){expected_textures=std::atoi(value.c_str()+11);continue;}
        if(value.rfind("--tilt=",0)==0){tilt=std::strtof(value.c_str()+7,nullptr);continue;}
        if(value.rfind("--yaw=",0)==0){yaw=std::strtof(value.c_str()+6,nullptr);continue;}
        if(value.rfind("--zoom=",0)==0){zoom=std::strtof(value.c_str()+7,nullptr);continue;}
        if(value.rfind("--size=",0)==0){const auto separator=value.find('x');assert(separator!=std::string::npos);width=std::atoi(value.c_str()+7);height=std::atoi(value.c_str()+separator+1);continue;}
        if(value=="--z-up"){z_up=true;continue;}
        for(std::size_t begin=0;begin<value.size();) {
            const auto end=value.find(',',begin);groups.push_back(value.substr(begin,end-begin));
            if(end==std::string::npos)break;begin=end+1;
        }
    }
    std::string error;
    const bool valid=museum::ObjectScene::validate(argv[1],&error,groups);
    if(validate_only) {
        std::printf("%s: %s\n",valid?"VALID":"REJECTED",error.c_str());return valid?0:2;
    }
    if(!valid){std::fprintf(stderr,"%s\n",error.c_str());return 2;}
    const auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));
    assert(get);
    EGLDisplay display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);
    EGLint major=0,minor=0;assert(eglInitialize(display,&major,&minor)&&eglBindAPI(EGL_OPENGL_API));
    const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};
    EGLContext gl=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);
    assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,gl));
    hui::gfx::set_glsl_prefix("#version 450 core\n");
    {
        museum::ObjectScene object;
        object.request(argv[1],groups);
        // CPU completion is not load completion. Before the first main-thread
        // handoff, the request must still report loading rather than a false
        // unavailable state while old GPU resources are being retired.
        for(int tick=0;tick<10000&&object.stage()=="Reading the original model";++tick)std::this_thread::sleep_for(std::chrono::milliseconds(1));
        assert(object.loading());
        for(int i=0;i<10000&&!object.ready();++i){object.upload_pending(adaptive_upload?1.5:2.,adaptive_upload);if(!object.loading()&&!object.ready())break;std::this_thread::sleep_for(std::chrono::milliseconds(5));}
        if(!object.ready()){std::fprintf(stderr,"%s\n",object.error().c_str());return 3;}
        assert(!object.loading());
        const auto stats=object.stats();
        std::printf("Geometry: %zu vertices, %zu triangles, %zu mesh draws, %zu geometry bytes, %zu texture bytes.\n",stats.vertices,stats.triangles,stats.draw_calls,stats.geometry_bytes,stats.texture_bytes);
        assert(stats.draw_calls<=128);
        if(expected_dedup>=0)assert(stats.deduplicated_images==static_cast<std::size_t>(expected_dedup));
        if(expected_textures>=0)assert(stats.srgb_textures+stats.linear_textures==static_cast<std::size_t>(expected_textures));
        std::printf("Lossless atlas identity: %zu duplicate image slots canonicalized; %zu colour + %zu material GPU textures.\n",stats.deduplicated_images,stats.srgb_textures,stats.linear_textures);
        const auto upload_timing=object.timings();struct rusage usage{};getrusage(RUSAGE_SELF,&usage);std::printf("Process peakRSS throughready: %llu bytes (host process includes softwareGL allocations). Adaptiveupload %d / currentbudget %zu KiB %.2fms / throughput %.2f MiB/ms.\n",static_cast<unsigned long long>(usage.ru_maxrss)*1024,adaptive_upload,upload_timing.upload_budget_bytes>>10,upload_timing.upload_budget_ms,upload_timing.transfer_bytes_per_ms/(1u<<20));if(expected_cache_hits>=0)assert(upload_timing.artwork_cache_hits==static_cast<std::size_t>(expected_cache_hits));std::printf("Derived artwork cache: %zu hits / %.2fms checked read+decompression / %.2fms residual packing.\n",upload_timing.artwork_cache_hits,upload_timing.total_cache_decode_ms,upload_timing.total_mip_prepare_ms);std::printf("Separated timing: source read %.2fms / parse+geometry+identity %.2fms / image decode sum %.2fms / mip+packing worker sum %.2fms / upload CPU sum %.2fms / GL storage sum %.2fms / GL row-transfer sum %.2fms / request-to-ready %.2fms (includes fixture scheduling sleeps).\n",upload_timing.source_read_ms,upload_timing.parse_ms,upload_timing.total_image_decode_ms,upload_timing.total_mip_prepare_ms,upload_timing.total_upload_cpu_ms,upload_timing.total_storage_ms,upload_timing.total_transfer_ms,upload_timing.load_ready_ms);assert(upload_timing.max_upload_bytes<=(adaptive_upload?(16u<<20):(2u<<20)));assert(upload_timing.encoded_model_bytes<=(160u<<20));assert(upload_timing.peak_staged_image_bytes<=(128u<<20));
        std::printf("Atlas streaming: encoded %zu MiB / peak staged image %zu MiB / last decode %.2fms.\n",upload_timing.encoded_model_bytes>>20,upload_timing.peak_staged_image_bytes>>20,upload_timing.image_decode_ms);
        std::printf("Staging: max %.2fms/call, %zu bytes/call, last mip %.2fms worker, retire %.2fms.\n",upload_timing.max_upload_ms,upload_timing.max_upload_bytes,upload_timing.mip_prepare_ms,upload_timing.last_retire_ms);
        std::printf("Allocation: %.2fms maximum / row transfer %.2fms maximum / delete %.2fms maximum / adaptive chunk %zu KiB / estimated GPU %.2f MiB / %zu unique sampler objects.\n",upload_timing.max_storage_ms,upload_timing.max_transfer_ms,upload_timing.max_delete_ms,upload_timing.transfer_chunk_bytes>>10,double(upload_timing.estimated_gpu_bytes)/(1u<<20),stats.sampler_objects);
        GLuint preserved_samplers[5]{},preserved_textures[5]{};
        glGenSamplers(5,preserved_samplers);glGenTextures(5,preserved_textures);
        for(unsigned slot=0;slot<5;++slot){glActiveTexture(GL_TEXTURE0+slot);glBindTexture(GL_TEXTURE_2D,preserved_textures[slot]);glBindSampler(slot,preserved_samplers[slot]);}
        glActiveTexture(GL_TEXTURE3);
        glViewport(9,11,123,321);glEnable(GL_SCISSOR_TEST);glDisable(GL_DEPTH_TEST);
        for(int frame=0;frame<2;++frame) {
            const GLuint texture=object.render(yaw+frame*-.9f,width,height,tilt,z_up,zoom,0,0,pin_studio);assert(texture);
            GLint viewport[4]{};glGetIntegerv(GL_VIEWPORT,viewport);
            assert(viewport[0]==9&&viewport[1]==11&&viewport[2]==123&&viewport[3]==321);
            assert(glIsEnabled(GL_SCISSOR_TEST)&&!glIsEnabled(GL_DEPTH_TEST));
            GLint active=0;glGetIntegerv(GL_ACTIVE_TEXTURE,&active);assert(active==GL_TEXTURE3);
            for(unsigned slot=0;slot<5;++slot){glActiveTexture(GL_TEXTURE0+slot);GLint texture_binding=0,sampler_binding=0;glGetIntegerv(GL_TEXTURE_BINDING_2D,&texture_binding);glGetIntegerv(GL_SAMPLER_BINDING,&sampler_binding);assert(GLuint(texture_binding)==preserved_textures[slot]&&GLuint(sampler_binding)==preserved_samplers[slot]);}
            glActiveTexture(GL_TEXTURE3);
            GLuint fbo=0;glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);
            glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,texture,0);
            std::vector<unsigned char> pixels(static_cast<std::size_t>(width)*static_cast<std::size_t>(height)*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
            std::size_t visible=0;for(std::size_t i=3;i<pixels.size();i+=4)if(pixels[i]>0)++visible;
            stbi_flip_vertically_on_write(1);
            const std::string output=std::string(argv[1])+"-"+std::to_string(frame)+".png";
            assert(stbi_write_png(output.c_str(),width,height,4,pixels.data(),width*4));
            std::printf("Coverage: %zu/%zu pixels.\n",visible,static_cast<std::size_t>(width)*static_cast<std::size_t>(height));std::fflush(stdout);
            assert(visible>static_cast<std::size_t>(width)*static_cast<std::size_t>(height)/100&&visible<static_cast<std::size_t>(width)*static_cast<std::size_t>(height)*9/10);
            glBindFramebuffer(GL_FRAMEBUFFER,0);glDeleteFramebuffers(1,&fbo);
            assert(glGetError()==GL_NO_ERROR);
            std::printf("Rendered %s: %zu visible pixels, no GL error, state restored.\n",output.c_str(),visible);
        }
        const auto rendered=object.timings();assert(rendered.gpu_timing_supported);std::printf("GPU: %.2fms last / %.2fms peak; CPU submission %.2fms; allocation %.2fms.\n",rendered.last_gpu_ms,rendered.max_gpu_ms,rendered.last_render_ms,rendered.target_allocation_ms);
        // Ready geometry and material atlases survive eviction of the cached
        // render surface. Only the inexpensive target is recreated on return.
        const auto atlas_calls=rendered.storage_calls,atlas_uploads=rendered.uploaded_bytes;
        object.release_render_target();assert(object.ready()&&!object.loading());
        for(unsigned tick=0;object.timings().pending_gpu_deletes&&tick<10;++tick)object.upload_pending();
        const auto cached=object.timings();assert(!cached.pending_gpu_deletes);
        assert(cached.estimated_gpu_bytes+static_cast<std::size_t>(width)*height*12==rendered.estimated_gpu_bytes);
        assert(cached.storage_calls==atlas_calls&&cached.uploaded_bytes==atlas_uploads&&object.stats().triangles==stats.triangles);
        museum::ObjectScene prepared;object.swap(prepared);
        assert(prepared.ready()&&!object.ready()&&prepared.timings().render_width==0);
        assert(prepared.stats().triangles==stats.triangles);
        object.swap(prepared);assert(object.ready()&&!prepared.ready());
        assert(object.render(yaw,width,height,tilt,z_up,zoom,0,0,pin_studio));
        assert(object.timings().storage_calls==atlas_calls&&object.timings().uploaded_bytes==atlas_uploads);
        assert(object.timings().estimated_gpu_bytes==rendered.estimated_gpu_bytes&&glGetError()==GL_NO_ERROR);
        std::printf("Cache/revisit PASS: %zu bytes of framebuffer retired; geometry and original atlases retained; zero additional atlas storage/upload calls; ready swap/revisit without GL errors.\n",rendered.estimated_gpu_bytes-cached.estimated_gpu_bytes);
        // The newest request wins. A new selection clears the previous object
        // so a failed download can never show another console by mistake.
        // Cancel after real row uploads have begun, with CPU maps still owned
        // by the pending model and a mip job. Retirement must not leave stale
        // frame state or corrupt the next worker handoff.
        object.request(argv[1],groups);
        for(int i=0;i<10000&&object.timings().uploaded_bytes==0;++i){object.upload_pending();if(!object.error().empty())break;std::this_thread::sleep_for(std::chrono::milliseconds(1));}
        assert(object.timings().uploaded_bytes>0);
        object.request("/missing.glb");object.request(argv[1],groups);
        for(int i=0;i<10000&&!object.ready();++i){object.upload_pending();if(!object.loading()&&!object.ready())break;std::this_thread::sleep_for(std::chrono::milliseconds(5));}
        assert(object.ready());
        object.cancel();assert(!object.ready()&&!object.loading());
        auto garbage=object.timings().pending_gpu_deletes;assert(garbage>0);
        for(unsigned tick=0;garbage&&tick<10000;++tick){object.upload_pending();const auto remaining=object.timings().pending_gpu_deletes;assert(remaining<=garbage&&garbage-remaining<=4);garbage=remaining;}
        assert(!garbage&&glGetError()==GL_NO_ERROR);
        assert(object.timings().estimated_gpu_bytes==static_cast<std::size_t>(rendered.render_width)*static_cast<std::size_t>(rendered.render_height)*12);
        object.release();assert(!object.ready());
        // Exercise the CPU-result publication boundary repeatedly. Cancel must
        // invalidate and retire both mailboxes atomically; a late old worker
        // result must never restart loading or become a visible object.
        for(unsigned attempt=0;attempt<32;++attempt){
            object.request(argv[1],groups);
            if((attempt%3)==0){
                for(unsigned tick=0;tick<10000&&object.stage()=="Reading the original model";++tick)
                    std::this_thread::sleep_for(std::chrono::microseconds(100));
            }else std::this_thread::sleep_for(std::chrono::microseconds(50*(attempt%5)));
            object.cancel();
            for(unsigned tick=0;tick<8;++tick){
                object.upload_pending();
                assert(!object.ready()&&!object.loading()&&object.stage().empty()&&object.error().empty());
                std::this_thread::sleep_for(std::chrono::microseconds(100));
            }
        }
        std::puts("Cancellation publication boundary: 32 requests remain cancelled after worker handoff.");
        for(unsigned slot=0;slot<5;++slot)glBindSampler(slot,0);
        glDeleteSamplers(5,preserved_samplers);glDeleteTextures(5,preserved_textures);
    }
    eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
    eglDestroyContext(display,gl);eglTerminate(display);
    return 0;
}
