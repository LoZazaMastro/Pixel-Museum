// Exercise the actual asynchronous resolver against deterministic HTTP/decoder responses.
#include "yt/service.hpp"
#include "yt/http.hpp"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <thread>

namespace {
std::atomic<int> opens{0},player_posts{0};
std::atomic<bool> codec_failure{false},rate_api{false},rate_decoder{false};
void require(bool ok,const char* why){if(!ok){std::fprintf(stderr,"FAIL %s\n",why);std::exit(1);}}
const char* js=R"(var nt=function(a){a=a.split("");a=a.reverse();return a.join("")};function f(u){u.set("n",nt(u.get("n")))};var cfg={signatureTimestamp:12345};)";
class Decoder final:public yt::Player {
 std::string error_;
 public:
 void set_decode_mode(yt::DecodeMode)override{}
 bool open(const std::string& video,const std::string& audio,yt::AudioSink*)override{
  ++opens;
  if(rate_decoder){error_="Server returned HTTP 429";return false;}
  if(video.find("first")!=std::string::npos){error_=codec_failure?"avcodec_open2: decoder unavailable":"avformat_open_input: Server returned HTTP 403 (access denied)";return false;}
  require(video.find("n=dcba")!=std::string::npos,"plain video n transformed before decoder");
  require(audio.find("n=zyxw")!=std::string::npos,"plain audio n transformed before decoder");return true;
 }
 void close()override{} bool running()const override{return true;}
 double duration_s()const override{return 60;}std::string quality_label()const override{return "fixture";}
 void update()override{} yt::VideoFrameView poll_frame()override{return {};}
 double clock_s()const override{return 0;}void seek(double)override{}void set_paused(bool)override{}
 bool paused()const override{return false;}double buffered_s()const override{return 0;}
 bool ended()const override{return false;}const std::string& error()const override{return error_;}
};
}
namespace yt {
std::unique_ptr<Player> make_player(){return std::make_unique<Decoder>();}
namespace log {void line(const char*,...) {}}
namespace http {
Response perform(const Request& r){
 if(r.url.find("/tv")!=std::string::npos && r.url.find(".js")==std::string::npos)
  return {200,R"(<script src="https://www.youtube.com/s/player/12345678/tv-player-ias.vflset/tv-player-ias.js"></script>)",{}};
 if(r.url.find(".js")!=std::string::npos)return {200,js,{}};
 if(r.url.find("/player?")==std::string::npos)return {200,"{}",{}};
 ++player_posts;
 if(rate_api)return {429,"",{}};
 const bool first=r.body.find("VISIONOS")!=std::string::npos;
 const std::string prefix=first?"first":"second";
 return {200,std::string(R"({"playabilityStatus":{"status":"OK"},"videoDetails":{"videoId":"fixture0001","title":"Fixture","lengthSeconds":"60"},"assets":{"js":"https://www.youtube.com/player.js"},"streamingData":{"adaptiveFormats":[{"itag":136,"mimeType":"video/mp4; codecs=\"avc1.64001F\"","width":1280,"height":720,"url":"https://media.example/)")+prefix+R"(?n=abcd"},{"itag":247,"mimeType":"video/webm; codecs=\"vp9\"","width":1280,"height":720,"url":"https://media.example/second?n=abcd"},{"itag":140,"mimeType":"audio/mp4; codecs=\"mp4a.40.2\"","url":"https://media.example/audio?n=wxyz"}]}})",{}};
}
}
}
int main(){
 for(bool codec:{false,true}){
  opens=0;player_posts=0;codec_failure=codec;
  yt::Service service("","",nullptr);yt::Service::Preferences p;p.history=false;service.set_preferences(p);
  service.start();yt::CodecChoice c;c.av1=false;c.max_height=720;c.decode=yt::DecodeMode::software;
  service.request_video("fixture0001",c);
  for(int n=0;n<2000 && service.video().state!=yt::Load::ready && service.video().state!=yt::Load::failed;++n)
   std::this_thread::sleep_for(std::chrono::milliseconds(1));
  auto view=service.video();require(view.state==yt::Load::ready,view.error.c_str());
  require(opens==2,"one failed decoder open then one successful open");
  require(view.source_client==(codec?"VISIONOS":"TVHTML5"),"HTTP refusal advances client; decoder failure tries another codec");
  require(service.take_player()!=nullptr,"ready player reaches bridge");service.stop();
 }
 for(bool api:{false,true}){
  opens=0;player_posts=0;rate_api=api;rate_decoder=!api;
  yt::Service service("","",nullptr);service.start();yt::CodecChoice c;c.av1=false;c.max_height=720;
  service.request_video("fixture0001",c);
  for(int n=0;n<1000&&service.video().state!=yt::Load::failed;++n)std::this_thread::sleep_for(std::chrono::milliseconds(1));
  require(service.video().state==yt::Load::failed,"429 finishes as failure");service.stop();
  require(player_posts==1&&opens==(api?0:1),"429 never advances client or repeats media request");
 }
 std::puts("PASS actual Service: plain audio/video n preparation, denied URL advances client immediately, codec fallback preserves client, ready player handoff");
}
