// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/desktop_settings.hpp"
#include <SDL3/SDL.h>
#include <string>
#include <vector>
namespace museum::desktop {
class Display {
public:
    ~Display();
    bool open(const DesktopVideoSettings&,bool hidden);
    bool apply(const DesktopVideoSettings&);
    std::vector<DesktopDisplayMode> modes()const;
    float refresh_hz()const;
    int width()const;int height()const;
    SDL_Window* window()const{return window_;}
    void swap(){SDL_GL_SwapWindow(window_);}
    const std::string& error()const{return error_;}
private:
    SDL_Window*window_=nullptr;SDL_GLContext context_=nullptr;std::string error_;
};
DesktopVideoSettings load_video_settings(const std::string& path);
void save_video_settings(const std::string& path,const DesktopVideoSettings&);
}
