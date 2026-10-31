// Pixel Museum - native geometry and PBR materials, not a rotated flat sprite.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/pin_scene.hpp"
#include <algorithm>
#include <cmath>

namespace museum {
unsigned PinScene::render(const std::string& badge,bool unlocked,int width,int height,
                          float yaw,float pitch,float zoom,float pan_y){
    if(badge.empty()||width<=0||height<=0){release();return 0;}
    if(badge.size()>96||badge.find_first_not_of(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")!=std::string::npos){
        error_="Invalid pin identifier";return 0;
    }
    if(!std::isfinite(yaw)||!std::isfinite(pitch)||!std::isfinite(zoom)||!std::isfinite(pan_y))return 0;
    // One physical mesh and one colour texture per pin. The UI desaturates the
    // rendered result for locked pins; curator preview keeps the original colour.
    (void)unlocked;
    const std::string key=badge+"-colour";
    if(attempted_!=key){
        release();attempted_=key;
        initialized_=scene_.init();
        if(!initialized_||!scene_.load(root_+"/assets/trophies/pins/"+key+".glb")){
            error_=scene_.error();return 0;
        }
    }
    if(!initialized_||!scene_.ready())return 0;
    constexpr float tau=6.28318530718f;
    return scene_.render(std::remainder(yaw,tau),width,height,
                         std::remainder(pitch,tau),false,std::clamp(zoom,.55f,2.5f),0,std::clamp(pan_y,-.65f,.65f),true);
}
void PinScene::release(){
    scene_.release();initialized_=false;attempted_.clear();error_.clear();
}
}
