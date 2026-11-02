// Real updater/save implementation with a bounded loopback-only test transport.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/database_updater.hpp"
#include "museum/catalog.hpp"
#include "museum/collection_sha256.hpp"
#include "core/save_file.hpp"
#include "yt/http.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <curl/curl.h>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <map>
#include <thread>
#include <fcntl.h>
#if defined(_WIN32)
#include <io.h>
#endif

namespace { std::map<std::string,std::string> fixture_urls; }
namespace yt::http {
Response perform(const Request&request){
    Response response;
    const auto mapped=fixture_urls.find(request.url);
    const std::string url=mapped==fixture_urls.end()?request.url:mapped->second;
    if(url.rfind("http://127.0.0.1:",0)!=0){response.error="test transport rejects non-loopback URLs";return response;}
    static const auto initialized=curl_global_init(CURL_GLOBAL_DEFAULT);(void)initialized;
    auto*handle=curl_easy_init();if(!handle){response.error="init";return response;}
    struct Sink {const Request*request;Response*response;std::size_t received=0;} sink{&request,&response};
    const auto body=+[](char*data,std::size_t size,std::size_t count,void*opaque)->std::size_t{
        auto&s=*static_cast<Sink*>(opaque);const auto length=size*count;
        if(length>s.request->max_bytes-s.received||(s.request->cancelled&&s.request->cancelled()))return 0;
        s.received+=length;
        if(s.request->on_body)return s.request->on_body(std::string_view(data,length))?length:0;
        s.response->body.append(data,length);return length;
    };
    const auto progress=+[](void*opaque,curl_off_t,curl_off_t,curl_off_t,curl_off_t)->int{auto&r=*static_cast<const Request*>(opaque);return r.cancelled&&r.cancelled()?1:0;};
    curl_easy_setopt(handle,CURLOPT_URL,url.c_str());curl_easy_setopt(handle,CURLOPT_PROTOCOLS_STR,"http");
    curl_easy_setopt(handle,CURLOPT_NOSIGNAL,1L);curl_easy_setopt(handle,CURLOPT_TIMEOUT,10L);
    curl_easy_setopt(handle,CURLOPT_CONNECTTIMEOUT,2L);curl_easy_setopt(handle,CURLOPT_WRITEFUNCTION,body);curl_easy_setopt(handle,CURLOPT_WRITEDATA,&sink);
    curl_easy_setopt(handle,CURLOPT_XFERINFOFUNCTION,progress);curl_easy_setopt(handle,CURLOPT_XFERINFODATA,&request);curl_easy_setopt(handle,CURLOPT_NOPROGRESS,0L);
    const auto result=curl_easy_perform(handle);curl_easy_getinfo(handle,CURLINFO_RESPONSE_CODE,&response.status);
    if(result!=CURLE_OK)response.error=curl_easy_strerror(result);
    curl_easy_cleanup(handle);return response;
}
}
namespace {
using Json=nlohmann::json;using Phase=museum::DatabaseUpdater::Phase;
const char*phase_name(Phase phase){
    switch(phase){case Phase::idle:return "idle";case Phase::checking:return "checking";case Phase::current:return "current";case Phase::available:return "available";case Phase::downloading:return "downloading";case Phase::ready:return "ready";case Phase::failed:return "failed";}return "unknown";
}
Json status(const museum::DatabaseUpdater::Snapshot&s){return {{"phase",phase_name(s.phase)},{"revision",s.revision},{"current_revision",s.current_revision},{"version",s.version},{"error",s.error},{"downloaded_bytes",s.downloaded_bytes},{"total_bytes",s.total_bytes},{"notes",s.notes}};}
bool wait(museum::DatabaseUpdater&updater){
    const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(12);
    while(std::chrono::steady_clock::now()<end){const auto phase=updater.snapshot().phase;if(phase!=Phase::checking&&phase!=Phase::downloading){std::this_thread::sleep_for(std::chrono::milliseconds(2));return true;}std::this_thread::sleep_for(std::chrono::milliseconds(2));}return false;
}
}
int main(int argc,char**argv){
    if(argc!=4&&argc!=5)return 2;
#if defined(_WIN32)
    _fmode=_O_BINARY;_setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
    if(argc==5){
        std::ifstream input(argv[4],std::ios::binary);const auto routes=Json::parse(input,nullptr,false);
        if(!routes.is_object())return 3;
        for(auto it=routes.begin();it!=routes.end();++it){
            if(!it.value().is_string()||it.key().rfind("https://github.com/LoZazaMastro/Pixel-Museum/releases/download/",0)!=0)return 3;
            const auto target=it.value().get<std::string>();if(target.rfind("http://127.0.0.1:",0)!=0)return 3;
            fixture_urls[it.key()]=target;
        }
    }
    const auto root=std::filesystem::absolute(argv[1]).lexically_normal().generic_string(),data=std::filesystem::absolute(argv[2]).lexically_normal().generic_string();
    const std::string feed=argv[3];museum::DatabaseUpdater updater;std::string line;
    while(std::getline(std::cin,line)){
        const auto command=Json::parse(line,nullptr,false);Json reply;
        if(!command.is_object()||!command.contains("op")||!command["op"].is_string()){reply={{"driver_error","invalid command"}};}
        else {
            const auto op=command["op"].get<std::string>();bool ok=true;
            if(op=="configure")ok=updater.configure(root,data,feed);
            else if(op=="check"){ok=updater.check();if(ok)ok=wait(updater);}
            else if(op=="install"){ok=updater.install();if(ok)ok=wait(updater);}
            else if(op=="install_async")ok=updater.install();
            else if(op=="shutdown")updater.shutdown();
            else if(op=="resolved_digest"){
                const auto path=command.value("path",std::string("content/catalog.json"));std::string bytes;
                ok=hui::save::read_file(root+"/"+path,&bytes,64u<<20);museum::CollectionSha256 hash;if(ok)hash.update(bytes.data(),bytes.size());
                reply["bytes"]=bytes.size();reply["sha256"]=ok?hash.finish():std::string();reply["resolved"]=hui::save::resolve_read_path(root+"/"+path);
            }
            else if(op=="catalogue_entry"){
                museum::Catalog catalog;ok=catalog.load(root+"/content/catalog.json");
                const auto locale=command.value("locale",std::string("en")),id=command.value("id",std::string("google-stadia"));
                if(ok)ok=catalog.set_locale(root,locale);
                reply["catalogue_error"]=catalog.error;reply["locale_error"]=catalog.locale_error();
                reply["resolved"]=hui::save::resolve_read_path(root+"/content/catalog.json");
                const auto*entry=ok?catalog.find_entry(id):nullptr;reply["entry"]=nullptr;
                if(entry){
                    Json rooms=Json::array(),images=Json::array();
                    for(const auto&room:entry->soundtrack_rooms){Json tracks=Json::array();for(const auto&track:room.tracks)tracks.push_back({{"id",track.youtube_id},{"title",track.title},{"start",track.start_seconds},{"end",track.end_seconds}});rooms.push_back({{"title",room.title},{"composer",room.composer},{"note",room.curator_note},{"tracks",tracks}});}
                    for(const auto&image:entry->images)images.push_back({{"url",image.url},{"title",image.title},{"paragraph",image.story_paragraph},{"dark_url",image.dark_url}});
                    reply["entry"]={{"id",entry->id},{"title",entry->title},{"subtitle",entry->subtitle},{"summary",entry->summary},{"year",entry->year},{"month",entry->month},{"day",entry->day},{"body",entry->body},{"story_headings",entry->story_headings},{"images",images},{"soundtrack_rooms",rooms}};
                }
            }
            else if(op=="read"){
                std::string bytes;const auto path=command.value("path",std::string("content/catalog.json"));
                ok=hui::save::read_file(root+"/"+path,&bytes,64u<<20);reply["content"]=bytes;reply["resolved"]=hui::save::resolve_read_path(root+"/"+path);
            }else if(op!="snapshot"){reply["driver_error"]="unknown command";ok=false;}
            reply["ok"]=ok;reply["state"]=status(updater.snapshot());
        }
        std::cout<<reply.dump()<<std::endl;
    }
    updater.shutdown();return 0;
}
