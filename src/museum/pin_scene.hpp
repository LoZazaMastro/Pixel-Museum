// Pixel Museum - one physical enamel pin, loaded only for inspection.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/object_scene.hpp"
#include <string>

namespace museum {
class PinScene {
public:
    void set_root(std::string root){release();root_=std::move(root);}
    // Call on the GL thread, outside an active UI draw batch. Empty badge or
    // zero viewport releases the single cached mesh and render targets.
    unsigned render(const std::string& badge, bool unlocked, int width, int height,
                    float yaw, float pitch, float zoom, float pan_y = 0);
    void release();
    const std::string& error() const { return error_; }
private:
    ObjectScene scene_;
    std::string attempted_,error_,root_=".";
    bool initialized_=false;
};
}
