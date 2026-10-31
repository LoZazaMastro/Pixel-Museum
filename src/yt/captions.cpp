// youtube-tv - Bounded timed text and advertised-language selection.
// Copyright (C) 2026 SponsorBlock for PS5 contributors, Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "yt/captions.hpp"
#include "yt/http.hpp"
#include "yt/log.hpp"
#include "third_party/yyjson/yyjson.h"
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstdlib>
#include <mutex>
#include <pthread.h>
#include <utility>
namespace yt::captions {
namespace {
constexpr std::size_t max_body=2u<<20,max_cues=12000,max_text=1u<<20,max_cue_text=2048;
std::string base_language(std::string_view value) {return std::string(value.substr(0,value.find('-')));}
bool caption_host(std::string_view url) {
    if(url.size()>16384||url.rfind("https://",0)!=0||url.find_first_of("\r\n\t ")!=std::string_view::npos) return false;
    const auto end=url.find_first_of("/?#",8);
    const auto host=url.substr(8,end==std::string_view::npos?url.size()-8:end-8);
    return host=="www.youtube.com"||host=="youtube.com"||host=="video.google.com"||host=="www.youtube-nocookie.com";
}
std::string_view query_field(std::string_view url,std::string_view name){
    const auto question=url.find('?');if(question==std::string_view::npos)return {};
    auto query=url.substr(question+1);
    while(!query.empty()){
        const auto end=query.find('&');const auto field=query.substr(0,end);const auto equals=field.find('=');
        if(equals!=std::string_view::npos&&field.substr(0,equals)==name)return field.substr(equals+1);
        if(end==std::string_view::npos)break;query.remove_prefix(end+1);
    }
    return {};
}
const char* caption_user_agent(std::string_view url){
    // A caption URL can be bound to the client that offered it; mirror the
    // maintained player contexts rather than sending a different browser UA.
    const auto client=query_field(url,"c");
    if(client=="VISIONOS")
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15";
    if((client=="TVHTML5"||client.empty())&&query_field(url,"cver")=="5.20260707")
        return "Mozilla/5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/2.4.0 TV Safari/538.1";
    // WEB timedtext can omit c entirely. Do not send the unrelated TV shell
    // context for those ordinary desktop tracks. This grants no attestation.
    if(client.empty()||client=="WEB"||client=="WEB_EMBEDDED_PLAYER"||client=="WEB_REMIX")
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36";
    return "Mozilla/5.0 (ChromiumStylePlatform) Cobalt/25.lts.30.1034943-gold (unlike Gecko), Unknown_TV_Unknown_0/Unknown (Unknown, Unknown)";
}
std::string caption_referer(std::string_view url){
    const auto id=query_field(url,"v");
    if(id.size()==11&&std::all_of(id.begin(),id.end(),[](char c){return(c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-';}))return "https://www.youtube.com/watch?v="+std::string(id);
    return "https://www.youtube.com/";
}
std::string caption_url(std::string_view raw,std::string_view translated,bool preserve=false,std::string_view format="json3") {
    if(!caption_host(raw)) return {};
    raw=raw.substr(0,raw.find('#'));
    const auto question=raw.find('?');
    std::string result(raw.substr(0,question)),query,existing_translation;
    if(question!=std::string_view::npos) {
        auto rest=raw.substr(question+1);
        while(!rest.empty()) {
            const auto end=rest.find('&'),equals=rest.substr(0,end).find('=');
            const auto field=rest.substr(0,end),key=field.substr(0,equals);
            if(key=="tlang") {if(equals!=std::string_view::npos) existing_translation=normalize_language(field.substr(equals+1));}
            else if(!field.empty()&&key!="fmt") {if(!query.empty())query+='&';query+=field;}
            if(end==std::string_view::npos)break;
            rest.remove_prefix(end+1);
        }
    }
    if(!query.empty())query+='&';
    query+="fmt=";query+=format;
    const std::string target=translated.empty()&&preserve?existing_translation:normalize_language(translated);
    if(!target.empty())query+="&tlang="+target;
    return result+'?'+query;
}
}
std::string normalize_language(std::string_view value) {
    if(value.size()<2||value.size()>16)return {};
    std::string out;out.reserve(value.size());bool separator=true;
    for(char c:value) {
        if(c=='_'||c=='-') {if(separator)return {};out+='-';separator=true;}
        else if((c>='a'&&c<='z')||(c>='A'&&c<='Z')) {out+=static_cast<char>(c>='A'&&c<='Z'?c-'A'+'a':c);separator=false;}
        else return {};
    }
    return separator?std::string{}:out;
}
Selection select_track(const VideoInfo &info,std::string_view locale) {
    const auto wanted=normalize_language(locale);if(wanted.empty())return {};
    struct Candidate{std::string url,language;bool translated=false;int score=0;};
    std::vector<Candidate> candidates;
    std::vector<Candidate> english;
    std::string target;
    for(const auto&language:info.caption_translation_languages){const auto code=normalize_language(language);
        if(code==wanted){target=code;break;}if(target.empty()&&base_language(code)==base_language(wanted))target=code;}
    for(const auto&track:info.captions){
        const auto language=normalize_language(track.language);
        if(language.empty()||!caption_host(track.url))continue;
        if(base_language(language)=="en")english.push_back({caption_url(track.url,{}),language,false,track.automatic?0:1});
        if(base_language(language)==base_language(wanted)){
            candidates.push_back({caption_url(track.url,{}),track.language,false,20+(language==wanted?4:0)+(track.automatic?0:2)});
        }else if(track.translatable&&!target.empty()){
            candidates.push_back({caption_url(track.url,target),target,true,(track.automatic?0:2)+(base_language(language)=="en"?8:0)});
        }
    }
    std::stable_sort(candidates.begin(),candidates.end(),[](const auto&a,const auto&b){return a.score>b.score;});
    Selection selected;int direct_count=0;
    for(const auto&candidate:candidates){
        // Do not let many clients advertising the same empty target-language
        // track crowd the English-source translation out of the bounded list.
        if(base_language(wanted)!="en"&&!candidate.translated&&direct_count>=1)continue;
        if(candidate.url.empty())continue;
        if(selected.url.empty()){selected.url=candidate.url;selected.language=candidate.language;selected.translated=candidate.translated;if(!candidate.translated)++direct_count;}
        else if(candidate.url!=selected.url&&selected.alternatives.size()<5&&std::find(selected.alternatives.begin(),selected.alternatives.end(),candidate.url)==selected.alternatives.end())selected.alternatives.push_back(candidate.url);
    }
    if(base_language(wanted)!="en") {
        std::stable_sort(english.begin(),english.end(),[](const auto&a,const auto&b){return a.score>b.score;});
        for(const auto&candidate:english)if(!candidate.url.empty()&&selected.english_fallbacks.size()<2&&std::find(selected.english_fallbacks.begin(),selected.english_fallbacks.end(),candidate.url)==selected.english_fallbacks.end())selected.english_fallbacks.push_back(candidate.url);
    }
    return selected;
}
bool parse_json3(std::string_view body,std::vector<Cue>* out) {
    if(!out)return false;
    out->clear();
    if(body.empty()||body.size()>max_body)return false;
    yyjson_doc* doc=yyjson_read(body.data(),body.size(),0);
    if(!doc)return false;
    auto* events=yyjson_obj_get(yyjson_doc_get_root(doc),"events");
    if(!yyjson_is_arr(events)||yyjson_arr_size(events)>50000) {yyjson_doc_free(doc);return false;}
    struct Raw {Cue cue;bool append=false;};
    std::vector<Raw> parsed;std::size_t bytes=0;bool valid=true;
    for(std::size_t i=0,n=yyjson_arr_size(events);i<n;++i) {
        auto* event=yyjson_arr_get(events,i);auto* segments=yyjson_obj_get(event,"segs");
        if(!yyjson_is_arr(segments))continue;
        if(yyjson_arr_size(segments)>256) {valid=false;break;}
        auto* start=yyjson_obj_get(event,"tStartMs");auto* duration=yyjson_obj_get(event,"dDurationMs");
        if(!yyjson_is_num(start)||!yyjson_is_num(duration))continue;
        const double at=yyjson_get_num(start)/1000.0,span=yyjson_get_num(duration)/1000.0;
        if(!std::isfinite(at)||!std::isfinite(span)||at<0||at>86400||span<=0||span>600||at+span>87000)continue;
        std::string text;
        for(std::size_t j=0,m=yyjson_arr_size(segments);j<m;++j) {
            auto* utf8=yyjson_obj_get(yyjson_arr_get(segments,j),"utf8");
            if(!yyjson_is_str(utf8))continue;
            const auto length=yyjson_get_len(utf8);
            if(length>max_cue_text-text.size()) {valid=false;break;}
            text.append(yyjson_get_str(utf8),length);
        }
        if(!valid)break;
        for(char &c:text)if((static_cast<unsigned char>(c)<32&&c!='\n')||c==127)c=' ';
        while(!text.empty()&&(text.back()=='\n'||text.back()==' '))text.pop_back();
        if(text.find_first_not_of(" \n")==std::string::npos)continue;
        if(parsed.size()>=max_cues||text.size()>max_text-bytes) {valid=false;break;}
        bytes+=text.size();
        const double window=yyjson_get_num(yyjson_obj_get(event,"wWinId"));
        if(!std::isfinite(window)||window<0||window>65535)continue;
        parsed.push_back({Cue{at,at+span,std::move(text),static_cast<int>(window)},yyjson_get_int(yyjson_obj_get(event,"aAppend"))==1});
    }
    yyjson_doc_free(doc);
    if(!valid)return false;
    std::stable_sort(parsed.begin(),parsed.end(),[](const Raw&a,const Raw&b){return a.cue.start_s<b.cue.start_s;});
    std::array<int,32> windows{},last{};std::size_t window_count=0,total=0;
    for(auto &raw:parsed) {
        std::size_t slot=0;while(slot<window_count&&windows[slot]!=raw.cue.window_id)++slot;
        if(slot==window_count) {
            if(window_count==windows.size()) {out->clear();return false;}
            windows[slot]=raw.cue.window_id;last[slot]=-1;++window_count;
        }
        if(last[slot]>=0) {
            auto &previous=(*out)[static_cast<std::size_t>(last[slot])];
            if(previous.end_s>raw.cue.start_s) {
                if(raw.append)raw.cue.text=previous.text+raw.cue.text;
                previous.end_s=raw.cue.start_s;
            }
        }
        if(raw.cue.text.size()>max_cue_text||raw.cue.text.size()>max_text-total) {out->clear();return false;}
        total+=raw.cue.text.size();last[slot]=static_cast<int>(out->size());out->push_back(std::move(raw.cue));
    }
    return true;
}
namespace {
std::string clean_caption(std::string_view source){
    std::string out;
    const auto utf8=[&](unsigned code){
        if(code<32&&code!=10)return;if(code>0x10ffff||(code>=0xd800&&code<=0xdfff))return;
        if(code<0x80)out+=char(code);
        else if(code<0x800){out+=char(0xc0|(code>>6));out+=char(0x80|(code&63));}
        else if(code<0x10000){out+=char(0xe0|(code>>12));out+=char(0x80|((code>>6)&63));out+=char(0x80|(code&63));}
        else{out+=char(0xf0|(code>>18));out+=char(0x80|((code>>12)&63));out+=char(0x80|((code>>6)&63));out+=char(0x80|(code&63));}
    };
    for(size_t i=0;i<source.size()&&out.size()<=max_cue_text;++i){
        if(source[i]=='<'){const auto end=source.find('>',i+1);if(end==std::string_view::npos)break;
            const auto tag=source.substr(i,end-i+1);if(tag=="<br>"||tag=="<br/>"||tag=="<br />")out+='\n';i=end;continue;}
        if(source[i]=='&'){const auto end=source.find(';',i+1);
            if(end!=std::string_view::npos&&end-i<=12){const auto entity=source.substr(i+1,end-i-1);bool known=true;
                if(entity=="amp")out+='&';else if(entity=="lt")out+='<';else if(entity=="gt")out+='>';else if(entity=="quot")out+='"';else if(entity=="apos"||entity=="#39")out+='\'';else if(entity=="nbsp")out+=' ';
                else if(!entity.empty()&&entity[0]=='#'){const bool hex=entity.size()>1&&(entity[1]=='x'||entity[1]=='X');const auto digits=std::string(entity.substr(hex?2:1));char*last=nullptr;const auto number=std::strtoul(digits.c_str(),&last,hex?16:10);if(digits.empty()||*last)known=false;else utf8(unsigned(number));}
                else known=false;
                if(known){i=end;continue;}
            }
        }
        const unsigned char c=static_cast<unsigned char>(source[i]);if((c>=32&&c!=127)||c=='\n')out+=char(c);
    }
    while(!out.empty()&&(out.back()==' '||out.back()=='\n'))out.pop_back();
    return out;
}
bool number(std::string_view text,double&out){if(text.empty()||text.size()>32)return false;const std::string s(text);char*end=nullptr;out=std::strtod(s.c_str(),&end);return end==s.c_str()+s.size()&&std::isfinite(out);}
std::string_view attribute(std::string_view tag,std::string_view name){
    size_t at=0;
    while((at=tag.find(name,at))!=std::string_view::npos){
        if(at&&tag[at-1]!=' '&&tag[at-1]!='\t'){++at;continue;}
        size_t next=at+name.size();while(next<tag.size()&&tag[next]==' ')++next;
        if(next>=tag.size()||tag[next++]!='='){++at;continue;}
        while(next<tag.size()&&tag[next]==' ')++next;if(next>=tag.size()||(tag[next]!='"'&&tag[next]!='\''))return {};
        const char quote=tag[next++];const auto end=tag.find(quote,next);return end==std::string_view::npos?std::string_view{}:tag.substr(next,end-next);
    }return {};
}
bool timestamp(std::string_view text,double&out){
    const auto space=text.find_first_of(" \t");text=text.substr(0,space);double total=0;int groups=0;
    while(!text.empty()){const auto colon=text.find(':');double value=0;if(!number(text.substr(0,colon),value)||value<0)return false;total=total*60+value;++groups;if(colon==std::string_view::npos)break;text.remove_prefix(colon+1);}
    out=total;return groups>=2&&groups<=3&&std::isfinite(total)&&total<=87000;
}
bool retain_cue(std::vector<Cue>&out,double start,double end,std::string text,size_t&bytes){
    if(!std::isfinite(start)||!std::isfinite(end)||start<0||start>86400||end<=start||end-start>600||end>87000)return true;
    if(text.find_first_not_of(" \n")==std::string::npos)return true;
    if(out.size()>=max_cues||text.size()>max_cue_text||text.size()>max_text-bytes)return false;
    bytes+=text.size();out.push_back({start,end,std::move(text),0});return true;
}
}
bool parse_timed_text(std::string_view body,std::vector<Cue>*out){
    if(!out)return false;out->clear();if(body.empty()||body.size()>max_body)return false;
    if(body.substr(0,3)=="\xef\xbb\xbf")body.remove_prefix(3);
    const auto first=body.find_first_not_of(" \n\r\t");if(first==std::string_view::npos)return false;body.remove_prefix(first);
    if(body[0]=='{')return parse_json3(body,out);
    size_t bytes=0;
    if(body.rfind("WEBVTT",0)==0){
        std::string normalized;normalized.reserve(body.size());for(char c:body)if(c!='\r')normalized+=c;
        const std::string_view text(normalized);size_t cursor=0;
        while(cursor<text.size()){
            const auto line_end=text.find('\n',cursor);const auto line=text.substr(cursor,line_end==std::string_view::npos?text.size()-cursor:line_end-cursor);cursor=line_end==std::string_view::npos?text.size():line_end+1;
            const auto arrow=line.find("-->");if(arrow==std::string_view::npos)continue;
            auto from=line.substr(0,arrow),to=line.substr(arrow+3);while(!from.empty()&&from.back()==' ')from.remove_suffix(1);while(!to.empty()&&to.front()==' ')to.remove_prefix(1);
            double start=0,end=0;if(!timestamp(from,start)||!timestamp(to,end))continue;
            const auto stop=text.find("\n\n",cursor);const auto caption=text.substr(cursor,stop==std::string_view::npos?text.size()-cursor:stop-cursor);
            cursor=stop==std::string_view::npos?text.size():stop+2;
            if(!retain_cue(*out,start,end,clean_caption(caption),bytes)){out->clear();return false;}
        }
    }else if(body.find("<transcript")!=std::string_view::npos||body.find("<timedtext")!=std::string_view::npos){
        const bool srv1=body.find("<transcript")!=std::string_view::npos;const std::string_view begin=srv1?"<text ":"<p ",close=srv1?"</text>":"</p>";
        size_t cursor=0;
        while((cursor=body.find(begin,cursor))!=std::string_view::npos){
            const auto tag_end=body.find('>',cursor),end=body.find(close,tag_end);if(tag_end==std::string_view::npos||end==std::string_view::npos)break;
            const auto tag=body.substr(cursor,tag_end-cursor);double start=0,duration=0;
            const bool valid=number(attribute(tag,srv1?"start":"t"),start)&&number(attribute(tag,srv1?"dur":"d"),duration);
            if(!srv1){start/=1000;duration/=1000;}
            if(valid&&!retain_cue(*out,start,start+duration,clean_caption(body.substr(tag_end+1,end-tag_end-1)),bytes)){out->clear();return false;}
            cursor=end+close.size();
        }
    }else return false;
    std::stable_sort(out->begin(),out->end(),[](const Cue&a,const Cue&b){return a.start_s<b.start_s;});
    for(size_t n=1;n<out->size();++n)if((*out)[n-1].end_s>(*out)[n].start_s)(*out)[n-1].end_s=(*out)[n].start_s;
    return true;
}
struct Loader::Shared {
    std::mutex mutex;std::condition_variable wake;
    std::atomic<std::uint64_t> generation{0};std::atomic<bool> stopping{false};
    std::vector<Cue> cues;std::string status;std::vector<std::string> urls,fallbacks;bool queued=false;std::size_t window_count=0;
    std::vector<std::string> requested_urls,requested_fallbacks;
    // Session-wide endpoint cooldowns survive clear(), signed URL changes and
    // language changes. A refused translation is never retried this session.
    bool translation_limited=false,source_limited=false;
    std::string cached_source;std::vector<Cue> cached_cues;
};
struct Loader::Worker {
    std::shared_ptr<Shared> shared;pthread_t thread{};bool running=false;
    static void* entry(void* pointer) {static_cast<Worker*>(pointer)->run();return nullptr;}
    void run() {
        for(;;) {
            std::vector<std::string> urls,fallbacks;std::uint64_t generation=0;
            {
                std::unique_lock<std::mutex> lock(shared->mutex);
                shared->wake.wait(lock,[&]{return shared->queued||shared->stopping.load();});
                if(shared->stopping.load())return;
                urls.swap(shared->urls);fallbacks.swap(shared->fallbacks);shared->queued=false;generation=shared->generation.load();
            }
            std::vector<Cue> cues;std::string status="unavailable";size_t attempts=0;
            // Some clients return HTTP200 with an empty JSON3 body even though
            // their VTT track or a different offered client's track is valid.
            const size_t requested_count=urls.size();
            urls.insert(urls.end(),fallbacks.begin(),fallbacks.end());
            const bool requested_translation=std::any_of(urls.begin(),urls.begin()+static_cast<std::ptrdiff_t>(requested_count),[](const std::string&u){return u.find("tlang=")!=std::string::npos;});
            bool translation_rate_limited=false,source_rate_limited=false;
            {std::lock_guard<std::mutex> lock(shared->mutex);translation_rate_limited=shared->translation_limited;source_rate_limited=shared->source_limited;}
            std::string successful_source;
            for(size_t source_index=0;source_index<urls.size();++source_index){
                const auto&source=urls[source_index];const bool fallback=source_index>=requested_count;
                // A translation-specific 429 must not trigger retries across
                // target formats/clients. An offered original-English track is
                // a separate bounded fallback, clearly identified to the viewer.
                const bool translated=source.find("tlang=")!=std::string::npos;
                if(translation_rate_limited&&translated){status="error: translation rate limited (HTTP 429)";continue;}
                if(!cues.empty()||shared->stopping.load()||generation!=shared->generation.load())break;
                if(!translated){std::lock_guard<std::mutex> lock(shared->mutex);if(source==shared->cached_source)cues=shared->cached_cues;}
                if(!cues.empty()){status=fallback?(requested_translation&&translation_rate_limited?"fallback: en (translation rate limited)":"fallback: en"):"ok";break;}
                if(source_rate_limited){status="error: HTTP 429";break;}
                for(const auto*format:{"json3","vtt","srv1"}){
                    if(attempts>=12||(!fallback&&attempts>=8)||shared->stopping.load()||generation!=shared->generation.load())break;
                    ++attempts;
                    std::string body;bool too_large=false;
                    http::Request request;request.url=caption_url(source,{},true,format);request.timeout_s=8;request.max_bytes=max_body;
                    request.headers={{"Accept","application/json, text/vtt, application/xml, text/xml, */*"},{"Referer",caption_referer(source)},{"User-Agent",caption_user_agent(source)}};
                    request.on_body=[&](std::string_view chunk){
                        if(shared->stopping.load()||generation!=shared->generation.load())return false;
                        if(chunk.size()>max_body-body.size()){too_large=true;return false;}body.append(chunk);return true;
                    };
                    const auto response=http::perform(request);
                    if(response.status==429){
                        std::lock_guard<std::mutex> lock(shared->mutex);
                        if(translated)shared->translation_limited=translation_rate_limited=true;
                        else shared->source_limited=source_rate_limited=true;
                    }
                    if(shared->stopping.load()||generation!=shared->generation.load())break;
                    if(body.empty()&&!response.body.empty())body=response.body;
                    if(too_large||body.size()>max_body){status="error: caption response too large";break;}
                    if(!response.ok())status="error: "+response.error;
                    else if(response.status!=200)status="error: HTTP "+std::to_string(response.status);
                    else if(body.empty())status="unavailable";
                    else if(!parse_timed_text(body,&cues))status="error: unsupported caption response";
                    else status=cues.empty()?"unavailable":fallback?(requested_translation&&translation_rate_limited?"fallback: en (translation rate limited)":"fallback: en"):"ok";
                    if(!cues.empty()&&!translated)successful_source=source;
                    log::line("captions: %s format=%s (%zu cues, %zu bytes)",status.c_str(),format,cues.size(),body.size());
                    if(!cues.empty()||response.status==403||response.status==429)break;
                }
                if(status=="error: HTTP 429"&&fallback)break;
            }
            if(cues.empty()&&requested_translation&&translation_rate_limited&&status!="error: HTTP 429")status="error: translation rate limited (HTTP 429)";
            if(shared->stopping.load()||generation!=shared->generation.load())continue;
            std::lock_guard<std::mutex> lock(shared->mutex);
            if(generation!=shared->generation.load()||shared->stopping.load())continue;
            std::array<int,32> windows{};std::size_t count=0;
            for(const auto &cue:cues) {
                const auto end=windows.begin()+static_cast<std::ptrdiff_t>(count);
                if(std::find(windows.begin(),end,cue.window_id)==end&&count<32)windows[count++]=cue.window_id;
            }
            if(!successful_source.empty()){shared->cached_source=std::move(successful_source);shared->cached_cues=cues;}
            shared->window_count=count;shared->cues=std::move(cues);shared->status=std::move(status);
        }
    }
};
Loader::Loader():shared_(std::make_shared<Shared>()),worker_(std::make_unique<Worker>()) {
    worker_->shared=shared_;pthread_attr_t attributes;
    if(pthread_attr_init(&attributes)!=0) {shared_->status="error: caption worker unavailable";return;}
    (void)pthread_attr_setstacksize(&attributes,1u<<20);
    worker_->running=pthread_create(&worker_->thread,&attributes,&Worker::entry,worker_.get())==0;
    pthread_attr_destroy(&attributes);
    if(!worker_->running)shared_->status="error: caption worker unavailable";
}
Loader::~Loader() {
    {std::lock_guard<std::mutex> lock(shared_->mutex);shared_->stopping.store(true);shared_->generation.fetch_add(1);}
    shared_->wake.notify_one();
    if(worker_->running)pthread_join(worker_->thread,nullptr);
}
void Loader::clear() {
    std::lock_guard<std::mutex> lock(shared_->mutex);shared_->generation.fetch_add(1);
    shared_->cues.clear();shared_->status.clear();shared_->urls.clear();shared_->fallbacks.clear();shared_->queued=false;
    shared_->requested_urls.clear();shared_->requested_fallbacks.clear();
}
void Loader::load(const std::string &url,const std::vector<std::string>&alternatives,const std::vector<std::string>&fallbacks) {
    const auto normalized=caption_url(url,{},true);
    std::vector<std::string> urls,english;
    if(!normalized.empty())urls.push_back(normalized);
    for(const auto&other:alternatives){const auto safe=caption_url(other,{},true);if(!safe.empty()&&urls.size()<6&&std::find(urls.begin(),urls.end(),safe)==urls.end())urls.push_back(safe);}
    for(const auto&other:fallbacks){const auto safe=caption_url(other,{},false);if(!safe.empty()&&english.size()<2&&std::find(english.begin(),english.end(),safe)==english.end())english.push_back(safe);}
    std::lock_guard<std::mutex> lock(shared_->mutex);
    if(!shared_->status.empty()&&urls==shared_->requested_urls&&english==shared_->requested_fallbacks)return;
    shared_->generation.fetch_add(1);shared_->cues.clear();
    shared_->queued=false;shared_->urls.clear();shared_->fallbacks.clear();
    if(normalized.empty()&&fallbacks.empty()) {shared_->status="error: invalid caption URL";return;}
    if(!worker_->running) {shared_->status="error: caption worker unavailable";return;}
    shared_->requested_urls=urls;shared_->requested_fallbacks=english;
    shared_->urls=std::move(urls);shared_->fallbacks=std::move(english);
    if(shared_->urls.empty()&&shared_->fallbacks.empty()){shared_->status="error: invalid caption URL";return;}
    shared_->queued=true;shared_->status="loading";shared_->wake.notify_one();
}
std::string Loader::text_at(double position) {
    if(!std::isfinite(position)||position<0)return {};
    std::lock_guard<std::mutex> lock(shared_->mutex);std::string text;
    auto end=std::upper_bound(shared_->cues.begin(),shared_->cues.end(),position,[](double value,const Cue&cue){return value<cue.start_s;});
    std::array<int,32> seen{};std::size_t count=0;
    while(end!=shared_->cues.begin()&&count<shared_->window_count) {
        --end;
        const auto seen_end=seen.begin()+static_cast<std::ptrdiff_t>(count);
        if(std::find(seen.begin(),seen_end,end->window_id)!=seen_end)continue;
        seen[count++]=end->window_id;
        if(position<end->end_s&&text.size()+end->text.size()+1<=4096) {if(!text.empty())text='\n'+text;text=end->text+text;}
    }
    return text;
}
std::string Loader::status() {std::lock_guard<std::mutex> lock(shared_->mutex);return shared_->status;}
} // namespace yt::captions

