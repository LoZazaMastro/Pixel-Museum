#include "yt/innertube.hpp"
#include "yt/http.hpp"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <thread>

namespace {
int posts=0,gets=0;bool refuse_first=false;
void require(bool condition,const char* message){if(!condition){std::fprintf(stderr,"FAIL %s\n",message);std::exit(1);}}
std::string response=R"({"playabilityStatus":{"status":"OK"},"videoDetails":{"videoId":"fixture0001","title":"Original fixture","lengthSeconds":"60"},"assets":{"js":"https://www.youtube.com/s/player/fixture/base.js"},"streamingData":{"adaptiveFormats":[{"itag":137,"mimeType":"video/mp4; codecs=\"avc1.640028\"","width":1920,"height":1080,"url":"https://media.example/video?itag=137"},{"itag":140,"mimeType":"audio/mp4; codecs=\"mp4a.40.2\"","url":"https://media.example/audio?itag=140"}]},"captions":{"playerCaptionsTracklistRenderer":{"captionTracks":[{"baseUrl":"https://www.youtube.com/api/timedtext?v=fixture","languageCode":"en","name":{"simpleText":"English"},"isTranslatable":true}],"translationLanguages":[{"languageCode":"it","languageName":{"simpleText":"Italian"}}]}}})";
}
namespace yt::log {void line(const char*,...) {}}
namespace yt::http {
Response perform(const Request&){++gets;std::this_thread::sleep_for(std::chrono::milliseconds(30));return {200,"var signatureTimestamp=12345;",{}};}
Response post_json(const std::string&,const std::vector<Header>&,const std::string& body,long){
 ++posts;std::this_thread::sleep_for(std::chrono::milliseconds(5));
 if(refuse_first&&body.find("VISIONOS")!=std::string::npos)return {403,{}, {}};
 return {200,response,{}};
}
}
int main(){
 using Clock=std::chrono::steady_clock;std::vector<yt::VideoInfo> answers;std::string error;
 yt::InnerTube complete;auto before=Clock::now();require(complete.player_variants("fixture0001",&answers,&error),"legacy complete chain still works");
 const auto old_ms=std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-before).count();
 require(posts==4&&answers.size()==4&&gets>=2,"full compatibility mode requests all maintained clients");
 posts=gets=0;yt::InnerTube incremental;before=Clock::now();
 require(incremental.player_variants("fixture0001",&answers,&error,0,1),"first client independently resolves");
 const auto new_ms=std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-before).count();
 require(posts==1&&gets==0&&answers.size()==1,"first URL usable before any TV/JS discovery or fallback request");
 require(answers.front().client=="VISIONOS"&&answers.front().formats.size()==2,"real parser retains media formats");
 require(!answers.front().captions.empty()&&answers.front().caption_translation_languages==std::vector<std::string>{"it"},"first response captions and automatic translation survive");
 require(old_ms>new_ms+40,"measured mocked-network startup excludes eager fallback overhead");
 posts=gets=0;
 for(std::size_t i=1;i<yt::InnerTube::player_client_count();++i)
   require(incremental.player_variants("fixture0001",&answers,&error,i,1,false),"deferred metadata remains available");
 require(posts==3&&gets==0,"deferred captions do not download TV bundles or player JS");
 require(!answers.front().captions.empty()&&answers.front().caption_translation_languages.size()==1,"WEB caption/translation metadata retained");
 posts=gets=0;refuse_first=true;yt::InnerTube fallback;
 require(!fallback.player_variants("fixture0001",&answers,&error,0,1),"first transport refusal returns for fallback");
 require(posts==1&&gets==0,"no retry or other client inside a failed slice");
 require(fallback.player_variants("fixture0001",&answers,&error,1,1),"next client can still resolve a refused first URL");
 require(posts==2&&answers.size()==1,"fallback advances without repeating the first request");
 std::printf("PASS actual InnerTube incremental/fallback/captions; simulated transport eager=%lldms incremental=%lldms (not physical PS5 timing)\n",static_cast<long long>(old_ms),static_cast<long long>(new_ms));
}
