// Pixel Museum — native PS5 lifecycle.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/music.hpp"
#include "museum/intro_audio.hpp"
#include "core/save_file.hpp"
#include "platform/ps5/display_egl.hpp"
#include "platform/ps5/museum_audio.hpp"
#include "platform/ps5/controller_audio.hpp"
#include "platform/ps5/pad.hpp"
#include "platform/ps5/system.hpp"
#include "audio/mixer.hpp"
#include "audio/cues.hpp"
#include "audio/museum_interface_mix.hpp"
#include "audio/volume_gain.hpp"
#include "runtime/large_heap.h"
#include <array>
#include <atomic>
#include <cstdio>
#include <cmath>
#include <sys/stat.h>
namespace {
struct Audio {museum::Music* music;museum::Screen* screen;hui::audio::Mixer* ui;hui::audio::ControllerFeedback*controller;std::atomic<float> master{1.f};std::atomic<bool> culture_pad{false};hui::audio::VolumeGain master_gain{};};
struct Timing {
    int64_t total=0,maximum=0;
    void add(int64_t elapsed){elapsed=std::max(int64_t(0),elapsed);total+=elapsed;maximum=std::max(maximum,elapsed);}
    double mean_ms(unsigned count)const{return count?double(total)/(1000.0*count):0;}
    double max_ms()const{return double(maximum)/1000;}
};
void audio_render(void* context,float* out,unsigned frames){
    auto&a=*static_cast<Audio*>(context);
    a.music->render(out,frames);
    std::array<float,256>speaker{};
    for(unsigned pos=0;pos<frames;){
        const unsigned n=std::min(256u,frames-pos);
        a.screen->mix_experience(out+pos*2,n,speaker.data());
        a.screen->mix_video(out+pos*2,n,speaker.data(),a.culture_pad.load(std::memory_order_relaxed));
        a.controller->submit_speaker(speaker.data(),n);
        pos+=n;
    }
    std::array<int16_t,2048> samples{};
    for(unsigned pos=0;pos<frames;){
        const unsigned n=std::min(1024u,frames-pos);
        a.ui->render(samples.data(),int(n));
        for(unsigned j=0;j<n*2;++j)out[pos*2+j]+=float(samples[j])/32768.f;
        pos+=n;
    }
    a.master_gain.process(out,frames,a.master.load(std::memory_order_relaxed));
}
std::string app_root(){struct stat st{};if(stat("/app0/content/catalog.json",&st)==0)return "/app0";return "/data/homebrew/PPSA70421";}
}
int main(){
    const auto started=hui::sys::monotonic_us();
    const auto phase=[&](const char*name){hui::sys::log("[Museum] startup +%.2fms / %s",double(hui::sys::monotonic_us()-started)/1000,name);};
    const std::string root=app_root(),data="/download0/pixelmuseum";
    hui::save::ensure_directory(data);
    std::string diagnostic_path=data+"/session.log";
    // Keep diagnostics reachable over FTP after the sandbox has been unmounted.
    // Preferences remain in the title's persistent download0 directory.
    if(FILE*probe=std::fopen("/data/homebrew/PPSA70421/session.log","a")){std::fclose(probe);diagnostic_path="/data/homebrew/PPSA70421/session.log";}
    FILE* log=std::freopen(diagnostic_path.c_str(),"w",stdout);if(log)std::setvbuf(log,nullptr,_IOLBF,8192);
    hui::sys::log("[Museum] Pixel Museum 0.1.4 / PPSA70421 / %s",root.c_str());
    hui::sys::log("[Museum] diagnostics %s / GPU composition trial 3",diagnostic_path.c_str());
    phase("diagnostics ready");
    size_t direct_pool=0,direct_available=0;const int direct_query=museum_direct_memory_info(&direct_pool,&direct_available);
    hui::sys::log("[Museum] direct-memory pool %zu MiB / largest available %zu MiB / query %d; lazy CPU large-block cap %zu MiB",direct_pool>>20,direct_available>>20,direct_query,museum_large_capacity()>>20);
    constexpr int render_width=3840,render_height=2160;
    hui::ps5::Display display;if(!display.open(render_width,render_height,120))hui::sys::quit();
    hui::sys::log("[Museum] native render requested %dx%d; EGL surface %dx%d",render_width,render_height,display.width(),display.height());
    if(display.width()!=render_width||display.height()!=render_height)hui::sys::log("[Museum] 4K render mode unavailable; using the actual EGL surface dimensions");
    phase("display ready");
    museum::Screen screen;screen.set_trophy_curator_preview(true);if(!screen.init(root,data)){hui::sys::log("[Museum] startup failed");hui::sys::quit();}
    phase("interface ready");
    museum::Music music;if(!music.init(root+"/music/eras"))hui::sys::log("[Museum] soundtrack unavailable: %s",music.error().c_str());
    music.onboarding_active(screen.onboarding_active()||screen.collection_pending());
    music.volume(screen.music_volume());music.muted(screen.music_muted());
    phase("music ready");
    hui::audio::Mixer mixer;hui::audio::SoundBank sounds;
    auto sound_stats=sounds.load(root+"/assets/audio/museum-navigation");
    if(sound_stats.files==0)hui::sys::log("[Museum] original interface bank unavailable; no SDK sound fallback");
    sounds.set_pitch_jitter(0.f);sounds.set_recordings_only(true);mixer.set_bus_gain(hui::audio::Bus::ui,.18f*screen.sfx_volume());mixer.set_bus_gain(hui::audio::Bus::sfx,screen.sfx_volume());
    museum::prepare_startup_sounds();
    hui::sys::log("[Museum] navigation sounds %d clips / %d rejected / score-aligned pitch",sound_stats.files,sound_stats.rejected);
    hui::audio::ControllerFeedback controller_signals;hui::ps5::ControllerAudio controller_audio;
    Audio context{&music,&screen,&mixer,&controller_signals};context.master.store(screen.master_volume());context.culture_pad.store(screen.culture_audio_on_pad());context.master_gain.snap(screen.master_volume());float applied_sfx=screen.sfx_volume();controller_signals.speaker_volume(screen.master_volume()*screen.sfx_volume()*screen.pad_volume());controller_signals.speaker_pcm_volume(screen.master_volume()*screen.pad_volume());hui::ps5::MuseumAudio audio;const bool audio_ok=audio.start(audio_render,&context);
    hui::sys::log("[Museum] audio %s; collection %zu exhibits; soundtrack %zu bytes decoded",audio_ok?"ready":"unavailable",screen.catalog().entries.size(),music.pcm_bytes());
    hui::ps5::Pad pad;pad.open();hui::InputTracker tracker;int64_t previous=hui::sys::monotonic_us(),window=previous,max_frame=0;unsigned frames=0;bool splash=true;
    hui::ps5::Pad secondary_pad;hui::InputTracker secondary_tracker;
    hui::audio::ControllerFeedback secondary_signals;hui::ps5::ControllerAudio secondary_audio;
    int64_t secondary_retry_at=0;
    const auto close_secondary=[&]{secondary_signals.enabled(false);secondary_audio.stop();secondary_pad.close();secondary_tracker=hui::InputTracker{};};
    if(pad.is_open())controller_audio.start(pad.user_id(),controller_signals);
    bool haptic_requested=false,haptic_mode=false,controller_connected=false;
    int64_t controller_retry_at=0;unsigned controller_retries=0;
    int64_t controller_report_at=previous+5000000;
    phase("audio and controller ready");
    Timing update_time,draw_time,swap_time;
    for(;;){const int64_t now=hui::sys::monotonic_us();const auto span=now-previous;const float dt=float(span)/1000000.f;previous=now;max_frame=std::max(max_frame,span);
        pad.set_motion_enabled(screen.motion_controls());
        std::array<hui::PadSample,64> samples;const size_t n=pad.read(samples);auto input=tracker.update(std::span(samples).first(n),uint64_t(now));
        const bool local_two_player=screen.secondary_controller_active();
        if(!local_two_player){if(secondary_pad.is_open())close_secondary();secondary_retry_at=0;}
        else{
            if(!secondary_pad.is_open()&&now>=secondary_retry_at){
                secondary_retry_at=now+750000;
                if(secondary_pad.open_secondary(pad.user_id())){secondary_tracker=hui::InputTracker{};secondary_audio.start(secondary_pad.user_id(),secondary_signals);}
            }
            if(secondary_pad.is_open()){
                std::array<hui::PadSample,64> extra;const auto count=secondary_pad.read(extra);
                const auto second=secondary_tracker.update(std::span(extra).first(count),uint64_t(now));
                input.secondary={second.pressed,second.held,second.stick_y,second.connected,second.focus_lost,second.touch};
                if(!second.connected){close_secondary();secondary_retry_at=now+750000;}
                else if(second.is_pressed(hui::Action::menu)&&!second.focus_lost&&input.connected&&!input.focus_lost)input.pressed|=hui::action_bit(hui::Action::menu);
            }
        }
        hui::ui::Feedback feedback;screen.handle(input,feedback);
        context.master.store(screen.master_volume(),std::memory_order_relaxed);
        context.culture_pad.store(screen.culture_audio_on_pad()&&controller_audio.speaker_ready(),std::memory_order_relaxed);
        if(applied_sfx!=screen.sfx_volume()){
            applied_sfx=screen.sfx_volume();
            mixer.set_bus_gain(hui::audio::Bus::ui,.18f*applied_sfx);
            mixer.set_bus_gain(hui::audio::Bus::sfx,applied_sfx);
        }
        const float pad_volume=screen.master_volume()*screen.sfx_volume()*screen.pad_volume();
        controller_signals.speaker_volume(pad_volume);secondary_signals.speaker_volume(pad_volume);
        controller_signals.speaker_pcm_volume(screen.master_volume()*screen.pad_volume());secondary_signals.speaker_pcm_volume(screen.master_volume()*screen.pad_volume());
        for(auto cue:feedback.cues){cue.gain=hui::audio::museum_original::interface_gain(cue.cue,cue.gain);sounds.play(mixer,hui::audio::SoundSet::glass,cue);}
        const bool usable=input.connected&&!input.focus_lost;
        if(!input.connected){controller_retries=0;controller_retry_at=0;}
        const bool output_missing=!controller_audio.haptics_ready()||!controller_audio.speaker_ready();
        if(input.connected&&output_missing&&(!controller_connected||(controller_retries<3&&now>=controller_retry_at))){
            ++controller_retries;controller_retry_at=now+2000000;
            hui::sys::log("[Museum] controller PCM recovery attempt=%u speaker=%d haptics=%d",controller_retries,int(controller_audio.speaker_ready()),int(controller_audio.haptics_ready()));
            controller_signals.enabled(false);controller_audio.stop();controller_audio.start(pad.user_id(),controller_signals);
        }
        controller_signals.enabled(usable);
        const bool desired=input.connected&&controller_audio.haptics_ready();
        if(desired!=haptic_requested||(input.connected&&!controller_connected)){
            haptic_mode=pad.set_advanced_haptics(desired)&&desired;haptic_requested=desired;
        }
        controller_connected=input.connected;
        int pixel_ordinal=-1;const int startup_note=screen.take_startup_note(&pixel_ordinal);
        if(pixel_ordinal>=0)feedback.feel(hui::audio::Tactile::touch,.09f,.022f,float(pixel_ordinal%3-1)*.18f);
        if(usable&&haptic_mode)for(const auto&effect:feedback.tactile)controller_signals.post(effect);
        if(usable&&controller_audio.speaker_ready())for(const auto&effect:feedback.speaker_cues)controller_signals.post_speaker(effect);
        const bool second_usable=local_two_player&&usable&&input.secondary.connected&&!input.secondary.focus_lost;
        secondary_signals.enabled(second_usable);
        const bool second_advanced=secondary_pad.is_open()&&secondary_pad.set_advanced_haptics(second_usable&&secondary_audio.haptics_ready())&&second_usable&&secondary_audio.haptics_ready();
        if(second_advanced)for(const auto&effect:feedback.tactile)secondary_signals.post(effect);
        if(second_usable&&secondary_audio.speaker_ready())for(const auto&effect:feedback.speaker_cues)secondary_signals.post_speaker(effect);
        secondary_pad.tick(dt,second_usable);
        if(second_usable&&!second_advanced&&feedback.rumble_seconds>0)secondary_pad.rumble(feedback.rumble_strength,feedback.rumble_seconds);
        museum::route_startup_note(mixer,controller_signals,startup_note,pixel_ordinal,usable&&controller_audio.speaker_ready());
        if(now>=controller_report_at){
            hui::sys::log("[Museum] controller PCM status enabled=%d advanced=%d speaker=%d haptics=%d nonzero=%llu/%llu peak=%u/%u dropped=%llu",int(usable),int(haptic_mode),int(controller_audio.speaker_ready()),int(controller_audio.haptics_ready()),static_cast<unsigned long long>(controller_audio.speaker_nonzero_blocks()),static_cast<unsigned long long>(controller_audio.haptics_nonzero_blocks()),controller_audio.speaker_peak(),controller_audio.haptics_peak(),static_cast<unsigned long long>(controller_signals.dropped()));
            controller_report_at=now+5000000;
        }
        pad.tick(dt,usable);if(usable&&!haptic_mode&&feedback.rumble_seconds>0)pad.rumble(feedback.rumble_strength,feedback.rumble_seconds);
        const int64_t update_start=hui::sys::monotonic_us();
        screen.update(dt);music.onboarding_active(screen.onboarding_active()||screen.collection_pending());music.select_year(screen.selected_year());music.select_timeline(screen.culture_timeline_active());music.archival_ambient_gain(screen.archival_ambient_gain());music.volume(screen.music_volume());music.muted(screen.music_muted()||screen.experience_active());music.video_active(screen.video_active());music.listening_room(screen.music_player_active());
        if(screen.take_trophy_sound())sounds.play(mixer,hui::audio::SoundSet::glass,{hui::audio::Cue::notify,1.f,0.f,hui::audio::museum_original::interface_gain(hui::audio::Cue::notify,1.f)});
        const int64_t update_end=hui::sys::monotonic_us();update_time.add(update_end-update_start);
        screen.draw(display.width(),display.height());
        const int64_t draw_end=hui::sys::monotonic_us();draw_time.add(draw_end-update_end);
        const bool swapped=display.swap();const int64_t swap_end=hui::sys::monotonic_us();swap_time.add(swap_end-draw_end);
        if(!swapped)break;screen.set_refresh_hz(float(display.refresh_hz()));if(splash){hui::sys::hide_splash_screen();splash=false;phase("first frame presented");hui::sys::log("[Museum] first frame %dx%d",display.width(),display.height());}
        if(screen.wants_quit())break;
        ++frames;
        if(swap_end-window>=5000000){
            hui::sys::log("[Museum] perf %.2fs / frames %u / %.2f fps / longest frame %.2fms / update mean %.3f max %.3fms / draw mean %.3f max %.3fms / swap mean %.3f max %.3fms / year %.0f / video %d",double(swap_end-window)/1000000,frames,double(frames)*1000000/double(swap_end-window),double(max_frame)/1000,update_time.mean_ms(frames),update_time.max_ms(),draw_time.mean_ms(frames),draw_time.max_ms(),swap_time.mean_ms(frames),swap_time.max_ms(),screen.selected_year(),screen.video_active());
            screen.log_performance();
            size_t live=0,peak=0,blocks=0,failures=0;int error=0;
            museum_large_stats(&live,&peak,&blocks,&failures,&error);
            hui::sys::log("[Museum] direct CPU live %zu MiB / peak %zu MiB / blocks %zu / refusals %zu / last %d",live>>20,peak>>20,blocks,failures,error);
            const int query=museum_direct_memory_info(&direct_pool,&direct_available);
            hui::sys::log("[Museum] shared physical direct pool %zu MiB / largest available range %zu MiB / query %d",direct_pool>>20,direct_available>>20,query);
            frames=0;max_frame=0;window=swap_end;update_time={};draw_time={};swap_time={};
        }
    }
    audio.stop();close_secondary();controller_signals.enabled(false);controller_audio.stop();pad.set_advanced_haptics(false);screen.shutdown();pad.close();display.close();std::fflush(nullptr);hui::sys::quit();return 0;
}
