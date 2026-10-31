#include "museum/culture_ambience.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <vector>
using A=museum::CultureAmbience;
static std::vector<float> mix(const char*path,float amplitude,float volume,float trim,bool split){
 {std::ofstream file(path);file<<"{\"schema\":1,\"cues\":[{\"entry_id\":\"test\",\"youtube_id\":\"abcdefghijk\",\"kind\":\"music\",\"start_seconds\":0,\"end_seconds\":10,\"reverb\":false,\"gain\":"<<trim<<",\"evidence\":\"synthetic normalization regression\"}]}";}
 A audio;assert(audio.load(path)&&audio.cues()[0].normalize_level);
 for(int n=0;n<9;++n)audio.update({"test",true,1},{},.25f);
 audio.update({"test",true,volume},{true,false,false,0},0);
 constexpr unsigned frames=48000*4;std::vector<float>in(frames*2),out(in.size());
 for(unsigned n=0;n<frames;++n)in[n*2]=in[n*2+1]=amplitude*std::sin(6.283185307179586*440*n/48000.);
 if(split){for(unsigned at=0;at<frames;){const unsigned count=std::min(137u,frames-at);audio.process(in.data()+at*2,out.data()+at*2,count);at+=count;}}
 else audio.process(in.data(),out.data(),frames);
 return out;
}
static double rms(const std::vector<float>&v){double energy=0;for(size_t n=48000*3*2;n<v.size();++n)energy+=double(v[n])*v[n];return std::sqrt(energy/(v.size()-48000*3*2));}
int main(int argc,char**argv){
 assert(argc==2);auto quiet=mix(argv[1],.02f,1,1,false),loud=mix(argv[1],.5f,1,1,false);
 const double qr=rms(quiet),lr=rms(loud);assert(std::abs(20*std::log10(qr/lr))<.15&&std::abs(qr-.12)<.002&&std::abs(lr-.12)<.002);
 assert(quiet==mix(argv[1],.02f,1,1,true));assert(loud==mix(argv[1],.5f,1,1,true));
 auto zero=mix(argv[1],.02f,0,1,false);assert(std::all_of(zero.begin(),zero.end(),[](float x){return x==0;}));
 auto trimmed=mix(argv[1],.02f,1,1.3f,false);assert(std::abs(rms(trimmed)/qr-1.3)<.001);
 A resume;assert(resume.load(argv[1]));for(int n=0;n<9;++n)resume.update({"test",true,1},{},.25f);
 resume.update({"test",true,1},{true,false,false,0},0);std::vector<float>constant(96000*2,.02f),mixed(constant.size());resume.process(constant.data(),mixed.data(),96000);
 assert(resume.update({"test",true,0},{true,false,false,2},.01f).kind==A::Command::none&&resume.owns_player()&&resume.ambient_gain()==1);
 mixed.assign(constant.size(),0);resume.process(constant.data(),mixed.data(),96000);assert(mixed.back()==0);
 assert(resume.update({"test",true,1},{true,false,false,4},.01f).kind==A::Command::none&&resume.owns_player());
 mixed.assign(constant.size(),0);resume.process(constant.data(),mixed.data(),96000);assert(mixed.back()>.1f);
 // First audible sample follows the existing one-second fade, with no pop.
 assert(std::abs(quiet[0])<1e-8&&std::abs(quiet[2])<.000001);
 museum::CultureLevel level;
 for(unsigned n=0;n<48000*3;++n)assert(level.process(0,0)==1);
 for(unsigned n=0;n<48000*2;++n)assert(level.process(.000001f,.000001f)==1);
 assert(!level.calibrated());
 for(unsigned n=0;n<48000*2;++n)level.process(.02f,.02f);
 assert(level.calibrated());const float target=level.target_gain();
 for(unsigned n=0;n<48000;++n){level.process(n<24000?0:.000001f,n<24000?0:.000001f);assert(level.target_gain()==target);}
 // The target stays fixed through a pause and quiet background: no noise chase.
 level.reset();assert(!level.calibrated()&&level.gain()==1&&level.target_gain()==1);
 for(unsigned n=0;n<48000*2;++n)level.process(.0011f,.0011f);
 assert(level.target_gain()==16);
 level.reset();for(unsigned n=0;n<48000*2;++n)level.process(n%2400==0?1.f:0.f,n%2400==0?1.f:0.f);
 assert(level.calibrated()&&level.target_gain()<=.85f);
 level.reset(false);for(unsigned n=0;n<48000*2;++n)assert(level.process(.5f,.5f)==1);
 std::printf("PASS normalized actual mixer quietRMS%.6f loudRMS%.6f delta%.4fdB;customtrim afterbalance;volume0/1;entryfade;splitblock exact;silence/tiny PCM preserved;pause stable;boost<=16;peakmargin;reset/bypass\n",qr,lr,20*std::log10(qr/lr));
}
