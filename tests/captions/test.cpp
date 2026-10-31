// Pixel Museum - Caption selection, malformed input and cancellation checks.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "yt/captions.hpp"
#include "yt/caption_metadata.hpp"
#include "yt/innertube.hpp"
#include "yt/http.hpp"
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <mutex>
#include <string>
#include <thread>
#include <utility>
namespace {int checks=0;std::atomic<int> running{0},peak{0},slow_started{0},limited_requests{0},requests{0};
std::mutex request_mutex;std::string last_url,last_ua,last_referer;
void require(bool pass,const char* message){++checks;if(!pass){std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}}
const std::string italian=R"({"events":[{"tStartMs":1000,"dDurationMs":2000,"segs":[{"utf8":"Prima frase"}]},{"tStartMs":4000,"dDurationMs":1000,"segs":[{"utf8":"Dopo il salto"}]}]})";
bool wait(yt::captions::Loader &loader){for(int i=0;i<400;++i){if(loader.status()!="loading")return true;std::this_thread::sleep_for(std::chrono::milliseconds(2));}return false;}
}
namespace yt::log {void line(const char*,...) {}}
namespace yt::http {
Response perform(const Request& request){
 requests.fetch_add(1);
 {std::lock_guard<std::mutex> lock(request_mutex);last_url=request.url;last_ua.clear();last_referer.clear();for(const auto&header:request.headers){if(header.name=="User-Agent")last_ua=header.value;if(header.name=="Referer")last_referer=header.value;}}
 const int count=running.fetch_add(1)+1;int previous=peak.load();while(count>previous&&!peak.compare_exchange_weak(previous,count)){}
 struct Done{~Done(){running.fetch_sub(1);}}done;
 // Simulated HTTP200 for the exact ASR track shape saved from the public PS1
 // player response. These strings are test responses, never live translations.
 if(request.url.find("v=U7w5i_YCFmQ")!=std::string::npos){
  std::string text="Automatic English";
  for(const auto&pair:{std::pair{"it","Buongiorno"},std::pair{"es","Buenos días"},std::pair{"fr","Bonjour"},std::pair{"de","Guten Tag"}})if(request.url.find(std::string("tlang=")+pair.first)!=std::string::npos)text=pair.second;
  const std::string body="{\"events\":[{\"tStartMs\":1000,\"dDurationMs\":2000,\"segs\":[{\"utf8\":\""+text+"\"}]}]}";
  if(request.on_body)request.on_body(body);return {200,request.on_body?std::string{}:body,{}};
 }
 if(request.url.find("slow=1")!=std::string::npos){slow_started.store(1);for(int i=0;i<100;++i){std::this_thread::sleep_for(std::chrono::milliseconds(2));if(!request.on_body(" "))return {0,{},"cancelled"};}}
 if(request.url.find("limited=1")!=std::string::npos){limited_requests.fetch_add(1);return {429,{}, {}};}
 if(request.url.find("foreign=1")!=std::string::npos){const auto at=request.url.find("tlang=");const std::string target=at==std::string::npos?"missing":request.url.substr(at+6,2);const std::string body="WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n"+target+" actual target\n\n";if(request.on_body)request.on_body(body);return {200,{}, {}};}
 if(request.url.find("denied=1")!=std::string::npos)return {403,{}, {}};
 if(request.url.find("fallback=1")!=std::string::npos){
  const std::string fallback=request.url.find("fmt=vtt")!=std::string::npos?"WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nFallback &amp; words\n\n":"";
  if(request.on_body)request.on_body(fallback);return {200,request.on_body?std::string{}:fallback,{}};
 }
 if(request.url.find("empty=1")!=std::string::npos)return {200,{}, {}};
 if(request.url.find("v=english")!=std::string::npos){const std::string body="WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nEnglish fallback\n\n";if(request.on_body)request.on_body(body);return {200,{}, {}};}
 const std::string body=request.url.find("large=1")!=std::string::npos?std::string((2u<<20)+1,'x'):italian;
 if(request.on_body&&!request.on_body(body))return {0,{},"cancelled"};
 return {200,request.on_body?std::string{}:body,{}};
}}
int main(){using namespace yt;using namespace yt::captions;
 VideoInfo early;early.captions={{"https://www.youtube.com/api/timedtext?v=late","en","English",false,false}};early.caption_translation_languages={"it"};
 require(select_track(early,"it").url.empty(),"early source cannot translate before capability arrives");
 auto enriched=early;auto late=early.captions.front();late.translatable=true;late.automatic=true;merge_track(enriched.captions,late);
 require(enriched.captions.size()==1&&!same_metadata(early,enriched),"same URL capability enrichment detected at constant count");
 require(select_track(enriched,"it").url.find("tlang=it")!=std::string::npos,"real selector requests UI translation after deferred enrichment");
 merge_track(enriched.captions,early.captions.front());require(enriched.captions.front().translatable,"sparse later response preserves offered translation capability");
 auto replacement=enriched;replacement.captions.front().url+="&sig=new";require(!same_metadata(enriched,replacement),"same count URL replacement detected");
 auto unrelated=enriched;unrelated.video_id="unrelated";require(same_metadata(enriched,unrelated),"unrelated metadata does not invalidate captions");
 auto relabelled=enriched;auto label=late;label.name="English automatic captions";merge_track(relabelled.captions,label);require(relabelled.captions.front().name==label.name&&same_metadata(enriched,relabelled),"label enrichment retained without invalidating caption playback");
 auto full=enriched;while(full.captions.size()<128){auto extra=late;extra.url+=std::to_string(full.captions.size());merge_track(full.captions,extra);}merge_track(full.captions,replacement.captions.front());require(full.captions.size()==128,"caption source limit retained");
 full.captions.front().translatable=false;merge_track(full.captions,late);require(full.captions.front().translatable,"existing source can still enrich at source limit");
 require(normalize_language("it_IT")=="it-it","regional locale normalization");
 require(normalize_language("it&tlang=de").empty(),"reject language query injection");
 VideoInfo info;info.captions={{"https://www.youtube.com/api/timedtext?v=x&sig=keep&fmt=vtt&xosf=1","en","English",false,true}};
 info.caption_translation_languages={"it","fr","de"};
 auto selected=select_track(info,"it");
 require(selected.translated&&selected.language=="it","translation only for advertised target");
 require(selected.url.find("tlang=it")!=std::string::npos&&selected.url.find("fmt=json3")!=std::string::npos,"translation json3 parameters");
 require(selected.url.find("sig=keep")!=std::string::npos&&selected.url.find("fmt=vtt")==std::string::npos&&selected.url.find("xosf=1")!=std::string::npos,"preserve offered fields including xosf; replace only format");
 VideoInfo signed_asr=info;signed_asr.captions[0].url="https://www.youtube.com/api/timedtext?v=U7w5i_YCFmQ&kind=asr&lang=en&exp=xpe&xosf=1&sparams=v%2Ckind%2Clang%2Cexp%2Cxosf&sig=keep%2Bencoded%3D";signed_asr.captions[0].automatic=true;
 const auto signed_choice=select_track(signed_asr,"it");require(signed_choice.url.find("xosf=1")!=std::string::npos&&signed_choice.url.find("sparams=v%2Ckind%2Clang%2Cexp%2Cxosf")!=std::string::npos&&signed_choice.url.find("sig=keep%2Bencoded%3D")!=std::string::npos&&signed_choice.url.find("exp=xpe")!=std::string::npos,"signed xosf/ASR/attestation fields remain exact, without invented token");
 require(!select_track(info,"en").url.empty()&&!select_track(info,"en-GB").url.empty(),"English authored captions enabled");
 require(select_track(info,"es").url.empty(),"never invent translation availability");
 info.captions[0].translatable=false;require(select_track(info,"it").url.empty(),"respect track translation permission");info.captions[0].translatable=true;
 info.captions.push_back({"https://www.youtube.com/api/timedtext?v=it&tlang=de","it","Italian",false,false});
 selected=select_track(info,"it");require(!selected.translated&&selected.language=="it"&&selected.url.find("tlang")==std::string::npos,"prefer direct track and remove stale translation");
 info.captions.push_back({"https://www.youtube.com/api/timedtext?v=asr","it","Italian automatic",true,true});
 require(select_track(info,"it").url.find("v=it")!=std::string::npos,"prefer authored exact-language track");
 info.captions[1].url="http://127.0.0.1/private";info.captions[2].url="https://www.youtube.com.evil.test/caption";
 require(select_track(info,"it").translated,"reject non-YouTube caption destinations");
 std::vector<Cue> cues;require(parse_json3(italian,&cues)&&cues.size()==2,"parse timed events");
 require(!parse_json3("{}",&cues)&&cues.empty(),"reject wrong shape and clear old cues");
 require(!parse_json3(std::string((2u<<20)+1,'x'),&cues),"bound encoded body");
 require(parse_json3(R"({"events":[{"tStartMs":-1,"dDurationMs":1000,"segs":[{"utf8":"bad"}]},{"tStartMs":1,"dDurationMs":-1,"segs":[{"utf8":"bad"}]},{"tStartMs":1e309,"dDurationMs":1000,"segs":[{"utf8":"bad"}]}]})",&cues)==false||cues.empty(),"reject non-finite and negative timing");
 require(parse_json3(R"({"events":[{"tStartMs":0,"dDurationMs":601000,"segs":[{"utf8":"bad"}]},{"tStartMs":0,"dDurationMs":1000,"segs":[{"utf8":"\n"}]}]})",&cues)&&cues.empty(),"ignore unsupported duration and empty scrolling event");
 std::string huge=R"({"events":[{"tStartMs":0,"dDurationMs":1000,"segs":[{"utf8":")"+std::string(2049,'a')+R"("}]}]})";
 require(!parse_json3(huge,&cues),"bound single cue text");
 const std::string overlap=R"({"events":[{"tStartMs":3000,"dDurationMs":2000,"wWinId":1,"segs":[{"utf8":"Final"}]},{"tStartMs":1000,"dDurationMs":3000,"wWinId":1,"segs":[{"utf8":"Hello"}]},{"tStartMs":2000,"dDurationMs":2000,"wWinId":1,"aAppend":1,"segs":[{"utf8":" world"}]}]})";
 require(parse_json3(overlap,&cues)&&cues.size()==3,"sort caption timestamps");
 require(cues[0].end_s==2&&cues[1].text=="Hello world"&&cues[1].end_s==3,"replace window and append ASR text without duplicate lines");
 VideoInfo parsed;
 (void)parse_video_info(R"({"playabilityStatus":{"status":"OK"},"captions":{"playerCaptionsTracklistRenderer":{"captionTracks":[{"baseUrl":"//www.youtube.com/api/timedtext?v=x","languageCode":"en","name":{"simpleText":"English"},"isTranslatable":true}],"translationLanguages":[{"languageCode":"it","languageName":{"simpleText":"Italian"}}]}}})",&parsed);
 require(parsed.captions.size()==1&&parsed.captions[0].translatable&&parsed.caption_translation_languages==std::vector<std::string>{"it"},"real InnerTube parser retains caption capabilities");
 require(parsed.captions[0].url=="https://www.youtube.com/api/timedtext?v=x","protocol-relative caption URL");
 require(parse_timed_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.000 align:center\n<b>Words</b> &amp; &#x1f3ae;\n\n",&cues)&&cues.size()==1&&cues[0].text=="Words & \xf0\x9f\x8e\xae"&&cues[0].start_s==1&&cues[0].end_s==3,"WebVTT timings, tag removal and entities");
 require(parse_timed_text("<transcript><text start=\"1.25\" dur=\"2.5\">One &amp; two<br/>Three</text></transcript>",&cues)&&cues.size()==1&&cues[0].text=="One & two\nThree"&&cues[0].end_s==3.75,"srv1 seconds and line breaks");
 require(parse_timed_text("<?xml version=\"1.0\"?><timedtext><body><p t=\"1000\" d=\"2000\"><s>Automatic </s><s>words</s></p></body></timedtext>",&cues)&&cues.size()==1&&cues[0].text=="Automatic words"&&cues[0].start_s==1,"srv3 millisecond segments");
 require(!parse_timed_text("<html><body>A consent page</body></html>",&cues),"HTML is never dialogue");
 require(parse_timed_text("WEBVTT\n\n00:00:01.000 --> 00:00:01.000\nzero\n\n00:00:01.000 --> 00:30:01.000\ntoo long\n\n",&cues)&&cues.empty(),"VTT rejects zero and oversized durations");
 require(parse_timed_text("<transcript><text start=\"nan\" dur=\"1\">bad</text><text start=\"-1\" dur=\"1\">bad</text></transcript>",&cues)&&cues.empty(),"XML rejects nonfinite and negative timing");
 VideoInfo crowded;crowded.caption_translation_languages={"it"};
 for(int n=0;n<10;++n)crowded.captions.push_back({"https://www.youtube.com/api/timedtext?v=empty-it-"+std::to_string(n),"it","Italian automatic",true,true});
 crowded.captions.push_back({"https://www.youtube.com/api/timedtext?v=english-source","en","English",true,true});
 const auto available=select_track(crowded,"it");require(available.alternatives.size()==1&&available.alternatives[0].find("tlang=it")!=std::string::npos,"many empty direct-client offers cannot hide the English translation request");
 Loader loader;loader.load("https://www.youtube.com/api/timedtext?v=test");require(wait(loader)&&loader.status()=="ok","async caption fetch");
 const int completed_requests=requests.load();loader.load("https://www.youtube.com/api/timedtext?v=test");
 require(loader.status()=="ok"&&requests.load()==completed_requests&&loader.text_at(1.5)=="Prima frase","identical completed load keeps cues and performs no new request");
 require(loader.text_at(.9).empty()&&loader.text_at(1)=="Prima frase"&&loader.text_at(2.99)=="Prima frase"&&loader.text_at(3).empty(),"inclusive start exclusive end on playback clock");
 require(loader.text_at(4.5)=="Dopo il salto"&&loader.text_at(1.5)=="Prima frase","forward and backward seek");
 require(loader.text_at(NAN).empty()&&loader.text_at(-1).empty(),"invalid clock is silent");
 loader.load("https://www.youtube.com/api/timedtext?slow=1");
 for(int i=0;i<200&&!slow_started.load();++i)std::this_thread::sleep_for(std::chrono::milliseconds(1));
 require(slow_started.load()!=0,"cancellation test entered transfer");const int inflight_requests=requests.load();loader.load("https://www.youtube.com/api/timedtext?slow=1");
 std::this_thread::sleep_for(std::chrono::milliseconds(10));require(loader.status()=="loading"&&requests.load()==inflight_requests,"identical in-flight load does not cancel or enqueue duplicate HTTP");loader.clear();
 require(loader.text_at(1.5).empty()&&loader.status().empty(),"clear invalidates pending cues immediately");
 loader.load("https://www.youtube.com/api/timedtext?v=new&tlang=it");require(wait(loader)&&loader.text_at(1.5)=="Prima frase","new generation survives old response");
 require(peak.load()==1,"only one HTTP caption worker");
 loader.load("https://www.youtube.com/api/timedtext?denied=1");require(wait(loader)&&loader.status()=="error: HTTP 403"&&loader.text_at(1.5).empty(),"HTTP failure has no stale dialogue");
 loader.load("https://www.youtube.com/api/timedtext?fallback=1&tlang=it");require(wait(loader)&&loader.status()=="ok"&&loader.text_at(1.5)=="Fallback & words","empty JSON3 falls back to offered VTT format");
 loader.load("https://www.youtube.com/api/timedtext?empty=1",{"https://www.youtube.com/api/timedtext?v=another-client"});require(wait(loader)&&loader.text_at(1.5)=="Prima frase","empty client captions fall back to another offered client track");
 loader.load("https://www.youtube.com/api/timedtext?large=1");require(wait(loader)&&loader.status()=="error: caption response too large","streaming response cap");
 loader.load("https://evil.test/text");require(loader.status()=="error: invalid caption URL","reject untrusted loader destination");
 VideoInfo translation;translation.captions={{"https://www.youtube.com/api/timedtext?v=spanish","es","Spanish",false,true},{"https://www.youtube.com/api/timedtext?v=english","en","English ASR",true,true}};translation.caption_translation_languages={"it","es","fr","de"};
 for(const auto*locale:{"it","fr","de"}){const auto choice=select_track(translation,locale);require(choice.url.find("v=english")!=std::string::npos&&choice.url.find(std::string("tlang=")+locale)!=std::string::npos,"automatic English source preferred to another language");require(choice.english_fallbacks.size()==1&&choice.english_fallbacks[0].find("tlang=")==std::string::npos,"fallback retains source English, never target label");}
 for(const auto*locale:{"it","es","fr","de"}){loader.load(std::string("https://www.youtube.com/api/timedtext?foreign=1&tlang=")+locale);require(wait(loader)&&loader.status()=="ok"&&loader.text_at(1.5)==std::string(locale)+" actual target","worker preserves selected translation target across format requests");}
 loader.load("https://www.youtube.com/api/timedtext?limited=1&tlang=it",{"https://www.youtube.com/api/timedtext?limited=1&tlang=fr"},{"https://www.youtube.com/api/timedtext?v=english&tlang=de"});
 require(wait(loader)&&loader.status()=="fallback: en (translation rate limited)"&&loader.text_at(1.5)=="English fallback","translation refusal is explicit while original-English fallback remains readable");
 require(limited_requests.load()==1,"429 stops translation retry clients and formats");
 const int after_limited=requests.load();loader.clear();require(loader.text_at(1.5).empty(),"clear hides old source dialogue while retaining session cooldown");
 loader.load("https://www.youtube.com/api/timedtext?limited=1&new_signature=2&tlang=fr",{},{"https://www.youtube.com/api/timedtext?v=english"});
 require(wait(loader)&&loader.status()=="fallback: en (translation rate limited)"&&loader.text_at(1.5)=="English fallback"&&requests.load()==after_limited,"clear/reopen changed signedURL and language neither retries429 nor refetches cachedEnglish");
 loader.load("https://video.google.com/api/timedtext?different_client=1&tlang=de");
 require(wait(loader)&&loader.status()=="error: translation rate limited (HTTP 429)"&&requests.load()==after_limited&&loader.text_at(1.5).empty(),"session translation cooldown covers other clients and videos without stale cues");
 loader.load("",{},{"https://www.youtube.com/api/timedtext?v=english"});require(wait(loader)&&loader.status()=="fallback: en","unadvertised target still has explicit English fallback");
 require(requests.load()==after_limited,"offered original fallback reuses the one-track cache");
 loader.load("https://www.youtube.com/api/timedtext?new_signature=3&tlang=it",{},{"https://www.youtube.com/api/timedtext?empty=1"});
 require(wait(loader)&&loader.status()=="error: translation rate limited (HTTP 429)"&&loader.text_at(1.5).empty(),"empty English fallback cannot misreport refused translation as missing tracks");
 Loader source_limited;source_limited.load("https://www.youtube.com/api/timedtext?limited=1");require(wait(source_limited)&&source_limited.status()=="error: HTTP 429","original source429 is retained");
 const int after_source_limit=requests.load();source_limited.clear();source_limited.load("https://www.youtube.com/api/timedtext?v=another-video");
 require(wait(source_limited)&&source_limited.status()=="error: HTTP 429"&&requests.load()==after_source_limit,"source endpoint429 cooldown survives clear and different video URL");
 // Optional focused replay of actual saved player metadata, entirely offline.
 if(const char*fixture=std::getenv("MUSEUM_CAPTION_ASR_FIXTURE")){
  std::ifstream file(fixture);const std::string json((std::istreambuf_iterator<char>(file)),{});VideoInfo actual;
  require(!json.empty(),"actual saved ASR metadata fixture is readable");(void)parse_video_info(json,&actual);
  require(actual.captions.size()==1&&actual.captions[0].automatic&&actual.captions[0].translatable&&actual.captions[0].language=="en","actual PS1 metadata offers English ASR and translation");
  require(actual.captions[0].url.find("kind=asr")!=std::string::npos&&actual.captions[0].url.find("exp=xpe")!=std::string::npos,"actual ASR attestation requirement remains present and unaltered");
  Loader translated;
  for(const auto&pair:{std::pair{"it","Buongiorno"},std::pair{"es","Buenos días"},std::pair{"fr","Bonjour"},std::pair{"de","Guten Tag"}}){
   const auto choice=select_track(actual,pair.first);require(choice.translated&&choice.language==pair.first,"actual ASR selection uses the offered target language");
   const auto query=actual.captions[0].url.substr(actual.captions[0].url.find('?')+1);size_t start=0;
   while(start<query.size()){const auto end=query.find('&',start);const auto field=query.substr(start,end==std::string::npos?end:end-start);const auto key=field.substr(0,field.find('='));if(key!="fmt"&&key!="tlang")require(choice.url.find(field)!=std::string::npos,"actual signed ASR query field retained byte-for-byte");if(end==std::string::npos)break;start=end+1;}
   translated.load(choice.url,choice.alternatives,choice.english_fallbacks);require(wait(translated)&&translated.status()=="ok"&&translated.text_at(1.5)==pair.second,"SIMULATED200 actual ASR request produces the selected-language cues");
   std::lock_guard<std::mutex> lock(request_mutex);require(last_ua.find("Chrome/")!=std::string::npos&&last_ua.find("Cobalt")==std::string::npos&&last_referer=="https://www.youtube.com/watch?v=U7w5i_YCFmQ","ordinary WEB no-c request uses desktop context and video Referer");require(last_url.find(std::string("tlang=")+pair.first)!=std::string::npos&&last_url.find("kind=asr")!=std::string::npos,"worker retains ASR identity and requested translation target");
   std::printf("SIMULATED_HTTP200_ACTUAL_ASR %s: target cues/desktop context/signed fields PASS; NOT live translation verification\n",pair.first);
  }
  for(const auto&pair:{std::pair{"WEB","Chrome/"},std::pair{"VISIONOS","Macintosh"},std::pair{"TVHTML5","Cobalt/"},std::pair{"TVHTML5&cver=5.20260707","SMART-TV"},std::pair{"&cver=5.20260707","SMART-TV"}}){
   translated.load(std::string("https://www.youtube.com/api/timedtext?v=U7w5i_YCFmQ&kind=asr&lang=en&c=")+pair.first+"&tlang=it");require(wait(translated)&&translated.status()=="ok","simulated ordinary client-context request parses");
   std::lock_guard<std::mutex> lock(request_mutex);require(last_ua.find(pair.second)!=std::string::npos,"known WEB/VISIONOS/TV client keeps its ordinary protocol context");
  }
 }
 std::printf("captions: %d checks passed\n",checks);
}
