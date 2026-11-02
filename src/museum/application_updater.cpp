// Verified Windows application payloads; replacement runs after this process exits.
// SPDX-License-Identifier: GPL-3.0-or-later
#if defined(_WIN32)
#include "museum/application_updater.hpp"
#include "museum/collection_sha256.hpp"
#include "core/save_file.hpp"
#include "yt/http.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdio>
#include <cwctype>
#include <fcntl.h>
#include <io.h>
#include <mutex>
#include <pthread.h>
#include <sys/stat.h>
#include <vector>

namespace museum {
namespace {
using Json=nlohmann::json;
constexpr std::uint64_t max_archive=(2ull<<30)-1,max_expanded=4ull<<30;
struct Version {std::array<unsigned,3> core{};std::vector<std::string> pre;bool valid=false;};
bool numeric(const std::string& s){return !s.empty()&&std::all_of(s.begin(),s.end(),[](char c){return c>='0'&&c<='9';});}
bool identifiers(const std::string& s,std::vector<std::string>* out){
    if(s.empty())return false;
    for(std::size_t i=0;i<s.size();){const auto end=s.find('.',i);const auto part=s.substr(i,end==std::string::npos?end:end-i);
        if(part.empty()||!std::all_of(part.begin(),part.end(),[](unsigned char c){return(c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-';}))return false;
        if(out){if(numeric(part)&&part.size()>1&&part[0]=='0')return false;out->push_back(part);}
        if(end==std::string::npos)return true;i=end+1;if(i==s.size())return false;
    }return true;
}
Version version(const std::string& raw){
    Version v;if(raw.empty()||raw.size()>80)return v;std::string s=raw;if(s[0]=='v')s.erase(0,1);
    const auto plus=s.find('+');if(plus!=std::string::npos){if(!identifiers(s.substr(plus+1),nullptr))return v;s.resize(plus);}
    const auto dash=s.find('-');if(dash!=std::string::npos){if(!identifiers(s.substr(dash+1),&v.pre))return v;s.resize(dash);}
    std::size_t pos=0;for(int part=0;part<3;++part){const auto start=pos;unsigned n=0;
        while(pos<s.size()&&s[pos]>='0'&&s[pos]<='9'){if(n>100000)return v;n=n*10+unsigned(s[pos++]-'0');}
        if(start==pos||(pos-start>1&&s[start]=='0'))return v;v.core[part]=n;
        if(part<2){if(pos>=s.size()||s[pos++]!='.')return v;}else if(pos!=s.size())return v;
    }v.valid=true;return v;
}
bool newer(const Version& a,const Version& b){
    if(!a.valid||!b.valid)return false;if(a.core!=b.core)return a.core>b.core;
    if(a.pre.empty()||b.pre.empty())return a.pre.empty()&&!b.pre.empty();
    for(std::size_t i=0;i<std::min(a.pre.size(),b.pre.size());++i){const auto& x=a.pre[i];const auto& y=b.pre[i];if(x==y)continue;
        const bool nx=numeric(x),ny=numeric(y);if(nx!=ny)return !nx;if(nx&&x.size()!=y.size())return x.size()>y.size();return x>y;
    }return a.pre.size()>b.pre.size();
}
std::string normalize(std::string s){std::replace(s.begin(),s.end(),'\\','/');while(s.size()>1&&s.back()=='/')s.pop_back();return s;}
std::wstring wide(const std::string& s){const int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.data(),int(s.size()),nullptr,0);if(n<=0)return {};std::wstring w(n,L'\0');MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.data(),int(s.size()),w.data(),n);return w;}
bool ordinary(const std::string& path,bool dir,std::uint64_t* size=nullptr){const auto w=wide(path);if(w.empty())return false;const auto a=GetFileAttributesW(w.c_str());if(a==INVALID_FILE_ATTRIBUTES||(a&FILE_ATTRIBUTE_REPARSE_POINT)||bool(a&FILE_ATTRIBUTE_DIRECTORY)!=dir)return false;struct _stat64 st{};if(_wstat64(w.c_str(),&st)!=0)return false;if(size)*size=std::uint64_t(st.st_size);return true;}
bool tree(const std::string& path,bool create){
    const auto p=normalize(path);if(p.size()<3||p[1]!=':'||p[2]!='/'||!((p[0]>='A'&&p[0]<='Z')||(p[0]>='a'&&p[0]<='z')))return false;
    for(std::size_t i=3;i<=p.size();++i)if(i==p.size()||p[i]=='/'){
        const auto part=p.substr(0,i);const auto w=wide(part);if(w.empty())return false;
        if(!ordinary(part,true)&&(!create||(!CreateDirectoryW(w.c_str(),nullptr)&&GetLastError()!=ERROR_ALREADY_EXISTS)||!ordinary(part,true)))return false;
    }return true;
}
bool hash_string(const std::string& s){return s.size()==64&&std::all_of(s.begin(),s.end(),[](char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f');});}
bool loopback(const std::string& s){return s.rfind("http://127.0.0.1:",0)==0||s.rfind("http://localhost:",0)==0;}
bool trusted(const std::string& s,bool local){return s.size()<4096&&s.find('\0')==std::string::npos&&(s.rfind("https://github.com/LoZazaMastro/Pixel-Museum/releases/download/",0)==0||(local&&loopback(s)));}
struct Release{std::string version,url,sha;std::uint64_t bytes=0,expanded=0;bool available=false;std::map<std::string,std::string> notes;};
bool parse(const Json& j,Release& r,bool local){
    if(!j.is_object()||!j.contains("schema_version")||!j["schema_version"].is_number_unsigned()||j["schema_version"]!=1||!j.contains("application_id")||!j["application_id"].is_string()||j["application_id"]!="pixel-museum"||!j.contains("platforms")||!j["platforms"].is_object()||!j["platforms"].contains("windows-x64"))return false;
    const auto& p=j["platforms"]["windows-x64"];
    if(!p.is_object()||!p.contains("version")||!p["version"].is_string()||!p.contains("available")||!p["available"].is_boolean())return false;
    r.version=p["version"].get<std::string>();r.available=p["available"].get<bool>();if(!version(r.version).valid)return false;
    if(p.contains("notes")){if(!p["notes"].is_object())return false;for(const char* lang:{"en","it","es","fr","de"})if(p["notes"].contains(lang)){if(!p["notes"][lang].is_string())return false;auto s=p["notes"][lang].get<std::string>();if(s.size()>4096)return false;r.notes[lang]=std::move(s);}}
    if(!r.available)return true;
    for(const char* name:{"url","sha256"})if(!p.contains(name)||!p[name].is_string())return false;
    for(const char* name:{"bytes","unpacked_bytes"})if(!p.contains(name)||!p[name].is_number_unsigned())return false;
    r.url=p["url"].get<std::string>();r.sha=p["sha256"].get<std::string>();r.bytes=p["bytes"].get<std::uint64_t>();r.expanded=p["unpacked_bytes"].get<std::uint64_t>();
    return trusted(r.url,local)&&hash_string(r.sha)&&r.bytes>=32&&r.bytes<=max_archive&&r.expanded>=r.bytes&&r.expanded<=max_expanded;
}
bool digest(const std::string& path,const Release& r,const std::atomic<bool>& stop){std::uint64_t size=0;if(!ordinary(path,false,&size)||size!=r.bytes)return false;FILE* f=std::fopen(path.c_str(),"rb");if(!f)return false;CollectionSha256 hash;std::array<char,256u<<10> data{};std::uint64_t count=0;while(!stop.load()){const auto n=std::fread(data.data(),1,data.size(),f);count+=n;hash.update(data.data(),n);if(n<data.size())break;}const bool good=!stop.load()&&!std::ferror(f)&&count==r.bytes;std::fclose(f);return good&&hash.finish()==r.sha;}
}

struct ApplicationUpdater::Impl{
    mutable std::mutex mutex;Snapshot state;Release release;std::string root,data,storage,source;
    std::atomic<bool> stop{false},running{false};pthread_t thread{};bool joinable=false,installing=false,local=false,configured=false;
    void fail(const char* message){std::lock_guard<std::mutex> lock(mutex);state.phase=Phase::failed;state.error=message;}
    std::string archive()const{return storage+"/payloads/"+release.sha+".zip";}
    void check_feed(){
        yt::http::Request req;req.url=source;req.max_bytes=1u<<20;req.timeout_s=15;req.cancelled=[this]{return stop.load();};req.headers={{"Cache-Control","no-cache"}};
        const auto res=yt::http::perform(req);if(stop.load())return;if(!res.http_ok()){fail("Cannot check for application updates. Please try again when connected.");return;}
        Release r;if(!parse(Json::parse(res.body,nullptr,false),r,local)){fail("The application update manifest is invalid.");return;}
        std::lock_guard<std::mutex> lock(mutex);state.version=r.version;state.notes=r.notes;state.downloaded_bytes=0;state.total_bytes=r.bytes;
        if(!r.available||!newer(version(r.version),version(state.current_version))){state.phase=Phase::current;return;}
        release=std::move(r);state.phase=Phase::available;
    }
    void download(){
        if(!tree(storage+"/payloads",true)){fail("Cannot prepare the application update folder.");return;}
        const auto target=archive();if(digest(target,release,stop)){std::lock_guard<std::mutex> lock(mutex);state.downloaded_bytes=release.bytes;state.phase=Phase::ready;return;}
        ULARGE_INTEGER free{};if(!GetDiskFreeSpaceExW(wide(storage).c_str(),&free,nullptr,nullptr)||free.QuadPart<release.bytes+release.expanded+release.expanded/2){fail("There is not enough free space for the application update.");return;}
        const auto part=target+".part";const auto wp=wide(part);std::uint64_t existing=0;
        if(!ordinary(part,false,&existing)||existing>release.bytes){if(GetFileAttributesW(wp.c_str())!=INVALID_FILE_ATTRIBUTES&&!DeleteFileW(wp.c_str())){fail("Cannot prepare the application update folder.");return;}existing=0;}
        CollectionSha256 hash;
        if(existing){FILE* old=std::fopen(part.c_str(),"rb");if(!old){fail("Cannot prepare the application update folder.");return;}std::array<char,256u<<10> b{};std::uint64_t nread=0;while(!stop.load()&&nread<existing){const auto n=std::fread(b.data(),1,std::min<std::uint64_t>(b.size(),existing-nread),old);if(!n)break;hash.update(b.data(),n);nread+=n;}std::fclose(old);if(stop.load())return;if(nread!=existing){DeleteFileW(wp.c_str());fail("The application update download could not be verified.");return;}}
        FILE* file=std::fopen(part.c_str(),existing?"ab":"wb");if(!file){fail("Cannot prepare the application update folder.");return;}
        std::array<char,1u<<20> buffer{};std::setvbuf(file,buffer.data(),_IOFBF,buffer.size());std::uint64_t received=existing;bool io=true;
        {std::lock_guard<std::mutex> lock(mutex);state.downloaded_bytes=received;}
        yt::http::Response response;response.status=206;
        if(received<release.bytes){
            std::uint64_t last_traffic=GetTickCount64();
            yt::http::Request req;req.url=release.url;req.max_bytes=std::size_t(release.bytes-existing+1);req.timeout_s=600;req.cancelled=[this,&last_traffic]{return stop.load()||GetTickCount64()-last_traffic>45000;};
            if(existing)req.headers.push_back({"Range","bytes="+std::to_string(existing)+"-"});
            req.on_body=[&](std::string_view bytes){if(stop.load()||bytes.size()>release.bytes-received)return false;if(std::fwrite(bytes.data(),1,bytes.size(),file)!=bytes.size()){io=false;return false;}last_traffic=GetTickCount64();hash.update(bytes.data(),bytes.size());received+=bytes.size();std::lock_guard<std::mutex> lock(mutex);state.downloaded_bytes=received;return true;};
            response=yt::http::perform(req);
        }
        if(std::fflush(file)!=0||_commit(_fileno(file))!=0)io=false;if(std::fclose(file)!=0)io=false;if(stop.load())return;
        const bool good=response.http_ok()&&(!existing||response.status==206)&&io&&received==release.bytes&&hash.finish()==release.sha;
        if(!good){if(!io||received==release.bytes||(!existing&&response.status!=200)||existing&&response.status!=206)DeleteFileW(wp.c_str());fail(io?"The application update download could not be verified.":"There is not enough free space for the application update.");return;}
        if(!MoveFileExW(wp.c_str(),wide(target).c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)){fail("Cannot save the verified application update.");return;}
        std::lock_guard<std::mutex> lock(mutex);state.phase=Phase::ready;
    }
    static void* entry(void* p){auto& self=*static_cast<Impl*>(p);if(self.installing)self.download();else self.check_feed();self.running.store(false);return nullptr;}
    bool launch(bool install){
        if(!configured||running.load())return false;if(joinable){pthread_join(thread,nullptr);joinable=false;}
        {std::lock_guard<std::mutex> lock(mutex);if(install&&(release.sha.empty()||!newer(version(release.version),version(state.current_version))))return false;if(!install&&state.phase==Phase::ready)return false;state.phase=install?Phase::downloading:Phase::checking;state.error.clear();state.downloaded_bytes=0;}
        stop.store(false);installing=install;pthread_attr_t attr;if(pthread_attr_init(&attr)!=0){fail("Cannot start the application update worker.");return false;}pthread_attr_setstacksize(&attr,3u<<20);running.store(true);const int result=pthread_create(&thread,&attr,&entry,this);pthread_attr_destroy(&attr);if(result){running.store(false);fail("Cannot start the application update worker.");return false;}joinable=true;return true;
    }
};
ApplicationUpdater::ApplicationUpdater():impl_(std::make_unique<Impl>()){}
ApplicationUpdater::~ApplicationUpdater(){shutdown();}
bool ApplicationUpdater::newer_version(const std::string& a,const std::string& b){return newer(version(a),version(b));}
bool ApplicationUpdater::configure(const std::string& root,const std::string& data,const std::string& source,const std::string& current){shutdown();auto& p=*impl_;p.root=normalize(root);p.data=normalize(data);p.storage=p.data+"/application-updates";p.source=source;p.local=loopback(source);p.state={};p.state.current_version=current;p.release={};p.configured=(source==feed_url||p.local)&&version(current).valid&&tree(p.root,false)&&tree(p.data,false);return p.configured;}
bool ApplicationUpdater::check(){return impl_->launch(false);}
bool ApplicationUpdater::install(){return impl_->launch(true);}
ApplicationUpdater::Snapshot ApplicationUpdater::snapshot()const{std::lock_guard<std::mutex> lock(impl_->mutex);return impl_->state;}
void ApplicationUpdater::shutdown(){if(!impl_)return;impl_->stop.store(true);if(impl_->joinable){pthread_join(impl_->thread,nullptr);impl_->joinable=false;}impl_->running.store(false);}
bool ApplicationUpdater::begin_restart(const std::string& language){
    auto& p=*impl_;const auto state=snapshot();if(state.phase!=Phase::ready&&state.phase!=Phase::failed)return false;
    auto same=[](std::wstring a,std::wstring b){std::transform(a.begin(),a.end(),a.begin(),std::towlower);std::transform(b.begin(),b.end(),b.begin(),std::towlower);return a==b;};
    if(!same(wide(p.root),wide(p.data))||!tree(p.root,false)||!ordinary(p.root+"/pixel-museum-install.json",false)){p.fail("Application updates require a completed Pixel Museum installation.");return false;}
    std::uint64_t bytes=0;if(!ordinary(p.archive(),false,&bytes)||bytes!=p.release.bytes){p.fail("The application update download could not be verified.");return false;}
    const auto helper=p.root+"/tools/windows-updater/Pixel-Museum-Updater.exe";
    if(!ordinary(helper,false)||!tree(p.storage+"/runner",true)){p.fail("The application updater is not available. Please reinstall Pixel Museum.");return false;}
    const auto pid=GetCurrentProcessId();FILETIME creation{},exit{},kernel{},user{};if(!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user)){p.fail("The application could not start its updater. Please try again.");return false;}
    const auto stem=std::to_string(pid)+"-"+std::to_string(GetTickCount64());const auto runner=p.storage+"/runner/updater-"+stem+".exe";const auto job=p.storage+"/runner/update-"+stem+".json";
    if(!CopyFileW(wide(helper).c_str(),wide(runner).c_str(),TRUE)){p.fail("The application could not start its updater. Please try again.");return false;}
    const std::string lang=(language=="en"||language=="it"||language=="es"||language=="fr"||language=="de")?language:"en";
    Json descriptor={{"schema_version",1},{"application_id","pixel-museum"},{"platform","windows-x64"},{"version",p.release.version},{"application_root",p.root},{"archive",p.archive()},{"archive_sha256",p.release.sha},{"archive_bytes",p.release.bytes},{"unpacked_bytes",p.release.expanded},{"parent_pid",pid},{"parent_creation_time",(std::uint64_t(creation.dwHighDateTime)<<32)|creation.dwLowDateTime},{"language",lang},{"result_path",p.storage+"/result.json"},{"restart",true}};
    if(!hui::save::write_atomic(job,descriptor.dump(2)).empty()){DeleteFileW(wide(runner).c_str());p.fail("The application could not start its updater. Please try again.");return false;}
    const auto wrunner=wide(runner),wroot=wide(p.root);std::wstring command=L"\""+wrunner+L"\" --apply-update \""+wide(job)+L"\"";STARTUPINFOW startup{};startup.cb=sizeof(startup);startup.dwFlags=STARTF_USESHOWWINDOW;startup.wShowWindow=SW_HIDE;PROCESS_INFORMATION child{};
    if(!CreateProcessW(wrunner.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW|CREATE_UNICODE_ENVIRONMENT,nullptr,wroot.c_str(),&startup,&child)){p.fail("The application could not start its updater. Please try again.");return false;}
    CloseHandle(child.hThread);CloseHandle(child.hProcess);return true;
}
}
#endif
