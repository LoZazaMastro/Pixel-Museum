// Pixel Museum - YouTube service and decoder bridge with a bounded frame mailbox.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/media.hpp"
#include "platform/playback_window.hpp"
#include "audio/stream_ring.hpp"
#include "gfx/renderer.hpp"
#include "platform/ps5/system.hpp"
#include "yt/log.hpp"
#include "yt/auth.hpp"
#include "yt/captions.hpp"
#include "yt/caption_metadata.hpp"
#include "yt/service.hpp"
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <mutex>
#include <pthread.h>
#include <sys/stat.h>
#include <vector>
namespace museum::media {
struct Video::Impl {
    struct Sink final : yt::AudioSink {
        hui::audio::StreamRing ring{1u << 17};
        SegmentFrames frames;
        std::atomic<bool> command_pending{false},decoder_paused{true};
        std::size_t write(const float *p, std::size_t n) override { const auto got=ring.write(p,frames.allowance(n));frames.written(got);return got; }
        std::size_t buffered() const override { return ring.available(); }
        void drain() override { ring.drain(); }
        void set_paused(bool paused) override { decoder_paused.store(paused,std::memory_order_release);ring.set_paused(paused||command_pending.load(std::memory_order_acquire)); }
    } sink;
    mutable std::mutex mutex;
    std::unique_ptr<yt::Service> service;
    std::string open_id, failure, progress;
    yt::captions::Loader captions;
    std::string caption_locale="en", caption_stage="off";
    bool captions_dirty=false;
    bool close_requested = false, pause_requested = false, want_pause = false, audio_only=false;
    std::atomic<float> volume{.6f};
    float audible_gain=.6f;
    std::atomic<float> level{0};
    double seek_requested = -1;
    PlaybackWindow playback_window;
    bool range_requested=false;
    State load = State::idle;
    double position = 0, length = 0;
    bool is_paused = false, is_ended = false;
    std::vector<std::uint8_t> pixels;
    int frame_w = 0, frame_h = 0, texture_w = 0, texture_h = 0;
    GLuint texture = 0;
    std::uint64_t generation=0;
    std::uint64_t range_revision=0;
    bool clear_texture=false;
    std::chrono::steady_clock::time_point loading_started{};
    std::atomic<bool> stopping{false};
    pthread_t thread{}; bool running = false;
    bool saved_connection=false; // Main-thread snapshot; never reads Auth's mutable token string.
    static void *entry(void *p) { static_cast<Impl *>(p)->run(); return nullptr; }
    void run() {
        std::unique_ptr<yt::Player> player;
        yt::VideoInfo caption_info;
        std::uint64_t caption_revision=0;
        std::string caption_request_url,caption_request_locale;
        std::uint64_t active_generation=0;
        auto last_tick=std::chrono::steady_clock::now();
        while (!stopping.load(std::memory_order_acquire)) {
            std::string id,locale; bool close = false, change_pause = false, paused = false, audio_only_request=false, refresh_captions=false,range_changed=false; double seek = -1;
            PlaybackWindow window;std::uint64_t tick_range_revision=0;
            { std::lock_guard<std::mutex> lock(mutex);
              id.swap(open_id);audio_only_request=audio_only; close = close_requested; close_requested = false;
              if (close || !id.empty()) active_generation=generation;
              change_pause = pause_requested; pause_requested = false; paused = want_pause;
              seek = seek_requested; seek_requested = -1;
              window=playback_window;range_changed=range_requested;range_requested=false;tick_range_revision=range_revision; }
            { std::lock_guard<std::mutex> lock(mutex);locale=caption_locale;refresh_captions=captions_dirty;captions_dirty=false; }
            if (close || !id.empty()) {
                captions.clear();caption_info=yt::VideoInfo{};caption_revision=0;
                caption_request_url.clear();caption_request_locale.clear();
                if (player) { player->close(); player.reset(); }
                service->request_close_video(); sink.ring.drain(); sink.ring.set_paused(true);
                std::lock_guard<std::mutex> lock(mutex); pixels.clear(); position=length=0;
            }
            if (!id.empty()) {
                yt::CodecChoice choice; choice.avc = true; choice.vp9 = true; choice.av1 = false;
                choice.audio_only=audio_only_request;choice.max_height = 720; choice.decode = yt::DecodeMode::software;
                service->request_video(id, choice);
            }
            const auto now=std::chrono::steady_clock::now();
            const float elapsed=std::chrono::duration<float>(now-last_tick).count();
            last_tick=now;
            service->video_watchdog(std::clamp(elapsed,0.0f,1.0f));
            bool timed_out=false;
            {
                std::lock_guard<std::mutex> lock(mutex);
                // The upstream watchdog excludes a known preroll wait. Bound the
                // entire request too, using wall time rather than the loop rate.
                if (load==State::loading && now-loading_started>std::chrono::seconds(60)) {
                    load=State::failed; failure="YouTube took too long to respond. Go back and try this film again";
                    progress.clear(); pixels.clear(); clear_texture=true;
                    timed_out=true;
                }
            }
            if (timed_out) {
                yt::log::line("museum: video request exceeded the 60-second total limit");
                service->request_close_video(); sink.ring.set_paused(true); sink.ring.drain();
            }
            if (!player) {
                auto next = service->take_player();
                bool active=false;
                { std::lock_guard<std::mutex> lock(mutex); active=load==State::loading && active_generation==generation; }
                if (next && active) {
                    player = std::move(next); sink.ring.drain();
                    const double total=player->duration_s();
                    if(window.bounded()&&total>0&&window.start>=total){
                        player->close();player.reset();sink.ring.set_paused(true);
                        std::lock_guard<std::mutex> lock(mutex);load=State::failed;failure="This recording no longer includes the selected passage";progress.clear();
                    }else{
                        // Seek before the first update can feed the sink, avoiding an
                        // audible burst from the album opening while resolving a cue.
                        sink.frames.reset(window.bounded()?window.duration(total):-1.);
                        if(window.start>0)player->seek(window.start);
                        const auto metadata=service->video();
                        caption_info=metadata.info;caption_revision=metadata.revision;refresh_captions=true;
                    }
                }
                else if (next) { next->close(); sink.ring.set_paused(true); sink.ring.drain(); }
                const auto view = service->video();
                std::lock_guard<std::mutex> lock(mutex);
                if (load == State::loading) {
                    progress = "Resolving the video and preparing playback";
                    if (view.state == yt::Load::failed) {
                        load = State::failed;
                        yt::log::line("museum: video unavailable: %s",view.error.c_str());
                        const bool refused=view.error.find("403")!=std::string::npos || view.error.find("Forbidden")!=std::string::npos;
                        if (view.error=="timeout") failure="YouTube took too long to respond. Go back and try this film again";
                        else if (view.unauthorized) failure="YouTube requests sign-in for this film. You can connect an account in Options";
                        else if (view.error.rfind("player_transform:",0)==0) failure="This film needs a YouTube player update before it can be opened";
                        else if (refused) failure="YouTube refused this playback request. Go back and try this film again";
                        else failure="YouTube could not open this film. Go back and try another exhibit";
                        progress.clear(); sink.ring.set_paused(true); sink.ring.drain();
                    }
                }
            }
            // Playback can now become ready before optional client metadata.
            // Pick up later caption/translation sources without restarting the
            // film or reloading the same caption on unrelated view revisions.
            if(player && service->video_revision()!=caption_revision){
                const auto metadata=service->video();caption_revision=metadata.revision;
                if(metadata.state==yt::Load::ready && metadata.info.video_id==caption_info.video_id &&
                   !yt::captions::same_metadata(metadata.info,caption_info)){
                    caption_info=metadata.info;refresh_captions=true;
                }
            }
            if (player && refresh_captions) {
                const auto track=audio_only_request?yt::captions::Selection{}:yt::captions::select_track(caption_info,locale);
                std::lock_guard<std::mutex> lock(mutex);
                if(active_generation==generation && locale==caption_locale) {
                    if(audio_only_request || locale.empty()) {
                        captions.clear();caption_stage="off";caption_request_url.clear();caption_request_locale.clear();
                    } else if(track.url.empty()&&track.english_fallbacks.empty()) {captions.clear();caption_stage="unavailable";caption_request_url.clear();caption_request_locale.clear();}
                    else {
                        const std::string status=captions.status();
                        const bool keep_request=!track.url.empty() && caption_request_url==track.url &&
                            caption_request_locale==locale && (status=="loading" || status=="ok" ||
                            status.rfind("fallback: en",0)==0);
                        if(!keep_request){
                            captions.load(track.url,track.alternatives,track.english_fallbacks);
                            caption_request_url=track.url;caption_request_locale=locale;
                        }
                        caption_stage="track";
                        yt::log::line("museum: captions requested=%s selected=%s translated=%s English-fallback=%s",locale.c_str(),track.language.c_str(),track.translated?"yes":"no",track.english_fallbacks.empty()?"no":"offered");
                    }
                }
            }
            if (player) {
                if(range_changed){seek=window.start;if(!change_pause){change_pause=true;paused=false;}}
                if (seek >= 0) {
                    const double target=window.seek(seek-window.start,player->duration_s());
                    sink.frames.reset(window.bounded()?std::max(0.,window.finish(player->duration_s())-target):-1.);
                    player->seek(target);
                }
                if (change_pause) player->set_paused(paused);
                {
                    // Keep old queued PCM silent until the decoder has applied
                    // the cut. A newer main-thread command must retain the gate.
                    std::lock_guard<std::mutex> lock(mutex);
                    if(active_generation==generation&&open_id.empty()&&!close_requested&&!range_requested&&seek_requested<0&&sink.command_pending.load(std::memory_order_acquire)){
                        sink.command_pending.store(false,std::memory_order_release);
                        sink.ring.set_paused(sink.decoder_paused.load(std::memory_order_acquire));
                    }
                }
                player->update();
                const bool passage_ended=window.bounded()&&sink.frames.exhausted()&&sink.ring.available()==0;
                if(passage_ended){player->set_paused(true);sink.ring.set_paused(true);}
                const auto frame = player->poll_frame();
                const bool fatal=!player->error().empty();
                {
                std::lock_guard<std::mutex> lock(mutex);
                // A same-recording cue change keeps the decoder generation.
                // Its previous tick must not publish an old ended=true over
                // the newly selected cue and make the playlist skip it.
                if (active_generation!=generation || tick_range_revision!=range_revision || load==State::idle || load==State::failed) continue;
                load = fatal ? State::failed : State::ready;
                failure = player->error(); length = player->duration_s();position=passage_ended?window.finish(length):player->clock_s();
                is_paused = player->paused(); is_ended = passage_ended||player->ended();
                if (!audio_only_request && frame.fresh && frame.rgba && frame.width > 0 && frame.height > 0 && frame.width <= 1920 && frame.height <= 1080) {
                    frame_w = frame.width; frame_h = frame.height;
                    pixels.assign(frame.rgba, frame.rgba + static_cast<std::size_t>(frame_w) * static_cast<std::size_t>(frame_h) * 4);
                }
                }
                if (fatal) {
                    captions.clear();
                    yt::log::line("museum: decoder failed: %s",player->error().c_str());
                    sink.ring.set_paused(true); sink.ring.drain();
                    player->close(); player.reset();
                }
            }
            hui::sys::sleep_us(4000);
        }
        if (player) player->close();
    }
};
Video::Video() : impl_(std::make_unique<Impl>()) {}
Video::~Video() { stop(); }
bool Video::start(const std::string &data, const std::string &root) {
    if (impl_->running) return true;
    mkdir(data.c_str(),0777);
    std::string log_path=data+"/youtube.log";
    // Keep the flushed decoder log reachable after a crash unmounts download0,
    // just as main.cpp already does for the application session log.
    if(FILE* probe=std::fopen("/data/homebrew/PPSA70421/youtube.log","a")){
        std::fclose(probe);log_path="/data/homebrew/PPSA70421/youtube.log";
    }
    yt::log::open(log_path.c_str());
    struct stat token{};
    impl_->saved_connection=stat((data+"/youtube-auth.json").c_str(),&token)==0 && token.st_size>0;
    impl_->service = std::make_unique<yt::Service>(data + "/youtube-auth.json", root, &impl_->sink);
    yt::Service::Preferences prefs; prefs.history = false; impl_->service->set_preferences(prefs);
    impl_->service->start(); impl_->stopping.store(false);
    pthread_attr_t attr; pthread_attr_init(&attr); pthread_attr_setstacksize(&attr, 2u << 20);
    const int rc = pthread_create(&impl_->thread, &attr, &Impl::entry, impl_.get()); pthread_attr_destroy(&attr);
    impl_->running = rc == 0;
    if (!impl_->running) impl_->service->stop();
    return impl_->running;
}
void Video::stop() {
    impl_->captions.clear();
    if (!impl_->running) return;
    impl_->stopping.store(true); pthread_join(impl_->thread,nullptr);
    impl_->service->stop(); impl_->service.reset(); impl_->running = false;
    yt::log::close();
}
void Video::open(const std::string &id,bool audio_only,double start_seconds,double end_seconds) {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    impl_->pause_requested=false;impl_->seek_requested=-1;impl_->want_pause=false;
    impl_->playback_window={start_seconds,end_seconds};impl_->range_requested=false;
    ++impl_->generation; impl_->clear_texture=true; impl_->pixels.clear();impl_->audio_only=audio_only;
    impl_->captions.clear();impl_->captions_dirty=true;
    impl_->caption_stage=audio_only?"off":"waiting";
    impl_->sink.command_pending.store(true,std::memory_order_release);
    impl_->sink.ring.set_paused(true); impl_->sink.ring.drain();
    impl_->close_requested=true; impl_->open_id.clear();
    if (!impl_->running) { impl_->load=State::failed; impl_->failure="Video service is unavailable"; return; }
    if((start_seconds!=0||end_seconds!=0)&&!PlaybackWindow::valid(start_seconds,end_seconds)){
        impl_->load=State::failed;impl_->failure="This recording has invalid passage boundaries";return;
    }
    if (id.size()!=11 || id.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-") != std::string::npos) {
        impl_->load=State::failed; impl_->failure="This exhibit has no valid YouTube video ID"; return;
    }
    impl_->open_id=id; impl_->load=State::loading; impl_->failure.clear(); impl_->progress="Contacting YouTube"; impl_->loading_started=std::chrono::steady_clock::now();
    impl_->is_ended=false; impl_->is_paused=false;
}
void Video::play_range(double start_seconds,double end_seconds){
    if((start_seconds!=0||end_seconds!=0)&&!PlaybackWindow::valid(start_seconds,end_seconds))return;
    std::lock_guard<std::mutex> lock(impl_->mutex);
    if(impl_->load!=State::ready)return;
    impl_->playback_window={start_seconds,end_seconds};impl_->range_requested=true;
    ++impl_->range_revision;
    impl_->seek_requested=-1;impl_->pause_requested=false;impl_->want_pause=false;
    impl_->position=start_seconds;impl_->is_ended=false;impl_->is_paused=false;
    impl_->sink.command_pending.store(true,std::memory_order_release);
    impl_->sink.ring.set_paused(true);impl_->sink.ring.drain();
}
void Video::close() {
    std::lock_guard<std::mutex> lock(impl_->mutex); impl_->open_id.clear(); impl_->close_requested=true;
    impl_->pause_requested=false;impl_->seek_requested=-1;impl_->want_pause=false;impl_->range_requested=false;
    impl_->playback_window={};
    ++impl_->generation; impl_->clear_texture=true; impl_->pixels.clear();
    impl_->captions.clear();impl_->caption_stage="off";impl_->captions_dirty=false;
    impl_->sink.command_pending.store(true,std::memory_order_release);
    impl_->load=State::idle; impl_->sink.ring.set_paused(true); impl_->sink.ring.drain();
}
void Video::pause(bool value) { std::lock_guard<std::mutex> lock(impl_->mutex); impl_->pause_requested=true; impl_->want_pause=value; }
void Video::seek(double seconds) { if(!std::isfinite(seconds))return;std::lock_guard<std::mutex> lock(impl_->mutex); impl_->seek_requested=std::max(0.0,seconds); }
void Video::update(float dt) { (void)dt; }
void Video::upload_pending(hui::gfx::Renderer &renderer) {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    if (impl_->clear_texture) {
        if (impl_->texture) glDeleteTextures(1,&impl_->texture);
        impl_->texture=0; impl_->texture_w=impl_->texture_h=0; impl_->clear_texture=false;
    }
    if (impl_->pixels.empty()) return;
    if (!impl_->texture || impl_->texture_w!=impl_->frame_w || impl_->texture_h!=impl_->frame_h) {
        if (impl_->texture) glDeleteTextures(1,&impl_->texture);
        impl_->texture=renderer.batch().create_texture(impl_->frame_w,impl_->frame_h,impl_->pixels.data());
        impl_->texture_w=impl_->frame_w; impl_->texture_h=impl_->frame_h;
    } else {
        glBindTexture(GL_TEXTURE_2D,impl_->texture);
        glTexSubImage2D(GL_TEXTURE_2D,0,0,0,impl_->frame_w,impl_->frame_h,GL_RGBA,GL_UNSIGNED_BYTE,impl_->pixels.data());
    }
    impl_->pixels.clear();
}
void Video::volume(float gain){if(std::isfinite(gain))impl_->volume.store(std::clamp(gain,0.f,1.f),std::memory_order_relaxed);}
void Video::mix_audio(float *out,unsigned frames) {
    std::array<float,2048> temporary{};
    unsigned at=0;float power=0;unsigned samples=0;
    while (at<frames) {
        const auto amount=std::min(1024u,frames-at);
        const auto got=impl_->sink.command_pending.load(std::memory_order_acquire)?0:impl_->sink.ring.read(temporary.data(),amount);
        const float target=impl_->volume.load(std::memory_order_relaxed);
        for (std::size_t n=0;n<got;++n){impl_->audible_gain+=(target-impl_->audible_gain)*.001f;
            power+=(temporary[n*2]*temporary[n*2]+temporary[n*2+1]*temporary[n*2+1])*.5f;++samples;
            out[static_cast<std::size_t>(at)*2+n*2]+=temporary[n*2]*impl_->audible_gain;
            out[static_cast<std::size_t>(at)*2+n*2+1]+=temporary[n*2+1]*impl_->audible_gain;}
        at+=amount;
    }
    const float rms=samples?std::sqrt(power/float(samples)):0;
    const float old=impl_->level.load(std::memory_order_relaxed);
    impl_->level.store(old+(std::clamp(rms*4.f,0.f,1.f)-old)*(rms>old?.65f:.18f),std::memory_order_relaxed);
}
float Video::audio_level()const{return impl_->level.load(std::memory_order_relaxed);}
State Video::state() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->load; }
std::string Video::error() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->failure; }
std::string Video::stage() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->progress; }
std::uint32_t Video::texture() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->load==State::ready?impl_->texture:0; }
int Video::width() const { return impl_->texture_w; }
int Video::height() const { return impl_->texture_h; }
double Video::time() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->position; }
double Video::duration() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->length; }
bool Video::paused() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->is_paused; }
bool Video::ended() const { std::lock_guard<std::mutex> lock(impl_->mutex); return impl_->is_ended; }
void Video::caption_language(std::string locale) {
    locale=yt::captions::normalize_language(locale);if(locale.empty())locale="en";
    std::lock_guard<std::mutex> lock(impl_->mutex);
    if(locale==impl_->caption_locale)return;
    impl_->caption_locale=std::move(locale);impl_->captions_dirty=true;impl_->captions.clear();
    impl_->caption_stage=impl_->audio_only || impl_->load==State::idle?"off":"waiting";
}
std::string Video::caption_text() const {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    if(impl_->audio_only || impl_->load!=State::ready || impl_->is_ended || impl_->caption_stage!="track")return {};
    return impl_->captions.text_at(impl_->position);
}
std::string Video::caption_status() const {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    return impl_->caption_stage=="track"?impl_->captions.status():impl_->caption_stage;
}
void Video::release_texture() { if (impl_->texture) glDeleteTextures(1,&impl_->texture); impl_->texture=0; impl_->texture_w=impl_->texture_h=0; }
Connection Video::connection() const {
    Connection out;
    if(!impl_->service) { out.state=State::failed; out.error="YouTube connection is unavailable"; return out; }
    const auto view=impl_->service->login();
    switch(view.state) {
        case yt::Load::idle: out.state=State::idle; break;
        case yt::Load::loading: out.state=State::loading; break;
        case yt::Load::ready: out.state=State::ready; break;
        case yt::Load::failed: out.state=State::failed; break;
    }
    out.signed_in=impl_->service->signed_in();
    if(out.signed_in) impl_->saved_connection=true;
    out.saved=impl_->saved_connection;
    out.user_code=view.user_code; out.verification_url=view.verification_url;
    out.qr_url=yt::prefilled_verification_url(view.verification_url,view.user_code);
    out.error=view.error; return out;
}
void Video::request_sign_in() { if(impl_->service) impl_->service->request_sign_in(); }
void Video::cancel_sign_in() { if(impl_->service) impl_->service->cancel_sign_in(); }
void Video::sign_out() { close(); impl_->saved_connection=false; if(impl_->service) impl_->service->sign_out(); }
void Video::restore_connection() { if(impl_->service) impl_->service->refresh_token(); }
} // namespace museum::media
