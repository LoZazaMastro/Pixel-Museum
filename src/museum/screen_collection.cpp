// Pixel Museum - the collection is installed before the first museum visit.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "core/save_file.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <cmath>
#include <cctype>
#include <cerrno>
#include <cstring>
#include <cstdio>

namespace museum {
namespace {
void removal_trace(const char*stage){
    hui::sys::log("[Museum] collection reset / %s",stage);
    std::fflush(stdout);
}
}
void Screen::handle_language_choice(const hui::InputFrame& input,hui::ui::Feedback& feedback){
    using hui::Action;using hui::Direction;using hui::audio::Cue;
    if(input.focus_lost||!input.connected)return;
    const int previous=language_focus_;
    if(input.nav==Direction::down||input.nav==Direction::right)language_focus_=std::min(4,language_focus_+1);
    if(input.nav==Direction::up||input.nav==Direction::left)language_focus_=std::max(0,language_focus_-1);
    if(previous!=language_focus_)feedback.play(Cue::focus);
    if(input.is_pressed(Action::confirm)){
        static constexpr const char* locales[]={"en","it","es","fr","de"};
        language_=locales[language_focus_];language_chosen_=true;language_choice_=false;
        theme_choice_=true;theme_confirming_=false;theme_confirm_progress_=0;
        apply_language();save_settings();feedback.play(Cue::select);
    }
}

bool Screen::start_collection_media(){
    if(collection_media_started_)return true;
    std::string media_data=data_;
#if defined(__FreeBSD__)
    // Keep the title's small preferences container separate from bulk caches.
    // This subtree remains within the collection reset helper's exact allowlist.
    media_data="/data/pixelmuseum/collection/media-cache";
    if(!hui::save::ensure_directory("/data/pixelmuseum")||
       !hui::save::ensure_directory("/data/pixelmuseum/collection")||
       !hui::save::ensure_directory(media_data)){
        hui::sys::log("[Museum] external media cache directory unavailable");
        collection_media_error_=true;return false;
    }
#endif
    if(!cache_.images_from_package(root_,collection_installer_.cache_root())||!cache_.start(media_data+"/cache")){
        hui::sys::log("[Museum] collection image worker could not start");
        collection_media_error_=true;return false;
    }
    if(!video_.start(media_data,root_))hui::sys::log("[Museum] video worker unavailable");
    initialize_object_programs();
    changed();initialize_trophies();
    collection_media_started_=true;collection_media_error_=false;
    return true;
}

CollectionInstallViewState Screen::collection_install_view_state()const{
    const auto state=collection_installer_.snapshot();
    CollectionInstallViewState view;
    view.downloaded_bytes=state.downloaded_bytes;view.total_bytes=state.total_bytes;
    view.pack_index=state.pack_index;view.pack_count=state.pack_count;
    view.bytes_per_second=state.bytes_per_second;
    view.installed_bytes=state.installed_bytes;view.total_expanded_bytes=state.total_expanded_bytes;
    view.installed_files=state.installed_files;view.total_files=state.total_files;
    using Phase=CollectionInstaller::Phase;
    switch(state.phase){
    case Phase::unconfigured:case Phase::idle:view.phase=CollectionInstallPhase::checking;break;
    case Phase::downloading:view.phase=CollectionInstallPhase::downloading;break;
    case Phase::verifying:view.phase=state.stage.find("Checking installed")!=std::string::npos?CollectionInstallPhase::checking:CollectionInstallPhase::preparing;break;
    case Phase::extracting:view.phase=state.stage.find("Migrat")!=std::string::npos||state.stage.find("Import")!=std::string::npos?CollectionInstallPhase::migrating:CollectionInstallPhase::installing;break;
    case Phase::paused:case Phase::cancelled:view.phase=CollectionInstallPhase::paused;break;
    case Phase::ready:view.phase=CollectionInstallPhase::complete;break;
    case Phase::removing:case Phase::removed:view.phase=CollectionInstallPhase::checking;break;
    case Phase::failed:{
        view.phase=CollectionInstallPhase::error;
        std::string error=state.error;
        std::transform(error.begin(),error.end(),error.begin(),[](unsigned char c){return char(std::tolower(c));});
        view.error=error.find("space")!=std::string::npos||error.find("disk")!=std::string::npos||error.find("storage")!=std::string::npos?CollectionInstallError::storage:
            error.find("checksum")!=std::string::npos||error.find("sha256")!=std::string::npos||error.find("archive")!=std::string::npos||error.find("manifest")!=std::string::npos||error.find("tar")!=std::string::npos?CollectionInstallError::invalid_files:CollectionInstallError::network;
        break;
    }}
    view.progress=collection_install_work_progress(view);
    if(collection_media_error_){view.phase=CollectionInstallPhase::error;view.error=CollectionInstallError::invalid_files;}
    return view;
}

void Screen::handle_collection_startup(const hui::InputFrame& input,hui::ui::Feedback& feedback){
    using hui::Action;using hui::audio::Cue;using Phase=CollectionInstaller::Phase;
    if(input.focus_lost||!input.connected)return;
    if(input.is_pressed(Action::back)){
        collection_installer_.pause();quit_=true;feedback.play(Cue::back);return;
    }
    if(collection_presentation_.quiet_validation)return;
    if(!input.is_pressed(Action::confirm))return;
    const auto phase=collection_installer_.snapshot().phase;
    if(collection_media_error_){
        if(start_collection_media())collection_pending_=false;
        feedback.play(collection_media_error_?Cue::error:Cue::select);return;
    }
    if(phase==Phase::paused||phase==Phase::failed||phase==Phase::cancelled){
        const bool started=collection_installer_.retry();collection_started_=started;
        feedback.play(started?Cue::select:Cue::error);
    }else if(phase==Phase::downloading||phase==Phase::verifying||phase==Phase::extracting){
        collection_installer_.pause();feedback.play(Cue::back);
    }else if(phase==Phase::ready){collection_ready_elapsed_=.6f;}
}

void Screen::update_collection_startup(float delta){
    const float elapsed=std::isfinite(delta)?std::clamp(delta,0.f,.1f):0.f;
    dt_=elapsed;
    if(language_choice_){
        // Replay enters this gate with the introduction faded out. The normal
        // Screen update is suspended here, so advance its appearance locally;
        // otherwise input works behind a permanently transparent language page.
        onboarding_fade_.target=1.f;onboarding_fade_.update(dt_,10);
        language_selection_.target=float(language_focus_);language_selection_.update(dt_,reduced_?60.f:16.f);return;
    }
    collection_elapsed_+=elapsed;
    if(quit_)return;
    if(!collection_started_){
        collection_started_=true;collection_installer_.start();
    }
    const auto state=collection_installer_.snapshot();
    collection_presentation_.observe(state,collection_media_error_);
    const int phase=int(state.phase),progress=state.total_bytes?int(std::min(10.,double(state.downloaded_bytes)*10./double(state.total_bytes))):-1;
    if(phase!=collection_phase_log_||progress>collection_progress_log_){
        hui::sys::log("[Museum] collection %s / pack %zu of %zu / %llu of %llu bytes / %s",state.stage.c_str(),state.pack_count?state.pack_index+1:0,state.pack_count,static_cast<unsigned long long>(state.downloaded_bytes),static_cast<unsigned long long>(state.total_bytes),state.error.empty()?"OK":state.error.c_str());
        if(!state.diagnostic.empty())hui::sys::log("[Museum] collection filesystem errno %d / %s",state.filesystem_errno,state.diagnostic.c_str());
        collection_phase_log_=phase;collection_progress_log_=std::max(collection_progress_log_,progress);
    }
    if(collection_installer_.is_ready()&&!collection_media_error_){
        collection_ready_elapsed_+=elapsed;
        // Completed downloads/replayed introductions get a short conclusion.
        // Ordinary reopen validation goes directly to the unchanged startup animation.
        // No onboarding clock, entry animation or startup note advances meanwhile.
        if(collection_ready_elapsed_>=collection_presentation_.completion_delay()&&start_collection_media())collection_pending_=false;
    }else collection_ready_elapsed_=0;
}

void Screen::join_collection_media_stop(){
    if(!collection_media_stop_joinable_)return;
    pthread_join(collection_media_stop_thread_,nullptr);
    collection_media_stop_joinable_=false;
}

bool Screen::begin_collection_removal(){
    removal_trace("confirmed; saving introduction preferences");
    collection_remove_dialog_=false;collection_remove_open_.snap(0);
    collection_removal_elapsed_=0;
    onboarding_complete_=false;language_chosen_=false;
    save_settings();
    removal_trace("introduction preferences saved");
    // A restart after an interrupted removal must begin at language selection,
    // rather than enter a collection whose files may only partly remain.
    if(!collection_media_started_){
        removal_trace("media already stopped; starting deletion");
        const bool started=collection_installer_.remove_downloaded();
        removal_trace(started?"deletion worker started":"deletion worker refused");
        collection_removal_state_=started?CollectionRemovalState::removing:CollectionRemovalState::failed;
        return started;
    }
    release_culture_ambience();stop_playlist();video_.close();
    removal_trace("playback closed");
    cache_.cancel_download();object_.cancel();
    for(auto&prepared:prepared_objects_)prepared.cancel();
    removal_trace("media requests cancelled; starting reader shutdown");
    collection_media_stop_done_.store(false,std::memory_order_release);
    collection_removal_state_=CollectionRemovalState::stopping_media;
    pthread_attr_t attributes;
    int code=pthread_attr_init(&attributes);
    if(!code){
        code=pthread_attr_setstacksize(&attributes,2u<<20);
        if(!code)code=pthread_create(&collection_media_stop_thread_,&attributes,[](void*owner)->void*{
            auto&screen=*static_cast<Screen*>(owner);
            // These joins may wait for an in-flight decode/network callback.
            // Keep them off the UI thread so the removal page stays animated.
            removal_trace("video shutdown begins");
            screen.video_.stop();
            removal_trace("video stopped; image worker shutdown begins");
            screen.cache_.stop();
            removal_trace("image worker stopped");
            screen.collection_media_stop_done_.store(true,std::memory_order_release);
            return nullptr;
        },this);
        pthread_attr_destroy(&attributes);
    }
    if(code){
        hui::sys::log("[Museum] collection reader shutdown worker: %s",std::strerror(code));
        collection_removal_state_=CollectionRemovalState::failed;
        return false;
    }
    collection_media_stop_joinable_=true;
    removal_trace("reader shutdown worker started");
    return true;
}

void Screen::handle_collection_removal(const hui::InputFrame&input,hui::ui::Feedback&feedback){
    using hui::Action;using hui::Direction;using hui::audio::Cue;
    if(input.focus_lost||!input.connected)return;
    if(collection_remove_dialog_){
        if(input.is_pressed(Action::back)||input.is_pressed(Action::menu)){
            collection_remove_dialog_=false;feedback.play(Cue::back);return;
        }
        const int previous=collection_remove_focus_;
        if(input.nav==Direction::left||input.nav==Direction::up)collection_remove_focus_=0;
        if(input.nav==Direction::right||input.nav==Direction::down)collection_remove_focus_=1;
        if(previous!=collection_remove_focus_)feedback.play(Cue::focus);
        if(!input.is_pressed(Action::confirm))return;
        if(collection_remove_focus_==0){collection_remove_dialog_=false;feedback.play(Cue::back);return;}
        feedback.play(begin_collection_removal()?Cue::select:Cue::error);
        return;
    }
    if(collection_removal_state_!=CollectionRemovalState::failed)return;
    if(input.is_pressed(Action::confirm))feedback.play(begin_collection_removal()?Cue::select:Cue::error);
    else if(input.is_pressed(Action::back)||input.is_pressed(Action::menu)){quit_=true;feedback.play(Cue::back);}
}

void Screen::update_collection_removal(float delta){
    using Phase=CollectionInstaller::Phase;
    dt_=std::isfinite(delta)?std::clamp(delta,0.f,.1f):0.f;
    collection_removal_elapsed_+=dt_;
    if(collection_removal_state_==CollectionRemovalState::stopping_media){
        if(!collection_media_stop_done_.load(std::memory_order_acquire))return;
        join_collection_media_stop();
        removal_trace("readers joined; waiting for GPU retirement");
        // GPU resources are released only on the GL thread, after every media
        // reader has stopped. No further file requests are made from this page.
        // The native driver unmaps direct GPU backing when resources retire.
        // Finish the previous exhibition frame before this bulk release.
        glFinish();
        removal_trace("GPU retired; GL cleanup begins");
        video_.release_texture();cache_.release_textures();
        removal_trace("video and image textures released");
        object_.release();for(auto&prepared:prepared_objects_)prepared.release();
        removal_trace("model resources released");
        prepared_paths_.fill({});prepared_use_.fill(0);prepared_programs_ready_=false;
        model_path_.clear();model_url_.clear();model_requested_=false;object_texture_=0;
        image_fades_.clear();image_wait_started_.clear();nearby_covers_.clear();
        collection_media_started_=false;collection_media_error_=false;
        removal_trace("GL cleanup complete; starting deletion");
        const bool started=collection_installer_.remove_downloaded();
        collection_removal_state_=started?CollectionRemovalState::removing:CollectionRemovalState::failed;
        removal_trace(started?"deletion worker started":"deletion worker refused");
        return;
    }
    if(collection_removal_state_!=CollectionRemovalState::removing)return;
    const auto status=collection_installer_.snapshot();
    if(status.phase==Phase::failed||status.phase==Phase::cancelled){
        hui::sys::log("[Museum] collection removal failed: %s / %s",status.error.c_str(),status.diagnostic.c_str());
        collection_removal_state_=CollectionRemovalState::failed;return;
    }
    if(status.phase!=Phase::removed)return;
    removal_trace("deletion complete; reconfiguring installer");
    collection_installer_.shutdown();
#if defined(__FreeBSD__)
    const bool configured=collection_installer_.configure(root_+"/content/collection-packs.json","/data/pixelmuseum",root_,false,data_);
#else
    const bool configured=collection_installer_.configure(root_+"/content/collection-packs.json",data_,root_);
#endif
    if(!configured){collection_removal_state_=CollectionRemovalState::failed;return;}
    removal_trace("installer configured; showing language selection");
    collection_pending_=true;collection_started_=false;
    collection_media_started_=false;collection_media_error_=false;
    collection_elapsed_=collection_ready_elapsed_=0;
    collection_phase_log_=collection_progress_log_=-1;collection_presentation_.replay();
    settings_=credits_=volumes_open_=connection_panel_=false;
    detail_=gallery_=screening_=fullscreen_=object_inspect_=false;
    chapters_=year_guide_=search_page_=workshop_active_=false;
    panel_.snap(0);credits_open_.snap(0);story_open_.snap(0);gallery_open_.snap(0);screening_open_.snap(0);object_open_.snap(0);
    onboarding_=language_choice_=theme_choice_=true;
    theme_confirming_=false;theme_confirm_progress_=0;onboarding_leaving_=false;
    onboarding_step_=0;onboarding_position_.snap(0);onboarding_fade_.snap(1);
    language_selection_.snap(float(language_focus_));boot_time_=0;boot_note_=0;
    collection_removal_state_=CollectionRemovalState::idle;
    save_settings();
    removal_trace("language selection ready");
}

void Screen::draw_collection_removal(){
    using namespace hui;
    using hui::gfx::Align;using hui::gfx::Color;using hui::gfx::Rect;
    const auto palette=colours();
    if(collection_removal_active()){
        overlay_.rounded_rect({0,0,1920,1080},0,palette.paper);
        logo(overlay_,905,256,110,palette.ink);
        const bool failed=collection_removal_state_==CollectionRemovalState::failed;
        ui::text(overlay_,fonts_.semibold,failed?"Downloaded data could not be removed.":"Removing downloaded data",960,491,42,palette.ink,Align::center);
        const char*message=failed?"Try again, or close the app.":"Please wait a moment.";
        ui::text(overlay_,fonts_.regular,message,960,554,26,palette.muted,Align::center);
        if(failed){
            hui::ui::Hint hints[]={{hui::ui::Button::cross,"Try again"},{hui::ui::Button::circle,"Close app"}};
            hui::ui::HintLayout layout;layout.cy=700;layout.size=28;layout.text_size=23;
            hui::ui::draw_hints(overlay_,fonts_,hui::ui::GlyphStyle::mono(palette.ink,Color::rgb(0,0)),hints,2,960,true,layout);
        }else{
            constexpr float radius=31;
            overlay_.circle(960,675,radius,palette.rule);
            overlay_.circle(960,675,radius-1.5f,palette.paper);
            const float angle=collection_removal_elapsed_*2.4f-1.5707963268f;
            overlay_.rounded_rect({956+std::cos(angle)*radius,671+std::sin(angle)*radius,8,8},0,palette.ink);
        }
        return;
    }
    const float alpha=std::clamp(collection_remove_open_.value,0.f,1.f);
    overlay_.push_opacity(alpha);
    overlay_.rounded_rect({0,0,1920,1080},0,Color::rgb(0,.44f));
    const float rise=(1-alpha)*18;
    const Rect card{410,255+rise,1100,560};
    overlay_.bordered_rect(card,0,palette.paper,1,palette.rule);
    ui::text(overlay_,fonts_.mono,"STORAGE",470,320+rise,18,palette.muted,Align::left,1.8f);
    ui::paragraph(overlay_,fonts_.semibold,"Remove downloaded data?",470,390+rise,38,980,48,palette.ink,2);
    ui::paragraph(overlay_,fonts_.regular,"The collection will need to be downloaded again. You will return to language selection.",470,480+rise,27,970,39,palette.muted,3);
    ui::text(overlay_,fonts_.regular,"Your trophy progress will be kept.",470,618+rise,23,palette.muted);
    for(int action=0;action<2;++action){
        const bool selected=collection_remove_focus_==action;
        const Rect button{470+action*505.f,675+rise,475,78};
        overlay_.bordered_rect(button,0,selected?palette.ink:palette.paper,1,selected?palette.ink:palette.rule);
        ui::text(overlay_,fonts_.semibold,action?"Remove":"Cancel",button.x+button.w*.5f,button.y+48,25,selected?palette.paper:palette.ink,Align::center);
    }
    overlay_.pop_opacity();
}
}
