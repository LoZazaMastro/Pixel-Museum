#if defined(_WIN32)
// SPDX-License-Identifier: GPL-3.0-or-later
#include <GL/glew.h>
#include "platform/windows/desktop_display.hpp"
#include "gfx/gl_program.hpp"
#include "core/save_file.hpp"
#include "third_party/nlohmann/json.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
namespace museum::desktop {
Display::~Display(){if(context_)SDL_GL_DestroyContext(context_);if(window_)SDL_DestroyWindow(window_);}
bool Display::open(const DesktopVideoSettings&s,bool hidden){
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK,SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER,1);SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE,24);SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE,8);
    for(int minor:{6,3}){
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION,4);SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION,minor);
        window_=SDL_CreateWindow("Pixel Museum",s.width,s.height,SDL_WINDOW_OPENGL|SDL_WINDOW_RESIZABLE|SDL_WINDOW_HIGH_PIXEL_DENSITY|(hidden?SDL_WINDOW_HIDDEN:0));
        if(window_)context_=SDL_GL_CreateContext(window_);
        if(context_)break;if(window_){SDL_DestroyWindow(window_);window_=nullptr;}
    }
    if(!context_){error_="OpenGL 4.3 or later is required. Please update the graphics driver. ";error_+=SDL_GetError();return false;}
    glewExperimental=GL_TRUE;const auto result=glewInit();glGetError();
    if(result!=GLEW_OK){error_=reinterpret_cast<const char*>(glewGetErrorString(result));return false;}
    hui::gfx::set_glsl_prefix(GLEW_VERSION_4_6?"#version 460 core\n":"#version 430 core\n");
    SDL_SetWindowMinimumSize(window_,960,540);
    hui::sys::log("[Windows] renderer %s / %s",glGetString(GL_RENDERER),glGetString(GL_VERSION));
    return apply(s);
}
bool Display::apply(const DesktopVideoSettings&s){
    error_.clear();
    if(s.width<960||s.height<540||s.width>16384||s.height>16384){error_="Unsupported resolution";return false;}
    if(s.fullscreen&&s.borderless){
        if(!SDL_SetWindowFullscreenMode(window_,nullptr)||!SDL_SetWindowFullscreen(window_,true)){error_=SDL_GetError();return false;}
    }else if(s.fullscreen){SDL_DisplayMode mode{};
        if(!SDL_GetClosestFullscreenDisplayMode(SDL_GetDisplayForWindow(window_),s.width,s.height,0,true,&mode)){error_=SDL_GetError();return false;}
        if(desktop_aspect(s.width,s.height)!="16:9"&&(mode.w!=s.width||mode.h!=s.height)){error_="Unsupported resolution";return false;}
        if(!SDL_SetWindowFullscreenMode(window_,&mode)||!SDL_SetWindowFullscreen(window_,true)){error_=SDL_GetError();return false;}
    }else{
        if(!SDL_SetWindowFullscreen(window_,false)||!SDL_SetWindowSize(window_,s.width,s.height)){error_=SDL_GetError();return false;}
    }
    if(!SDL_GL_SetSwapInterval(s.vsync?1:0)){error_=SDL_GetError();return false;}
    return true;
}
DesktopDisplayModes Display::modes()const{
    DesktopDisplayModes result;
    int count=0;
    auto** modes=SDL_GetFullscreenDisplayModes(SDL_GetDisplayForWindow(window_),&count);
    for(int i=0;i<count;++i){
        const DesktopDisplayMode mode{modes[i]->w,modes[i]->h};
        if(desktop_resolution_listed(mode))result.exclusive.push_back(mode);
    }
    SDL_free(modes);
    result.windowed=result.exclusive;
    result.windowed.insert(result.windowed.end(),std::begin(desktop_window_presets),std::end(desktop_window_presets));
    for(auto* list:{&result.exclusive,&result.windowed}){
        std::sort(list->begin(),list->end(),[](auto a,auto b){return a.width!=b.width?a.width<b.width:a.height<b.height;});
        list->erase(std::unique(list->begin(),list->end()),list->end());
    }
    return result;
}
double Display::refresh_hz()const{
    const auto* mode=SDL_GetCurrentDisplayMode(SDL_GetDisplayForWindow(window_));
    if(mode&&mode->refresh_rate_numerator>0&&mode->refresh_rate_denominator>0)
        return double(mode->refresh_rate_numerator)/mode->refresh_rate_denominator;
    return mode&&mode->refresh_rate>0?mode->refresh_rate:60.;
}
int Display::width()const{int w=0;SDL_GetWindowSizeInPixels(window_,&w,nullptr);return w;}
int Display::height()const{int h=0;SDL_GetWindowSizeInPixels(window_,nullptr,&h);return h;}
DesktopVideoSettings load_video_settings(const std::string&path){
    DesktopVideoSettings s;int displays=0;auto*ids=SDL_GetDisplays(&displays);
    if(displays){SDL_Rect area{};if(SDL_GetDisplayUsableBounds(ids[0],&area)){s.width=std::max(960,std::min(1600,area.w-120));s.height=std::max(540,std::min(900,area.h-120));}}
    SDL_free(ids);std::string text;if(!hui::save::read_file(path,&text,16384))return s;
    auto j=nlohmann::json::parse(text,nullptr,false);if(!j.is_object())return s;
    if(j.contains("width")&&j["width"].is_number_integer())s.width=std::clamp(j["width"].get<int>(),960,7680);
    if(j.contains("height")&&j["height"].is_number_integer())s.height=std::clamp(j["height"].get<int>(),540,4320);
    if(j.contains("fullscreen")&&j["fullscreen"].is_boolean())s.fullscreen=j["fullscreen"].get<bool>();
    if(j.contains("borderless")&&j["borderless"].is_boolean())s.borderless=j["borderless"].get<bool>();
    s.borderless=s.fullscreen&&s.borderless;
    if(j.contains("vsync")&&j["vsync"].is_boolean())s.vsync=j["vsync"].get<bool>();
    if(j.contains("frame_limit")&&j["frame_limit"].is_number_integer())s.frame_limit=std::clamp(j["frame_limit"].get<int>(),0,360);
    return s;
}
void save_video_settings(const std::string&path,const DesktopVideoSettings&s){
    const auto error=hui::save::write_atomic(path,nlohmann::json({{"width",s.width},{"height",s.height},{"fullscreen",s.fullscreen},{"borderless",s.fullscreen&&s.borderless},{"vsync",s.vsync},{"frame_limit",s.frame_limit}}).dump(2));
    if(!error.empty())hui::sys::log("[Windows] video preferences: %s",error.c_str());
}
}

#endif // _WIN32
