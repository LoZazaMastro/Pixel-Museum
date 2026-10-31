// Pixel Museum - pinned downloads and safe USTAR staging, never into /app0.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_installer.hpp"
#include "museum/collection_sha256.hpp"
#include "platform/media.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <curl/curl.h>
#if defined(__FreeBSD__)
#include "platform/ps5/console_curl.h"
#endif
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cerrno>
#include <cctype>
#include <fcntl.h>
#include <dirent.h>
#include <mutex>
#include <set>
#include <string_view>
#include <thread>
#include <sys/stat.h>
#include <unistd.h>
#if __has_include(<sys/statvfs.h>)
#include <sys/statvfs.h>
#pragma weak statvfs
#define PM_COLLECTION_STATVFS 1
#endif
namespace museum {
namespace {
using Json=nlohmann::json;
constexpr std::uint64_t max_pack=900ull*1024*1024;
std::string parent(const std::string& path){const auto at=path.find_last_of('/');return at==std::string::npos?".":at==0?"/":path.substr(0,at);}
bool safe_relative(const std::string& path){
    if(path.empty()||path.size()>240||path.front()=='/'||path.back()=='/'||path.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-")!=std::string::npos)return false;
    std::size_t begin=0;while(begin<path.size()){auto end=path.find('/',begin);if(end==std::string::npos)end=path.size();const auto part=path.substr(begin,end-begin);if(part.empty()||part=="."||part=="..")return false;begin=end+1;}return true;
}
bool component(const std::string& value){return !value.empty()&&value.size()<=64&&value!="."&&value!=".."&&value.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")==std::string::npos;}
bool hex_sha(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
std::string storage_error(const char*operation,int code=errno){return(code==ENOSPC||code==EDQUOT)?"Not enough free space in collection storage":std::string(operation)+": collection storage error ("+std::strerror(code)+")";}
bool regular(const std::string& path,std::uint64_t* bytes=nullptr){struct stat st{};if(lstat(path.c_str(),&st)||!S_ISREG(st.st_mode))return false;if(bytes)*bytes=st.st_size;return true;}
bool directory(const std::string& path){struct stat st{};return lstat(path.c_str(),&st)==0&&S_ISDIR(st.st_mode);}
bool mkdirs(const std::string& path){
    if(path.empty()||path.front()!='/')return false;
    std::size_t at=1;for(;;){at=path.find('/',at);const auto part=at==std::string::npos?path:path.substr(0,at);if(!part.empty()&&!directory(part)){if(mkdir(part.c_str(),0700)||!directory(part))return false;}if(at==std::string::npos)break;++at;}return true;
}
bool sync_directory(const std::string& path){int fd=open(path.c_str(),O_RDONLY|O_DIRECTORY);if(fd<0)return false;const bool ok=fsync(fd)==0;close(fd);return ok;}
std::uint64_t staged_bytes(const std::string&path){
    if(!directory(path))return 0;DIR*dir=opendir(path.c_str());if(!dir)return 0;std::uint64_t bytes=0;
    while(auto*entry=readdir(dir)){const std::string name=entry->d_name;if(name=="."||name=="..")continue;const auto file=path+"/"+name;struct stat st{};if(lstat(file.c_str(),&st))continue;if(S_ISREG(st.st_mode))bytes+=st.st_size;else if(S_ISDIR(st.st_mode))bytes+=staged_bytes(file);}closedir(dir);return bytes;
}
bool available_bytes(const std::string&path,std::uint64_t&bytes){
#if defined(PM_COLLECTION_STATVFS)
    if(!statvfs)return false;struct statvfs info{};if(statvfs(path.c_str(),&info))return false;const auto unit=info.f_frsize?info.f_frsize:info.f_bsize;if(!unit||std::uint64_t(info.f_bavail)>UINT64_MAX/unit)return false;bytes=std::uint64_t(info.f_bavail)*unit;return true;
#else
    (void)path;(void)bytes;return false;
#endif
}
std::string read_small(const std::string& path,std::size_t maximum=4u<<20){
    std::uint64_t size=0;if(!regular(path,&size)||size>maximum)return{};FILE* f=std::fopen(path.c_str(),"rb");if(!f)return{};std::string bytes(size,'\0');const bool ok=std::fread(bytes.data(),1,size,f)==size;std::fclose(f);return ok?bytes:std::string();
}
bool atomic_text(const std::string& path,const std::string& text){
    const auto tmp=path+".tmp";int fd=open(tmp.c_str(),O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0600);if(fd<0)return false;
    std::size_t pos=0;bool ok=true;while(pos<text.size()){const auto n=write(fd,text.data()+pos,text.size()-pos);if(n<=0){ok=false;break;}pos+=n;}if(fsync(fd))ok=false;if(close(fd))ok=false;
    if(!ok||std::rename(tmp.c_str(),path.c_str()))return false;
    return sync_directory(parent(path));
}
std::string digest_text(const std::string& value){CollectionSha256 hash;hash.update(value.data(),value.size());return hash.finish();}
bool octal(const char* p,std::size_t length,std::uint64_t& value){
    value=0;std::size_t n=0;while(n<length&&p[n]==' ')++n;bool ended=false;for(;n<length;++n){const unsigned char c=p[n];if(c==0||c==' '){ended=true;continue;}if(ended||c<'0'||c>'7'||value>(UINT64_MAX-7)/8)return false;value=value*8+c-'0';}return true;
}
std::string field(const char* p,std::size_t n){const auto end=static_cast<const char*>(std::memchr(p,0,n));return std::string(p,end?std::size_t(end-p):n);}
}
struct CollectionInstaller::Impl {
    struct Pack {std::string id,url,sha;std::uint64_t bytes=0,file_count=0,expanded_bytes=0;};
    mutable std::mutex mutex;
    std::mutex lifecycle;
    Status status;
    std::vector<Pack> packs;
    std::string base,stage_root,ready_root,bundled,manifest_sha,image_manifest_sha,active_root;
    bool configured=false,allow_http=false;
    std::atomic<int> command{0}; // 0 run,1 pause,2 cancel,3 shutdown.
    std::atomic<bool> running{false};
    std::thread worker;
    std::uint64_t completed=0;
    std::uint64_t expanded_bytes=0,maximum_pack=0;
    void update(Phase phase,const std::string& stage,const std::string& error={}){std::lock_guard<std::mutex>lock(mutex);status.phase=phase;status.stage=stage;status.error=error;status.bytes_per_second=0;}
    bool interrupted()const{return command.load(std::memory_order_acquire)!=0;}
    void interrupted_status(){const auto c=command.load();update(c==1?Phase::paused:Phase::cancelled,c==1?"Paused":"Stopped");}
    std::string marker(std::size_t n,const std::string&root={})const{return(root.empty()?stage_root:root)+"/.pack-"+std::to_string(n)+".json";}
    bool pack_done(std::size_t index,const std::string&root={}){
        const auto&tree=root.empty()?stage_root:root;const auto raw=read_small(marker(index,tree));auto j=Json::parse(raw,nullptr,false);if(!j.is_object()||!j.contains("sha256")||!j["sha256"].is_string()||j["sha256"].get<std::string>()!=packs[index].sha||!j.contains("files")||!j["files"].is_array())return false;
        std::uint64_t expanded=0;std::set<std::string>paths;
        for(const auto& f:j["files"]){if(interrupted())return false;if(!f.is_object()||!f.contains("path")||!f["path"].is_string()||!f.contains("bytes")||!f["bytes"].is_number_unsigned())return false;const auto path=f["path"].get<std::string>();if(!safe_relative(path)||path.rfind("assets/images/",0)!=0||!paths.insert(path).second)return false;std::uint64_t size=0;if(!regular(tree+"/"+path,&size)||size!=f["bytes"].get<std::uint64_t>())return false;expanded+=size;if(path=="assets/images/manifest.json"&&!image_manifest_sha.empty()&&digest_text(read_small(tree+"/"+path,16u<<20))!=image_manifest_sha)return false;}
        return !j["files"].empty()&&(!packs[index].file_count||packs[index].file_count==paths.size())&&(!packs[index].expanded_bytes||packs[index].expanded_bytes==expanded);
    }
    bool ready_on_disk(){
        auto j=Json::parse(read_small(ready_root+"/.complete.json"),nullptr,false);if(!directory(ready_root)||!j.is_object()||!j.contains("manifest_sha256")||!j["manifest_sha256"].is_string()||j["manifest_sha256"].get<std::string>()!=manifest_sha||!j.contains("image_manifest_sha256")||!j["image_manifest_sha256"].is_string())return false;
        const auto expected=j["image_manifest_sha256"].get<std::string>();if(!hex_sha(expected)||digest_text(read_small(ready_root+"/assets/images/manifest.json",16u<<20))!=expected)return false;
        update(Phase::verifying,"Checking downloaded collection");for(std::size_t n=0;n<packs.size();++n)if(!pack_done(n,ready_root))return false;return true;
    }
    bool hash_pack(const Pack& pack,const std::string& path){
        update(Phase::verifying,"Verifying "+pack.id);FILE* file=std::fopen(path.c_str(),"rb");if(!file)return false;CollectionSha256 hash;bool ok=true;std::array<unsigned char,65536>buffer{};std::uint64_t bytes=0;
        while(ok&&!interrupted()){const auto n=std::fread(buffer.data(),1,buffer.size(),file);bytes+=n;if(n)hash.update(buffer.data(),n);if(n<buffer.size()){if(std::ferror(file))ok=false;break;}}
        std::string sha;if(ok&&!interrupted())sha=hash.finish();std::fclose(file);return ok&&bytes==pack.bytes&&sha==pack.sha;
    }
    struct Transfer {Impl* owner;FILE* file;const Pack* pack;std::uint64_t offset,written=0;long response=0;bool valid_range=false,range_seen=false,restart=false;std::chrono::steady_clock::time_point start;int storage_errno=0;};
    static std::size_t header(char* p,std::size_t size,std::size_t count,void* data){
        auto&t=*static_cast<Transfer*>(data);const auto bytes=size*count;std::string line(p,bytes);
        if(line.rfind("HTTP/",0)==0){const auto at=line.find(' ');t.response=at==std::string::npos?0:std::strtol(line.c_str()+at+1,nullptr,10);t.valid_range=false;t.range_seen=false;}
        std::string lower=line;std::transform(lower.begin(),lower.end(),lower.begin(),[](unsigned char c){return char(std::tolower(c));});
        if(lower.rfind("content-range:",0)==0){unsigned long long begin=0,end=0,total=0;t.range_seen=true;t.valid_range=std::sscanf(lower.c_str(),"content-range: bytes %llu-%llu/%llu",&begin,&end,&total)==3&&begin==t.offset&&end>=begin&&total==t.pack->bytes;}
        return bytes;
    }
    static std::size_t write_body(char*p,std::size_t size,std::size_t count,void*data){
        auto&t=*static_cast<Transfer*>(data);const auto bytes=size*count;
        if(t.owner->interrupted())return 0;
        if(t.response>=300&&t.response<400)return bytes; // Redirect bodies are not pack data.
        if(t.offset&&(t.response==200||t.response==416)){t.restart=true;return 0;}
        if((t.offset&&(t.response!=206||!t.valid_range))||(!t.offset&&t.response!=200&&!(t.response==206&&t.valid_range)))return 0;
        if(bytes>t.pack->bytes-t.offset-t.written)return 0;
        const auto written=std::fwrite(p,1,bytes,t.file);if(written!=bytes)t.storage_errno=errno;t.written+=written;t.owner->progress(t);return written;
    }
    void progress(const Transfer&t){
        const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t.start).count();std::lock_guard<std::mutex>lock(mutex);status.downloaded_bytes=completed+t.offset+t.written;status.bytes_per_second=seconds>.05?double(t.written)/seconds:0;
    }
    static int progress_callback(void*data,curl_off_t,curl_off_t,curl_off_t,curl_off_t){return static_cast<Transfer*>(data)->owner->interrupted()?1:0;}
    bool download(const Pack&pack,const std::string&path,std::string&error){
        for(unsigned attempt=0;attempt<2&&!interrupted();++attempt){
            std::uint64_t offset=0;const bool exists=regular(path,&offset);if(exists&&offset>pack.bytes){std::remove(path.c_str());offset=0;}if(offset==pack.bytes)return true;
            int fd=open(path.c_str(),O_WRONLY|O_CREAT|O_NOFOLLOW|(offset?O_APPEND:O_TRUNC),0600);if(fd<0){error=storage_error("Cannot write partial pack");return false;}FILE* file=fdopen(fd,"ab");if(!file){const int code=errno;close(fd);error=storage_error("Cannot open partial pack",code);return false;}
            CURL*curl=curl_easy_init();if(!curl){std::fclose(file);error="Cannot initialize collection download";return false;}
#if defined(__FreeBSD__)
            console_curl_setup(curl);
#endif
            Transfer transfer{this,file,&pack,offset,0,0,false,false,false,std::chrono::steady_clock::now()};update(Phase::downloading,"Downloading "+pack.id);progress(transfer);
            curl_easy_setopt(curl,CURLOPT_URL,pack.url.c_str());curl_easy_setopt(curl,CURLOPT_NOSIGNAL,1L);curl_easy_setopt(curl,CURLOPT_FOLLOWLOCATION,1L);curl_easy_setopt(curl,CURLOPT_MAXREDIRS,5L);
            curl_easy_setopt(curl,CURLOPT_PROTOCOLS_STR,allow_http?"http,https":"https");curl_easy_setopt(curl,CURLOPT_REDIR_PROTOCOLS_STR,allow_http?"http,https":"https");
            curl_easy_setopt(curl,CURLOPT_CONNECTTIMEOUT,10L);curl_easy_setopt(curl,CURLOPT_LOW_SPEED_LIMIT,1024L);curl_easy_setopt(curl,CURLOPT_LOW_SPEED_TIME,20L);curl_easy_setopt(curl,CURLOPT_USERAGENT,"PixelMuseum-Collection/1");
            curl_easy_setopt(curl,CURLOPT_HTTP_CONTENT_DECODING,0L);curl_easy_setopt(curl,CURLOPT_HEADERFUNCTION,header);curl_easy_setopt(curl,CURLOPT_HEADERDATA,&transfer);curl_easy_setopt(curl,CURLOPT_WRITEFUNCTION,write_body);curl_easy_setopt(curl,CURLOPT_WRITEDATA,&transfer);
            curl_easy_setopt(curl,CURLOPT_NOPROGRESS,0L);curl_easy_setopt(curl,CURLOPT_XFERINFOFUNCTION,progress_callback);curl_easy_setopt(curl,CURLOPT_XFERINFODATA,&transfer);
            if(offset)curl_easy_setopt(curl,CURLOPT_RESUME_FROM_LARGE,curl_off_t(offset));
            const auto result=curl_easy_perform(curl);long response=0;curl_easy_getinfo(curl,CURLINFO_RESPONSE_CODE,&response);curl_easy_cleanup(curl);
            int storage_errno=transfer.storage_errno;bool durable=std::fflush(file)==0;if(!durable)storage_errno=errno;if(fsync(fd)){storage_errno=errno;durable=false;}if(std::fclose(file)){storage_errno=errno;durable=false;}
            if(interrupted())return false;
            if(offset&&(transfer.restart||result==CURLE_RANGE_ERROR||response==416)){if(std::remove(path.c_str())){error="Cannot reset unsupported range download";return false;}continue;}
            if(result!=CURLE_OK||!durable||offset+transfer.written!=pack.bytes){error=storage_errno?storage_error("Cannot save collection pack",storage_errno):"Download interrupted: "+std::string(curl_easy_strerror(result));return false;}
            return true;
        }
        if(!interrupted())error="Server does not provide a usable complete pack";return false;
    }
    bool extract(const Pack&pack,const std::string&path,std::size_t index,std::string&error){
        update(Phase::extracting,"Installing "+pack.id);FILE*tar=std::fopen(path.c_str(),"rb");if(!tar){error="Cannot read verified pack";return false;}
        std::array<char,512>h{};std::array<char,65536>buffer{};Json files=Json::array();std::set<std::string>seen,dirty_dirs;std::uint64_t read=0,payload=0;bool ok=true,ended=false;
        while(ok&&!interrupted()){
            if(std::fread(h.data(),1,h.size(),tar)!=h.size()){error="Truncated USTAR header";ok=false;break;}read+=512;
            if(std::all_of(h.begin(),h.end(),[](char c){return c==0;})){
                if(std::fread(h.data(),1,h.size(),tar)!=h.size()||!std::all_of(h.begin(),h.end(),[](char c){return c==0;})){error="Invalid USTAR end marker";ok=false;break;}read+=512;
                while(read<pack.bytes){const auto n=std::min<std::uint64_t>(buffer.size(),pack.bytes-read);if(std::fread(buffer.data(),1,n,tar)!=n||!std::all_of(buffer.begin(),buffer.begin()+n,[](char c){return c==0;})){error="Unexpected trailing USTAR data";ok=false;break;}read+=n;}
                ended=true;break;
            }
            std::uint64_t checksum=0,bytes=0;unsigned sum=0;for(unsigned n=0;n<512;++n)sum+=n>=148&&n<156?' ':static_cast<unsigned char>(h[n]);
            if(std::memcmp(h.data()+257,"ustar",5)||h[262]!=0||std::memcmp(h.data()+263,"00",2)||!octal(h.data()+148,8,checksum)||sum!=checksum||!octal(h.data()+124,12,bytes)){error="Invalid USTAR header/checksum";ok=false;break;}
            auto name=field(h.data(),100);const auto prefix=field(h.data()+345,155);if(!prefix.empty())name=prefix+"/"+name;const char type=h[156];if(type=='5'&&!name.empty()&&name.back()=='/')name.pop_back();
            const bool allowed=name.rfind("assets/images/",0)==0||(type=='5'&&(name=="assets"||name=="assets/images"));
            if(!safe_relative(name)||!allowed||name.find("/.pack-")!=std::string::npos||(type!=0&&type!='0'&&type!='5')||bytes>pack.bytes-read||payload+bytes>pack.bytes){error="Unsafe or unsupported collection archive entry";ok=false;break;}
            if(type=='5'){if(bytes||!mkdirs(stage_root+"/"+name)){error="Cannot create collection directory";ok=false;}continue;}
            if(!seen.insert(name).second){error="Duplicate collection archive path";ok=false;break;}
            const auto destination=stage_root+"/"+name;const auto tmp=destination+".install-tmp";
            if(!mkdirs(parent(destination))){error="Unsafe collection directory";ok=false;break;}
            struct stat old{};if(lstat(destination.c_str(),&old)==0&&!S_ISREG(old.st_mode)){error="Non-regular collection destination";ok=false;break;}
            int fd=open(tmp.c_str(),O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0600);if(fd<0){error=storage_error("Cannot stage collection file");ok=false;break;}
            std::uint64_t remaining=bytes;while(remaining&&ok&&!interrupted()){
                const auto want=std::min<std::uint64_t>(remaining,buffer.size());const auto got=std::fread(buffer.data(),1,want,tar);if(got!=want){error="Truncated collection file";ok=false;break;}
                std::size_t pos=0;while(pos<got){const auto n=write(fd,buffer.data()+pos,got-pos);if(n<=0){error=storage_error("Cannot save collection file");ok=false;break;}pos+=n;}remaining-=got;read+=got;
            }
            if(fsync(fd)){error=storage_error("Cannot flush collection file");ok=false;}if(close(fd)){error=storage_error("Cannot close collection file");ok=false;}
            if(!ok||interrupted()){std::remove(tmp.c_str());break;}
            if(std::rename(tmp.c_str(),destination.c_str())){error=storage_error("Cannot commit collection file");ok=false;break;}
            for(auto dir=parent(destination);dir.size()>=stage_root.size();dir=parent(dir)){dirty_dirs.insert(dir);if(dir==stage_root)break;}
            const auto padding=(512-bytes%512)%512;if(padding&&std::fread(buffer.data(),1,padding,tar)!=padding){error="Truncated USTAR padding";ok=false;break;}read+=padding;payload+=bytes;files.push_back({{"path",name},{"bytes",bytes}});
        }
        std::fclose(tar);if(interrupted())return false;if(!ok||!ended||files.empty()){if(error.empty())error="Empty or incomplete collection archive";return false;}
        if((pack.file_count&&pack.file_count!=files.size())||(pack.expanded_bytes&&pack.expanded_bytes!=payload)){error="Collection pack inventory does not match the bundled manifest";return false;}
        // Flush every installed file above, then each changed directory once,
        // deepest first, before the durable checkpoint permits deleting the tar.
        for(auto dir=dirty_dirs.rbegin();dir!=dirty_dirs.rend();++dir)if(!sync_directory(*dir)){error=storage_error("Cannot flush collection directory");return false;}
        if(!atomic_text(marker(index),Json({{"sha256",pack.sha},{"files",files}}).dump())){error=storage_error("Cannot commit pack checkpoint");return false;}return true;
    }
    void run(){
        struct Finish {Impl*p;~Finish(){p->running.store(false,std::memory_order_release);}}finish{this};
        if(!bundled.empty()){update(Phase::verifying,"Checking installed collection");if(media::packaged_images_complete(bundled)){if(interrupted()){interrupted_status();return;}std::lock_guard<std::mutex>lock(mutex);active_root.clear();status.phase=Phase::ready;status.stage="Bundled collection ready";status.downloaded_bytes=status.total_bytes;return;}}
        if(interrupted()){interrupted_status();return;}
        if(!mkdirs(base)||!mkdirs(base+"/downloads")){update(Phase::failed,"Installation unavailable","Collection storage is not writable");return;}
        if(ready_on_disk()){std::lock_guard<std::mutex>lock(mutex);active_root=ready_root;status.phase=Phase::ready;status.stage="Collection ready";status.downloaded_bytes=status.total_bytes;return;}
        if(interrupted()){interrupted_status();return;}
        // Repair an incomplete same-version tree in private staging. Preserve
        // its checkpoints and all good files; the worker re-fetches only bad packs.
        if(directory(ready_root)&&!directory(stage_root)&&std::rename(ready_root.c_str(),stage_root.c_str())){update(Phase::failed,"Installation failed",storage_error("Cannot stage collection repair"));return;}
        if(!mkdirs(stage_root)){update(Phase::failed,"Installation unavailable","Cannot create safe collection staging directory");return;}
        std::uint64_t free=0;const auto present=std::min(expanded_bytes,staged_bytes(stage_root+"/assets/images"));const auto required=expanded_bytes-present+maximum_pack;
        if(available_bytes(base,free)&&free<required){update(Phase::failed,"Not enough storage","Not enough free space in collection storage: "+std::to_string(required)+" additional bytes required");return;}
        static std::once_flag curl_once;static CURLcode curl_status=CURLE_FAILED_INIT;std::call_once(curl_once,[]{curl_status=curl_global_init(CURL_GLOBAL_DEFAULT);});if(curl_status!=CURLE_OK){update(Phase::failed,"Download unavailable","Cannot initialize network");return;}
        completed=0;
        for(std::size_t n=0;n<packs.size();++n){
            {std::lock_guard<std::mutex>lock(mutex);status.pack_index=n;status.downloaded_bytes=completed;}
            if(interrupted()){interrupted_status();return;}const auto&pack=packs[n];const auto path=base+"/downloads/"+pack.sha+".tar.part";
            if(pack_done(n)){completed+=pack.bytes;continue;}
            std::string error;if(!download(pack,path,error)){if(interrupted())interrupted_status();else update(Phase::failed,"Download failed",error);return;}
            if(!hash_pack(pack,path)){if(interrupted())interrupted_status();else{std::remove(path.c_str());update(Phase::failed,"Verification failed","Collection pack checksum does not match the bundled manifest");}return;}
            if(!extract(pack,path,n,error)){if(interrupted())interrupted_status();else update(Phase::failed,"Installation failed",error);return;}
            completed+=pack.bytes;std::remove(path.c_str());
        }
        if(interrupted()){interrupted_status();return;}
        if(!regular(stage_root+"/assets/images/manifest.json")){update(Phase::failed,"Installation failed","Collection image manifest is missing");return;}
        if(!image_manifest_sha.empty()){
            Pack image_index;image_index.id="image index";image_index.sha=image_manifest_sha;regular(stage_root+"/assets/images/manifest.json",&image_index.bytes);
            if(!hash_pack(image_index,stage_root+"/assets/images/manifest.json")){if(interrupted())interrupted_status();else update(Phase::failed,"Verification failed","Collection image manifest checksum does not match");return;}
        }
        const auto index_sha=digest_text(read_small(stage_root+"/assets/images/manifest.json",16u<<20));
        if(!atomic_text(stage_root+"/.complete.json",Json({{"schema_version",1},{"manifest_sha256",manifest_sha},{"image_manifest_sha256",index_sha},{"pack_count",packs.size()}}).dump())||std::rename(stage_root.c_str(),ready_root.c_str())||!sync_directory(base)){update(Phase::failed,"Installation failed",storage_error("Cannot activate completed collection"));return;}
        std::lock_guard<std::mutex>lock(mutex);active_root=ready_root;status.phase=Phase::ready;status.stage="Collection ready";status.downloaded_bytes=status.total_bytes;status.bytes_per_second=0;
    }
};
CollectionInstaller::CollectionInstaller():impl_(new Impl){}
CollectionInstaller::~CollectionInstaller(){shutdown();}
bool CollectionInstaller::configure(const std::string& manifest_path,const std::string& data_directory,const std::string& bundled_root,bool allow_http_for_tests){
    shutdown();auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);std::lock_guard<std::mutex>lock(p.mutex);p.status={};p.configured=false;p.active_root.clear();p.packs.clear();
    const auto raw=read_small(manifest_path,1u<<20);if(raw.empty())return false;auto j=Json::parse(raw,nullptr,false);
    const auto reject=[&](const char*why){p.status.phase=Phase::failed;p.status.error=why;p.status.stage="Invalid collection manifest";return false;};
    if(data_directory.empty()||data_directory.front()!='/'||data_directory=="/app0"||data_directory.rfind("/app0/",0)==0||data_directory.find("..")!=std::string::npos||data_directory.find('\\')!=std::string::npos)return reject("Persistent writable collection directory required");
    if(!j.is_object()||!j.contains("schema_version")||!j["schema_version"].is_number_integer()||j["schema_version"].get<int>()!=1||!j.contains("collection_id")||!j["collection_id"].is_string()||!component(j["collection_id"].get<std::string>())||!j.contains("packs")||!j["packs"].is_array()||j["packs"].empty()||j["packs"].size()>256)return reject("Invalid collection manifest schema");
    std::set<std::string>ids;p.maximum_pack=0;p.expanded_bytes=0;
    for(const auto&row:j["packs"]){
        for(const char*key:{"id","url","sha256","format"})if(!row.is_object()||!row.contains(key)||!row[key].is_string())return reject("Invalid pack fields");
        Impl::Pack pack;pack.id=row["id"].get<std::string>();pack.url=row["url"].get<std::string>();pack.sha=row["sha256"].get<std::string>();if(!component(pack.id)||!ids.insert(pack.id).second||!hex_sha(pack.sha)||row["format"].get<std::string>()!="tar"||!row.contains("bytes")||!row["bytes"].is_number_unsigned())return reject("Invalid pinned collection pack");
        pack.bytes=row["bytes"].get<std::uint64_t>();if(pack.bytes<1024||pack.bytes>max_pack||pack.bytes%512||!(pack.url.rfind("https://",0)==0||(allow_http_for_tests&&pack.url.rfind("http://",0)==0)))return reject("Unsafe pack URL, size or format");
        for(const char*key:{"file_count","expanded_bytes"})if(row.contains(key)&&!row[key].is_number_unsigned())return reject("Invalid pack inventory fields");
        if(row.contains("file_count"))pack.file_count=row["file_count"].get<std::uint64_t>();if(row.contains("expanded_bytes"))pack.expanded_bytes=row["expanded_bytes"].get<std::uint64_t>();if(pack.file_count>1000000||pack.expanded_bytes>pack.bytes)return reject("Invalid pack inventory size");
        p.status.total_bytes+=pack.bytes;p.maximum_pack=std::max(p.maximum_pack,pack.bytes);p.packs.push_back(std::move(pack));
    }
    p.expanded_bytes=p.status.total_bytes;if(j.contains("expanded_bytes")){if(!j["expanded_bytes"].is_number_unsigned()||!j["expanded_bytes"].get<std::uint64_t>()||j["expanded_bytes"].get<std::uint64_t>()>p.status.total_bytes)return reject("Invalid expanded collection size");p.expanded_bytes=j["expanded_bytes"].get<std::uint64_t>();}
    p.image_manifest_sha.clear();if(j.contains("image_manifest_sha256")){if(!j["image_manifest_sha256"].is_string()||!hex_sha(j["image_manifest_sha256"].get<std::string>()))return reject("Invalid image manifest checksum");p.image_manifest_sha=j["image_manifest_sha256"].get<std::string>();}
    p.manifest_sha=digest_text(raw);if(p.manifest_sha.empty())return reject("Cannot identify bundled manifest");p.base=data_directory+"/collection";const auto suffix=j["collection_id"].get<std::string>()+"-"+p.manifest_sha.substr(0,24);p.stage_root=p.base+"/.stage-"+suffix;p.ready_root=p.base+"/"+suffix;p.bundled=bundled_root;p.allow_http=allow_http_for_tests;p.configured=true;p.status.phase=Phase::idle;p.status.pack_count=p.packs.size();p.status.stage="Collection installation required";return true;
}
bool CollectionInstaller::start(){auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);if(!p.configured||p.running.load())return false;if(p.worker.joinable())p.worker.join();{std::lock_guard<std::mutex>lock(p.mutex);if(p.status.phase==Phase::ready)return true;p.status.error.clear();}p.command.store(0);p.running.store(true);p.worker=std::thread([&p]{p.run();});return true;}
bool CollectionInstaller::retry(){return start();}
void CollectionInstaller::pause(){impl_->command.store(1,std::memory_order_release);}
void CollectionInstaller::cancel(){impl_->command.store(2,std::memory_order_release);}
void CollectionInstaller::shutdown(){if(!impl_)return;auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);p.command.store(3,std::memory_order_release);if(p.worker.joinable())p.worker.join();}
CollectionInstaller::Status CollectionInstaller::snapshot()const{std::lock_guard<std::mutex>lock(impl_->mutex);return impl_->status;}
bool CollectionInstaller::is_ready()const{return snapshot().phase==Phase::ready;}
std::string CollectionInstaller::cache_root()const{std::lock_guard<std::mutex>lock(impl_->mutex);return impl_->status.phase==Phase::ready?impl_->active_root:std::string();}
}
