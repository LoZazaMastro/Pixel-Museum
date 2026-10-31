// Host checks for the exact playback implementation used on PS5.
#include "museum/music.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
#include <chrono>
#include <numeric>

namespace museum {
struct MusicInspection {
    static unsigned clock(const Music&m){return m.frame_;}
    static unsigned target(const Music&m){return m.target_era_;}
    static unsigned remaining(const Music&m){return m.fade_remaining_;}
    static float weight(const Music&m,unsigned era){return m.weights_[era];}
    static unsigned technology(const Music&m){return m.target_technology_;}
    static unsigned technology_remaining(const Music&m){return m.technology_remaining_;}
    static float technology_sum(const Music&m){return std::accumulate(m.technology_weights_.begin(),m.technology_weights_.end(),0.f);}
    static float year(const Music&m){return m.year_.load();}
    static void fixture(Music&m,float hz) {
        m.ready_=true; m.frame_=0; m.gain_=0; m.filters_={};
        m.target_era_=Music::kEraCount; m.target_technology_=Music::kTechnologyCount;
        m.weights_.fill(0); m.technology_weights_.fill(0);
        m.fade_remaining_=m.technology_remaining_=0;
        for(auto &stem:m.pcm_) {
            stem.resize(Music::kSourceRate*Music::kSeconds*2);
            for(unsigned i=0;i<Music::kSourceRate*Music::kSeconds;++i) {
                const float phase=6.28318530718f*hz*float(i%Music::kSourceRate)/Music::kSourceRate;
                stem[i*2]=std::int16_t(6000*std::sin(phase));
                stem[i*2+1]=std::int16_t(3500*std::sin(phase+.7f));
            }
        }
    }
    static float sum(const Music&m){return std::accumulate(m.weights_.begin(),m.weights_.end(),0.f);}
};
}

static void historical_checks() {
    using Music=museum::Music; using Inspect=museum::MusicInspection;
    Music a,b;
    Inspect::fixture(a,300); Inspect::fixture(b,300);
    std::vector<float> whole(12000*2), chunks(12000*2);
    const float years[]={1833,1876,1877,1886,1887,1910,1925,1949,1950,1957,1958,1981,1982,2024,1890,1910};
    const unsigned profiles[]={0,0,1,1,2,2,3,3,4,4,5,5,6,6,2,2};
    float prior=0,step=0;
    for(unsigned n=0;n<std::size(years);++n) {
        a.select_year(years[n]); b.select_year(years[n]);
        const auto before=Inspect::clock(a);
        a.render(whole.data(),12000);
        for(unsigned done=0;done<12000;) {
            const unsigned count=std::min(193u,12000-done);
            b.render(chunks.data()+done*2,count);done+=count;
        }
        assert(whole==chunks); // Includes every historical transition, not only steady state.
        assert(Inspect::technology(a)==profiles[n]);
        assert(Inspect::technology_remaining(a)==0);
        assert(std::abs(Inspect::technology_sum(a)-1)<1e-5f);
        assert(Inspect::clock(a)==before+12000);
        for(unsigned i=0;i<12000;++i) {
            assert(std::isfinite(whole[i*2])&&std::isfinite(whole[i*2+1]));
            step=std::max(step,std::abs(whole[i*2]-prior));prior=whole[i*2];
        }
        if(profiles[n]>=1&&profiles[n]<=4)
            for(unsigned i=10000;i<12000;++i) assert(whole[i*2]==whole[i*2+1]);
    }
    assert(step<.025f); // 300 Hz continuous fixture: no transition discontinuity.
    // Two years within the same acoustic-disc technology must sound identical.
    Inspect::fixture(a,300);Inspect::fixture(b,300);
    a.select_year(1890);b.select_year(1890);a.render(whole.data(),12000);b.render(chunks.data(),12000);
    a.select_year(1910);a.render(whole.data(),12000);b.render(chunks.data(),12000);
    assert(whole==chunks&&Inspect::technology_remaining(a)==0&&Inspect::remaining(a)==0);
    // Retargeting in the middle of a technology fade preserves its current sum/phase.
    a.select_year(1982);a.render(whole.data(),1000);const auto clock=Inspect::clock(a);
    a.select_year(1877);a.render(whole.data(),1);
    assert(Inspect::clock(a)==clock+1&&Inspect::technology_remaining(a)==Music::kCrossfadeFrames-1);
    assert(std::abs(Inspect::technology_sum(a)-1)<1e-5f);
    a.select_year(-100);assert(Inspect::year(a)==1833);a.select_year(3000);assert(Inspect::year(a)==2024);
    // A real high-frequency input is strongly reduced by the acoustic profile,
    // rather than transformed into few-bit/sample-held computer noise.
    Inspect::fixture(a,8000);Inspect::fixture(b,8000);
    a.select_year(1877);b.select_year(1982);a.render(whole.data(),12000);b.render(chunks.data(),12000);
    double old_energy=0,modern_energy=0;
    for(unsigned i=10000;i<12000;++i){old_energy+=whole[i*2]*whole[i*2];modern_energy+=chunks[i*2]*chunks[i*2];}
    assert(old_energy<modern_energy*.02&&modern_energy>0.1);
    std::printf("PASS historical profiles:1833 clean,1877 phonograph,1887 gramophone,1925 electrical,1950 tape,1958 stereo,1982 digital; exact block invariance across all transitions;1890/1910 identical; click-free retarget max step %.6f; acoustic8kHz energy ratio %.6f.\n",step,old_energy/modern_energy);
}

int main(int argc, char **argv) {
    historical_checks();
    assert(argc == 2);
    museum::Music music;
    std::vector<float> silence(4096, 1);
    music.render(silence.data(), 2048);
    assert(std::all_of(silence.begin(), silence.end(), [](float x){return x==0;}));
    assert(!music.init("/missing/pixel-museum-music"));
    assert(!music.error().empty());
    assert(music.init(argv[1]));
    assert(music.pcm_bytes()==17u*64u*24000u*2u*2u);
    museum::Music split;
    assert(split.init(argv[1]));
    music.select_year(1967.5f);
    split.select_year(1967.5f);
    std::vector<float> together(24000*2), pieces(24000*2);
    music.render(together.data(), 24000);
    for (unsigned done=0; done<24000;) {
        unsigned count=std::min(137u,24000-done);
        split.render(pieces.data()+done*2,count);
        done+=count;
    }
    assert(together==pieces);
    // Both compositions advance on the very same sample clock. Exercise
    // changing and reversing a fade with different callback block sizes.
    for(unsigned turn=0;turn<6;++turn) {
        music.select_timeline(turn%2==0);split.select_timeline(turn%2==0);
        music.render(together.data(),24000);
        for(unsigned done=0;done<24000;) {
            const unsigned count=std::min(137u,24000-done);
            split.render(pieces.data()+done*2,count);done+=count;
        }
        assert(together==pieces);
        assert(museum::MusicInspection::clock(music)==museum::MusicInspection::clock(split));
    }
    // Return from culture at the continuously advancing gaming position,
    // rather than replaying the gaming track's entrance.
    museum::Music reference;assert(reference.init(argv[1]));
    reference.select_year(1967.5f);
    for(unsigned n=0;n<7;++n)reference.render(pieces.data(),24000);
    music.select_timeline(false);
    for(unsigned n=0;n<4;++n){music.render(together.data(),24000);reference.render(pieces.data(),24000);}
    float difference=0;
    for(unsigned n=0;n<together.size();++n)difference=std::max(difference,std::abs(together[n]-pieces[n]));
    assert(difference<1e-5f);
    music.select_timeline(true);music.render(together.data(),24000);reference.render(pieces.data(),24000);
    double distinct=0;for(unsigned n=0;n<together.size();++n)distinct+=std::abs(together[n]-pieces[n]);
    assert(distinct>1);
    music.select_timeline(false);music.render(together.data(),24000);
    std::puts("PASS dual compositions: exact block invariance across timeline changes, shared advancing clock, distinct music and return without restart.");
    using Inspect=museum::MusicInspection;
    assert(Inspect::target(music)==1); //1967 belongs to the1960s, never a70/30 era blend.
    const unsigned before=Inspect::clock(music);
    music.select_year(2020);
    float immediate[2];music.render(immediate,1);
    assert(Inspect::clock(music)==before+1&&Inspect::target(music)==7);
    assert(Inspect::weight(music,7)>0&&Inspect::remaining(music)==museum::Music::kCrossfadeFrames-1);
    assert(std::abs(Inspect::sum(music)-1)<1e-5f);
    std::vector<float> crossfade(museum::Music::kCrossfadeFrames*2);
    music.render(crossfade.data(),museum::Music::kCrossfadeFrames-1);
    assert(Inspect::remaining(music)==0&&Inspect::weight(music,7)==1);
    assert(Inspect::clock(music)==before+museum::Music::kCrossfadeFrames);
    // Retargeting halfway through a fade starts from the current mix rather
    // than dropping an audible arrangement or restarting its shared phase.
    music.select_year(1950);music.render(crossfade.data(),1000);
    const float current=Inspect::weight(music,0);const auto phase=Inspect::clock(music);
    music.select_year(1989);music.render(immediate,1);
    assert(Inspect::target(music)==3&&Inspect::clock(music)==phase+1);
    assert(Inspect::weight(music,0)>0&&std::abs(Inspect::weight(music,0)-current)<.001f);
    assert(std::abs(Inspect::sum(music)-1)<1e-5f);
    music.render(crossfade.data(),museum::Music::kCrossfadeFrames);
    music.select_year(1980);music.render(immediate,1);
    assert(Inspect::remaining(music)==0&&Inspect::weight(music,3)==1);
    assert(music.init(argv[1]));music.select_year(1967.5f);music.render(together.data(),24000);
    std::vector<float> block(1024*2);
    double energy=0;
    float peak=0, previous=0, join=0;
    for (unsigned done=24000; done<48000*131u;) {
        unsigned count=std::min(1024u,48000*131u-done);
        if (done>48000*70u) music.select_year(2020);
        music.render(block.data(),count);
        for (unsigned i=0;i<count;++i) {
            const float l=block[i*2];
            assert(std::isfinite(l) && std::isfinite(block[i*2+1]));
            peak=std::max(peak,std::abs(l));
            energy+=l*l;
            if ((done+i)% (48000*64u)==0) join=std::max(join,std::abs(l-previous));
            previous=l;
        }
        done+=count;
    }
    assert(energy>1 && peak<0.25f && join<0.015f);
    music.video_active(true);
    for (int i=0;i<150;++i) music.render(block.data(),1024);
    float duck=0;
    for (float x:block) duck=std::max(duck,std::abs(x));
    assert(duck<0.01f);
    music.muted(true);
    const auto muted_phase=Inspect::clock(music);
    for (int i=0;i<150;++i) music.render(block.data(),1024);
    assert(Inspect::clock(music)==(muted_phase+150*1024)%(museum::Music::kOutputRate*64));
    for (float x:block) assert(std::abs(x)<1e-8f);
    music.muted(false);music.video_active(false);
    const auto started=std::chrono::steady_clock::now();
    for(unsigned n=0;n<10000;++n){music.select_year(1950+float(n%8)*10);music.render(block.data(),1024);assert(std::abs(Inspect::sum(music)-1)<1e-5f);}
    const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    std::printf("PASS: all8arrangements share an advancing clock;200ms immediate-start constant-sum crossfades; rapid retarget; no restart on era/mute/video; exact lengths; block invariance; two loop joins; peak %.5f; seam %.5f; video duck; mute. PCM %zu bytes. Worst-case continuous8era retarget: %.4fs per213.33s stereo audio (host,notPS5).\n",peak,join,music.pcm_bytes(),seconds);
}
