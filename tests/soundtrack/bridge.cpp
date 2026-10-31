// Exercise the actual asynchronous Video bridge with a deterministic decoder.
#include "platform/media.hpp"
#include "platform/playback_window.hpp"
#include "yt/service.hpp"
#include "yt/captions.hpp"
#include "platform/ps5/system.hpp"
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <thread>
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL %d %s\n",__LINE__,#x);std::abort();}}while(0)
namespace {
std::atomic<int> resolutions{0},seeks{0};std::atomic<double> first_update{-1};
std::atomic<int> caption_epoch{0},caption_loads{0};
std::atomic<bool> requested_italian{false};
std::atomic<bool> requested_replacement{false};
std::atomic<bool> block_write{false},write_waiting{false},release_write{false},delay_seek{false},seek_waiting{false};
std::atomic<bool> block_end_frame{false},end_frame_waiting{false},release_end_frame{false};
class Decoder final:public yt::Player{
 yt::AudioSink* sink_;double decoded_=0;bool paused_=false;std::string error_;
 public:explicit Decoder(yt::AudioSink*s):sink_(s){sink_->set_paused(false);}
 void set_decode_mode(yt::DecodeMode)override{}
 bool open(const std::string&,const std::string&,yt::AudioSink*)override{return true;}
 void close()override{}bool running()const override{return true;}
 double duration_s()const override{return 100;}
 std::string quality_label()const override{return "fixture";}
 void update()override{if(paused_)return;if(block_write.exchange(false)){write_waiting=true;while(!release_write.load())std::this_thread::sleep_for(std::chrono::milliseconds(1));}if(first_update.load()<0)first_update=decoded_;std::array<float,8192> pcm;pcm.fill(float(decoded_<30?.25:.75));decoded_+=double(sink_->write(pcm.data(),4096))/48000.;}
 yt::VideoFrameView poll_frame()override{
  if(block_end_frame.load()&&decoded_>=20.99999&&decoded_<21.00001&&sink_->buffered()==0&&block_end_frame.exchange(false)){
   end_frame_waiting=true;while(!release_end_frame.load())std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }return {};
 }
 double clock_s()const override{return decoded_-double(sink_->buffered())/48000.;}
 void seek(double t)override{++seeks;if(delay_seek.exchange(false)){seek_waiting=true;std::this_thread::sleep_for(std::chrono::milliseconds(40));seek_waiting=false;}sink_->set_paused(true);sink_->drain();decoded_=t;paused_=false;sink_->set_paused(false);}
 void set_paused(bool p)override{paused_=p;sink_->set_paused(p);}
 bool paused()const override{return paused_;}double buffered_s()const override{return double(sink_->buffered())/48000.;}
 bool ended()const override{return decoded_>=100&&sink_->buffered()==0;}
 const std::string&error()const override{return error_;}
};
}
namespace yt {
struct Service::Impl{AudioSink*s;std::unique_ptr<Player>pending;std::string id;};
Service::Service(std::string,std::string,AudioSink*s):impl_(std::make_unique<Impl>()){impl_->s=s;}
Service::~Service()=default;void Service::start(){}void Service::stop(){}
void Service::set_preferences(const Preferences&){}
void Service::request_close_video(){impl_->pending.reset();}
void Service::request_video(std::string id,CodecChoice){++resolutions;impl_->id=std::move(id);impl_->pending=std::make_unique<Decoder>(impl_->s);}
void Service::video_watchdog(float){}
std::unique_ptr<Player>Service::take_player(){return std::move(impl_->pending);}
std::uint64_t Service::video_revision()const{return static_cast<std::uint64_t>(caption_epoch.load());}
VideoView Service::video()const{VideoView v;v.state=Load::ready;v.info.video_id=impl_->id;const int epoch=caption_epoch.load();v.revision=epoch;if(epoch>0){v.info.captions={{epoch>=5?"https://example.test/replaced":"https://example.test/caption","en",epoch>=7?"English automatic captions":"English",false,epoch!=3}};v.info.caption_translation_languages={"it"};if(epoch>=8){auto extra=v.info.captions.front();extra.url+="?client=extra";v.info.captions.push_back(extra);}}return v;}
namespace log {void open(const char*){}void close(){}void line(const char*,...){} }
namespace captions {
std::string normalize_language(std::string_view value){return std::string(value);}
struct Loader::Worker{};Loader::Loader()=default;Loader::~Loader()=default;
void Loader::clear(){}std::string Loader::status(){return "ok";}void Loader::load(const std::string&url,const std::vector<std::string>&,const std::vector<std::string>&){requested_italian=url.find("tlang=it")!=std::string::npos;requested_replacement=url.find("/replaced")!=std::string::npos;++caption_loads;}
// Lifecycle-only stub. The production selector and merge are exercised together
// in tests/captions; here observe the asynchronous Video request/restart path.
Selection select_track(const VideoInfo&info,std::string_view locale){Selection s;if(!info.captions.empty()&&(locale=="en"||info.captions.front().translatable)){s.url=info.captions.front().url;if(locale=="it")s.url+="?tlang=it";}return s;}
}
}
namespace hui::sys {void sleep_us(std::uint32_t n){std::this_thread::sleep_for(std::chrono::microseconds(n));}}
using museum::media::Video;using museum::media::State;
int wait_number=0;template<class F>void wait(F f){++wait_number;for(int n=0;n<1000&&!f();++n)std::this_thread::sleep_for(std::chrono::milliseconds(2));if(!f())std::fprintf(stderr,"Wait %d timed out; resolutions=%d seeks=%d first=%f\n",wait_number,resolutions.load(),seeks.load(),first_update.load());CHECK(f());}
static std::size_t drain_until_end(Video&v,float expected){std::size_t heard=0;for(int tick=0;tick<3000&&!v.ended();++tick){std::array<float,1994>p{};v.mix_audio(p.data(),997);for(std::size_t n=0;n<997;++n)if(p[n*2]!=0){CHECK(std::abs(p[n*2]-expected)<.0001f);CHECK(p[n*2]==p[n*2+1]);++heard;}std::this_thread::sleep_for(std::chrono::milliseconds(1));}CHECK(v.ended());return heard;}
int main(){
 using namespace museum::media;
 PlaybackWindow unknown;CHECK(unknown.seek(15,0)==15&&unknown.time(8,0)==8);PlaybackWindow w{10,12};CHECK(w.duration(100)==2&&w.time(10,100)==0&&w.time(11,100)==1&&w.time(20,100)==2);CHECK(w.seek(-1,100)==10&&w.seek(30,100)==12);CHECK(!PlaybackWindow::valid(10,10)&&!PlaybackWindow::valid(-1,10)&&!PlaybackWindow::valid(0,INFINITY));
 // Museum ambience remains suppressed in every audio-room state.
 for(bool ready:{false,true})for(bool paused:{false,true})for(bool ended:{false,true})CHECK(suspend_ambient(true,true,ready,paused,ended));
 CHECK(!suspend_ambient(false,false,false,false,false));CHECK(!suspend_ambient(false,true,true,true,false));CHECK(suspend_ambient(false,true,true,false,false));
 Video v;CHECK(v.start("build/soundtrack-test-data","."));v.volume(1);v.open("AAAAAAAAAAA",true,20,21);wait([&]{return v.state()==State::ready;});CHECK(first_update.load()==20&&resolutions==1&&seeks==1);
 // Gain has a deliberate ramp. Count all source frames, without assuming its shape.
 std::size_t heard=0;for(int tick=0;tick<3000&&!v.ended();++tick){std::array<float,1994>p{};v.mix_audio(p.data(),997);for(std::size_t n=0;n<997;++n){CHECK(p[n*2]>=0&&p[n*2]<=.25001f);if(p[n*2]!=0)++heard;}std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 CHECK(v.ended()&&heard==48000&&v.time()==21);
 // Reuse same decoder; no resolver or network request, exact next passage only.
 v.play_range(40,41);wait([&]{return !v.ended()&&v.time()>=40;});CHECK(drain_until_end(v,.75f)==48000);CHECK(resolutions==1&&seeks==2&&v.time()==41);
 // Pause holds PCM, resume continues; seeking is clamped to this passage.
 v.play_range(50,52);wait([&]{return !v.ended()&&v.time()>=50;});v.pause(true);wait([&]{return v.paused();});std::array<float,2048>silent{};v.mix_audio(silent.data(),1024);for(float x:silent)CHECK(x==0);CHECK(suspend_ambient(true,true,true,v.paused(),v.ended()));
 v.pause(false);wait([&]{return !v.paused();});v.seek(0);wait([&]{return seeks.load()>=4;});CHECK(v.time()>=50&&v.time()<=52);
 // Exit immediately silences queued PCM. A fresh bounded open cancels old work.
 v.close();silent.fill(0);v.mix_audio(silent.data(),1024);for(float x:silent)CHECK(x==0);CHECK(v.state()==State::idle);CHECK(!suspend_ambient(false,false,false,false,false));
 v.open("BBBBBBBBBBB",true,60,61);v.close();v.open("CCCCCCCCCCC",true,70,71);wait([&]{return v.state()==State::ready;});CHECK(drain_until_end(v,.75f)==48000);CHECK(v.time()==71);
 // Race regression: old decoder writes AFTER main-thread drain. During a
 // deliberately slow next seek, none of that previous passage may be audible.
 v.open("AAAAAAAAAAA",true,50,60);wait([&]{return v.state()==State::ready;});block_write=true;wait([&]{return write_waiting.load();});delay_seek=true;v.play_range(20,21);release_write=true;wait([&]{return seek_waiting.load();});
 for(int n=0;n<10;++n){silent.fill(0);v.mix_audio(silent.data(),1024);for(float x:silent)CHECK(x==0);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 wait([&]{return !seek_waiting.load();});CHECK(drain_until_end(v,.25f)==48000);
 v.open("AAAAAAAAAAA",true);wait([&]{return v.state()==State::ready;});bool audible=false;for(int n=0;n<10;++n){silent.fill(0);v.mix_audio(silent.data(),1024);for(float x:silent)audible|=x>0;std::this_thread::sleep_for(std::chrono::milliseconds(2));}CHECK(audible);v.close();
 v.open("AAAAAAAAAAA",true,110,111);wait([&]{return v.state()==State::failed;});CHECK(v.error().find("passage")!=std::string::npos);
 v.open("AAAAAAAAAAA",true,2,1);CHECK(v.state()==State::failed);
 // Actual asynchronous bridge receives captions after the decoder was taken.
 // An unrelated metadata revision must not reload the same subtitle source.
 const int previous=resolutions.load();v.open("DDDDDDDDDDD",false);wait([&]{return resolutions.load()>previous;});
 std::this_thread::sleep_for(std::chrono::milliseconds(15));caption_epoch=1;wait([&]{return caption_loads.load()==1;});
 caption_epoch=2;std::this_thread::sleep_for(std::chrono::milliseconds(20));CHECK(caption_loads==1);
 v.caption_language("it");wait([&]{return caption_loads.load()==2;});CHECK(requested_italian);
 const int stable_resolutions=resolutions.load(),stable_seeks=seeks.load();
 // Same URL/count/targets, first unavailable then newly translatable.
 caption_epoch=3;wait([&]{return v.caption_status()=="unavailable";});CHECK(caption_loads==2);
 caption_epoch=4;wait([&]{return caption_loads.load()==3;});CHECK(requested_italian);
 // A refreshed signed URL at the same count must also reload captions only.
 caption_epoch=5;wait([&]{return caption_loads.load()==4;});CHECK(requested_italian&&requested_replacement);
 caption_epoch=6;std::this_thread::sleep_for(std::chrono::milliseconds(25));CHECK(caption_loads==4);
 // A localized display label does not change the selected subtitle request.
 caption_epoch=7;std::this_thread::sleep_for(std::chrono::milliseconds(25));CHECK(caption_loads==4);
 caption_epoch=8;std::this_thread::sleep_for(std::chrono::milliseconds(25));CHECK(caption_loads==4);
 CHECK(resolutions==stable_resolutions&&seeks==stable_seeks&&v.state()==State::ready);
 // The previous decoder tick has computed ended=true but has not published it.
 // Selecting the next cue must keep that old result from skipping the new cue.
 v.open("AAAAAAAAAAA",true,20,21);wait([&]{return v.state()==State::ready;});block_end_frame=true;
 for(int n=0;n<3000&&!end_frame_waiting.load();++n){silent.fill(0);v.mix_audio(silent.data(),1024);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 CHECK(end_frame_waiting);delay_seek=true;v.play_range(40,41);release_end_frame=true;wait([&]{return seek_waiting.load();});
 for(int n=0;n<10;++n){CHECK(!v.ended()&&v.time()>=40);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 wait([&]{return !seek_waiting.load();});CHECK(drain_until_end(v,.75f)==48000);v.stop();
 std::puts("Soundtrack bridge PASS: seek-before-PCM, exact48000-frame boundary, reuse, relative seek, pause/resume ambience, exit/cancel and invalid ranges. Network/PS5 output not exercised.");
}

