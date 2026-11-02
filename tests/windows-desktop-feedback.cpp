// Native SDL event and virtual-controller regression checks. No installed data
// or real controller is modified; the virtual gamepad exists in this process.
#include "platform/windows/desktop_input.hpp"
#include "platform/windows/tactile_rumble.hpp"
#include "audio/controller_feedback.hpp"
#include "ui/glyphs.hpp"
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <limits>

namespace hui::sys {
std::int64_t monotonic_us(){return std::int64_t(SDL_GetTicksNS()/1000);}
void log(const char*,...){}
}
namespace museum::desktop {
struct InputInspection {
    static void focus(Input&i,bool value){i.focused_=value;}
    static void isolate(Input&i,SDL_JoystickID virtual_id){
        for(auto&p:i.pads_){if(p)SDL_CloseGamepad(p);p=nullptr;}
        i.pads_[0]=SDL_OpenGamepad(virtual_id);assert(i.pads_[0]);
    }
};
}
struct Motors { unsigned calls=0;Uint16 low=0,high=0; };
static bool SDLCALL rumble(void*raw,Uint16 low,Uint16 high){auto&m=*static_cast<Motors*>(raw);++m.calls;m.low=low;m.high=high;return true;}
static std::string read(const char*path){std::ifstream f(path,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
int main(){
    using namespace hui;
    assert(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMEPAD));
    auto*window=SDL_CreateWindow("Pixel Museum input regression",960,540,SDL_WINDOW_HIDDEN);assert(window);
    Motors motors;SDL_VirtualJoystickDesc desc{};SDL_INIT_INTERFACE(&desc);
    desc.type=SDL_JOYSTICK_TYPE_GAMEPAD;desc.vendor_id=0x045e;desc.product_id=0x028e;
    desc.naxes=SDL_GAMEPAD_AXIS_COUNT;desc.nbuttons=SDL_GAMEPAD_BUTTON_COUNT;
    desc.axis_mask=(1u<<SDL_GAMEPAD_AXIS_COUNT)-1;desc.button_mask=(1u<<SDL_GAMEPAD_BUTTON_COUNT)-1;
    desc.name="Pixel Museum isolated Xbox test";desc.userdata=&motors;desc.Rumble=rumble;
    const auto id=SDL_AttachVirtualJoystick(&desc);assert(id);
    {
        museum::desktop::Input input;bool quit=false,toggle=false;
        input.poll(window,false,quit,toggle);assert(input.gamepad());
        museum::desktop::InputInspection::isolate(input,id);
        assert(SDL_GetGamepadID(input.gamepad())==id);
        SDL_Event event{};event.type=SDL_EVENT_GAMEPAD_BUTTON_DOWN;event.gbutton.which=id;event.gbutton.button=SDL_GAMEPAD_BUTTON_SOUTH;event.gbutton.down=true;assert(SDL_PushEvent(&event));
        auto frame=input.poll(window,false,quit,toggle);assert(frame.controller_style==DesktopControllerStyle::generic);
        // A hidden test window has no OS focus; isolate the focus gate from the
        // actual SDL rumble transport after exercising native event routing.
        museum::desktop::InputInspection::focus(input,true);assert(input.controller_active());
        input.rumble(1,.1f);assert(motors.low>0&&motors.low<=22938&&motors.high<motors.low);
        const auto before=motors.calls;
        event={};event.type=SDL_EVENT_KEY_DOWN;event.key.scancode=SDL_SCANCODE_ESCAPE;event.key.down=true;assert(SDL_PushEvent(&event));
        frame=input.poll(window,false,quit,toggle);
        assert(frame.desktop_escape_pressed&&frame.is_pressed(Action::back));
        assert(frame.controller_style==DesktopControllerStyle::keyboard_mouse&&motors.calls>before&&motors.low==0&&motors.high==0);
        museum::desktop::InputInspection::focus(input,true);const auto stopped=motors.calls;
        input.rumble(1,1);assert(motors.calls==stopped); // connected but not in use
        frame=input.poll(window,false,quit,toggle);assert(!frame.desktop_escape_pressed);
        event={};event.type=SDL_EVENT_GAMEPAD_BUTTON_DOWN;event.gbutton.which=id;event.gbutton.button=SDL_GAMEPAD_BUTTON_SOUTH;event.gbutton.down=true;assert(SDL_PushEvent(&event));
        input.poll(window,false,quit,toggle);museum::desktop::InputInspection::focus(input,true);
        input.rumble(.4f,.2f);assert(motors.low>0);
        event={};event.type=SDL_EVENT_MOUSE_MOTION;event.motion.xrel=6;assert(SDL_PushEvent(&event));
        frame=input.poll(window,false,quit,toggle);assert(frame.controller_style==DesktopControllerStyle::keyboard_mouse&&motors.low==0);
        for(const auto dimensions:{std::pair{1920,1080},std::pair{3840,2160}}){
            assert(SDL_SetWindowSize(window,dimensions.first,dimensions.second));
            input.poll(window,false,quit,toggle);
            int w=0,h=0;assert(SDL_GetWindowSize(window,&w,&h));
            const float scale=std::min(w/1920.f,h/1080.f);
            event={};event.type=SDL_EVENT_MOUSE_MOTION;event.motion.xrel=22*scale;event.motion.yrel=-11*scale;
            assert(SDL_PushEvent(&event));frame=input.poll(window,false,quit,toggle);
            assert(std::abs(frame.pointer.delta_x-22)<.01f&&std::abs(frame.pointer.delta_y+11)<.01f);
        }
        std::puts("PASS: native SDL mouse displacement remains22x11logical pixels at1080p and4K.");
        std::puts("PASS: real SDL events select Xbox/keyboard/mouse, Escape is contextual, Xbox motors reduced and cancelled immediately on mouse/keyboard.");
    }
    SDL_DetachVirtualJoystick(id);SDL_DestroyWindow(window);SDL_Quit();

    ui::Feedback feedback;feedback.feel(audio::Tactile::rotate,.5f,.1f);
    assert(windows::desktop_feedback(feedback,true,true,false,false).seconds==0);
    assert(windows::desktop_feedback(feedback,false,true,true,true).seconds==0);
    const auto tap=windows::desktop_feedback(feedback,true,true,false,true);assert(tap.strength<=.10f&&tap.seconds<=.025f);
    assert(windows::desktop_feedback(feedback,true,true,true,false).seconds>0);
    assert(windows::desktop_feedback(feedback,true,false,false,false).seconds>0);
    std::puts("PASS: Xbox interface rotations/focus silent, one tiny tap per actual panel/timeline transition; experience and PlayStation feedback preserved.");

    audio::ControllerFeedback signals;signals.enabled(true);assert(signals.post({audio::Tactile::rotate,.3f,.1f}));
    std::array<float,512>pcm{};signals.render_haptics(pcm.data(),256);assert(std::any_of(pcm.begin(),pcm.end(),[](float x){return x!=0;}));
    signals.tactile_enabled(false);signals.tactile_enabled(true);signals.render_haptics(pcm.data(),256);assert(std::all_of(pcm.begin(),pcm.end(),[](float x){return x==0;}));
    signals.tactile_enabled(false);assert(!signals.post({}));std::array<float,256>speech{},heard{};speech.fill(.1f);
    signals.submit_speaker(speech.data(),256);signals.render_speaker(heard.data(),256);assert(std::all_of(heard.begin(),heard.end(),[](float x){return x>.09f;}));
    std::puts("PASS: switching to mouse flushes queued and playing haptics without muting controller cultural audio.");

    gfx::Font regular,mono;assert(regular.load(read("assets/fonts/inter-regular.huifont")));assert(mono.load(read("assets/fonts/dejavu-sans-mono.huifont")));
    ui::Fonts fonts;fonts.regular=fonts.semibold=fonts.display=fonts.pixel=fonts.hand={&regular,1};fonts.mono={&mono,2};
    ui::install_inline_controls();std::array<std::size_t,3>counts{};
    for(unsigned n=0;n<3;++n){ui::set_control_device(ui::ControlDevice(n));gfx::DrawList out;
        ui::draw_button(out,fonts,ui::GlyphStyle::mono(gfx::Color::rgb(0),gfx::Color::rgb(0,0)),ui::Button::cross,0,50,32);counts[n]=out.instances().size();
        const auto width=ui::text(out,fonts.regular,"Press {cross} then {touchpad} or {dpad}.",0,110,24,gfx::Color::rgb(0));
        assert(std::abs(width-fonts.regular.measure("Press {cross} then {touchpad} or {dpad}.",24))<.01f);
        for(const auto&i:out.instances())for(float v:i.rect)assert(std::isfinite(v));
        auto lines=ui::paragraph_lines(fonts.regular,"Use {triangle} and {dpad} to choose, {cross} to play.",24,230,99);for(const auto&line:lines.lines)assert(fonts.regular.measure(line,24)<=230.01f);
    }
    assert(counts[0]!=counts[1]&&counts[0]!=counts[2]&&counts[1]!=counts[2]);
    std::puts("PASS: distinct PlayStation/Xbox/keyboard vector glyphs; inline measurement, drawing and wrapping agree.");
}
