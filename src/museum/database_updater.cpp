// Immutable, hash-verified editorial snapshots, activated only on the next launch.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/database_updater.hpp"
#include "museum/collection_sha256.hpp"
#include "core/save_file.hpp"
#include "yt/http.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <atomic>
#include <array>
#include <cerrno>
#include <chrono>
#include <cstring>
#include <cstdio>
#include <fcntl.h>
#include <mutex>
#include <pthread.h>
#include <set>
#include <sys/stat.h>
#include <unistd.h>
#if defined(__FreeBSD__)
#include "platform/ps5/system.hpp"
#endif
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#ifndef O_BINARY
#define O_BINARY 0
#endif
#endif

namespace museum {
namespace {
using Json = nlohmann::json;
constexpr std::uint64_t max_total = 4ull << 30;
constexpr std::size_t download_workers = 4;
constexpr std::size_t worker_stack = 3u << 20;
using Clock = std::chrono::steady_clock;
void database_trace(const char* step,const std::string& detail={},int code=0) {
#if defined(__FreeBSD__)
    hui::sys::log("[Museum] database %s / %s / code=%d (%s)",step,detail.c_str(),code,code?std::strerror(code):"ok");
#else
    (void)step;(void)detail;(void)code;
#endif
}
struct File { std::string path, url, sha; std::uint64_t bytes = 0; };
struct Manifest {
    std::uint64_t revision = 0;
    std::string version;
    std::map<std::string, std::string> notes;
    std::vector<File> files;
};
std::string normalize(std::string p) {
    std::replace(p.begin(), p.end(), '\\', '/');
    while(p.size()>1 && p.back()=='/')p.pop_back();
    return p;
}
bool hash_text(const std::string& s) {
    return s.size()==64 && std::all_of(s.begin(),s.end(),[](char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f');});
}
bool allowed_path(const std::string& s) {
    if(s.empty()||s.size()>512||s.front()=='/'||s.back()=='/'||s.find('\\')!=std::string::npos||s.find(':')!=std::string::npos||s.find('\0')!=std::string::npos)return false;
    std::size_t at=0;
    while(at<s.size()){
        const auto end=s.find('/',at);const auto part=s.substr(at,end==std::string::npos?end:end-at);
        if(part.empty()||part=="."||part=="..")return false;
        at=end==std::string::npos?s.size():end+1;
    }
    if(s=="content/catalog.json"||s=="content/human-history.json"||s=="content/culture-memories.json"||s=="content/credits.json"||s=="content/collection-image-supplements.json")return true;
    for(const char* lang:{"en","it","es","fr","de"})for(const char* group:{"locales","ui-locales"})if(s==std::string("content/")+group+"/"+lang+".json")return true;
    const auto dot=s.find_last_of('.');const auto ext=dot==std::string::npos?std::string():s.substr(dot);
    if(s.rfind("assets/image-supplements/",0)==0)return ext==".png"||ext==".jpg"||ext==".jpeg"||ext==".webp";
    return s.rfind("assets/culture-audio/",0)==0&&ext==".wav";
}
bool loopback(const std::string& s) { return s.rfind("http://127.0.0.1:",0)==0||s.rfind("http://localhost:",0)==0; }
bool trusted_url(const std::string& s,bool local) {
    return s.size()<4096&&s.find('\0')==std::string::npos&&(s.rfind("https://github.com/LoZazaMastro/Pixel-Museum/releases/download/",0)==0||(local&&loopback(s)));
}
bool parse_manifest(const Json& j,Manifest& m,bool local) {
    if(!j.is_object()||!j.contains("schema_version")||!j["schema_version"].is_number_unsigned()||j["schema_version"].get<std::uint64_t>()!=1||!j.contains("database_id")||!j["database_id"].is_string()||j["database_id"].get<std::string>()!="pixel-museum"||!j.contains("revision")||!j["revision"].is_number_unsigned()||!j.contains("version")||!j["version"].is_string()||!j.contains("files")||!j["files"].is_array()||j["files"].size()>16384)return false;
    if(j.contains("minimum_reader")&&(!j["minimum_reader"].is_number_unsigned()||j["minimum_reader"].get<std::uint64_t>()>1))return false;
    m.revision=j["revision"].get<std::uint64_t>();m.version=j["version"].get<std::string>();
    if(!m.revision||m.version.empty()||m.version.size()>80)return false;
    if(j.contains("notes")){
        if(!j["notes"].is_object())return false;
        for(const char* lang:{"en","it","es","fr","de"})if(j["notes"].contains(lang)){
            if(!j["notes"][lang].is_string())return false;
            auto text=j["notes"][lang].get<std::string>();if(text.size()>4096)return false;m.notes[lang]=std::move(text);
        }
    }
    std::set<std::string> paths;std::uint64_t total=0;
    for(const auto& row:j["files"]){
        if(!row.is_object())return false;
        for(const char* key:{"path","url","sha256"})if(!row.contains(key)||!row[key].is_string())return false;
        if(!row.contains("bytes")||!row["bytes"].is_number_unsigned())return false;
        File f{row["path"].get<std::string>(),row["url"].get<std::string>(),row["sha256"].get<std::string>(),row["bytes"].get<std::uint64_t>()};
        if(!allowed_path(f.path)||!paths.insert(f.path).second||!trusted_url(f.url,local)||!hash_text(f.sha)||f.bytes==0||f.bytes>(64u<<20)||total>max_total-f.bytes)return false;
        total+=f.bytes;m.files.push_back(std::move(f));
    }
    return true;
}
Json manifest_json(const Manifest& m) {
    Json j={{"schema_version",1},{"database_id","pixel-museum"},{"minimum_reader",1},{"revision",m.revision},{"version",m.version},{"notes",m.notes},{"files",Json::array()}};
    for(const auto& f:m.files)j["files"].push_back({{"path",f.path},{"url",f.url},{"sha256",f.sha},{"bytes",f.bytes}});
    return j;
}
#if defined(_WIN32)
std::wstring wide(const std::string& p) {
    const int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,p.data(),int(p.size()),nullptr,0);if(n<=0)return {};
    std::wstring s(std::size_t(n),L'\0');MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,p.data(),int(p.size()),s.data(),n);return s;
}
#endif
bool ordinary(const std::string& path,bool directory,std::uint64_t* bytes=nullptr) {
#if defined(_WIN32)
    const auto w=wide(path);if(w.empty())return false;
    const DWORD flags=GetFileAttributesW(w.c_str());
    if(flags==INVALID_FILE_ATTRIBUTES||(flags&FILE_ATTRIBUTE_REPARSE_POINT)||bool(flags&FILE_ATTRIBUTE_DIRECTORY)!=directory)return false;
#endif
    struct stat st{};
#if defined(_WIN32)
    if(::stat(path.c_str(),&st)!=0)return false;
#else
    // The PS5 SDK's lstat import is unreliable. Inspect a kernel-opened
    // descriptor, as collection storage already does; never follow a leaf
    // link or block on a FIFO while checking an ordinary file/directory.
    const int fd=::open(path.c_str(),O_RDONLY|O_NOFOLLOW|O_NONBLOCK|(directory?O_DIRECTORY:0));
    if(fd<0)return false;
    const int result=::fstat(fd,&st);const int code=errno;::close(fd);
    if(result!=0){errno=code;return false;}
#endif
    if(directory?!S_ISDIR(st.st_mode):!S_ISREG(st.st_mode)){errno=directory?ENOTDIR:EINVAL;return false;}
    if(bytes)*bytes=std::uint64_t(st.st_size);return true;
}
bool mkdirs(const std::string& path) {
    const auto p=normalize(path);
    for(std::size_t i=1;i<=p.size();++i)if(i==p.size()||p[i]=='/'){
        auto part=p.substr(0,i);if(part.size()==2&&part[1]==':')continue;
        if(!ordinary(part,true)){
            if(::mkdir(part.c_str(),0755)!=0&&errno!=EEXIST){const int code=errno;database_trace("mkdir failed",part,code);errno=code;return false;}
            if(!ordinary(part,true)){const int code=errno;database_trace("directory check failed",part,code);errno=code;return false;}
        }
    }
    return true;
}
bool digest_file(const std::string& path,const File& f,const std::atomic<bool>& stop) {
    std::uint64_t size=0;if(!ordinary(path,false,&size)||size!=f.bytes)return false;
    FILE* file=std::fopen(path.c_str(),"rb");if(!file)return false;
    std::array<unsigned char,256u<<10> buffer{};CollectionSha256 hash;std::uint64_t count=0;
    while(!stop.load(std::memory_order_relaxed)){
        const auto n=std::fread(buffer.data(),1,buffer.size(),file);count+=n;hash.update(buffer.data(),n);
        if(n<buffer.size())break;
    }
    const bool ok=!stop.load()&&!std::ferror(file)&&count==f.bytes;std::fclose(file);
    return ok&&hash.finish()==f.sha;
}
bool json_file(const std::string& path,const File& f) {
    if(f.path.size()<5||f.path.substr(f.path.size()-5)!=".json")return true;
    std::string text;if(!hui::save::read_file(path,&text,64u<<20))return false;
    const auto j=Json::parse(text,nullptr,false);if(!j.is_object())return false;
    if(f.path=="content/catalog.json"||f.path=="content/human-history.json"){
        if(!j.contains("entries")||!j["entries"].is_array())return false;
        return std::any_of(j["entries"].begin(),j["entries"].end(),[](const Json& row){
            if(!row.is_object()||!row.contains("id")||!row["id"].is_string()||row["id"].get<std::string>().empty()||!row.contains("title")||!row["title"].is_string()||row["title"].get<std::string>().empty()||!row.contains("year")||!row["year"].is_number_integer())return false;
            const auto& year=row["year"];return year>=1800&&year<=2100;
        });
    }
    if(f.path.rfind("content/locales/",0)==0||f.path.rfind("content/ui-locales/",0)==0){
        const auto locale=f.path.substr(f.path.size()-7,2);
        if(!j.contains("locale")||!j["locale"].is_string()||j["locale"].get<std::string>()!=locale)return false;
        const char* key=f.path.rfind("content/ui-locales/",0)==0?"strings":"entries";
        return j.contains(key)&&j[key].is_object();
    }
    if(f.path=="content/culture-memories.json")return j.contains("schema")&&j["schema"].is_number_unsigned()&&j.contains("cues")&&j["cues"].is_array();
    if(f.path=="content/collection-image-supplements.json")return j.contains("schema_version")&&j["schema_version"].is_number_unsigned()&&j["schema_version"]==1&&j.contains("images")&&j["images"].is_object()&&(!j.contains("metadata")||j["metadata"].is_object());
    return true;
}
}

struct DatabaseUpdater::Impl {
    mutable std::mutex mutex;
    Snapshot state;
    std::string root,storage,source;
    Manifest available;
    std::atomic<bool> stopping{false},running{false};
    pthread_t thread{};bool joinable=false,installing=false,local=false;
    void phase(Phase value,const std::string& error={}) {std::lock_guard<std::mutex> lock(mutex);state.phase=value;state.error=error;}
    void failed(const std::string& s) {database_trace("failed",s);phase(Phase::failed,s);}
    std::string blob(const File& f)const{return storage+"/blobs/"+f.sha;}
    void check_feed(){
        yt::http::Request request;request.url=source;request.max_bytes=4u<<20;request.timeout_s=15;
        request.cancelled=[this]{return stopping.load();};
        request.headers={{"Cache-Control","no-cache"}};
        const auto response=yt::http::perform(request);
        database_trace("feed result","status="+std::to_string(response.status)+" transport="+response.error+" bytes="+std::to_string(response.body.size()));
        if(stopping.load())return;
        if(!response.http_ok()){failed("Cannot check the content database. Please try again when connected.");return;}
        Manifest m;const auto j=Json::parse(response.body,nullptr,false);
        if(!parse_manifest(j,m,local)){failed("The content update manifest is invalid or needs a newer application.");return;}
        std::lock_guard<std::mutex> lock(mutex);
        state.revision=m.revision;state.version=m.version;state.notes=m.notes;state.total_bytes=0;state.downloaded_bytes=0;
        for(const auto& f:m.files)state.total_bytes+=f.bytes;
        if(m.revision<=state.current_revision){state.phase=Phase::current;return;}
        if(m.files.empty()){state.phase=Phase::failed;state.error="The new database has no content files.";return;}
        available=std::move(m);state.phase=Phase::available;
    }
    const char* fetch_file(const File& f,const std::atomic<const char*>& batch_error){
        const auto target=blob(f);
        const auto cancelled=[&]{return stopping.load()||batch_error.load()!=nullptr;};
        if(cancelled())return nullptr;
        const auto part=target+".part";
        std::uint64_t ignored=0;if(ordinary(part,false,&ignored)){::unlink(part.c_str());}
        const int fd=::open(part.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_BINARY,0644);
        if(fd<0){database_trace("file create failed",part,errno);return "Cannot create the content update file. Check free space and folder permissions.";}
        FILE* file=::fdopen(fd,"wb");if(!file){const int code=errno;::close(fd);::unlink(part.c_str());database_trace("fdopen failed",part,code);return "Cannot open the content update file.";}
        std::array<char,1u<<20> buffer;std::setvbuf(file,buffer.data(),_IOFBF,buffer.size());
        CollectionSha256 hash;std::uint64_t received=0;bool io_ok=true;int io_error=0;
        yt::http::Request request;request.url=f.url;request.max_bytes=std::size_t(f.bytes+1);request.timeout_s=90;
        request.cancelled=cancelled;
        request.on_body=[&](std::string_view chunk){
            if(cancelled()||chunk.size()>f.bytes-received)return false;
            if(std::fwrite(chunk.data(),1,chunk.size(),file)!=chunk.size()){io_ok=false;io_error=errno;return false;}
            hash.update(chunk.data(),chunk.size());received+=chunk.size();
            std::lock_guard<std::mutex> lock(mutex);state.downloaded_bytes+=chunk.size();return true;
        };
        const auto response=yt::http::perform(request);
        if(std::fflush(file)!=0){io_ok=false;if(!io_error)io_error=errno;}
        const bool hash_ok=received==f.bytes&&hash.finish()==f.sha;
        const bool json_ok=!cancelled()&&response.http_ok()&&io_ok&&hash_ok&&json_file(part,f);
        if(json_ok&&::fsync(fd)!=0){io_ok=false;if(!io_error)io_error=errno;}
        if(std::fclose(file)!=0){io_ok=false;if(!io_error)io_error=errno;}
        if(!json_ok||!io_ok||cancelled()){
            ::unlink(part.c_str());
            if(cancelled())return nullptr;
            database_trace("file failed",f.path+" status="+std::to_string(response.status)+" transport="+response.error+" received="+std::to_string(received)+" expected="+std::to_string(f.bytes)+" hash="+std::to_string(hash_ok)+" json="+std::to_string(json_ok)+" io="+std::to_string(io_ok),io_error);
            return io_ok?"The content download could not be verified. Your current database is unchanged.":"There is not enough writable space for the content update.";
        }
#if defined(_WIN32)
        const auto src=wide(part),dst=wide(target);
        if(!MoveFileExW(src.c_str(),dst.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)){
#else
        if(::rename(part.c_str(),target.c_str())!=0){
#endif
            const int code=errno;database_trace("file commit failed",target,code);::unlink(part.c_str());return "Cannot finish the verified content file.";
        }
        return nullptr;
    }
    bool download_files(const std::vector<const File*>& pending){
        if(pending.empty())return !stopping.load();
        std::atomic<std::size_t> next{0};
        std::atomic<const char*> batch_error{nullptr};
        auto run=[&]{
            while(!stopping.load()&&!batch_error.load()){
                const auto index=next.fetch_add(1);
                if(index>=pending.size())return;
                if(const char* error=fetch_file(*pending[index],batch_error)){
                    const char* expected=nullptr;
                    batch_error.compare_exchange_strong(expected,error);
                }
            }
        };
        const auto start=Clock::now();
        std::array<pthread_t,download_workers-1> workers{};
        std::size_t started=0;
        pthread_attr_t attr;
        if(pthread_attr_init(&attr)==0){
            if(pthread_attr_setstacksize(&attr,worker_stack)==0){
                const auto worker=+[](void* data)->void*{(*static_cast<decltype(run)*>(data))();return nullptr;};
                const auto count=std::min(pending.size(),download_workers)-1;
                for(;started<count;++started){
                    const int code=pthread_create(&workers[started],&attr,worker,&run);
                    if(code){database_trace("parallel worker unavailable",{},code);break;}
                }
            }
            pthread_attr_destroy(&attr);
        }
        run();
        for(std::size_t i=0;i<started;++i)pthread_join(workers[i],nullptr);
        database_trace("transfer batch","files="+std::to_string(pending.size())+" workers="+std::to_string(started+1)+
                       " elapsed_ms="+std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-start).count()));
        if(stopping.load())return false;
        if(const char* error=batch_error.load()){failed(error);return false;}
        return true;
    }
    void install_files(){
        Manifest m;{std::lock_guard<std::mutex> lock(mutex);m=available;}
        if(m.files.empty()){failed("No content update is available.");return;}
        database_trace("storage",storage);
        if(!mkdirs(storage+"/blobs")){database_trace("storage prepare failed",storage+"/blobs",errno);failed("Cannot prepare the database update folder.");return;}
        // The feed is a cumulative snapshot. Download only missing blobs,
        // with one total for every change since the installed revision.
        const auto scan_start=Clock::now();
        std::vector<const File*> pending, aliases;
        std::set<std::string> missing;
        std::uint64_t total=0;
        for(const auto& f:m.files){
            if(stopping.load())return;
            if(missing.contains(f.sha)){aliases.push_back(&f);continue;}
            const auto path=blob(f);
            if(digest_file(path,f,stopping)&&json_file(path,f))continue;
            // A fresh bootstrap can already contain most of this cumulative
            // snapshot. Reuse its verified immutable file instead of fetching
            // and storing the same image again.
            const auto bundled=root+"/"+f.path;
            if(digest_file(bundled,f,stopping)&&json_file(bundled,f))continue;
            missing.insert(f.sha);pending.push_back(&f);total+=f.bytes;
        }
        {std::lock_guard<std::mutex> lock(mutex);state.total_bytes=total;}
        database_trace("cache scan","files="+std::to_string(m.files.size())+" pending="+std::to_string(pending.size())+
                       " bytes="+std::to_string(total)+" elapsed_ms="+
                       std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now()-scan_start).count()));
        if(!download_files(pending))return;
        for(const auto* f:aliases){
            if(stopping.load())return;
            if(!digest_file(blob(*f),*f,stopping)||!json_file(blob(*f),*f)){
                if(!stopping.load())failed("The content download could not be verified. Your current database is unchanged.");
                return;
            }
        }
        if(stopping.load())return;
        // One atomic pointer write commits the complete snapshot. Existing
        // catalogue/audio/image readers keep the previous immutable mapping.
        const auto activation_error=hui::save::write_atomic(storage+"/active.json",manifest_json(m).dump(2)+"\n");
        if(!activation_error.empty()){
            database_trace("activation failed",storage+"/active.json / "+activation_error);
            failed("Cannot activate the database update. Your current database is unchanged.");return;
        }
        database_trace("ready","revision="+std::to_string(m.revision)+" bytes="+std::to_string(total));phase(Phase::ready);
    }
    static void* entry(void* p){auto& self=*static_cast<Impl*>(p);if(self.installing)self.install_files();else self.check_feed();self.running.store(false);return nullptr;}
    bool launch(bool install){
        if(running.load())return false;
        if(joinable){pthread_join(thread,nullptr);joinable=false;}
        stopping.store(false);installing=install;
        {std::lock_guard<std::mutex> lock(mutex);if(install&&available.files.empty())return false;state.phase=install?Phase::downloading:Phase::checking;state.error.clear();state.downloaded_bytes=0;if(install)state.total_bytes=0;}
        pthread_attr_t attr;const int initialized=pthread_attr_init(&attr);if(initialized!=0){database_trace("worker attr failed",{},initialized);failed("Cannot start the content update worker.");return false;}
        const int stack=pthread_attr_setstacksize(&attr,worker_stack);if(stack){pthread_attr_destroy(&attr);database_trace("worker stack failed","3145728 bytes",stack);failed("Cannot start the content update worker.");return false;}running.store(true);
        const int result=pthread_create(&thread,&attr,&Impl::entry,this);pthread_attr_destroy(&attr);
        database_trace("worker start",install?"install / stack=3145728":"check / stack=3145728",result);
        if(result){running.store(false);failed("Cannot start the content update worker.");return false;}
        joinable=true;return true;
    }
};

DatabaseUpdater::DatabaseUpdater():impl_(std::make_unique<Impl>()){}
DatabaseUpdater::~DatabaseUpdater(){shutdown();}
bool DatabaseUpdater::configure(const std::string& application_root,const std::string& data_root,const std::string& source){
    shutdown();auto& p=*impl_;p.root=normalize(application_root);p.source=source;p.local=loopback(source);
#if defined(__FreeBSD__)
    (void)data_root;
    p.storage="/data/pixelmuseum/database";
#else
    p.storage=normalize(data_root)+"/database";
#endif
    hui::save::set_read_overlay({});p.state={};p.available={};
    if(source!=feed_url&&!p.local)return false;
    std::string bytes;
    if(hui::save::read_file(p.root+"/content/database-version.json",&bytes,4096)){
        const auto j=Json::parse(bytes,nullptr,false);
        if(j.is_object()&&j.contains("revision")&&j["revision"].is_number_unsigned())p.state.current_revision=std::max(bundled_revision,j["revision"].get<std::uint64_t>());
    }
    if(!ordinary(p.storage,true)||!ordinary(p.storage+"/blobs",true)||!hui::save::read_file(p.storage+"/active.json",&bytes,4u<<20))return true;
    Manifest m;if(!parse_manifest(Json::parse(bytes,nullptr,false),m,p.local)||m.files.empty()||m.revision<=p.state.current_revision)return true;
    std::map<std::string,std::string> overlay;
    p.stopping.store(false);
    for(const auto& f:m.files){
        auto path=p.blob(f);
        if(!digest_file(path,f,p.stopping)||!json_file(path,f)){
            path=p.root+"/"+f.path;
            if(!digest_file(path,f,p.stopping)||!json_file(path,f))return true;
        }
        overlay[p.root+"/"+f.path]=path;
    }
    hui::save::set_read_overlay(std::move(overlay));p.state.current_revision=m.revision;p.state.revision=m.revision;p.state.version=m.version;
    return true;
}
bool DatabaseUpdater::check(){return impl_->launch(false);}
bool DatabaseUpdater::install(){return impl_->launch(true);}
DatabaseUpdater::Snapshot DatabaseUpdater::snapshot()const{std::lock_guard<std::mutex> lock(impl_->mutex);return impl_->state;}
void DatabaseUpdater::shutdown(){if(!impl_)return;impl_->stopping.store(true);if(impl_->joinable){pthread_join(impl_->thread,nullptr);impl_->joinable=false;}impl_->running.store(false);}
}
