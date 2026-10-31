// Actual state machine + signal processing, offline. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/culture_ambience.hpp"
#include "audio/output_peak_guard.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <vector>
using A=museum::CultureAmbience;
static void fixture(const char*path,bool music=true){std::ofstream f(path);f<<"{\"schema\":1,\"cues\":[{\"entry_id\":\"selected\",\"youtube_id\":\"abcdefghijk\",\"start_seconds\":12,\"end_seconds\":30,\"kind\":\""<<(music?"music":"voice")<<"\",\"normalize_level\":false,\"reverb\":"<<(music?"false":"true")<<",\"gain\":1,\"evidence\":\"actual bounded test fixture\"}]}";}
static void start(A&a){A::Context c{"selected",true,.4f};for(int n=0;n<19;++n)assert(a.update(c,{},.1f).kind==A::Command::none);auto cmd=a.update(c,{},.11f);assert(cmd.kind==A::Command::open&&cmd.cue->start==12&&cmd.cue->end==30&&a.owns_player());}
static double signal(A&a,float amplitude,float*peak=nullptr){std::vector<float>in(256*2),out(in.size());double sum=0;unsigned count=0;float max=0;for(unsigned at=0;at<48000*3;at+=256){for(unsigned n=0;n<256;++n)in[n*2]=in[n*2+1]=amplitude*std::sin(6.28318530718f*220*float(at+n)/48000);std::fill(out.begin(),out.end(),0);a.process(in.data(),out.data(),256);for(float v:out){assert(std::isfinite(v));max=std::max(max,std::abs(v));if(at>48000*2){sum+=v*v;++count;}}}if(peak)*peak=max;return std::sqrt(sum/count);}
int main(int argc,char**argv){assert(argc==3);fixture(argv[1]);A a;assert(a.load(argv[1]));
 A::Context c{"selected",true,.4f};
 for(int n=0;n<100;++n){c.entry_id=n%2?"selected":"other";assert(a.update(c,{},.1f).kind==A::Command::none);} // No requests during fast scrolling.
 c.entry_id="other";a.update(c,{},.1f);start(a);
 for(int n=0;n<100;++n)assert(a.update({"selected",true,.4f},{true,false,false,13},.1f).kind==A::Command::none);
 assert(a.update({"selected",true,.4f},{true,true,false,30},.1f).kind==A::Command::close);
 for(int n=0;n<100;++n)assert(a.update({"selected",true,.4f},{},.1f).kind==A::Command::none); // One-shot EOF latch.
 a.update({"other",true,.4f},{},.1f);start(a);a.relinquish();assert(!a.owns_player()&&!a.rendering()); // Explicit player wins immediately.
 a.update({"other",true,.4f},{},.1f);start(a);assert(a.update({"other",true,.4f},{true,false,false,13},.1f).kind==A::Command::none);assert(a.update({"selected",true,.4f},{true,false,false,13},.1f).kind==A::Command::close); // Returning during fade still requires new dwell.
 A quiet,loud,silence;assert(quiet.load(argv[1])&&loud.load(argv[1])&&silence.load(argv[1]));start(quiet);start(loud);start(silence);float qp=0,lp=0;double qr=signal(quiet,.05f,&qp),lr=signal(loud,.5f,&lp),sr=signal(silence,.000001f);
 const double scale=.4*.8/std::sqrt(2.);
 assert(std::abs(qr-.05*scale)<1e-5&&std::abs(lr-.5*scale)<1e-5&&std::abs(sr-.000001*scale)<1e-9);
 assert(std::abs(qr/lr-.1)<1e-5&&lp>.15f); // Original dynamics and orchestral peaks are not normalized or clipped.
 // Fade on menu/focus loss is sample-smooth and reaches silence before close.
 quiet.update({"selected",false,.4f},{true,false,false,14},.1f);std::vector<float>in(9600*2,.5f),out(in.size());quiet.process(in.data(),out.data(),9600);for(unsigned n=8000;n<9600;++n)assert(std::abs(out[n*2])<1e-8f);
 // Music is rigorously dry: after an impulse there is no delayed output.
 A dry;assert(dry.load(argv[1]));start(dry);signal(dry,.5f);in.assign(9600*2,0);out.assign(in.size(),0);in[0]=in[1]=.5f;dry.process(in.data(),out.data(),9600);for(unsigned n=1;n<9600;++n)assert(out[n*2]==0&&out[n*2+1]==0);
 A whole,split;assert(whole.load(argv[1])&&split.load(argv[1]));start(whole);start(split);
 whole.update({"selected",true,.4f},{true,false,false,29.8},.01f);split.update({"selected",true,.4f},{true,false,false,29.8},.01f);
 in.assign(24000*2,.5f);out.assign(in.size(),0);std::vector<float>parts(in.size(),0);whole.process(in.data(),out.data(),24000);
 for(unsigned at=0;at<24000;){unsigned n=std::min(137u,24000-at);split.process(in.data()+at*2,parts.data()+at*2,n);at+=n;}assert(out==parts);
 whole.relinquish();assert(whole.ambient_gain()==1);
 fixture(argv[1],false);A voice;assert(voice.load(argv[1]));start(voice);voice.update({"selected",true,.4f},{true,false,false,13},.01f);assert(voice.ambient_gain()==1);signal(voice,.01f);assert(std::abs(voice.ambient_gain())<1e-6f);
 voice.update({"selected",true,.4f},{true,false,true,13},.01f);assert(!voice.owns_player()&&voice.ambient_gain()==1);
 for(int n=0;n<100;++n)assert(voice.update({"selected",true,.4f},{},.1f).kind==A::Command::none); // Failure is not an automatic retry loop.
 // Reject invalid/misclassified or duplicate untrusted cue records.
 {std::ofstream f(argv[1]);f<<"{\"schema\":1,\"cues\":[{\"entry_id\":\"x\",\"youtube_id\":\"abcdefghijk\",\"start_seconds\":0,\"end_seconds\":2,\"kind\":\"music\",\"normalize_level\":false,\"reverb\":true,\"evidence\":\"test\"}]}";}A invalid;assert(!invalid.load(argv[1]));
 // Exact quiet PCM passthrough after the intentional entry fade, for music and dry voice.
 for(bool is_music:{true,false}){
  {std::ofstream f(argv[1]);f<<"{\"schema\":1,\"cues\":[{\"entry_id\":\"selected\",\"youtube_id\":\"abcdefghijk\",\"start_seconds\":12,\"end_seconds\":30,\"kind\":\""<<(is_music?"music":"voice")<<"\",\"normalize_level\":false,\"reverb\":false,\"gain\":1,\"evidence\":\"quiet waveform test\"}]}";}
  A passthrough;assert(passthrough.load(argv[1]));start(passthrough);
  std::vector<float>tiny(48000*2,.000001f),result(tiny.size());passthrough.process(tiny.data(),result.data(),48000);
  const float expected=.000001f*.4f*.8f;
  assert(result[(48000-1)*2]==expected&&result[(48000-1)*2+1]==expected); // Full one-second fade, no gate/boost, exact20%trim.
 }
 // Bounded source table accepts the requested expansion, still rejects oversized input.
 for(unsigned count:{512u,513u}){
  {std::ofstream f(argv[1]);f<<"{\"schema\":1,\"cues\":[";for(unsigned i=0;i<count;++i){if(i)f<<',';f<<"{\"entry_id\":\"entry"<<i<<"\",\"youtube_id\":\"abcdefghijk\",\"start_seconds\":0,\"end_seconds\":5,\"kind\":\"music\",\"normalize_level\":false,\"reverb\":false,\"evidence\":\"bounded test\"}";}f<<"]}";}
  A bounded;assert(bounded.load(argv[1])==(count==512));
 }
 // Curated static gain can raise one quiet recording without AGC or gating.
 for(float gain:{1.f,1.3f,2.f,2.001f,0.f}){
  {std::ofstream f(argv[1]);f<<"{\"schema\":1,\"cues\":[{\"entry_id\":\"selected\",\"youtube_id\":\"abcdefghijk\",\"start_seconds\":12,\"end_seconds\":30,\"kind\":\"music\",\"normalize_level\":false,\"reverb\":false,\"gain\":"<<gain<<",\"evidence\":\"static gain test\"}]}";}
  A curated;const bool valid=gain>0&&gain<=2;assert(curated.load(argv[1])==valid);if(!valid)continue;
  start(curated);std::vector<float>pcm(48000*2,.5f),mix(pcm.size());curated.process(pcm.data(),mix.data(),48000);assert(mix.back()==.5f*.4f*gain*.8f);
 }
 // Every archival voice silences the museum bed, including older tables
 // which still carry the former duck policy.
 for(const char*policy:{"silence","duck","invalid"}){
  {std::ofstream f(argv[1]);f<<"{\"schema\":1,\"cues\":[{\"entry_id\":\"selected\",\"youtube_id\":\"abcdefghijk\",\"start_seconds\":12,\"end_seconds\":30,\"kind\":\"voice\",\"normalize_level\":false,\"reverb\":false,\"ambient_policy\":\""<<policy<<"\",\"evidence\":\"voice mixing policy\"}]}";}
  A voice;bool valid=std::string(policy)!="invalid";assert(voice.load(argv[1])==valid);if(!valid)continue;
  start(voice);voice.update({"selected",true,.4f},{true,false,false,12},0);
  std::vector<float>pcm(48000*2,.5f),mix(pcm.size());voice.process(pcm.data(),mix.data(),48000);
  assert(std::abs(voice.ambient_gain())<1e-6f);
  assert(mix.back()==.5f*.4f*.8f);
 }
 hui::audio::OutputPeakGuard protection;float overload[]={1.3f,.65f,-1.3f,-.65f};std::int16_t protected_pcm[4];protection.convert(overload,protected_pcm,2);assert(protected_pcm[0]==32767&&protected_pcm[2]==-32767);assert(std::abs(int(protected_pcm[1])*2-int(protected_pcm[0]))<=1); // One stereo block gain, no waveshaping.
 // Invalid metadata/local paths remain isolated; a rejected ID must not
 // reserve that name and prevent a later valid cue from loading.
 fixture(argv[1]);nlohmann::json mixed;{std::ifstream file(argv[1]);file>>mixed;}
 auto good=mixed["cues"][0],bad=good;bad["local_audio_path"]="../outside.wav";
 mixed["cues"]=nlohmann::json::array({bad,good,bad});{std::ofstream file(argv[1]);file<<mixed;}
 A resilient;assert(resilient.load(argv[1])&&resilient.cues().size()==1&&resilient.cues()[0].entry_id=="selected");start(resilient);
 A actual;assert(actual.load(argv[2])&&actual.cues().size()>=12&&actual.cues().size()<=512);unsigned music=0,voices=0,local_music=0;
 for(const auto&cue:actual.cues()){
  if(cue.kind=="music"){++music;assert(!cue.reverb);if(cue.local_audio)++local_music;}else ++voices;
  actual.relinquish();A::Context context{cue.entry_id,true,1.f};A::Command command;
  for(int n=0;n<9&&command.kind!=A::Command::open;++n)command=actual.update(context,{},.25f);
  assert(command.kind==A::Command::open&&command.cue->entry_id==cue.entry_id);
  actual.update(context,{true,false,false,cue.start},.01f);
  std::vector<float>input(512*2,.1f),output(input.size());float peak=0;
  for(int block=0;block<110;++block){std::fill(output.begin(),output.end(),0);actual.process(input.data(),output.data(),512);for(float sample:output){assert(std::isfinite(sample));peak=std::max(peak,std::abs(sample));}}
  assert(peak>0); // Real packaged PCM, or synthetic decoder PCM through the stream mixer.
 }
 assert(music+voices==actual.cues().size());
 std::printf("PASS actual package: %zu cues load/open/mix, %u local music cue(s); no YouTube request or download.\n",actual.cues().size(),local_music);
 std::printf("PASS actual2s dwell/fastscroll0requests/one-shotEOF/explicitownership/focusfade+restart; quietRMS %.8f loudRMS %.8f originalDynamics exact0.8trim tinyQuietPreserved musicdry.\n",qr,lr);
}
