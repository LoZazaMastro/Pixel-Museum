// Pixel Museum - platform-neutral desktop display preferences.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#if defined(MUSEUM_DESKTOP)
#include <algorithm>
#include <cstdint>
#include <string_view>
#include <vector>
namespace museum {
constexpr std::string_view desktop_aspect(int width,int height){
    if(width<960||height<540||width>16384||height>16384)return {};
    if(width*9==height*16)return "16:9";
    if(width*9==height*32)return "32:9";
    if(width*10==height*32)return "32:10";
    // 2560x1080, 3440x1440 and 3840x1600 share the 21:9 display family.
    if(width*4>=height*9&&width*2<=height*5)return "21:9";
    return {};
}

// The main content keeps its original coordinates. Only the canvas reaches
// past its edges when the window has room for a longer timeline.
constexpr float desktop_canvas_left(int width,int height){
    return height>0?std::min(0.f,(1920.f-1080.f*width/height)*.5f):0.f;
}

struct DesktopDisplayMode {
    int width=1920,height=1080;
    bool operator==(const DesktopDisplayMode&)const=default;
};
inline constexpr DesktopDisplayMode desktop_window_presets[]={
    {1280,720},{1600,900},{1920,1080},{2560,1080},{2560,1440},
    {3440,1440},{3840,1600},{3840,2160},{5120,2160}
};
inline bool desktop_resolution_listed(DesktopDisplayMode mode){
    const auto aspect=desktop_aspect(mode.width,mode.height);
    return !aspect.empty()&&(aspect!="21:9"||mode.height>=1080);
}
struct DesktopDisplayModes {
    std::vector<DesktopDisplayMode> exclusive,windowed;
};
struct DesktopVideoSettings {
    int width=1920,height=1080;
    bool fullscreen=false,vsync=true;
    // Desktop fullscreen keeps the display's native mode; false is exclusive.
    bool borderless=false;
    // Zero allows an uncapped presentation rate (vsync can still cap it).
    int frame_limit=60;
    bool operator==(const DesktopVideoSettings&)const=default;
};

class DesktopFramePacer {
public:
    std::uint64_t delay_ns(const DesktopVideoSettings& settings,double refresh,
                           std::uint64_t now){
        constexpr std::uint64_t second=1'000'000'000;
        // VSync alone caps a matching display, including fractional modes
        // such as 59.94 Hz. Waiting here too can miss a refresh entirely.
        if(settings.frame_limit<=0||(settings.vsync&&refresh<=settings.frame_limit+.25)){
            next_frame_=0;
            return 0;
        }
        const auto interval=second/std::uint64_t(settings.frame_limit);
        if(!next_frame_||limit_!=settings.frame_limit||vsync_!=settings.vsync||refresh_!=refresh||
           now>next_frame_+interval){
            limit_=settings.frame_limit;
            vsync_=settings.vsync;
            refresh_=refresh;
            next_frame_=now+interval;
        }
        // On faster displays present on the closest refresh. Keep the target
        // tied to a clock so 60 on 144 Hz alternates two and three refreshes.
        const auto lead=settings.vsync?std::uint64_t(.5*second/refresh):0;
        const auto deadline=next_frame_-lead;
        next_frame_+=interval;
        return deadline>now?deadline-now:0;
    }
private:
    std::uint64_t next_frame_=0;
    int limit_=0;
    bool vsync_=false;
    double refresh_=0;
};
}
#endif
