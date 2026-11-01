// Pixel Museum - first-run collection download, independent of network and input.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "gfx/draw_list.hpp"
#include "ui/fonts.hpp"
#include <cstddef>
#include <cstdint>

namespace museum {
enum class CollectionInstallPhase { checking, preparing, downloading, paused, error, complete, installing, migrating };
enum class CollectionInstallError { none, network, storage, invalid_files, unknown };
struct CollectionInstallViewState {
    CollectionInstallPhase phase=CollectionInstallPhase::checking;
    // Negative derives the fraction from byte counts. No total means indeterminate.
    float progress=-1.f;
    std::uint64_t downloaded_bytes=0,total_bytes=0;
    double bytes_per_second=0;
    std::size_t pack_index=0,pack_count=0;
    CollectionInstallError error=CollectionInstallError::none;
    std::uint64_t installed_bytes=0,total_expanded_bytes=0,installed_files=0,total_files=0;
};
// Byte work, not an estimate of elapsed or remaining time. Uses only work reported
// by the installer; a resumed download prefix and extracted files count once.
inline float collection_install_work_progress(const CollectionInstallViewState& s){
    if(s.phase==CollectionInstallPhase::complete)return 1.f;
    const double total=double(s.total_bytes)+double(s.total_expanded_bytes);
    if(total<=0)return 0.f;
    const double done=double(s.downloaded_bytes>s.total_bytes?s.total_bytes:s.downloaded_bytes)
        +double(s.installed_bytes>s.total_expanded_bytes?s.total_expanded_bytes:s.installed_bytes);
    return float(done/total);
}
// Records a complete 1920x1080 virtual-canvas frame. Does not clear the caller's
// list, access the network, change locale, or advance onboarding. The owner handles
// Cross: pause while downloading, resume when paused, retry on error. Circle closes
// the app. Completion is advanced automatically by the owner; no Continue prompt.
void draw_collection_install_view(hui::gfx::DrawList&,const hui::ui::Fonts&,
    const CollectionInstallViewState&,float dark_mix,float elapsed_seconds,
    bool reduced_motion=false);
}
