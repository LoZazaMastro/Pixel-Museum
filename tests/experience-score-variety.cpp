// Real callback PCM: distinct original scores, loop seams and ownership.
#include "museum/experience_audio.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <set>
#include <string_view>
#include <vector>

int main(){
    constexpr std::string_view ids[]={"paddle","bricks","formation","maze","gravity","orbit","wireframe","jump","momentum","dash","sequencer","raycast","scale","portals","pocket-budget","jump-lab","city-system","pixels"};
    constexpr float bpm[]={80,88,72,96,72,64,68,92,104,84,80,76,90,66,62,70,64,60};
    std::set<std::uint64_t> signatures;
    for(unsigned profile=0;profile<std::size(ids);++profile){
        museum::ExperienceAudio audio;audio.start(ids[profile]);
        std::array<float,512> pcm{};std::array<float,256> pad{};
        const unsigned seam=unsigned(std::llround(48000.*60./bpm[profile]*32.));
        const unsigned length=seam+1024;
        double energy=0;float peak=0,max_seam_step=0,previous=0;std::uint64_t hash=1469598103934665603ull;
        for(unsigned at=0;at<length;at+=256){
            const unsigned count=std::min(256u,length-at);pcm.fill(0);pad.fill(1);audio.render(pcm.data(),count,pad.data());
            for(unsigned n=0;n<count;++n){
                assert(pad[n]==0); // Background score never leaks to controller.
                for(unsigned channel=0;channel<2;++channel){const float v=pcm[n*2+channel];assert(std::isfinite(v));peak=std::max(peak,std::abs(v));energy+=v*v;}
                if(at+n>=seam-4&&at+n<=seam+4)max_seam_step=std::max(max_seam_step,std::abs(pcm[n*2]-previous));
                previous=pcm[n*2];
                if(at+n<48000*4){const auto sample=std::int32_t(std::lround(pcm[n*2]*1000000));hash=(hash^std::uint32_t(sample))*1099511628211ull;}
            }
        }
        assert(energy>1&&peak>.015f&&peak<.25f&&max_seam_step<.015f);
        assert(signatures.insert(hash).second);
        const double paused=audio.time_s();audio.paused(true);pcm.fill(.25f);audio.render(pcm.data(),256,pad.data());
        for(float v:pcm)assert(v==.25f);assert(audio.time_s()==paused);
        audio.paused(false);pcm.fill(0);audio.render(pcm.data(),256);assert(std::abs(audio.time_s()-paused-256./48000)<1e-6);
        audio.stop();for(int n=0;n<80;++n){pcm.fill(0);audio.render(pcm.data(),256);}for(float v:pcm)assert(v==0);
        std::printf("%.*s PASS peak%.4f seam-step%.6f unique%llu\n",int(ids[profile].size()),ids[profile].data(),peak,max_seam_step,static_cast<unsigned long long>(hash));
    }
    for(const auto id:{std::string_view("adaptive-pulse"),std::string_view("unknown")}){
        museum::ExperienceAudio audio;audio.start(id);std::array<float,512> pcm{};audio.render(pcm.data(),256);for(float v:pcm)assert(v==0);
    }
    // Explicit rhythm selection is sample-identical to the untouched DDR path.
    museum::ExperienceAudio legacy,explicit_rhythm;legacy.start();explicit_rhythm.start("rhythm");
    std::array<float,512> a{},b{};std::array<float,256> pa{},pb{};
    for(int n=0;n<500;++n){a.fill(0);b.fill(0);legacy.render(a.data(),256,pa.data());explicit_rhythm.render(b.data(),256,pb.data());assert(a==b&&pa==pb);}
    std::puts("PASS18distinct original loop scores, continuous seams, silentpad, pause/resume/exit; DDR and Kondo exclusions preserved.");
}
