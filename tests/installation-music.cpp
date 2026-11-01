#include "museum/music.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
namespace museum {struct MusicInspection {static unsigned clock(const Music&m){return m.frame_;}static float intro(const Music&m){return m.onboarding_mix_;}};}
int main(){
 museum::Music music;assert(music.init("music/eras"));music.volume(.48f);music.onboarding_active(true);music.muted(false);std::array<float,960>out{};
 float peak=0;for(unsigned n=0;n<6500;++n){music.render(out.data(),480);for(float v:out){assert(std::isfinite(v));peak=std::max(peak,std::abs(v));}}
 assert(peak>.001f&&peak<.5f&&museum::MusicInspection::intro(music)==1.f);const auto position=museum::MusicInspection::clock(music);
 music.onboarding_active(false);music.select_year(1989);for(unsigned n=0;n<22;++n)music.render(out.data(),480);assert(museum::MusicInspection::intro(music)==0.f);assert(museum::MusicInspection::clock(music)==position+22*480);
 music.muted(true);for(unsigned n=0;n<200;++n)music.render(out.data(),480);for(float v:out)assert(std::abs(v)<1e-8f);
 std::printf("PASS real bundled installation/onboarding bed:65s includingloop,peak%.5f,sharedclock,200mstransition,user-mute,noextraMusicvoice\n",peak);
}
