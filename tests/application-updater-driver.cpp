// Application updater with a bounded loopback-only test transport.
// Real handoff requires an explicit CLI opt-in and an isolated-fixture sentinel.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/application_updater.hpp"
#include "core/save_file.hpp"
#include "yt/http.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <curl/curl.h>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <thread>
#include <fcntl.h>
#if defined(_WIN32)
#include <io.h>
#endif

namespace yt::http {
Response perform(const Request&request){
    Response response;
    if(request.url.rfind("http://127.0.0.1:",0)!=0){response.error="test transport rejects non-loopback URLs";return response;}
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
    curl_easy_setopt(handle,CURLOPT_URL,request.url.c_str());curl_easy_setopt(handle,CURLOPT_PROTOCOLS_STR,"http");
    curl_easy_setopt(handle,CURLOPT_NOSIGNAL,1L);curl_easy_setopt(handle,CURLOPT_TIMEOUT,10L);
    curl_easy_setopt(handle,CURLOPT_CONNECTTIMEOUT,2L);curl_easy_setopt(handle,CURLOPT_WRITEFUNCTION,body);curl_easy_setopt(handle,CURLOPT_WRITEDATA,&sink);
    curl_easy_setopt(handle,CURLOPT_XFERINFOFUNCTION,progress);curl_easy_setopt(handle,CURLOPT_XFERINFODATA,&request);curl_easy_setopt(handle,CURLOPT_NOPROGRESS,0L);
    curl_slist* headers=nullptr;for(const auto&h:request.headers)headers=curl_slist_append(headers,(h.name+": "+h.value).c_str());curl_easy_setopt(handle,CURLOPT_HTTPHEADER,headers);
    const auto result=curl_easy_perform(handle);curl_easy_getinfo(handle,CURLINFO_RESPONSE_CODE,&response.status);
    if(result!=CURLE_OK)response.error=curl_easy_strerror(result);
    curl_slist_free_all(headers);curl_easy_cleanup(handle);return response;
}
}
namespace {
using Json=nlohmann::json;using Phase=museum::ApplicationUpdater::Phase;
const char*phase_name(Phase phase){
    switch(phase){case Phase::idle:return "idle";case Phase::checking:return "checking";case Phase::current:return "current";case Phase::available:return "available";case Phase::downloading:return "downloading";case Phase::ready:return "ready";case Phase::failed:return "failed";}return "unknown";
}
Json status(const museum::ApplicationUpdater::Snapshot&s){return {{"phase",phase_name(s.phase)},{"current_version",s.current_version},{"version",s.version},{"error",s.error},{"downloaded_bytes",s.downloaded_bytes},{"total_bytes",s.total_bytes},{"notes",s.notes}};}
bool wait(museum::ApplicationUpdater&updater){
    const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(12);
    while(std::chrono::steady_clock::now()<end){const auto phase=updater.snapshot().phase;if(phase!=Phase::checking&&phase!=Phase::downloading){std::this_thread::sleep_for(std::chrono::milliseconds(2));return true;}std::this_thread::sleep_for(std::chrono::milliseconds(2));}return false;
}
}
int main(int argc,char**argv){
    if(argc!=4&&(argc!=5||std::string(argv[4])!="--allow-test-handoff"))return 2;
    const bool allow_handoff=argc==5;
#if defined(_WIN32)
    _fmode=_O_BINARY;_setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
    const auto root=std::filesystem::absolute(argv[1]).lexically_normal().generic_string(),data=std::filesystem::absolute(argv[2]).lexically_normal().generic_string();
    const std::string feed=argv[3];museum::ApplicationUpdater updater;std::string line;
    while(std::getline(std::cin,line)){
        const auto command=Json::parse(line,nullptr,false);Json reply;
        if(!command.is_object()||!command.contains("op")||!command["op"].is_string()){reply={{"driver_error","invalid command"}};}
        else {
            const auto op=command["op"].get<std::string>();bool ok=true;
            if(op=="configure")ok=updater.configure(root,data,feed,command.value("current",std::string("0.2.0-preview")));
            else if(op=="newer")reply["newer"]=museum::ApplicationUpdater::newer_version(command.value("candidate",std::string()),command.value("current",std::string()));
            else if(op=="restart")ok=updater.begin_restart("it");
            else if(op=="handoff"){
                std::string sentinel;
                ok=allow_handoff&&hui::save::read_file(root+"/.test-updater-handoff",&sentinel,128)&&sentinel=="pixel-museum-isolated-updater-bridge"&&updater.begin_restart(command.value("language",std::string("it")));
            }
            else if(op=="check"){ok=updater.check();if(ok)ok=wait(updater);}
            else if(op=="install"){ok=updater.install();if(ok)ok=wait(updater);}
            else if(op=="install_async")ok=updater.install();
            else if(op=="shutdown")updater.shutdown();
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
