#if defined(_WIN32)
// Pixel Museum - the production museum renderer and content, on Windows.
// SPDX-License-Identifier: GPL-3.0-or-later
#include <GL/glew.h>
#include "platform/windows/desktop_display.hpp"
#include "platform/windows/desktop_input.hpp"
#include "platform/windows/desktop_audio.hpp"
#include "platform/windows/tactile_rumble.hpp"
#include "platform/windows/system.hpp"
#include "museum/screen.hpp"
#include "museum/music.hpp"
#include "museum/intro_audio.hpp"
#include "museum/localization.hpp"
#include "audio/cues.hpp"
#include "audio/museum_interface_mix.hpp"
#include "ui/glyphs.hpp"
#include "core/save_file.hpp"
#include "third_party/nlohmann/json.hpp"
#include "host/desktop_input_checks.hpp"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#include <SDL3/SDL_main.h>
#include <filesystem>
#include <vector>
#include <string>
#include <fstream>
#include <atomic>
#include <thread>
#include <cmath>
#include <fcntl.h>
#include <cstdlib>
#include <algorithm>
#include <exception>
namespace {
std::string normalized(const std::filesystem::path&p){
    const auto absolute=std::filesystem::absolute(p).lexically_normal();
    auto u=absolute.generic_u8string();const auto minimum=absolute.root_path().generic_u8string().size();
    while(u.size()>minimum&&u.back()==u8'/')u.pop_back();
    return {u.begin(),u.end()};
}
void screenshot(const std::string&path,int w,int h){
    std::vector<unsigned char>pixels(std::size_t(w)*h*4),top(pixels.size());
    glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,w,h,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
    for(int y=0;y<h;++y)std::copy_n(pixels.data()+std::size_t(h-1-y)*w*4,std::size_t(w)*4,top.data()+std::size_t(y)*w*4);
    stbi_write_png(path.c_str(),w,h,4,top.data(),w*4);
}
}
int main(int argc,char**argv){
    _set_fmode(_O_BINARY);_setmode(_fileno(stdin),_O_BINARY);
    SDL_SetHint(SDL_HINT_JOYSTICK_HIDAPI_PS5,"1");
    SDL_SetHint(SDL_HINT_AUDIO_DEVICE_SAMPLE_FRAMES,"512");
    if(!SDL_Init(SDL_INIT_VIDEO|SDL_INIT_AUDIO|SDL_INIT_GAMEPAD|SDL_INIT_SENSOR))return 1;
    int result=0;bool noninteractive=false;
    try{
        const char*base=SDL_GetBasePath();std::string root=normalized(std::filesystem::u8path(base?base:".")),data;
        bool hidden=false,smoke=false,ui_checks=false;int limit=0,preview=-1;std::string capture,select,script_path;
        for(int i=1;i<argc;++i){const std::string arg=argv[i];
            const auto value=[&](){if(i+1>=argc)throw std::runtime_error("Missing value for "+arg);return std::string(argv[++i]);};
            if(arg=="--root")root=normalized(std::filesystem::u8path(value()));
            else if(arg=="--data")data=normalized(std::filesystem::u8path(value()));
            else if(arg=="--smoke"){smoke=true;limit=300;hidden=true;noninteractive=true;}
            else if(arg=="--frames")limit=std::stoi(value());
            else if(arg=="--screenshot")capture=value();
            else if(arg=="--preview")preview=std::stoi(value());
            else if(arg=="--select")select=value();
            else if(arg=="--script")script_path=value();
            else if(arg=="--ui-checks"){ui_checks=true;hidden=true;noninteractive=true;}
        }
        if(data.empty())data=root;
        std::filesystem::create_directories(std::filesystem::u8path(data));
        if(!std::filesystem::exists(std::filesystem::u8path(root+"/content/catalog.json")))
            throw std::runtime_error("Pixel Museum's resources were not found. Please run the setup and choose the Pixel Museum installation folder.");
        std::freopen((data+"/session-windows.log").c_str(),"w",stdout);std::setvbuf(stdout,nullptr,_IOLBF,8192);
        hui::sys::log("[Windows] Pixel Museum 0.2.0 development / root=%s / data=%s",root.c_str(),data.c_str());
        auto video=museum::desktop::load_video_settings(data+"/video-settings.json");
        if(smoke){video.width=1280;video.height=720;video.fullscreen=false;video.borderless=false;video.vsync=false;video.frame_limit=60;}
        museum::desktop::Display display;
        if(!display.open(video,hidden))throw std::runtime_error(display.error());
        hui::ui::set_control_device(hui::ui::ControlDevice::keyboard_mouse);
        museum::Screen screen;
        // Curator access is confined to explicit render previews. A normal
        // launch must retain locked pins and deliver earned trophy notices.
        screen.set_trophy_curator_preview(preview>=0);
        if(!screen.init(root,data))throw std::runtime_error("The museum could not initialize. See session-windows.log in the installation folder.");
        screen.set_desktop_video_modes(display.modes(),video);
        if(ui_checks){const bool good=museum::DesktopInputInspection::run(screen);screen.shutdown();if(!good)result=1;}
        else {
        if(!select.empty())screen.select(select);
        if(preview>=0)screen.preview(preview);
        museum::Music music;
        if(!music.init(root+"/music/eras"))hui::sys::log("[Windows] ambience unavailable: %s",music.error().c_str());
        hui::audio::Mixer mixer;hui::audio::SoundBank sounds;
        const auto stats=sounds.load(root+"/assets/audio/museum-navigation");
        hui::sys::log("[Windows] original UI bank: %d clips",stats.files);
        sounds.set_pitch_jitter(0);sounds.set_recordings_only(true);
        museum::prepare_startup_sounds();
        hui::audio::ControllerFeedback signals;signals.enabled(true);
        museum::desktop::Audio audio;audio.master.store(screen.master_volume());
        audio.start(music,screen,mixer,signals);
        museum::desktop::Input input;
        std::vector<std::pair<int,nlohmann::json>>script;
        if(!script_path.empty()){
            std::ifstream f(std::filesystem::u8path(script_path));const auto j=nlohmann::json::parse(f,nullptr,false);
            if(j.is_array())for(const auto&entry:j)if(entry.is_object()&&entry.contains("frame"))script.emplace_back(entry["frame"].get<int>(),entry);
        }
        hui::PointerInput preview_pointer{};bool preview_pointer_active=false;
        bool quit=false,cursor_hidden=false,last_borderless_fullscreen=video.fullscreen&&video.borderless;auto last=SDL_GetTicksNS();std::uint64_t frame_number=0,next_controller_probe=0;float applied_sfx=-1;
        while(!quit){
            const auto frame_start=SDL_GetTicksNS();const float dt=std::clamp(float(frame_start-last)*1e-9f,.0001f,.1f);last=frame_start;
            bool fullscreen=false;auto frame=input.poll(display.window(),screen.wants_text_input(),quit,fullscreen);
            if(smoke){frame.focus_lost=false;frame.connected=true;}
            const bool pixel_cursor=frame.pointer.available&&frame.pointer.x>=0&&frame.pointer.x<1920&&frame.pointer.y>=0&&frame.pointer.y<1080;
            if(pixel_cursor!=cursor_hidden){if(pixel_cursor)SDL_HideCursor();else SDL_ShowCursor();cursor_hidden=pixel_cursor;}
            for(const auto&[at,event]:script)if(at==int(frame_number)){
                const auto action=[&](const char*name,hui::Action a){if(event.value("action",std::string())==name){frame.pressed|=hui::action_bit(a);frame.held|=hui::action_bit(a);}};
                action("confirm",hui::Action::confirm);action("back",hui::Action::back);action("menu",hui::Action::menu);action("touch",hui::Action::touch);action("west",hui::Action::west);action("north",hui::Action::north);
                if(event.contains("text"))frame.text_utf8=event["text"].get<std::string>();
                if(event.value("search",false))frame.search_pressed=true;
                if(event.contains("wheel"))frame.pointer.wheel_y=event["wheel"].get<float>();
                if(event.contains("pointer")){const auto& p=event["pointer"];preview_pointer_active=p.is_array()&&p.size()==2;if(preview_pointer_active){preview_pointer.available=true;preview_pointer.x=p[0].get<float>();preview_pointer.y=p[1].get<float>();}}
                if(event.contains("click")){frame.pointer.available=true;frame.pointer.primary_pressed=true;frame.pointer.x=event["click"][0].get<float>();frame.pointer.y=event["click"][1].get<float>();}
                if(event.contains("capture"))screenshot(event["capture"].get<std::string>(),display.width(),display.height());
            }
            if(preview_pointer_active){frame.pointer.available=true;frame.pointer.x=preview_pointer.x;frame.pointer.y=preview_pointer.y;}
            if(fullscreen){auto requested=video;if(video.fullscreen){last_borderless_fullscreen=video.borderless;requested.fullscreen=false;requested.borderless=false;}else{requested.fullscreen=true;requested.borderless=last_borderless_fullscreen;}
                if(display.apply(requested)){video=requested;if(video.fullscreen)last_borderless_fullscreen=video.borderless;screen.set_desktop_video_settings_applied(video);museum::desktop::save_video_settings(data+"/video-settings.json",video);}
                else display.apply(video);}
            if(frame_start>=next_controller_probe){
                audio.refresh_controller(input.gamepad()&&SDL_GetGamepadType(input.gamepad())==SDL_GAMEPAD_TYPE_PS5);
                if(audio.controller_audio()&&input.gamepad()){
                    SDL_RumbleGamepad(input.gamepad(),0,0,0);
                    std::array<std::uint8_t,47>effect{};effect[0]=0xA0;effect[5]=100;effect[7]=0x30;
                    if(!SDL_SendGamepadEffect(input.gamepad(),effect.data(),int(effect.size())))hui::sys::log("[Windows] DualSense speaker routing: %s",SDL_GetError());
                }
                next_controller_probe=frame_start+2000000000ull;
            }
            hui::ui::set_control_device(frame.controller_style==hui::DesktopControllerStyle::keyboard_mouse?hui::ui::ControlDevice::keyboard_mouse:
                frame.controller_style==hui::DesktopControllerStyle::dualsense?hui::ui::ControlDevice::playstation:hui::ui::ControlDevice::xbox);
            const auto navigation_before=screen.desktop_navigation_feedback_state();
            hui::ui::Feedback feedback;screen.handle(frame,feedback);
            const bool controller_input=input.controller_active();
            const bool xbox=frame.controller_style==hui::DesktopControllerStyle::generic;
            const bool pad_audio=audio.controller_audio();
            const bool tactile_audio=pad_audio&&controller_input&&frame.controller_style==hui::DesktopControllerStyle::dualsense;
            audio.master.store(screen.master_volume(),std::memory_order_relaxed);
            audio.culture_pad.store(screen.culture_audio_on_pad()&&pad_audio,std::memory_order_relaxed);
            if(applied_sfx!=screen.sfx_volume()){applied_sfx=screen.sfx_volume();mixer.set_bus_gain(hui::audio::Bus::ui,.18f*applied_sfx);mixer.set_bus_gain(hui::audio::Bus::sfx,applied_sfx);}
            signals.speaker_volume(screen.sfx_volume()*screen.pad_volume()*(pad_audio?screen.master_volume():1.f));
            signals.speaker_pcm_volume(screen.master_volume()*screen.pad_volume());
            signals.tactile_enabled(tactile_audio);
            for(auto cue:feedback.cues){cue.gain=hui::audio::museum_original::interface_gain(cue.cue,cue.gain);sounds.play(mixer,hui::audio::SoundSet::glass,cue);}
            for(const auto&cue:feedback.speaker_cues)signals.post_speaker(cue);
            if(tactile_audio)for(const auto&effect:feedback.tactile)signals.post(effect);
            auto conventional=hui::windows::desktop_feedback(feedback,controller_input,xbox,screen.experience_active(),navigation_before!=screen.desktop_navigation_feedback_state());
            // Conventional motors cannot express subtle PCM textures. Keep
            // object rotation, focus and timeline ticks silent on Xbox pads;
            // only accepted panel/exhibit/timeline transitions get a tiny tap.
            if(controller_input&&screen.secondary_controller_active()&&conventional.seconds>0)input.rumble(conventional.strength,conventional.seconds,1);
            int ordinal=-1;const int note=screen.take_startup_note(&ordinal);
            museum::route_startup_note(mixer,signals,note,ordinal,tactile_audio);
            if(!tactile_audio&&controller_input){
                if(!xbox){const auto startup=hui::windows::conventional_startup_note(note,ordinal);conventional.strength=std::max(conventional.strength,startup.strength);conventional.seconds=std::max(conventional.seconds,startup.seconds);}
                if(conventional.seconds>0)input.rumble(conventional.strength,conventional.seconds);
            }
            screen.update(dt);
            std::string desktop_url;
            if(screen.take_desktop_url_request(desktop_url)&&(desktop_url.starts_with("https://")||desktop_url.starts_with("http://")))SDL_OpenURL(desktop_url.c_str());
            if(screen.take_application_restart_request()&&screen.begin_application_restart())quit=true;
            museum::DesktopVideoSettings requested;
            if(screen.take_desktop_video_request(requested)){
                if(display.apply(requested)){video=requested;if(video.fullscreen)last_borderless_fullscreen=video.borderless;screen.set_desktop_video_settings_applied(video);museum::desktop::save_video_settings(data+"/video-settings.json",video);}
                else{const auto error=display.error();display.apply(video);screen.desktop_video_apply_failed(error);}
            }
            music.onboarding_active(screen.onboarding_active()||screen.collection_pending());music.select_year(screen.selected_year());music.select_timeline(screen.culture_timeline_active());
            music.archival_ambient_gain(screen.archival_ambient_gain());music.volume(screen.music_volume());music.muted(screen.music_muted()||screen.experience_active());music.video_active(screen.video_active());music.listening_room(screen.music_player_active());
            if(screen.take_trophy_sound())sounds.play(mixer,hui::audio::SoundSet::glass,{hui::audio::Cue::notify,1.f,0.f,hui::audio::museum_original::interface_gain(hui::audio::Cue::notify,1.f)});
            const float refresh=display.refresh_hz();screen.set_refresh_hz(video.frame_limit>0?std::min(refresh,float(video.frame_limit)):refresh);
            screen.draw(display.width(),display.height());
            ++frame_number;const bool done=screen.wants_quit()||(limit>0&&frame_number>=std::uint64_t(limit));
            if(done&&!capture.empty())screenshot(capture,display.width(),display.height());
            display.swap();if(done)break;
            if(video.frame_limit>0){const auto budget=std::uint64_t(1e9/double(video.frame_limit));const auto spent=SDL_GetTicksNS()-frame_start;if(spent<budget)SDL_DelayNS(budget-spent);}
            if(SDL_GetWindowFlags(display.window())&SDL_WINDOW_MINIMIZED)SDL_Delay(50);
        }
        SDL_ShowCursor();audio.stop();screen.shutdown();
        hui::sys::log("[Windows] clean shutdown after %llu frames",static_cast<unsigned long long>(frame_number));
        }
    }catch(const std::exception&e){hui::sys::log("[Windows] %s",e.what());if(!noninteractive){const std::string message(museum::i18n::tr(e.what()));SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,"Pixel Museum",message.c_str(),nullptr);}result=1;}
    SDL_Quit();return result;
}

#endif // _WIN32
