// ps5-homebrew-ui - DualSense input through scePad.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#include "platform/ps5/pad.hpp"
#include "platform/ps5/pad_state.hpp"

#include "platform/ps5/system.hpp"

#include <cstddef>
#include <cstdint>
#include <algorithm>
#include <cmath>

namespace
{

using hui::ps5::detail::RawPadSample;

constexpr int kAlreadyInitialized = static_cast<int>(0x80960003);
// The classic two-motor rumble (the other mode is the DualSense's haptics).
constexpr int kVibrationModeCompatible = 2;
constexpr int kVibrationModeAdvanced = 1;

struct PadVibration
{
    std::uint8_t large_motor;
    std::uint8_t small_motor;
};

struct PadColor
{
    std::uint8_t r;
    std::uint8_t g;
    std::uint8_t b;
    std::uint8_t reserved;
};

} // namespace

extern "C"
{
    int sceUserServiceInitialize(const void *params);
    int sceUserServiceTerminate(void);
    int sceUserServiceGetInitialUser(int *user);
    int sceUserServiceGetLoginUserIdList(int users[4]);
    int scePadInit(void);
    int scePadOpen(int user, int type, int index, const void *parameters);
    int scePadRead(int handle, RawPadSample *samples, int count);
    int scePadReadState(int handle, RawPadSample *sample);
    int scePadClose(int handle);
    int scePadSetVibrationMode(int handle, int mode);
    int scePadSetVibration(int handle, const PadVibration *vibration);
    int scePadSetLightBar(int handle, const PadColor *color);
    int scePadSetMotionSensorState(int handle, bool enable);
}

namespace hui::ps5
{

Pad::~Pad()
{
    close();
}

bool Pad::open()
{
    const int init = sceUserServiceInitialize(nullptr);
    owns_user_service_ = init == 0;
    if (init != 0 && init != kAlreadyInitialized)
        sys::log("[HUI] pad sceUserServiceInitialize=0x%08x", static_cast<unsigned>(init));
    if (sceUserServiceGetInitialUser(&user_) != 0)
    {
        sys::log("[HUI] pad no initial user");
        return false;
    }
    const int pad_init = scePadInit();
    if (pad_init != 0)
        sys::log("[HUI] pad scePadInit=0x%08x", static_cast<unsigned>(pad_init));
    // The pad service can lag behind title start; retry briefly.
    for (int attempt = 0; attempt < 20; ++attempt)
    {
        handle_ = scePadOpen(user_, 0, 0, nullptr);
        if (handle_ >= 0)
        {
            const int mode = scePadSetVibrationMode(handle_, advanced_requested_?kVibrationModeAdvanced:kVibrationModeCompatible);
            advanced_enabled_=advanced_requested_&&mode==0;advanced_attempted_=true;advanced_request_ok_=mode==0;
            if(mode!=0&&advanced_requested_)scePadSetVibrationMode(handle_,kVibrationModeCompatible);
            sys::log("[HUI] pad open user=0x%08x handle=%d attempts=%d vibration_mode=0x%x",
                     static_cast<unsigned>(user_), handle_, attempt + 1,
                     static_cast<unsigned>(mode));
            return true;
        }
        sys::sleep_us(50000);
    }
    sys::log("[HUI] pad scePadOpen failed=0x%08x", static_cast<unsigned>(handle_));
    handle_ = -1;
    return false;
}

bool Pad::open_secondary(int primary_user)
{
    if(handle_>=0)return true;
    int users[4]={-1,-1,-1,-1};
    if(sceUserServiceGetLoginUserIdList(users)!=0)return false;
    for(int user:users){
        if(user<0||user==primary_user)continue;
        const int candidate=scePadOpen(user,0,0,nullptr);
        if(candidate<0)continue;
        RawPadSample state{};
        if(scePadReadState(candidate,&state)!=0||!state.connected){scePadClose(candidate);continue;}
        handle_=candidate;user_=user;owns_user_service_=false;
        initial_sample_=detail::decode_pad_state(state,false);initial_sample_pending_=true;
        advanced_enabled_=advanced_attempted_=false;light_bar_=0xffffffffu;
        sys::log("[Museum] second controller open user=0x%08x handle=%d",unsigned(user_),handle_);
        return true;
    }
    return false;
}

void Pad::set_light_bar(std::uint8_t r, std::uint8_t g, std::uint8_t b)
{
    const std::uint32_t packed =
        (static_cast<std::uint32_t>(r) << 16) | (static_cast<std::uint32_t>(g) << 8) | b;
    if (handle_ < 0 || packed == light_bar_)
        return;
    light_bar_ = packed;
    const PadColor color{r, g, b, 0};
    const int result = scePadSetLightBar(handle_, &color);
    if (result != 0)
        sys::log("[HUI] pad scePadSetLightBar=0x%08x", static_cast<unsigned>(result));
}

void Pad::rumble(float strength, float seconds)
{
    if(advanced_enabled_||handle_<0||!std::isfinite(strength)||!std::isfinite(seconds)||strength<=0||seconds<=0)return;
    const float clamped=std::clamp(strength,0.f,1.f);
    // The earlier mapping left the large actuator OFF for every experience
    // action and sent only 18-40/255 to the small one. Use both actuators even
    // for a short, quiet UI pulse so the physical response is perceptible.
    const float weight=std::sqrt(clamped);
    const PadVibration vibration{static_cast<std::uint8_t>(weight*255),static_cast<std::uint8_t>((.12f+.88f*weight)*255)};
    int result=scePadSetVibration(handle_,&vibration);
    if(result!=0){const int mode=scePadSetVibrationMode(handle_,kVibrationModeCompatible);if(mode==0)result=scePadSetVibration(handle_,&vibration);}
    if(rumble_reports_<12){sys::log("[Museum] controller pulse motors=%u/%u duration=%.3f result=0x%08x",unsigned(vibration.large_motor),unsigned(vibration.small_motor),seconds,unsigned(result));++rumble_reports_;}
    if(result==0)rumble_left_=std::clamp(seconds,.035f,.3f);
}

void Pad::tick(float dt, bool active)
{
    if (rumble_left_ <= 0.0f)
        return;
    if(!active){
        rumble_left_=0;
        if(handle_>=0&&!advanced_enabled_){const PadVibration stop{0,0};const int result=scePadSetVibration(handle_,&stop);sys::log("[Museum] controller pulse cancelled off focus result=0x%08x",unsigned(result));}
        return;
    }
    rumble_left_ -= dt;
    if (rumble_left_ <= 0.0f && handle_ >= 0)
    {
        const PadVibration stop{0, 0};
        scePadSetVibration(handle_, &stop);
    }
}

void Pad::close()
{
    if (handle_ >= 0)
    {
        if(motion_enabled_)scePadSetMotionSensorState(handle_,false);
        const PadVibration stop{0, 0};
        scePadSetVibration(handle_, &stop);
        scePadClose(handle_);
    }
    handle_ = -1;
    if (owns_user_service_)
        sceUserServiceTerminate();
    owns_user_service_ = false;last_connected_=false;
    initial_sample_pending_=false;
    motion_requested_ = motion_enabled_ = false;advanced_enabled_=false;advanced_attempted_=false;
}

bool Pad::set_advanced_haptics(bool enabled)
{
    if(enabled==advanced_requested_&&advanced_attempted_&&handle_>=0)return advanced_request_ok_;
    advanced_requested_=enabled;advanced_attempted_=false;
    if(handle_<0)return false;
    const PadVibration stop{0,0};scePadSetVibration(handle_,&stop);rumble_left_=0;
    const int result=scePadSetVibrationMode(handle_,enabled?kVibrationModeAdvanced:kVibrationModeCompatible);
    advanced_attempted_=true;advanced_request_ok_=result==0;
    if(result==0)advanced_enabled_=enabled;
    else if(enabled){const int fallback=scePadSetVibrationMode(handle_,kVibrationModeCompatible);if(fallback==0)advanced_enabled_=false;}
    sys::log("[Museum] advanced haptics request=%s result=0x%08x",enabled?"on":"off",unsigned(result));
    return result==0;
}

bool Pad::set_motion_enabled(bool enabled)
{
    if(handle_<0)return false;
    if(enabled==motion_requested_)return motion_enabled_==enabled;
    motion_requested_=enabled;motion_reports_=0;
    const int result=scePadSetMotionSensorState(handle_,enabled);
    motion_enabled_=enabled&&result==0;
    sys::log("[HUI] pad motion request=%s result=0x%08x",enabled?"on":"off",static_cast<unsigned>(result));
    return result==0;
}

std::size_t Pad::read(std::span<PadSample> out)
{
    if (out.empty())
        return 0;
    if(initial_sample_pending_){out[0]=initial_sample_;initial_sample_pending_=false;return 1;}
    if (handle_ < 0)
    {
        out[0] = PadSample{};
        return 1;
    }
    RawPadSample raw[64]{};
    const int limit = static_cast<int>(out.size() < 64 ? out.size() : 64);
    const int count = scePadRead(handle_, raw, limit);
    if(count<0){out[0]=PadSample{};return 1;}
    if (count <= 0)
        return 0;
    for (int index = 0; index < count; ++index)
    {
        out[static_cast<std::size_t>(index)]=detail::decode_pad_state(raw[index],motion_enabled_);
        const bool connected=out[static_cast<std::size_t>(index)].connected;
        if(connected&&!last_connected_){
            const int mode=scePadSetVibrationMode(handle_,advanced_requested_?kVibrationModeAdvanced:kVibrationModeCompatible);
            advanced_enabled_=advanced_requested_&&mode==0;advanced_attempted_=true;advanced_request_ok_=mode==0;
            if(mode!=0&&advanced_requested_)scePadSetVibrationMode(handle_,kVibrationModeCompatible);
            sys::log("[Museum] controller connected; advanced=%d vibration mode result=0x%08x",advanced_enabled_?1:0,unsigned(mode));
            if(motion_requested_){const int result=scePadSetMotionSensorState(handle_,true);motion_enabled_=result==0;sys::log("[Museum] controller reconnect motion result=0x%08x",unsigned(result));}
            rumble_reports_=0;
        }
        if(!connected){rumble_left_=0;advanced_enabled_=false;advanced_attempted_=false;motion_reports_=0;}
        const auto& motion=out[static_cast<std::size_t>(index)].motion;
        if(motion.available&&motion_reports_++==0)sys::log("[Museum] gyro first valid x=%.4f y=%.4f z=%.4f gravity=%.3f/%.3f/%.3f",double(motion.angular_velocity[0]),double(motion.angular_velocity[1]),double(motion.angular_velocity[2]),double(motion.direction[0]),double(motion.direction[1]),double(motion.direction[2]));
        last_connected_=connected;
    }
    return static_cast<std::size_t>(count);
}

} // namespace hui::ps5
