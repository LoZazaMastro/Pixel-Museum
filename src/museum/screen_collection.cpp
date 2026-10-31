// Pixel Museum - the collection is installed before the first museum visit.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <cmath>
#include <cctype>

namespace museum {
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
    if(!cache_.images_from_package(root_,collection_installer_.cache_root())||!cache_.start(data_+"/cache")){
        hui::sys::log("[Museum] collection image worker could not start");
        collection_media_error_=true;return false;
    }
    if(!video_.start(data_,root_))hui::sys::log("[Museum] video worker unavailable");
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
    using Phase=CollectionInstaller::Phase;
    switch(state.phase){
    case Phase::unconfigured:case Phase::idle:view.phase=CollectionInstallPhase::checking;break;
    case Phase::downloading:view.phase=CollectionInstallPhase::downloading;break;
    case Phase::verifying:case Phase::extracting:view.phase=CollectionInstallPhase::preparing;break;
    case Phase::paused:case Phase::cancelled:view.phase=CollectionInstallPhase::paused;break;
    case Phase::ready:view.phase=CollectionInstallPhase::complete;break;
    case Phase::failed:{
        view.phase=CollectionInstallPhase::error;
        std::string error=state.error;
        std::transform(error.begin(),error.end(),error.begin(),[](unsigned char c){return char(std::tolower(c));});
        view.error=error.find("space")!=std::string::npos||error.find("disk")!=std::string::npos||error.find("storage")!=std::string::npos?CollectionInstallError::storage:
            error.find("checksum")!=std::string::npos||error.find("sha256")!=std::string::npos||error.find("archive")!=std::string::npos||error.find("manifest")!=std::string::npos||error.find("tar")!=std::string::npos?CollectionInstallError::invalid_files:CollectionInstallError::network;
        break;
    }}
    if(collection_media_error_){view.phase=CollectionInstallPhase::error;view.error=CollectionInstallError::invalid_files;}
    return view;
}

void Screen::handle_collection_startup(const hui::InputFrame& input,hui::ui::Feedback& feedback){
    using hui::Action;using hui::audio::Cue;using Phase=CollectionInstaller::Phase;
    if(input.focus_lost||!input.connected)return;
    if(input.is_pressed(Action::back)){
        collection_installer_.pause();quit_=true;feedback.play(Cue::back);return;
    }
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
    if(language_choice_){language_selection_.target=float(language_focus_);language_selection_.update(dt_,reduced_?60.f:16.f);return;}
    collection_elapsed_+=elapsed;
    if(quit_)return;
    if(!collection_started_){
        collection_started_=true;collection_installer_.start();
    }
    const auto state=collection_installer_.snapshot();
    const int phase=int(state.phase),progress=state.total_bytes?int(std::min(10.,double(state.downloaded_bytes)*10./double(state.total_bytes))):-1;
    if(phase!=collection_phase_log_||progress>collection_progress_log_){
        hui::sys::log("[Museum] collection %s / pack %zu of %zu / %llu of %llu bytes / %s",state.stage.c_str(),state.pack_count?state.pack_index+1:0,state.pack_count,static_cast<unsigned long long>(state.downloaded_bytes),static_cast<unsigned long long>(state.total_bytes),state.error.empty()?"OK":state.error.c_str());
        if(!state.diagnostic.empty())hui::sys::log("[Museum] collection filesystem errno %d / %s",state.filesystem_errno,state.diagnostic.c_str());
        collection_phase_log_=phase;collection_progress_log_=std::max(collection_progress_log_,progress);
    }
    if(collection_installer_.is_ready()&&!collection_media_error_){
        collection_ready_elapsed_+=elapsed;
        // A completed download gets a short, clear conclusion before onboarding.
        // No onboarding clock, entry animation or startup note advances meanwhile.
        if(collection_ready_elapsed_>=.6f&&start_collection_media())collection_pending_=false;
    }else collection_ready_elapsed_=0;
}
}
