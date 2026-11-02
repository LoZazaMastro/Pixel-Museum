#if defined(_WIN32)
// Pixel Museum - physical keyboard, pointer and hot-pluggable standard pads.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/windows/desktop_input.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <cmath>
namespace museum::desktop {
namespace {
std::uint32_t key(SDL_Scancode code,bool text){
    using namespace hui::pad_bits;
    if(code==SDL_SCANCODE_ESCAPE)return kCircle;
    if(text)return 0;
    switch(code){
    case SDL_SCANCODE_UP:case SDL_SCANCODE_W:return kUp;
    case SDL_SCANCODE_DOWN:case SDL_SCANCODE_S:return kDown;
    case SDL_SCANCODE_LEFT:case SDL_SCANCODE_A:return kLeft;
    case SDL_SCANCODE_RIGHT:case SDL_SCANCODE_D:return kRight;
    case SDL_SCANCODE_RETURN:case SDL_SCANCODE_KP_ENTER:return kCross;
    case SDL_SCANCODE_SPACE:return kSquare;
    case SDL_SCANCODE_R:return kTriangle;
    case SDL_SCANCODE_Q:return kL1;
    case SDL_SCANCODE_E:return kR1;
    case SDL_SCANCODE_Z:return kL2;
    case SDL_SCANCODE_C:return kR2;
    case SDL_SCANCODE_TAB:return kTouchpad;
    case SDL_SCANCODE_O:case SDL_SCANCODE_F10:return kOptions;
    case SDL_SCANCODE_LSHIFT:case SDL_SCANCODE_RSHIFT:return kL3;
    case SDL_SCANCODE_X:case SDL_SCANCODE_V:return kR3;
    default:return 0;
    }
}
}
Input::~Input(){stop_rumble();for(auto*p:pads_)if(p)SDL_CloseGamepad(p);}
void Input::stop_rumble(){if(!rumbling_)return;for(auto*p:pads_)if(p)SDL_RumbleGamepad(p,0,0,0);rumbling_=false;}
void Input::refresh_gamepads(){
    for(auto& p:pads_)if(p&&!SDL_GamepadConnected(p)){SDL_CloseGamepad(p);p=nullptr;}
    int count=0;auto*ids=SDL_GetGamepads(&count);
    for(int i=0;i<count;++i){
        if(std::any_of(pads_.begin(),pads_.end(),[&](auto*p){return p&&SDL_GetGamepadID(p)==ids[i];}))continue;
        auto slot=std::find(pads_.begin(),pads_.end(),nullptr);if(slot==pads_.end())break;
        *slot=SDL_OpenGamepad(ids[i]);if(*slot){
            SDL_SetGamepadSensorEnabled(*slot,SDL_SENSOR_ACCEL,true);
            SDL_SetGamepadSensorEnabled(*slot,SDL_SENSOR_GYRO,true);
            hui::sys::log("[Windows] controller %s",SDL_GetGamepadName(*slot));
        }
    }
    SDL_free(ids);
}
hui::PadSample Input::sample(SDL_Gamepad*p,std::uint64_t now){
    hui::PadSample out;out.timestamp_us=now;
    if(!p||!SDL_GamepadConnected(p))return out;out.connected=true;
    using namespace hui::pad_bits;
    for(auto[b,mask]:{std::pair{SDL_GAMEPAD_BUTTON_DPAD_UP,kUp},{SDL_GAMEPAD_BUTTON_DPAD_DOWN,kDown},
        {SDL_GAMEPAD_BUTTON_DPAD_LEFT,kLeft},{SDL_GAMEPAD_BUTTON_DPAD_RIGHT,kRight},
        {SDL_GAMEPAD_BUTTON_SOUTH,kCross},{SDL_GAMEPAD_BUTTON_EAST,kCircle},{SDL_GAMEPAD_BUTTON_WEST,kSquare},
        {SDL_GAMEPAD_BUTTON_NORTH,kTriangle},{SDL_GAMEPAD_BUTTON_LEFT_SHOULDER,kL1},
        {SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER,kR1},{SDL_GAMEPAD_BUTTON_LEFT_STICK,kL3},
        {SDL_GAMEPAD_BUTTON_RIGHT_STICK,kR3},{SDL_GAMEPAD_BUTTON_START,kOptions},
        {SDL_GAMEPAD_BUTTON_BACK,kTouchpad},{SDL_GAMEPAD_BUTTON_TOUCHPAD,kTouchpad}})
        if(SDL_GetGamepadButton(p,b))out.buttons|=mask;
    const auto axis=[&](SDL_GamepadAxis a){return std::uint8_t((int(SDL_GetGamepadAxis(p,a))+32768)/256);};
    out.left_x=axis(SDL_GAMEPAD_AXIS_LEFTX);out.left_y=axis(SDL_GAMEPAD_AXIS_LEFTY);
    out.right_x=axis(SDL_GAMEPAD_AXIS_RIGHTX);out.right_y=axis(SDL_GAMEPAD_AXIS_RIGHTY);
    out.l2=std::uint8_t(std::max(0,int(SDL_GetGamepadAxis(p,SDL_GAMEPAD_AXIS_LEFT_TRIGGER)))/129);
    out.r2=std::uint8_t(std::max(0,int(SDL_GetGamepadAxis(p,SDL_GAMEPAD_AXIS_RIGHT_TRIGGER)))/129);
    float accel[3]{},gyro[3]{};
    if(SDL_GetGamepadSensorData(p,SDL_SENSOR_ACCEL,accel,3)&&SDL_GetGamepadSensorData(p,SDL_SENSOR_GYRO,gyro,3)){
        const float magnitude=std::sqrt(accel[0]*accel[0]+accel[1]*accel[1]+accel[2]*accel[2]);
        out.motion.available=magnitude>.001f;
        for(int j=0;j<3;++j){out.motion.acceleration[j]=accel[j]/SDL_STANDARD_GRAVITY;out.motion.direction[j]=magnitude>.001f?accel[j]/magnitude:0;out.motion.angular_velocity[j]=gyro[j];}
    }
    for(int i=0;i<2;++i){bool down=false;float x=0,y=0,pressure=0;
        if(SDL_GetGamepadTouchpadFinger(p,0,i,&down,&x,&y,&pressure)&&down){out.touch.available=true;out.touch.points[out.touch.count++]={x,y,std::uint8_t(i)};}}
    return out;
}
hui::InputFrame Input::poll(SDL_Window*window,bool text,bool&quit,bool&toggle){
    if(text!=text_active_){if(text)SDL_StartTextInput(window);else SDL_StopTextInput(window);text_active_=text;}
    hui::InputFrame desktop;std::uint32_t tapped=0;SDL_Event event;
    while(SDL_PollEvent(&event)){
        if(event.type==SDL_EVENT_QUIT)quit=true;
        if(event.type==SDL_EVENT_GAMEPAD_ADDED||event.type==SDL_EVENT_GAMEPAD_REMOVED)refresh_gamepads();
        if(event.type==SDL_EVENT_GAMEPAD_BUTTON_DOWN||event.type==SDL_EVENT_GAMEPAD_AXIS_MOTION){
            if(event.type==SDL_EVENT_GAMEPAD_BUTTON_DOWN||std::abs(event.gaxis.value)>9000){
                auto*active=SDL_GetGamepadFromID(event.type==SDL_EVENT_GAMEPAD_BUTTON_DOWN?event.gbutton.which:event.gaxis.which);
                const auto type=active?SDL_GetGamepadType(active):SDL_GAMEPAD_TYPE_UNKNOWN;
                style_=(type==SDL_GAMEPAD_TYPE_PS5||type==SDL_GAMEPAD_TYPE_PS4||type==SDL_GAMEPAD_TYPE_PS3)?hui::DesktopControllerStyle::dualsense:hui::DesktopControllerStyle::generic;
            }
        }
        if(event.type==SDL_EVENT_KEY_DOWN){
            style_=hui::DesktopControllerStyle::keyboard_mouse;desktop.keyboard_active=true;
            if(event.key.scancode==SDL_SCANCODE_ESCAPE&&!event.key.repeat)desktop.desktop_escape_pressed=true;
            if(event.key.scancode==SDL_SCANCODE_F11&&!event.key.repeat)toggle=true;
            if(event.key.scancode==SDL_SCANCODE_F&&!text&&!event.key.repeat)desktop.search_pressed=true;
            if((event.key.mod&SDL_KMOD_CTRL)&&event.key.scancode==SDL_SCANCODE_F&&!event.key.repeat)desktop.search_pressed=true;
            if(!event.key.repeat)tapped|=key(event.key.scancode,text);
            if(!text&&event.key.scancode==SDL_SCANCODE_PAGEDOWN)desktop.desktop_scroll+=300;
            if(!text&&event.key.scancode==SDL_SCANCODE_PAGEUP)desktop.desktop_scroll-=300;
            if(text){
                desktop.text_backspace|=event.key.scancode==SDL_SCANCODE_BACKSPACE;
                desktop.text_delete|=event.key.scancode==SDL_SCANCODE_DELETE;
                desktop.text_left|=event.key.scancode==SDL_SCANCODE_LEFT;
                desktop.text_right|=event.key.scancode==SDL_SCANCODE_RIGHT;
                desktop.text_home|=event.key.scancode==SDL_SCANCODE_HOME;
                desktop.text_end|=event.key.scancode==SDL_SCANCODE_END;
                desktop.text_submit|=event.key.scancode==SDL_SCANCODE_RETURN||event.key.scancode==SDL_SCANCODE_KP_ENTER;
                desktop.text_select_all|=(event.key.mod&SDL_KMOD_CTRL)&&event.key.scancode==SDL_SCANCODE_A;
                if((event.key.mod&SDL_KMOD_CTRL)&&event.key.scancode==SDL_SCANCODE_V){char*p=SDL_GetClipboardText();if(p){desktop.text_utf8+=p;SDL_free(p);}}
            }
        }
        if(event.type==SDL_EVENT_TEXT_INPUT)desktop.text_utf8+=event.text.text;
        if(event.type==SDL_EVENT_MOUSE_MOTION){desktop.pointer.moved=true;desktop.pointer.delta_x+=event.motion.xrel;desktop.pointer.delta_y+=event.motion.yrel;style_=hui::DesktopControllerStyle::keyboard_mouse;}
        if(event.type==SDL_EVENT_MOUSE_BUTTON_DOWN){desktop.pointer.primary_pressed|=event.button.button==SDL_BUTTON_LEFT;desktop.pointer.secondary_pressed|=event.button.button==SDL_BUTTON_RIGHT;style_=hui::DesktopControllerStyle::keyboard_mouse;}
        if(event.type==SDL_EVENT_MOUSE_BUTTON_UP)desktop.pointer.primary_released|=event.button.button==SDL_BUTTON_LEFT;
        if(event.type==SDL_EVENT_MOUSE_WHEEL){desktop.pointer.wheel_y+=event.wheel.y*(event.wheel.direction==SDL_MOUSEWHEEL_FLIPPED?-1.f:1.f);style_=hui::DesktopControllerStyle::keyboard_mouse;}
        if(event.type==SDL_EVENT_WINDOW_FOCUS_LOST)desktop.focus_lost=true;
    }
    if(!pads_[0])refresh_gamepads();
    const auto now=std::uint64_t(hui::sys::monotonic_us());auto state=sample(pads_[0],now);
    const bool focused=(SDL_GetWindowFlags(window)&SDL_WINDOW_INPUT_FOCUS)!=0;
    focused_=focused;
    // A connected controller is not necessarily the device in use. Cancel an
    // already-playing pulse too, rather than merely ignoring the next one.
    if(!controller_active())stop_rumble();
    if(focused){int count=0;const bool*keys=SDL_GetKeyboardState(&count);for(int i=0;i<count;++i)if(keys[i])state.buttons|=key(SDL_Scancode(i),text);
        if(!text){
            if(keys[SDL_SCANCODE_A]||keys[SDL_SCANCODE_LEFT])state.left_x=0;
            if(keys[SDL_SCANCODE_D]||keys[SDL_SCANCODE_RIGHT])state.left_x=255;
            if(keys[SDL_SCANCODE_W]||keys[SDL_SCANCODE_UP])state.left_y=0;
            if(keys[SDL_SCANCODE_S]||keys[SDL_SCANCODE_DOWN])state.left_y=255;
            if(keys[SDL_SCANCODE_J])state.right_x=0;if(keys[SDL_SCANCODE_L])state.right_x=255;
            if(keys[SDL_SCANCODE_I])state.right_y=0;if(keys[SDL_SCANCODE_K])state.right_y=255;
        }state.connected=true;}
    else{state.buttons=0;state.left_x=state.left_y=state.right_x=state.right_y=128;state.l2=state.r2=0;state.connected=false;}
    auto frame=primary_.update(std::span(&state,1),now);
    frame.pressed|=hui::InputTracker::map_buttons(hui::PadSample{.buttons=tapped},false);
    auto second=sample(pads_[1],now);if(!focused)second.connected=false;
    auto f2=secondary_.update(std::span(&second,1),now);
    frame.secondary={f2.pressed,f2.held,f2.stick_y,f2.connected,f2.focus_lost,f2.touch};
    float mx=0,my=0;const auto buttons=SDL_GetMouseState(&mx,&my);int w=1920,h=1080;SDL_GetWindowSize(window,&w,&h);
    const float scale=std::max(.001f,std::min(w/1920.f,h/1080.f));
    desktop.pointer.x=(mx-(w-1920.f*scale)*.5f)/scale;desktop.pointer.y=(my-(h-1080.f*scale)*.5f)/scale;
    desktop.pointer.delta_x/=scale;desktop.pointer.delta_y/=scale;
    desktop.pointer.available=focused&&SDL_GetMouseFocus()==window&&style_==hui::DesktopControllerStyle::keyboard_mouse;
    desktop.pointer.primary_held=focused&&(buttons&SDL_BUTTON_LMASK);
    desktop.pointer.secondary_held=focused&&(buttons&SDL_BUTTON_RMASK);
    frame.pointer=desktop.pointer;frame.controller_style=style_;frame.keyboard_active=desktop.keyboard_active;
    frame.desktop_escape_pressed=desktop.desktop_escape_pressed;
    frame.text_utf8=std::move(desktop.text_utf8);frame.text_backspace=desktop.text_backspace;frame.text_delete=desktop.text_delete;
    frame.text_submit=desktop.text_submit;frame.text_home=desktop.text_home;frame.text_end=desktop.text_end;
    frame.text_left=desktop.text_left;frame.text_right=desktop.text_right;frame.text_select_all=desktop.text_select_all;
    frame.search_pressed=desktop.search_pressed;frame.focus_lost|=desktop.focus_lost;
    frame.desktop_scroll=desktop.desktop_scroll;
    return frame;
}
void Input::rumble(float strength,float seconds,unsigned index){
    if(!controller_active())return;
    if(auto*p=gamepad(index)){
        const auto type=SDL_GetGamepadType(p);
        const float gain=(type==SDL_GAMEPAD_TYPE_PS5||type==SDL_GAMEPAD_TYPE_PS4||type==SDL_GAMEPAD_TYPE_PS3)?1.f:.35f;
        const float finite_strength=std::isfinite(strength)?strength:0.f;
        const float finite_seconds=std::isfinite(seconds)?seconds:0.f;
        const auto low=std::uint16_t(std::clamp(finite_strength,0.f,1.f)*gain*65535);
        const auto high=std::uint16_t(low*.7f);
        rumbling_=rumbling_||low>0;
        SDL_RumbleGamepad(p,low,high,std::uint32_t(std::clamp(finite_seconds,0.f,2.f)*1000));
    }
}
}

#endif // _WIN32
