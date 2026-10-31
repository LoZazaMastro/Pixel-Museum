// Real Music PCM render: listening-room ownership must silence museum ambience.
#include "museum/music.hpp"
#include "platform/playback_window.hpp"
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL %d %s\n",__LINE__,#x);std::abort();}}while(0)
namespace museum {
struct MusicInspection {
    static void constant_source(Music& m){
        for(auto& pcm:m.pcm_)pcm.assign(Music::kSourceRate*Music::kSeconds*2,8192);
        m.ready_=true;
    }
    static unsigned frame(const Music& m){return m.frame_;}
};
}
static float settle(museum::Music& music){
    std::array<float,960> pcm{};
    for(int n=0;n<200;++n)music.render(pcm.data(),480); // Two seconds of real gain fade.
    float peak=0;for(float sample:pcm)peak=std::max(peak,std::abs(sample));return peak;
}
int main(){
    museum::Music music;museum::MusicInspection::constant_source(music);
    music.select_year(2020);music.volume(.5f);
    const float normal=settle(music);CHECK(normal>.12f&&normal<.13f);
    // The separate film policy still ducks by30dB, rather than muting films.
    music.video_active(true);const float film=settle(music);
    CHECK(film>normal*.031f&&film<normal*.032f);
    music.listening_room(true);const unsigned before=museum::MusicInspection::frame(music);
    const float playing=settle(music);CHECK(playing<1e-10f);
    CHECK(museum::MusicInspection::frame(music)==before+96000);
    // Loading, pause, completion and even loss of the film-duck signal cannot
    // restore ambience while the listening room still owns the player.
    float paused=0;
    for(bool ready:{false,true})for(bool pause:{false,true})for(bool ended:{false,true}){
        music.video_active(museum::media::suspend_ambient(true,true,ready,pause,ended));
        paused=std::max(paused,settle(music));CHECK(paused<1e-10f);
    }
    music.video_active(false);CHECK(settle(music)<1e-10f);
    music.video_active(true);CHECK(settle(music)<1e-10f); // Resume stays silent.
    // Only the actual exit relinquishes room ownership and restores ambience.
    music.listening_room(false);music.video_active(false);
    const float exited=settle(music);CHECK(std::abs(exited-normal)<.00001f);
    music.muted(true);CHECK(settle(music)<1e-10f); // Existing user mute wins.
    std::printf("Music PCM PASS: normal=%.6f film-duck=%.6f room=%.12f paused=%.12f exit=%.6f; real render/fade, no PS5 output claim.\n",normal,film,playing,paused,exited);
}
