// Caption metadata shared by early and deferred player responses.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "yt/types.hpp"
#include <algorithm>
namespace yt::captions {
inline void merge_track(std::vector<CaptionTrack>& tracks,const CaptionTrack& track) {
    const auto found=std::find_if(tracks.begin(),tracks.end(),[&](const CaptionTrack& value){return value.url==track.url;});
    if(found==tracks.end()) {if(tracks.size()<128)tracks.push_back(track);return;}
    // A second client may enrich the same signed URL. Missing fields in a
    // later answer must not erase capabilities explicitly offered earlier.
    if(!track.language.empty())found->language=track.language;
    if(!track.name.empty())found->name=track.name;
    found->automatic=found->automatic||track.automatic;
    found->translatable=found->translatable||track.translatable;
}
inline bool same_metadata(const VideoInfo& a,const VideoInfo& b) {
    if(a.caption_translation_languages!=b.caption_translation_languages||a.captions.size()!=b.captions.size())return false;
    for(std::size_t n=0;n<a.captions.size();++n){
        const auto& x=a.captions[n];const auto& y=b.captions[n];
        if(x.url!=y.url||x.language!=y.language||x.automatic!=y.automatic||x.translatable!=y.translatable)return false;
    }
    return true;
}
}
