#include "audio/controller_feedback.hpp"
#include "platform/ps5/controller_audio.hpp"
#include "museum/intro_audio.hpp"
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <limits>
#include <map>
#include <mutex>
#include <thread>
using hui::audio::ControllerFeedback;using hui::audio::Tactile;using hui::audio::TactileEvent;
namespace {struct Port{unsigned channels=0;bool closed=false;unsigned frames=0,outputs=0;};std::mutex gate;std::map<int,Port>ports;int next_port=1;bool fail_open=false,fail_speaker=false,fail_haptics=false;std::atomic<bool>fail_output{false};unsigned closes=0;}
namespace hui::sys {void log(const char*,...){}void sleep_us(unsigned n){std::this_thread::sleep_for(std::chrono::microseconds(n));}}
extern "C" {
int sceAudioOutInit(){return 0;}
int sceAudioOutOpen(int user,int type,int index,unsigned frames,unsigned rate,unsigned format){assert(user==42&&index==0&&frames==256&&rate==48000);assert((type==4&&format==0)||(type==10&&format==1));std::lock_guard lock(gate);if(fail_open||(type==4&&fail_speaker)||(type==10&&fail_haptics))return -1;const int id=next_port++;ports[id]={format==0?1u:2u,false,frames,0};return id;}
int sceAudioOutOutput(int id,const void*pcm){std::this_thread::sleep_for(std::chrono::milliseconds(1));std::lock_guard lock(gate);auto&port=ports.at(id);assert(!port.closed);if(pcm){const auto*s=static_cast<const short*>(pcm);for(unsigned n=0;n<port.frames*port.channels;++n)assert(s[n]>=-32767);++port.outputs;}return fail_output.load()?-1:0;}
int sceAudioOutClose(int id){std::lock_guard lock(gate);auto&port=ports.at(id);assert(!port.closed);port.closed=true;++closes;return 0;}
}
void finite(const float*p,unsigned n,float limit){for(unsigned j=0;j<n;++j)assert(std::isfinite(p[j])&&std::abs(p[j])<=limit);}
int main(){
 using hui::audio::SpeakerCue;
 for(unsigned cue=0;cue<=unsigned(SpeakerCue::ui_back);++cue){
  ControllerFeedback speaker;speaker.enabled(true);assert(speaker.post_speaker({SpeakerCue(cue),1.f,.12f}));
  std::array<float,48000>out{};speaker.render_speaker(out.data(),unsigned(out.size()));finite(out.data(),unsigned(out.size()),.3f);
  assert(std::any_of(out.begin(),out.end(),[](float v){return std::abs(v)>.001f;}));assert(out.back()==0.f);
 }
 {ControllerFeedback whole,chunked;whole.enabled(true);chunked.enabled(true);
  assert(whole.post_speaker({SpeakerCue::ring,1.4f,.22f}));assert(chunked.post_speaker({SpeakerCue::ring,1.4f,.22f}));
  std::array<float,8192>left{},right{};whole.render_speaker(left.data(),8192);
  for(unsigned n=0;n<32;++n)chunked.render_speaker(right.data()+n*256,256);assert(left==right);
  ControllerFeedback pitched;pitched.enabled(true);pitched.post_speaker({SpeakerCue::ring,.7f,.22f});pitched.render_speaker(right.data(),8192);assert(left!=right);
 }
 {ControllerFeedback speaker;speaker.enabled(true);for(unsigned n=0;n<64;++n)assert(speaker.post_speaker({SpeakerCue::coin}));assert(!speaker.post_speaker({SpeakerCue::coin}));
  speaker.enabled(false);speaker.enabled(true);std::array<float,256>out{};speaker.render_speaker(out.data(),256);assert(std::all_of(out.begin(),out.end(),[](float v){return v==0;}));
 }
 {constexpr int notes[]={50,57,60,62,64,65,69,72,74,76,77,81,86};
  for(int ordinal=0;ordinal<13;++ordinal){hui::audio::Mixer tv;ControllerFeedback pad;pad.enabled(true);
   const auto route=museum::route_startup_note(tv,pad,notes[ordinal],ordinal,true);
   assert(route==museum::StartupRoute::television_and_controller);
   std::array<float,256>speaker{};pad.render_speaker(speaker.data(),256);
   assert(std::any_of(speaker.begin(),speaker.end(),[](float v){return v!=0;}));
   std::array<std::int16_t,512>television{};tv.render(television.data(),256);
   assert(std::any_of(television.begin(),television.end(),[](auto v){return v!=0;}));
   hui::audio::Mixer reference;museum::play_startup_note(reference,notes[ordinal]);
   std::array<std::int16_t,512>expected{};reference.render(expected.data(),256);
   assert(television==expected); // Every pixel keeps its unchanged TV voice alongside the pad voice.
  }
  hui::audio::Mixer tv;ControllerFeedback pad;pad.enabled(true);
  assert(museum::route_startup_note(tv,pad,60,-1,true)==museum::StartupRoute::television);
  assert(museum::route_startup_note(tv,pad,60,1,false)==museum::StartupRoute::television);
  pad.enabled(false);assert(museum::route_startup_note(tv,pad,60,1,true)==museum::StartupRoute::television);
  assert(museum::route_startup_note(tv,pad,-1,-1,true)==museum::StartupRoute::silent);
  // Routing a controller note never stops, resets, ducks or drains the TV stream.
  hui::audio::Mixer ambient;hui::audio::StreamRing stream(1024);std::array<float,512>bed;bed.fill(.1f);stream.write(bed.data(),256);
  ambient.attach_stream(0,&stream);ambient.set_stream_gain(0,1.f,0.f);pad.enabled(true);
  assert(museum::route_startup_note(ambient,pad,60,1,true)==museum::StartupRoute::television_and_controller);
  std::array<std::int16_t,512>television{};ambient.render(television.data(),256);
  assert(std::all_of(television.begin(),television.end(),[](auto v){return v>0;}));
 }
 ControllerFeedback a,b;a.enabled(true);b.enabled(true);std::array<float,4096>one{},parts{};
 assert(a.post({Tactile::confirm,.4f,.03f,.25f}));assert(b.post({Tactile::confirm,.4f,.03f,.25f}));a.render_haptics(one.data(),2048);for(unsigned n=0;n<8;++n)b.render_haptics(parts.data()+n*512,256);assert(one==parts);finite(one.data(),4096,.7f);assert(std::any_of(one.begin(),one.end(),[](float v){return std::abs(v)>.01f;}));assert(one.back()==0);
 for(unsigned mode=0;mode<=unsigned(Tactile::passage);++mode){ControllerFeedback c;c.enabled(true);assert(c.post({Tactile(mode),.65f,.03f,-.7f}));c.render_haptics(one.data(),2048);finite(one.data(),4096,.7f);}
 {
  const auto render=[](TactileEvent event){ControllerFeedback drive;drive.enabled(true);assert(drive.post(event));std::vector<float>samples(48000);drive.render_haptics(samples.data(),24000);return samples;};
  const auto impact=render({Tactile::impact,.14f,.055f,0}),shot=render({Tactile::touch,.025f,.018f,0}),passage=render({Tactile::passage,.34f,.16f,0}),air=render({Tactile::airflow,.09f,.12f,.4f});
  const auto peak=[](const auto&samples){float p=0;for(float v:samples)p=std::max(p,std::abs(v));return p;};
  assert(peak(impact)>.09f&&peak(shot)<peak(impact)*.4f&&peak(passage)>.35f&&peak(air)>.12f);
  assert(std::any_of(passage.begin()+4800,passage.begin()+9600,[](float v){return std::abs(v)>.05f;}));
  assert(impact!=passage&&air!=passage);finite(passage.data(),unsigned(passage.size()),.7f);
  const auto rms=[](const auto&samples,unsigned first,unsigned last){double energy=0;for(unsigned n=first;n<last;++n)energy+=samples[n]*samples[n];return std::sqrt(energy/(last-first));};
  ControllerFeedback mixed;mixed.enabled(true);assert(mixed.post({Tactile::airflow,.09f,.12f,.4f}));
  std::array<float,2048>pre{};mixed.render_haptics(pre.data(),1024);assert(mixed.post({Tactile::passage,.34f,.16f,0}));
  std::array<float,15360>combined{};mixed.render_haptics(combined.data(),7680);finite(combined.data(),unsigned(combined.size()),.7f);
  assert(rms(combined,2048,8192)>rms(air,2048,8192)*2.0); // A ring remains distinct over the airflow bed.
  const auto miss=render({Tactile::error,.28f,.12f,0});assert(miss!=passage&&rms(passage,4096,8192)>rms(miss,4096,8192));
  ControllerFeedback busy;busy.enabled(true);assert(busy.post({Tactile::passage,.34f,.16f,0}));for(unsigned n=0;n<16;++n)assert(busy.post({Tactile::airflow,.09f,.12f,0}));std::array<float,15360>bed{};busy.render_haptics(bed.data(),7680);assert(rms(bed,2048,8192)>rms(air,2048,8192)*2); // Background bursts cannot steal the success voice.
  std::printf("PCM peak impact %.4f / light shot %.4f / passage %.4f / airflow %.4f; mixed passage RMS %.4f vs airflow %.4f\n",peak(impact),peak(shot),peak(passage),peak(air),rms(combined,2048,8192),rms(air,2048,8192));
  puts("PASS: authored impact has useful PCM drive, shot stays lighter; sustained passage and airflow differ, bounded mixed output. Physical intensity remains unverified.");
 }
 ControllerFeedback c;c.enabled(true);for(int n=0;n<64;++n)assert(c.post({}));assert(!c.post({})&&c.dropped()==1);c.enabled(false);c.enabled(true);c.render_haptics(one.data(),2048);assert(std::all_of(one.begin(),one.end(),[](float x){return x==0;}));assert(!c.post({Tactile::error,std::numeric_limits<float>::quiet_NaN(),.04f,0}));assert(c.post({Tactile::back,.2f,.03f,0}));c.enabled(false);c.enabled(true);assert(c.post({Tactile::confirm,.2f,.03f,0}));c.render_haptics(one.data(),2048);assert(std::any_of(one.begin(),one.end(),[](float x){return std::abs(x)>.001f;}));
 std::array<float,256>music;music.fill(.5f);std::array<float,256>mono{};c.render_speaker(mono.data(),256);c.submit_speaker(music.data(),256);c.render_speaker(mono.data(),256);for(float v:mono)assert(v==.22f);
 c.submit_speaker(music.data(),256);c.enabled(false);c.enabled(true);c.render_speaker(mono.data(),256);for(float v:mono)assert(v==0);
 for(int n=0;n<10;++n)c.submit_speaker(music.data(),256);c.render_speaker(mono.data(),256);for(float v:mono)assert(v==0);music.fill(.1f);c.submit_speaker(music.data(),256);c.render_speaker(mono.data(),256);for(float v:mono)assert(v==.1f);
 std::atomic<bool>done=false;std::thread consumer([&]{std::array<float,256>out{};while(!done.load()){c.render_speaker(out.data(),256);finite(out.data(),256,.22f);}});for(int n=0;n<10000;++n){music.fill(n%2?.12f:-.12f);c.submit_speaker(music.data(),256);}done=true;consumer.join();
 {ControllerFeedback mixed;mixed.enabled(true);std::atomic<bool>finished=false;
  std::thread speaker([&]{std::array<float,256>out{};while(!finished.load()){mixed.render_speaker(out.data(),256);finite(out.data(),256,.3f);}});
  std::thread ddr([&]{std::array<float,256>beat;beat.fill(.18f);for(unsigned n=0;n<10000;++n)mixed.submit_speaker(beat.data(),256);});
  for(unsigned n=0;n<10000;++n)mixed.post_speaker({SpeakerCue::coin,1.f,.22f});ddr.join();finished=true;speaker.join();
 }
 {hui::ps5::ControllerAudio output;assert(output.start(42,c));assert(output.speaker_ready()&&output.haptics_ready());assert(output.start(42,c));std::this_thread::sleep_for(std::chrono::milliseconds(15));output.stop();assert(!output.speaker_ready()&&!output.haptics_ready());output.stop();assert(output.start(42,c));std::this_thread::sleep_for(std::chrono::milliseconds(10));fail_output=true;std::this_thread::sleep_for(std::chrono::milliseconds(35));assert(!output.speaker_ready()&&!output.haptics_ready());output.stop();fail_output=false;}
 fail_open=true;{hui::ps5::ControllerAudio output;assert(!output.start(42,c));output.stop();}fail_open=false;fail_haptics=true;{hui::ps5::ControllerAudio output;assert(output.start(42,c));assert(output.speaker_ready()&&!output.haptics_ready());output.stop();}fail_haptics=false;
 for(auto&[id,port]:ports){(void)id;assert(port.closed);}assert(closes==ports.size());
 std::puts("PASS13 semantic speaker cues +13 startup notes on both TV/pad concurrently with exact unchanged TV PCM, workshop/failure TV fallback, ambient TV preservation;14 tactile patterns, block invariance, queuefull, disable epoch, exact DDR PCM, concurrent ring overrun, mono/stereo256frames, thread lifecycle/failures. No physical output claim.");
}
