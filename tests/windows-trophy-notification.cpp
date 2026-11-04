// Exercise the Windows trophy chime and mixer, with no audio device or user data.
#include "museum/desktop_trophy_notification.hpp"
#include "audio/museum_interface_mix.hpp"
#include "audio/wav.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <vector>

int main(int argc,char**argv){
    using namespace hui::audio;
    using namespace museum::desktop_trophy;
    assert(duration==6.f);
    assert(opacity(duration)==0&&opacity(5.f)==1&&opacity(0)==0);
    assert(text_offset(300,494,3,false)==0);
    assert(text_offset(900,494,5.3f,false)==0);
    assert(text_offset(900,494,.5f,false)==406);
    assert(text_offset(900,494,2,true)==0);
    float previous=0;
    for(int n=0;n<=600;++n){
        const float offset=text_offset(900,494,duration-n*.01f,false);
        assert(offset>=previous&&offset>=0&&offset<=406);previous=offset;
    }
    const char*path=argc>1?argv[1]:"assets/audio/museum-navigation/glass/notify_01.wav";
    std::ifstream source(path,std::ios::binary);assert(source);
    const std::string bytes{std::istreambuf_iterator<char>(source),{}};
    auto wav=decode_wav(bytes);assert(wav.ok()&&wav.frames>4800);
    const auto frames=wav.frames;
    const auto& chime=museum_original::trophy_chime();
    assert(chime.frames==29760&&chime.samples[0]==0&&chime.samples[chime.frames*2-1]==0);
    SoundBank bank;bank.set_pitch_jitter(0);bank.set_recordings_only(true);
    bank.add(SoundSet::glass,Cue::notify,std::move(wav.samples),frames);
    const auto rms=[&](float master,float sfx,bool trophy){
        Mixer mixer;mixer.set_bus_gain(Bus::ui,.18f*sfx);mixer.set_bus_gain(Bus::sfx,sfx);mixer.set_master_gain(master);
        std::vector<std::int16_t> silence(24000*2);mixer.render(silence.data(),24000);
        if(trophy)play_sound(mixer,master,sfx);
        else bank.play(mixer,SoundSet::glass,{Cue::notify,1,0,museum_original::interface_gain(Cue::notify,1)},Bus::sfx);
        const auto render_frames=std::max(frames,chime.frames)+512;
        std::vector<std::int16_t> rendered(render_frames*2);mixer.render(rendered.data(),int(render_frames));
        double energy=0;for(auto value:rendered)energy+=double(value)*value;
        if(trophy){
            int peak=0;for(auto value:rendered)peak=std::max(peak,std::abs(int(value)));
            assert(peak<.44*32768);
        }
        return std::sqrt(energy/rendered.size())/32768.;
    };
    const auto audible=rms(1,1,true),old_notify=rms(1,1,false);
    assert(audible>.05&&audible>old_notify);
    assert(rms(1,0,true)==0&&rms(0,1,true)==0);
    const auto half_sfx=rms(1,.5f,true),half_master=rms(.5f,1,true);
    assert(std::abs(half_sfx/audible-.5)<.025&&std::abs(half_master/audible-.5)<.025);
    std::printf("PASS: 6s lifetime; bounded subtitle marquee; trophy RMS=%.6f old notify RMS=%.6f; peak below -7 dBFS, both volume controls and mutes honored.\n",audible,old_notify);
}
