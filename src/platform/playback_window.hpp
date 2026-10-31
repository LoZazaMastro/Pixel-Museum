// Bounded soundtrack passages; absolute decoder clock, relative listening-room UI.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
namespace museum::media {
struct PlaybackWindow {
    double start=0,end=0;
    bool bounded()const{return end>start;}
    static bool valid(double first,double last){return std::isfinite(first)&&std::isfinite(last)&&first>=0&&last>first&&last<=31622400.;}
    double finish(double duration)const{return bounded()?(duration>0?std::min(end,duration):end):std::max(0.,duration);}
    double duration(double total)const{return std::max(0.,finish(total)-start);}
    double time(double absolute,double total)const{return !bounded()&&total<=0?std::max(0.,absolute):std::clamp(absolute-start,0.,duration(total));}
    double seek(double relative,double total)const{return !bounded()&&total<=0?std::max(0.,relative):std::clamp(start+relative,start,std::max(start,finish(total)));}
};
// Producer-only sample budget. A decoder block crossing the cue boundary is
// truncated before entering the ring; the following cue cannot leak audibly.
class SegmentFrames {
public:
    void reset(double seconds){left_=seconds>=0?std::uint64_t(std::floor(std::max(0.,seconds)*48000.+.000001)):unlimited;}
    std::size_t allowance(std::size_t n)const{return left_==unlimited?n:std::size_t(std::min<std::uint64_t>(n,left_));}
    void written(std::size_t n){if(left_!=unlimited)left_-=std::min<std::uint64_t>(left_,n);}
    bool exhausted()const{return left_==0;}
private:
    static constexpr auto unlimited=std::numeric_limits<std::uint64_t>::max();
    std::uint64_t left_=unlimited;
};
inline bool suspend_ambient(bool listening_room,bool screening,bool ready,bool paused,bool ended){return listening_room||(screening&&ready&&!paused&&!ended);}
// Only a successful player EOF closes a standalone screening. Keep the
// exhibit/card selection untouched; the existing overlay fade owns cleanup.
// Playlist EOF belongs to its separate advance/completion policy.
inline bool finish_screening(bool&screening,bool&fullscreen,bool playlist,bool ready,bool ended){
    if(!screening||playlist||!ready||!ended)return false;
    screening=false;fullscreen=false;return true;
}
}
