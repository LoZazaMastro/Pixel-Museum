#include "yt/decipher.hpp"
#include "yt/innertube.hpp"
#include "yt/http.hpp"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>

namespace {
const char* js_url="https://www.youtube.com/s/player/12345678/tv-player-ias.vflset/tv-player-ias.js";
int gets=0; bool explicit_js=false; bool discover=true;
const char* transform=R"JS(var nt=function(a){a=a.split("");a=a.reverse();a=a.slice(1);return a.join("")};function fix(u){u.set("n",nt(u.get("n")))};var settings={signatureTimestamp:20746};)JS";
void require(bool ok,const char* why){if(!ok){std::fprintf(stderr,"FAIL %s\n",why);std::exit(1);}}
}
namespace yt::log {void line(const char*,...) {}}
namespace yt::http {
Response perform(const Request& r){++gets;
 if(!discover)return {200,"",{}};
 if(r.url=="https://www.youtube.com/tv")return {200,std::string("<script src=\"")+js_url+"\"></script>",{}};
 if(r.url==js_url)return {200,transform,{}};
 return {200,"",{}};
}
Response post_json(const std::string&,const std::vector<Header>&,const std::string&,long){
 return {200,std::string(R"({"playabilityStatus":{"status":"OK"},"videoDetails":{"videoId":"fixture0001","title":"Original","lengthSeconds":"60"},)")+
 (explicit_js?R"("assets":{"js":"https://www.youtube.com/s/player/explicit/base.js"},)":"")+
 R"("streamingData":{"formats":[{"itag":18,"mimeType":"video/mp4; codecs=\"avc1.42001E, mp4a.40.2\"","url":"https://media.example/play?n=abcdef"}]}})",{}};
}
}
int main(int argc,char** argv){
 std::vector<yt::VideoInfo> out;std::string error;
 yt::InnerTube tv;require(tv.player_variants("fixture0001",&out,&error,1,1),"TV response");
 require(out.size()==1&&out[0].player_js_url==js_url,"missing assets uses actual successful TV discovery");
 yt::Descrambler d;require(d.prepare(out[0].player_js_url,&error)&&d.can_transform_n(),"discovered JS exposes real n helper");
 require(d.descramble(out[0].formats[0].url,"","",&error)=="https://media.example/play?n=edcba","plain direct URL n is transformed");
 require(d.descramble("https://media.example/n/abcdef/play?n=abcdef","","",&error)=="https://media.example/n/edcba/play?n=edcba","query and path n both transformed");
 explicit_js=true;require(tv.player_variants("fixture0001",&out,&error,1,1),"explicit TV assets");require(out[0].player_js_url.find("explicit")!=std::string::npos,"explicit response JS never overwritten");
 explicit_js=false;gets=0;yt::InnerTube metadata;require(metadata.player_variants("fixture0001",&out,&error,1,1,false),"metadata response");require(gets==0&&out[0].player_js_url.empty(),"metadata has no eager JS discovery");
 discover=false;yt::InnerTube failed;require(failed.player_variants("fixture0001",&out,&error,1,1),"discovery failure leaves response available");require(out[0].player_js_url.empty(),"failed discovery never invents JS identity");
 require(!d.prepare_js("",&error)&&!d.can_transform_n(),"failed prepare clears stale capability");
 require(d.prepare_js(R"(var s=function(a){a=a.split("");a=a.reverse();return a.join("")};function f(u){u.set("signature",s(u.get("s")))})",&error),"signature-only build valid");require(!d.can_transform_n(),"signature helper is not n capability");
 if(argc>1){std::ifstream f(argv[1]);std::string js((std::istreambuf_iterator<char>(f)),{});require(!js.empty(),"actual JS fixture present");bool ok=d.prepare_js(js,&error);std::printf("OBSERVED_TV_JS prepare=%d n=%d reason=%s\n",ok,d.can_transform_n(),error.c_str());}
 std::puts("PASS TV JS provenance, direct/query/path n, explicit precedence, lazy metadata and stale-capability reset");
}
