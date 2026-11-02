// Pixel Museum - platform-neutral desktop display preferences.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#if defined(MUSEUM_DESKTOP)
namespace museum {
struct DesktopDisplayMode {
    int width=1920,height=1080;
    bool operator==(const DesktopDisplayMode&)const=default;
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
}
#endif
