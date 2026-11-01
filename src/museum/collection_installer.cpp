// Pixel Museum - pinned downloads and safe USTAR staging, never into /app0.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_installer.hpp"
#include "museum/collection_sha256.hpp"
#include "museum/collection_download_rate.hpp"
#include "museum/collection_write_buffer.hpp"
#include "platform/media.hpp"
#if defined(__FreeBSD__) || defined(MUSEUM_COLLECTION_WRITER_TEST)
#include "platform/collection_writer.hpp"
#define PM_COLLECTION_WRITER 1
#endif
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <curl/curl.h>
#if defined(__FreeBSD__)
#include "platform/ps5/console_curl.h"
#include "platform/ps5/system.hpp"
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
#include <climits>
#include <fcntl.h>
#include <dirent.h>
#include <mutex>
#include <set>
#include <string_view>
#include <pthread.h>
#include <vector>
#include <sys/stat.h>
#include <unistd.h>
#if !defined(__FreeBSD__) && __has_include(<sys/statvfs.h>)
#include <sys/statvfs.h>
#pragma weak statvfs
#define PM_COLLECTION_STATVFS 1
#endif
namespace museum {
namespace {
using Json=nlohmann::json;
constexpr std::uint64_t max_pack=900ull*1024*1024;
constexpr std::size_t worker_stack_bytes=2u<<20;
using WorkerClock=std::chrono::steady_clock;
double elapsed_seconds(WorkerClock::time_point start){return std::chrono::duration<double>(WorkerClock::now()-start).count();}
void phase_receipt(const char*phase,const std::string&id,std::uint64_t bytes,double seconds){
#if defined(__FreeBSD__)
    hui::sys::log("[Museum] collection timing %s %s / %llu bytes / %.3fs / %.2f MiB/s",phase,id.c_str(),static_cast<unsigned long long>(bytes),seconds,seconds>0?double(bytes)/(1048576.*seconds):0.);
#else
    (void)phase;(void)id;(void)bytes;(void)seconds;
#endif
}
void worker_trace(const char*step,int code=0){
#if defined(__FreeBSD__)
    hui::sys::log("[Museum] collection worker %s / code=%d",step,code);
#else
    (void)step;(void)code;
#endif
}
std::string parent(const std::string& path){const auto at=path.find_last_of('/');return at==std::string::npos?".":at==0?"/":path.substr(0,at);}
bool safe_relative(const std::string& path){
    if(path.empty()||path.size()>240||path.front()=='/'||path.back()=='/'||path.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-")!=std::string::npos)return false;
    std::size_t begin=0;while(begin<path.size()){auto end=path.find('/',begin);if(end==std::string::npos)end=path.size();const auto part=path.substr(begin,end-begin);if(part.empty()||part=="."||part=="..")return false;begin=end+1;}return true;
}
bool component(const std::string& value){return !value.empty()&&value.size()<=64&&value!="."&&value!=".."&&value.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")==std::string::npos;}
bool hex_sha(const std::string& value){return value.size()==64&&value.find_first_not_of("0123456789abcdef")==std::string::npos;}
std::string storage_error(const char*operation,int code=errno){return(code==ENOSPC||code==EDQUOT)?"Not enough free space in collection storage":std::string(operation)+": collection storage error ("+std::strerror(code)+")";}
// The payload SDK imports lstat separately from the proven open/stat path.
// Inspect an already opened descriptor instead: O_NOFOLLOW remains enforced
// by the kernel, and O_NONBLOCK prevents an unexpected FIFO from blocking us.
bool nofollow_info(const std::string&path,struct stat&info){
    int fd=open(path.c_str(),O_RDONLY|O_NOFOLLOW|O_NONBLOCK);if(fd<0)return false;
    const int result=fstat(fd,&info);const int saved=errno;close(fd);errno=saved;return result==0;
}
bool regular(const std::string& path,std::uint64_t* bytes=nullptr){struct stat st{};if(!nofollow_info(path,st))return false;if(!S_ISREG(st.st_mode)||st.st_size<0){errno=EINVAL;return false;}if(bytes)*bytes=st.st_size;return true;}
bool directory(const std::string& path){const int fd=open(path.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW);if(fd<0)return false;const int saved=errno;close(fd);errno=saved;return true;}
bool mkdirs(const std::string& path){
    if(path.empty()||path.front()!='/')return false;
    std::size_t at=1;for(;;){at=path.find('/',at);const auto part=at==std::string::npos?path:path.substr(0,at);if(!part.empty()&&!directory(part)){if(mkdir(part.c_str(),0700)||!directory(part))return false;}if(at==std::string::npos)break;++at;}return true;
}
bool sync_directory(const std::string& path){int fd=open(path.c_str(),O_RDONLY|O_DIRECTORY);if(fd<0)return false;const bool ok=fsync(fd)==0;close(fd);return ok;}
std::uint64_t staged_bytes(const std::string&path){
    if(!directory(path))return 0;DIR*dir=opendir(path.c_str());if(!dir)return 0;std::uint64_t bytes=0;
    while(auto*entry=readdir(dir)){const std::string name=entry->d_name;if(name=="."||name=="..")continue;const auto file=path+"/"+name;struct stat st{};if(!nofollow_info(file,st))continue;if(S_ISREG(st.st_mode))bytes+=st.st_size;else if(S_ISDIR(st.st_mode))bytes+=staged_bytes(file);}closedir(dir);return bytes;
}
bool available_bytes(const std::string&path,std::uint64_t&bytes){
#if defined(__FreeBSD__)
    // Both volume-stat paths are unsafe in the actual PS5 application sandbox:
    // the console log stops inside statfs despite the SDK providing its wrapper.
    // This preflight is optional; the reserved 16 GiB container remains in force,
    // and writes/flushes still report ENOSPC/EDQUOT explicitly. Never substitute
    // another unverified native filesystem-stat entry point here.
    (void)path;(void)bytes;errno=ENOSYS;return false;
#elif defined(PM_COLLECTION_STATVFS)
    if(!statvfs)return false;struct statvfs info{};if(statvfs(path.c_str(),&info))return false;const auto unit=info.f_frsize?info.f_frsize:info.f_bsize;if(!unit||std::uint64_t(info.f_bavail)>UINT64_MAX/unit)return false;bytes=std::uint64_t(info.f_bavail)*unit;return true;
#else
    (void)path;(void)bytes;return false;
#endif
}
struct SmallRead {bool ok=false;std::string bytes,operation;int code=0;};
SmallRead read_bounded(const std::string&path,std::size_t maximum,bool trusted_bundle=false){
    // Match hui::save::read_file's working open/read path for the bundled
    // read-only manifest. Private worker JSON keeps the no-follow protection.
    SmallRead result;const int fd=open(path.c_str(),O_RDONLY|(trusted_bundle?0:O_NOFOLLOW|O_NONBLOCK));
    if(fd<0){result.code=errno;result.operation="open";return result;}
    std::array<char,4096>buffer{};
    for(;;){const auto n=::read(fd,buffer.data(),buffer.size());if(n<0){if(errno==EINTR)continue;result.code=errno;result.operation="read";break;}if(!n){result.ok=true;break;}if(std::size_t(n)>maximum-result.bytes.size()){result.code=EFBIG;result.operation="bounded read";break;}result.bytes.append(buffer.data(),std::size_t(n));}
    close(fd);if(!result.ok)result.bytes.clear();errno=result.code;return result;
}
std::string read_small(const std::string& path,std::size_t maximum=4u<<20){return read_bounded(path,maximum).bytes;}
bool verified_missing_bundle(const std::string&path,int open_errno){
    if(open_errno!=ENOENT)return false;
    // Only the trusted bundled path may use stat: never staging or extracted
    // data. An unavailable /app0 parent is not a legacy missing-manifest case.
    struct stat info{};if(::stat(path.c_str(),&info)==0||errno!=ENOENT)return false;
    return ::stat(parent(path).c_str(),&info)==0&&S_ISDIR(info.st_mode);
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

// Descriptor-relative host fixtures use POSIX directly. Native destructive
// operations run only in the already proven restricted writer payload.
#if !defined(__FreeBSD__)
int removal_openat(int directory,const char*name,int flags){
    return openat(directory,name,flags);
}
int removal_unlinkat(int directory,const char*name,int flags){
    return unlinkat(directory,name,flags);
}
#endif
bool normal_absolute(const std::string&input,std::string&output){
    output.clear();if(input.empty()||input.front()!='/'||input.find('\\')!=std::string::npos||input.find('\0')!=std::string::npos)return false;
    std::size_t begin=1;
    while(begin<input.size()){
        auto end=input.find('/',begin);if(end==std::string::npos)end=input.size();
        const auto name=input.substr(begin,end-begin);
        if(name=="."||name=="..")return false;
        if(!name.empty())output+="/"+name;
        begin=end+1;
    }
    if(output.empty())output="/";
    return true;
}
bool overlaps_tree(const std::string&a,const std::string&b){return a==b||(a.size()<b.size()&&b.compare(0,a.size(),a)==0&&b[a.size()]=='/')||(b.size()<a.size()&&a.compare(0,b.size(),b)==0&&a[b.size()]=='/');}
}
struct CollectionInstaller::Impl {
    struct Pack {std::string id,url,sha;std::uint64_t bytes=0,file_count=0,expanded_bytes=0;};
    mutable std::mutex mutex;
    std::mutex lifecycle;
    Status status;
    std::vector<Pack> packs;
    std::string base,stage_root,ready_root,bundled,manifest_sha,image_manifest_sha,active_root,legacy_base,legacy_stage,legacy_ready;
    std::string archive_index_path,collection_id;
    bool archive_mode=false;
#if defined(PM_COLLECTION_WRITER)
    std::unique_ptr<CollectionWriter>writer;
    bool ensure_writer(std::string&error){
        if(writer)return true;auto service=std::make_unique<CollectionWriter>();std::vector<CollectionWriter::Pack>allowed;for(const auto&pack:packs)allowed.push_back({pack.sha,pack.bytes});
        std::string reason;if(!service->start(allowed,reason)){error="Installation service unavailable: "+reason;return false;}writer=std::move(service);return true;
    }
#endif
    std::vector<std::uint64_t>installed_pack_bytes,installed_pack_files;
    bool configured=false,allow_http=false;
    std::atomic<int> command{0}; // 0 run,1 pause,2 cancel,3 shutdown.
    std::atomic<bool> running{false};
    pthread_t worker{};
    bool worker_joinable=false; // Protected by lifecycle, not running.
    std::uint64_t completed=0;
    std::uint64_t expanded_bytes=0,maximum_pack=0;
    WorkerClock::time_point last_progress_at{}; // Protected by mutex.
    void update(Phase phase,const std::string& stage,const std::string& error={},int code=0,const std::string&diagnostic={}){std::lock_guard<std::mutex>lock(mutex);status.phase=phase;status.stage=stage;status.error=error;status.bytes_per_second=0;status.filesystem_errno=code;status.diagnostic=diagnostic;}
    void storage_failure(const char*operation,const std::string&path,int code){update(Phase::failed,"Installation storage unavailable",storage_error(operation,code),code,std::string(operation)+" ["+path+"] errno="+std::to_string(code)+" ("+std::strerror(code)+")");}
    bool interrupted()const{return command.load(std::memory_order_acquire)!=0;}
    void interrupted_status(){const auto c=command.load();update(c==1?Phase::paused:Phase::cancelled,c==1?"Paused":"Stopped");}
#if !defined(__FreeBSD__)
    bool remove_tree_at(int parent_fd,const std::string&name,unsigned depth,std::uint64_t&entries,std::string&path){
        if(interrupted()){errno=ECANCELED;return false;}
        if(depth>64||++entries>1000000){errno=EOVERFLOW;return false;}
        const int fd=removal_openat(parent_fd,name.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_NONBLOCK);
        if(fd<0){
            const int code=errno;
            if(code==ENOENT)return true;
            // An entry that is not an opened directory is unlinked by name.
            // This removes symlinks themselves and never opens their targets.
            if(code!=ENOTDIR&&code!=ELOOP)return false;
            return removal_unlinkat(parent_fd,name.c_str(),0)==0||errno==ENOENT;
        }
        DIR*dir=fdopendir(fd);if(!dir){const int code=errno?errno:EIO;close(fd);errno=code;return false;}
        bool ok=true;int code=0;
        for(;;){
            errno=0;auto*entry=readdir(dir);
            if(!entry){if(errno){ok=false;code=errno;}break;}
            const std::string child=entry->d_name;
            if(child=="."||child=="..")continue;
            if(child.empty()||child.find('/')!=std::string::npos){ok=false;code=EINVAL;break;}
            const auto previous=path;path+="/"+child;
            if(!remove_tree_at(fd,child,depth+1,entries,path)){ok=false;code=errno;break;}
            path=previous;
        }
        if(closedir(dir)&&ok){ok=false;code=errno;}
        if(!ok){errno=code;return false;}
        if(interrupted()){errno=ECANCELED;return false;}
        return removal_unlinkat(parent_fd,name.c_str(),AT_REMOVEDIR)==0||errno==ENOENT;
    }
#endif
    bool removal_path(const std::string&target,std::string&normalized,std::string&diagnostic)const{
        std::string bundle;
        if(!normal_absolute(target,normalized)||normalized=="/collection"||normalized.size()<11||normalized.compare(normalized.size()-11,11,"/collection")){
            errno=EINVAL;diagnostic="Refused collection reset path: "+target;return false;
        }
        if(!bundled.empty()&&(!normal_absolute(bundled,bundle)||bundle=="/"||overlaps_tree(normalized,bundle))){
            errno=EPERM;diagnostic="Refused collection reset overlapping application bundle: "+target;return false;
        }
#if defined(__FreeBSD__)
        if(normalized!="/data/pixelmuseum/collection"&&normalized!="/download0/pixelmuseum/collection"){
            errno=EPERM;diagnostic="Refused collection reset outside native allowlist: "+target;return false;
        }
#endif
        return true;
    }
#if !defined(__FreeBSD__)
    bool remove_collection_tree(const std::string&target,std::string&diagnostic){
        std::string normalized;if(!removal_path(target,normalized,diagnostic))return false;
        int fd=open("/",O_RDONLY|O_DIRECTORY|O_NOFOLLOW);
        if(fd<0){diagnostic="Cannot open collection reset root";return false;}
        std::size_t begin=1;
        const std::string parents=parent(normalized);
        while(begin<parents.size()){
            auto end=parents.find('/',begin);if(end==std::string::npos)end=parents.size();
            const auto name=parents.substr(begin,end-begin);
            const int next=removal_openat(fd,name.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_NONBLOCK);
            if(next<0){const int code=errno;close(fd);errno=code;if(code==ENOENT)return true;diagnostic="Cannot open collection reset parent: "+parents.substr(0,end);return false;}
            close(fd);fd=next;begin=end+1;
        }
        // Reject a redirected root rather than claiming an outside collection
        // has been erased. Symlinks *inside* the owned root are removed safely.
        const int root_fd=removal_openat(fd,"collection",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_NONBLOCK);
        if(root_fd<0){const int code=errno;close(fd);errno=code;if(code==ENOENT)return true;diagnostic="Cannot open collection reset directory: "+normalized;return false;}
        close(root_fd);
        std::uint64_t entries=0;std::string path=normalized;
        const bool ok=remove_tree_at(fd,"collection",0,entries,path);
        const int code=errno;
        if(ok&&fsync(fd)){const int saved=errno;close(fd);errno=saved;diagnostic="Cannot synchronize removed collection: "+parents;return false;}
        close(fd);errno=code;
        if(!ok)diagnostic="Cannot remove downloaded collection: "+path;
        return ok;
    }
#else
    bool removal_absent(const std::string&target,std::string&diagnostic){
        const int fd=open(target.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_NONBLOCK);
        if(fd<0){if(errno==ENOENT)return true;diagnostic="Cannot verify removed collection: "+target;return false;}
        close(fd);errno=EBUSY;diagnostic="Downloaded collection remains visible: "+target;return false;
    }
#endif
    void run_removal(){
        struct Finish {Impl*p;~Finish(){p->running.store(false,std::memory_order_release);}}finish{this};
        std::printf("[Museum] collection removal worker entered\n");std::fflush(stdout);
        update(Phase::removing,"Removing downloaded data");
        // Clear both known locations so the installer cannot import a legacy
        // copy immediately after the user has explicitly removed the data.
        std::vector<std::string> targets{base};if(!legacy_base.empty()&&legacy_base!=base)targets.push_back(legacy_base);
        // Validate every configured target before the first destructive step.
        for(const auto&target:targets){
            std::string normalized,diagnostic;
            if(!removal_path(target,normalized,diagnostic)){
                const int code=errno;update(Phase::failed,"Could not remove downloaded data",storage_error("Cannot remove downloaded data",code),code,diagnostic+" errno="+std::to_string(code));return;
            }
        }
#if defined(__FreeBSD__)
        if(writer){writer->stop();writer.reset();}
        std::string service_error;
        std::printf("[Museum] collection removal launching restricted writer\n");std::fflush(stdout);
        if(!ensure_writer(service_error)||!writer->remove_downloaded(service_error)){
            const int code=errno?errno:EIO;
            if(writer){writer->stop();writer.reset();}
            update(Phase::failed,"Could not remove downloaded data",service_error.empty()?storage_error("Cannot remove downloaded data",code):service_error,code,"Restricted collection writer removal failed errno="+std::to_string(code));return;
        }
        writer->stop();writer.reset();
        std::printf("[Museum] collection removal writer acknowledged; checking app-visible roots\n");std::fflush(stdout);
        for(const auto&target:targets){
            std::string diagnostic;
            if(!removal_absent(target,diagnostic)){
                const int code=errno?errno:EIO;update(Phase::failed,"Could not remove downloaded data",storage_error("Cannot remove downloaded data",code),code,diagnostic+" errno="+std::to_string(code));return;
            }
        }
#else
        for(const auto&target:targets){
            std::string diagnostic;
            if(!remove_collection_tree(target,diagnostic)){
                const int code=errno;
                if(code==ECANCELED||interrupted()){interrupted_status();return;}
                update(Phase::failed,"Could not remove downloaded data",storage_error("Cannot remove downloaded data",code),code,diagnostic+" errno="+std::to_string(code));return;
            }
        }
#endif
        if(interrupted()){interrupted_status();return;}
        std::printf("[Museum] collection removal complete\n");std::fflush(stdout);
        std::fill(installed_pack_bytes.begin(),installed_pack_bytes.end(),0);std::fill(installed_pack_files.begin(),installed_pack_files.end(),0);completed=0;
        std::lock_guard<std::mutex>lock(mutex);active_root.clear();status.phase=Phase::removed;status.stage="Downloaded data removed";status.error.clear();status.diagnostic.clear();status.filesystem_errno=0;status.downloaded_bytes=0;status.installed_bytes=0;status.installed_files=0;status.pack_index=0;status.bytes_per_second=0;
    }
    std::string marker(std::size_t n,const std::string&root={})const{return(root.empty()?stage_root:root)+"/.pack-"+std::to_string(n)+".json";}
    void installed_work(std::size_t index,std::uint64_t bytes,std::uint64_t files){
        installed_pack_bytes[index]=bytes;installed_pack_files[index]=files;std::uint64_t all_bytes=0,all_files=0;for(auto n:installed_pack_bytes)all_bytes+=n;for(auto n:installed_pack_files)all_files+=n;
        std::lock_guard<std::mutex>lock(mutex);status.installed_bytes=std::min(status.total_expanded_bytes,all_bytes);status.installed_files=status.total_files?std::min(status.total_files,all_files):all_files;
    }
    void account_checkpoint(std::size_t index){const auto j=Json::parse(read_small(marker(index)),nullptr,false);if(!j.is_object())return;if(j.contains("storage")&&j["storage"].is_string()&&j["storage"].get<std::string>()=="archive"){installed_work(index,packs[index].expanded_bytes,packs[index].file_count);return;}if(!j.contains("files")||!j["files"].is_array())return;std::uint64_t bytes=0;for(const auto&f:j["files"])bytes+=f["bytes"].get<std::uint64_t>();installed_work(index,bytes,j["files"].size());}
    bool load_archive_index(std::string&error){
        archive_mode=false;const auto input=read_bounded(archive_index_path,32u<<20,true);
        if(!input.ok){if(input.operation=="open"&&verified_missing_bundle(archive_index_path,input.code))return true;error="Cannot read bundled collection archive index";return false;}
        const auto j=Json::parse(input.bytes,nullptr,false);
        if(!j.is_object()||!j.contains("schema_version")||!j["schema_version"].is_number_integer()||j["schema_version"].get<int>()!=1||!j.contains("collection_id")||!j["collection_id"].is_string()||j["collection_id"].get<std::string>()!=collection_id||image_manifest_sha.empty()||!j.contains("image_manifest_sha256")||!j["image_manifest_sha256"].is_string()||j["image_manifest_sha256"].get<std::string>()!=image_manifest_sha||!j.contains("packs")||!j["packs"].is_array()||j["packs"].size()!=packs.size()){error="Invalid bundled collection archive index";return false;}
        std::set<std::string>paths;std::uint64_t total_payload=0,total_files=0;
        for(std::size_t n=0;n<packs.size();++n){const auto&row=j["packs"][n];const auto&pack=packs[n];
            if(!row.is_object()||!row.contains("id")||!row["id"].is_string()||row["id"].get<std::string>()!=pack.id||!row.contains("sha256")||!row["sha256"].is_string()||row["sha256"].get<std::string>()!=pack.sha||!row.contains("bytes")||!row["bytes"].is_number_unsigned()||row["bytes"].get<std::uint64_t>()!=pack.bytes||!row.contains("files")||!row["files"].is_array()||row["files"].empty()||row["files"].size()>1000000){error="Archive index pack does not match pinned manifest";return false;}
            std::uint64_t payload=0,last_end=0;
            for(const auto&file:row["files"]){
                if(!file.is_object()||!file.contains("path")||!file["path"].is_string()||!file.contains("offset")||!file["offset"].is_number_unsigned()||!file.contains("bytes")||!file["bytes"].is_number_unsigned()){error="Invalid archive index file record";return false;}
                const auto path=file["path"].get<std::string>();const auto offset=file["offset"].get<std::uint64_t>();const auto bytes=file["bytes"].get<std::uint64_t>();
                if(!safe_relative(path)||path.rfind("assets/images/",0)!=0||path.find("/.pack-")!=std::string::npos||!paths.insert(path).second||offset<512||offset%512||offset>pack.bytes||bytes>pack.bytes-offset||offset<last_end||payload>pack.bytes-bytes){error="Unsafe archive index path, range or duplicate";return false;}last_end=offset+bytes;payload+=bytes;
            }
            if((pack.file_count&&pack.file_count!=row["files"].size())||(pack.expanded_bytes&&pack.expanded_bytes!=payload)){error="Archive index inventory does not match pinned manifest";return false;}
            total_payload+=payload;total_files+=row["files"].size();
        }
        if(total_payload!=expanded_bytes||(status.total_files&&total_files!=status.total_files)||!paths.count("assets/images/manifest.json")){error="Archive index collection totals do not match manifest";return false;}
        archive_mode=true;return true;
    }
    bool pack_done(std::size_t index,const std::string&root={}){
        const auto&tree=root.empty()?stage_root:root;const auto raw=read_small(marker(index,tree));auto j=Json::parse(raw,nullptr,false);if(!j.is_object()||!j.contains("sha256")||!j["sha256"].is_string()||j["sha256"].get<std::string>()!=packs[index].sha)return false;
        if(j.contains("storage")){
            if(!archive_mode||!j["storage"].is_string()||j["storage"].get<std::string>()!="archive"||!j.contains("archive")||!j["archive"].is_string()||j["archive"].get<std::string>()!="archives/"+packs[index].sha+".tar"||!j.contains("bytes")||!j["bytes"].is_number_unsigned()||j["bytes"].get<std::uint64_t>()!=packs[index].bytes)return false;
            std::uint64_t bytes=0;return directory(tree+"/archives")&&regular(tree+"/"+j["archive"].get<std::string>(),&bytes)&&bytes==packs[index].bytes;
        }
        if(!j.contains("files")||!j["files"].is_array())return false;
        std::uint64_t expanded=0;std::set<std::string>paths;
        for(const auto& f:j["files"]){if(interrupted())return false;if(!f.is_object()||!f.contains("path")||!f["path"].is_string()||!f.contains("bytes")||!f["bytes"].is_number_unsigned())return false;const auto path=f["path"].get<std::string>();if(!safe_relative(path)||path.rfind("assets/images/",0)!=0||!paths.insert(path).second)return false;std::uint64_t size=0;if(!regular(tree+"/"+path,&size)||size!=f["bytes"].get<std::uint64_t>())return false;expanded+=size;if(path=="assets/images/manifest.json"&&!image_manifest_sha.empty()&&digest_text(read_small(tree+"/"+path,16u<<20))!=image_manifest_sha)return false;}
        return !j["files"].empty()&&(!packs[index].file_count||packs[index].file_count==paths.size())&&(!packs[index].expanded_bytes||packs[index].expanded_bytes==expanded);
    }
    bool ready_on_disk(const std::string&other={}){
        const auto&tree=other.empty()?ready_root:other;
        auto j=Json::parse(read_small(tree+"/.complete.json"),nullptr,false);if(!directory(tree)||!j.is_object()||!j.contains("manifest_sha256")||!j["manifest_sha256"].is_string()||j["manifest_sha256"].get<std::string>()!=manifest_sha||!j.contains("image_manifest_sha256")||!j["image_manifest_sha256"].is_string())return false;
        const auto expected=j["image_manifest_sha256"].get<std::string>();if(!hex_sha(expected)||(!image_manifest_sha.empty()&&expected!=image_manifest_sha)||digest_text(read_small(tree+"/assets/images/manifest.json",16u<<20))!=expected)return false;
        update(Phase::verifying,"Checking downloaded collection");for(std::size_t n=0;n<packs.size();++n)if(!pack_done(n,tree))return false;return true;
    }
    bool storage_benchmark(){
        const auto receipt=base+"/.write-probe-"+manifest_sha.substr(0,24)+".json";
        const auto previous=Json::parse(read_small(receipt),nullptr,false);if(previous.is_object()&&previous.contains("manifest_sha256")&&previous["manifest_sha256"].is_string()&&previous["manifest_sha256"].get<std::string>()==manifest_sha&&previous.contains("complete")&&previous["complete"].is_boolean()&&previous["complete"].get<bool>())return true;
        update(Phase::verifying,"Checking collection storage");const auto begin=WorkerClock::now();
        const auto path=base+"/.write-probe-"+std::to_string(getpid())+"-"+std::to_string(WorkerClock::now().time_since_epoch().count())+".tmp";
        int fd=open(path.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);if(fd<0){storage_failure("Cannot test preferred collection storage",path,errno);return false;}
        std::vector<char>buffer(1u<<20,0x5a);bool ok=true;int code=0;std::uint64_t bytes=0;
        for(unsigned n=0;n<16&&ok&&!interrupted();++n){std::size_t pos=0;while(pos<buffer.size()){const auto count=write(fd,buffer.data()+pos,buffer.size()-pos);if(count<0&&errno==EINTR)continue;if(count<=0){code=errno?errno:EIO;ok=false;break;}pos+=std::size_t(count);bytes+=std::size_t(count);}}
        const auto flush_begin=WorkerClock::now();if(fsync(fd)){code=errno;ok=false;}const auto flush_time=elapsed_seconds(flush_begin);if(close(fd)){code=errno;ok=false;}const int removal=unlink(path.c_str());if(removal&&ok){code=errno;ok=false;}
        phase_receipt("preferred-storage-write-probe",base,bytes,elapsed_seconds(begin));
#if defined(__FreeBSD__)
        hui::sys::log("[Museum] collection storage probe / fsync %.3fs / complete=%d",flush_time,ok&&!interrupted());
#endif
        if(interrupted())return false;if(!ok){storage_failure("Preferred collection storage write failed",base,code);return false;}
        if(!atomic_text(receipt,Json({{"manifest_sha256",manifest_sha},{"complete",true},{"bytes",bytes},{"seconds",elapsed_seconds(begin)},{"fsync_seconds",flush_time}}).dump())){storage_failure("Cannot commit storage probe",receipt,errno);return false;}return true;
    }
    bool copy_legacy_file(const std::string&source,const std::string&target,std::uint64_t bytes,std::string&error,std::size_t pack_index=SIZE_MAX,std::uint64_t prior_bytes=0,std::uint64_t prior_files=0){
        // Check every source ancestor without creating anything in the legacy
        // tree. No symlink may redirect a read outside the known title paths.
        const auto source_parent=parent(source);std::size_t at=1;for(;;){at=source_parent.find('/',at);const auto part=at==std::string::npos?source_parent:source_parent.substr(0,at);if(!directory(part)){error="Unsafe legacy collection directory";return false;}if(at==std::string::npos)break;++at;}
        int input=open(source.c_str(),O_RDONLY|O_NOFOLLOW|O_NONBLOCK);if(input<0){error=storage_error("Cannot read legacy collection file");return false;}struct stat info{};if(fstat(input,&info)||!S_ISREG(info.st_mode)||info.st_size<0||std::uint64_t(info.st_size)!=bytes){close(input);error="Legacy collection file changed during migration";return false;}
        if(!mkdirs(parent(target))){const int code=errno;close(input);error=storage_error("Cannot create preferred collection directory",code);return false;}
        const auto temporary=target+".migration-tmp";int output=open(temporary.c_str(),O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0600);if(output<0){const int code=errno;close(input);error=storage_error("Cannot write migrated collection file",code);return false;}
        std::vector<char>buffer(1u<<20);std::uint64_t copied=0;bool ok=true;int code=0;
        while(copied<bytes&&ok&&!interrupted()){
            const auto count=read(input,buffer.data(),std::min<std::uint64_t>(buffer.size(),bytes-copied));if(count<0&&errno==EINTR)continue;if(count<=0){code=count<0?errno:EIO;ok=false;break;}
            std::size_t pos=0;while(pos<std::size_t(count)&&!interrupted()){const auto written=write(output,buffer.data()+pos,std::size_t(count)-pos);if(written<0&&errno==EINTR)continue;if(written<=0){code=errno?errno:EIO;ok=false;break;}pos+=std::size_t(written);copied+=std::size_t(written);if(pack_index!=SIZE_MAX)installed_work(pack_index,prior_bytes+copied,prior_files);}
        }
        if(!interrupted()&&ok){char tail=0;const auto count=read(input,&tail,1);if(count!=0){code=count<0?errno:EIO;ok=false;}}
        if(fsync(output)){code=errno;ok=false;}if(close(output)){code=errno;ok=false;}close(input);
        if(!ok||interrupted()){unlink(temporary.c_str());if(!interrupted())error=storage_error("Cannot preserve legacy collection copy",code);return false;}
        if(rename(temporary.c_str(),target.c_str())){error=storage_error("Cannot commit migrated collection file");return false;}return true;
    }
    bool import_legacy(std::string&error){
        if(legacy_base.empty())return true;
        for(std::size_t n=0;n<packs.size();++n){
            if(interrupted())return false;if(pack_done(n)){account_checkpoint(n);continue;}
            std::string source;if(pack_done(n,legacy_stage))source=legacy_stage;else if(pack_done(n,legacy_ready))source=legacy_ready;
            if(source.empty())continue;update(Phase::extracting,"Migrating collection");{std::lock_guard<std::mutex>lock(mutex);status.pack_index=n;}
            const auto checkpoint=read_small(marker(n,source));const auto record=Json::parse(checkpoint,nullptr,false);std::uint64_t bytes=0,files=0;std::set<std::string>dirty;
            if(record.contains("storage")){error="Legacy archive migration is unsupported; existing source collection has been preserved";return false;}
            for(const auto&file:record["files"]){const auto relative=file["path"].get<std::string>();const auto size=file["bytes"].get<std::uint64_t>();if(!copy_legacy_file(source+"/"+relative,stage_root+"/"+relative,size,error,n,bytes,files))return false;bytes+=size;++files;installed_work(n,bytes,files);for(auto dir=parent(stage_root+"/"+relative);dir.size()>=stage_root.size();dir=parent(dir)){dirty.insert(dir);if(dir==stage_root)break;}}
            for(auto dir=dirty.rbegin();dir!=dirty.rend();++dir)if(!sync_directory(*dir)){error=storage_error("Cannot flush migrated collection directory");return false;}
            if(!atomic_text(marker(n),checkpoint)){error=storage_error("Cannot commit migrated pack checkpoint");return false;}
            if(!pack_done(n)){error="Migrated collection checkpoint verification failed";return false;}
        }
        for(std::size_t n=0;n<packs.size();++n){if(interrupted())return false;if(pack_done(n))continue;const auto name=packs[n].sha+".tar.part";const auto source=legacy_base+"/downloads/"+name;const auto target=base+"/downloads/"+name;std::uint64_t old_size=0,new_size=0;
            if(!regular(source,&old_size)||!old_size||old_size>packs[n].bytes)continue;if(regular(target,&new_size)&&new_size>=old_size)continue;
            update(Phase::extracting,"Migrating collection");if(!copy_legacy_file(source,target,old_size,error)||!sync_directory(parent(target))){if(error.empty())error=storage_error("Cannot commit migrated download prefix");return false;}
        }return true;
    }
    bool hash_pack(const Pack& pack,const std::string& path){
        const auto begin=WorkerClock::now();
        update(Phase::verifying,"Verifying "+pack.id);FILE* file=std::fopen(path.c_str(),"rb");if(!file)return false;CollectionSha256 hash;bool ok=true;std::array<unsigned char,65536>buffer{};std::uint64_t bytes=0;
        while(ok&&!interrupted()){const auto n=std::fread(buffer.data(),1,buffer.size(),file);bytes+=n;if(n)hash.update(buffer.data(),n);if(n<buffer.size()){if(std::ferror(file))ok=false;break;}}
        std::string sha;if(ok&&!interrupted())sha=hash.finish();std::fclose(file);phase_receipt("SHA256",pack.id,bytes,elapsed_seconds(begin));return ok&&bytes==pack.bytes&&sha==pack.sha;
    }
    bool promote_archive(std::size_t index,const std::string&source,std::string&error){
        const auto&pack=packs[index];const auto relative="archives/"+pack.sha+".tar";const auto target=stage_root+"/"+relative;
        update(Phase::extracting,"Installing "+pack.id);
        if(!mkdirs(stage_root+"/archives")){error=storage_error("Cannot create archive collection directory");return false;}
        struct stat previous{};if(nofollow_info(target,previous)){if(!S_ISREG(previous.st_mode)){error="Unsafe archive collection destination";return false;}}else if(errno!=ENOENT){error=storage_error("Cannot inspect archive collection destination");return false;}
        if(source!=target&&rename(source.c_str(),target.c_str())){error=storage_error("Cannot activate verified collection archive");return false;}
        if(!sync_directory(stage_root+"/archives")||!sync_directory(stage_root)||(source!=target&&!sync_directory(parent(source)))){error=storage_error("Cannot flush verified collection archive");return false;}
        if(!atomic_text(marker(index),Json({{"sha256",pack.sha},{"storage","archive"},{"archive",relative},{"bytes",pack.bytes}}).dump())){error=storage_error("Cannot commit collection archive checkpoint");return false;}
        installed_work(index,pack.expanded_bytes,pack.file_count);worker_trace("verified archive checkpoint committed");return true;
    }
    struct Transfer {Impl* owner;int fd;const Pack* pack;std::uint64_t offset,written=0;long response=0;bool valid_range=false,range_seen=false,restart=false;std::chrono::steady_clock::time_point start;int storage_errno=0;
        CollectionWriteBuffer buffer;
        CollectionDownloadRate rate;double write_seconds=0,max_write_seconds=0,report_time=0,report_write_seconds=0,report_max_write=0;std::uint64_t report_bytes=0;
    };
    static std::ptrdiff_t write_disk(Transfer&t,const char*bytes,std::size_t size){
        const auto begin=WorkerClock::now();
#if defined(PM_COLLECTION_WRITER)
        const auto written=t.owner->writer->write(bytes,size);
#else
        const auto written=write(t.fd,bytes,size);
#endif
        const int code=written==0?EIO:errno;const double elapsed=elapsed_seconds(begin);t.write_seconds+=elapsed;t.max_write_seconds=std::max(t.max_write_seconds,elapsed);t.report_max_write=std::max(t.report_max_write,elapsed);if(written==0||(written<0&&code!=EINTR))t.storage_errno=code?code:EIO;errno=code;return written;
    }
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
        const bool ok=t.buffer.append(p,bytes,[&](const char*data,std::size_t count){return write_disk(t,data,count);});t.written=t.buffer.accepted();t.owner->progress(t);return ok?bytes:0;
    }
    void progress(Transfer&t){
        const auto now=WorkerClock::now();const double seconds=std::chrono::duration<double>(now-t.start).count();const auto speed=t.rate.observe(seconds,t.written);
        {std::lock_guard<std::mutex>lock(mutex);status.downloaded_bytes=completed+t.offset+t.written;status.bytes_per_second=speed;last_progress_at=now;}
        if(seconds-t.report_time>=5.){
#if defined(__FreeBSD__)
            const auto interval=seconds-t.report_time;const auto accepted=t.written-t.report_bytes;
            hui::sys::log("[Museum] collection interval %s / %.3fs / %llu accepted bytes / %.2f MiB/s / disk %llu bytes / raw-write %.3fs / max write %.2fms",t.pack->id.c_str(),interval,static_cast<unsigned long long>(accepted),double(accepted)/(1048576.*interval),static_cast<unsigned long long>(t.buffer.flushed()),t.write_seconds-t.report_write_seconds,t.report_max_write*1000.);
#endif
            t.report_time=seconds;t.report_bytes=t.written;t.report_write_seconds=t.write_seconds;t.report_max_write=0;
        }
    }
    static int progress_callback(void*data,curl_off_t,curl_off_t,curl_off_t,curl_off_t){return static_cast<Transfer*>(data)->owner->interrupted()?1:0;}
    bool download(const Pack&pack,const std::string&path,std::string&error){
        for(unsigned attempt=0;attempt<2&&!interrupted();++attempt){
            const auto begin=WorkerClock::now();
            std::uint64_t offset=0;const bool exists=regular(path,&offset);if(exists&&offset>pack.bytes){std::remove(path.c_str());offset=0;}
#if !defined(PM_COLLECTION_WRITER)
            if(offset==pack.bytes)return true;
#endif
            int fd=-1;
#if defined(PM_COLLECTION_WRITER)
            if(!ensure_writer(error))return false;std::string service_error;
            if(!writer->open(std::size_t(&pack-packs.data()),offset,service_error)){error="Installation service unavailable: "+service_error;return false;}
            if(offset>pack.bytes){std::string ignored;writer->finish(ignored);error="Installation service returned an invalid saved offset";return false;}
            if(offset==pack.bytes){if(!writer->finish(service_error)){error="Installation service unavailable: "+service_error;return false;}return true;}
#else
            fd=open(path.c_str(),O_WRONLY|O_CREAT|O_NOFOLLOW|(offset?O_APPEND:O_TRUNC),0600);if(fd<0){error=storage_error("Cannot write partial pack");return false;}
#endif
            CURL*curl=curl_easy_init();if(!curl){
#if defined(PM_COLLECTION_WRITER)
                std::string ignored;writer->finish(ignored);
#else
                close(fd);
#endif
                error="Cannot initialize collection download";return false;}
#if defined(__FreeBSD__)
            console_curl_setup_bulk(curl);
#endif
            Transfer transfer{this,fd,&pack,offset,0,0,false,false,false,std::chrono::steady_clock::now()};transfer.rate.reset();update(Phase::downloading,"Downloading "+pack.id);progress(transfer);
            curl_easy_setopt(curl,CURLOPT_URL,pack.url.c_str());curl_easy_setopt(curl,CURLOPT_NOSIGNAL,1L);curl_easy_setopt(curl,CURLOPT_FOLLOWLOCATION,1L);curl_easy_setopt(curl,CURLOPT_MAXREDIRS,5L);
            curl_easy_setopt(curl,CURLOPT_PROTOCOLS_STR,allow_http?"http,https":"https");curl_easy_setopt(curl,CURLOPT_REDIR_PROTOCOLS_STR,allow_http?"http,https":"https");
            curl_easy_setopt(curl,CURLOPT_CONNECTTIMEOUT,10L);curl_easy_setopt(curl,CURLOPT_LOW_SPEED_LIMIT,1024L);curl_easy_setopt(curl,CURLOPT_LOW_SPEED_TIME,20L);curl_easy_setopt(curl,CURLOPT_USERAGENT,"PixelMuseum-Collection/1");
            curl_easy_setopt(curl,CURLOPT_BUFFERSIZE,256L<<10);
            curl_easy_setopt(curl,CURLOPT_HTTP_CONTENT_DECODING,0L);curl_easy_setopt(curl,CURLOPT_HEADERFUNCTION,header);curl_easy_setopt(curl,CURLOPT_HEADERDATA,&transfer);curl_easy_setopt(curl,CURLOPT_WRITEFUNCTION,write_body);curl_easy_setopt(curl,CURLOPT_WRITEDATA,&transfer);
            curl_easy_setopt(curl,CURLOPT_NOPROGRESS,0L);curl_easy_setopt(curl,CURLOPT_XFERINFOFUNCTION,progress_callback);curl_easy_setopt(curl,CURLOPT_XFERINFODATA,&transfer);
            if(offset)curl_easy_setopt(curl,CURLOPT_RESUME_FROM_LARGE,curl_off_t(offset));
            const auto result=curl_easy_perform(curl);long response=0;double transfer_seconds=0;curl_off_t wire_bytes=0;curl_easy_getinfo(curl,CURLINFO_RESPONSE_CODE,&response);curl_easy_getinfo(curl,CURLINFO_TOTAL_TIME,&transfer_seconds);curl_easy_getinfo(curl,CURLINFO_SIZE_DOWNLOAD_T,&wire_bytes);curl_easy_cleanup(curl);
            // Always drain accepted RAM bytes after curl, including pause,
            // shutdown, network failure and callback errors. Resume uses only
            // the actual descriptor size, never the accepted counter.
            auto io_begin=WorkerClock::now();bool durable=transfer.buffer.flush([&](const char*data,std::size_t count){return write_disk(transfer,data,count);});transfer.written=transfer.buffer.accepted();progress(transfer);int storage_errno=transfer.storage_errno;if(!durable&&!storage_errno)storage_errno=errno?errno:EIO;const double fflush_seconds=elapsed_seconds(io_begin);io_begin=WorkerClock::now();
#if defined(PM_COLLECTION_WRITER)
            const bool finished=writer->finish(service_error);if(!finished){durable=false;if(!storage_errno)storage_errno=errno?errno:EIO;}
            const double fsync_seconds=elapsed_seconds(io_begin),fclose_seconds=0;
#else
            if(fsync(fd)){storage_errno=errno;durable=false;}const double fsync_seconds=elapsed_seconds(io_begin);io_begin=WorkerClock::now();if(close(fd)){storage_errno=errno;durable=false;}const double fclose_seconds=elapsed_seconds(io_begin);
#endif
            phase_receipt("curl-body",pack.id,wire_bytes>0?std::uint64_t(wire_bytes):0,transfer_seconds);phase_receipt("download-with-flush",pack.id,transfer.written,elapsed_seconds(begin));
#if defined(__FreeBSD__)
            hui::sys::log("[Museum] collection I/O %s / accepted %llu / flushed %llu / raw-write %.3fs / max write %.2fms / RAM-flush %.3fs / fsync %.3fs / close %.3fs",pack.id.c_str(),static_cast<unsigned long long>(transfer.buffer.accepted()),static_cast<unsigned long long>(transfer.buffer.flushed()),transfer.write_seconds,transfer.max_write_seconds*1000.,fflush_seconds,fsync_seconds,fclose_seconds);
#endif
            if(!durable||storage_errno||transfer.buffer.flushed()!=transfer.written){
#if defined(PM_COLLECTION_WRITER)
                const auto reason=service_error.empty()?writer->last_error():service_error;error="Installation service unavailable: "+(reason.empty()?storage_error("Cannot save collection pack",storage_errno?storage_errno:EIO):reason);
#else
                error=storage_error("Cannot save collection pack",storage_errno?storage_errno:EIO);
#endif
                return false;}
            if(interrupted())return false;
            if(offset&&(transfer.restart||result==CURLE_RANGE_ERROR||response==416)){if(std::remove(path.c_str())){error="Cannot reset unsupported range download";return false;}continue;}
            if(result!=CURLE_OK||!durable||offset+transfer.written!=pack.bytes){error=storage_errno?storage_error("Cannot save collection pack",storage_errno):"Download interrupted: "+std::string(curl_easy_strerror(result));return false;}
            return true;
        }
        if(!interrupted())error="Server does not provide a usable complete pack";return false;
    }
    bool extract(const Pack&pack,const std::string&path,std::size_t index,std::string&error){
        const auto begin=WorkerClock::now();double file_flush_seconds=0,read_seconds=0,write_seconds=0,metadata_seconds=0,close_seconds=0,rename_seconds=0,status_seconds=0,last_report=0;std::uint64_t read_calls=0,write_calls=0;
        update(Phase::extracting,"Installing "+pack.id);FILE*tar=std::fopen(path.c_str(),"rb");if(!tar){error="Cannot read verified pack";return false;}
        std::vector<char>buffer(1u<<20),tar_buffer(1u<<20);if(setvbuf(tar,tar_buffer.data(),_IOFBF,tar_buffer.size())){std::fclose(tar);error="Cannot buffer verified collection archive";return false;}
        const auto read_tar=[&](void*target,std::size_t bytes){const auto start=WorkerClock::now();const auto count=std::fread(target,1,bytes,tar);read_seconds+=elapsed_seconds(start);++read_calls;return count;};
        const auto installed=[&](std::uint64_t bytes,std::uint64_t files){const auto start=WorkerClock::now();installed_work(index,bytes,files);status_seconds+=elapsed_seconds(start);const double elapsed=elapsed_seconds(begin);if(elapsed-last_report>=5.){
#if defined(__FreeBSD__)
            hui::sys::log("[Museum] collection extract-progress %s / %.3fs / %llu bytes / %llu files / read %.3fs / write %.3fs / metadata %.3fs / fsync %.3fs / close %.3fs / rename %.3fs / status %.3fs",pack.id.c_str(),elapsed,static_cast<unsigned long long>(bytes),static_cast<unsigned long long>(files),read_seconds,write_seconds,metadata_seconds,file_flush_seconds,close_seconds,rename_seconds,status_seconds);
#endif
            last_report=elapsed;}};
        std::array<char,512>h{};Json files=Json::array();std::set<std::string>seen,dirty_dirs,validated_parents;std::uint64_t read=0,payload=0;bool ok=true,ended=false;
        while(ok&&!interrupted()){
            if(read_tar(h.data(),h.size())!=h.size()){error="Truncated USTAR header";ok=false;break;}read+=512;
            if(std::all_of(h.begin(),h.end(),[](char c){return c==0;})){
                if(read_tar(h.data(),h.size())!=h.size()||!std::all_of(h.begin(),h.end(),[](char c){return c==0;})){error="Invalid USTAR end marker";ok=false;break;}read+=512;
                while(read<pack.bytes){const auto n=std::min<std::uint64_t>(buffer.size(),pack.bytes-read);if(read_tar(buffer.data(),n)!=n||!std::all_of(buffer.begin(),buffer.begin()+n,[](char c){return c==0;})){error="Unexpected trailing USTAR data";ok=false;break;}read+=n;}
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
            // Private 0700 staging, one writer, and no archive links allowed.
            // Revalidate every parent on each extraction/retry, but not once
            // for every sibling file. File opens still enforce O_NOFOLLOW.
            const auto metadata_begin=WorkerClock::now();
            const auto destination_parent=parent(destination);
            if(!validated_parents.count(destination_parent)){if(!mkdirs(destination_parent)){error="Unsafe collection directory";ok=false;break;}validated_parents.insert(destination_parent);}
            struct stat old{};if(nofollow_info(destination,old)){if(!S_ISREG(old.st_mode)){error="Non-regular collection destination";ok=false;break;}}else if(errno!=ENOENT){error=storage_error("Unsafe or unreadable collection destination");ok=false;break;}
            int fd=open(tmp.c_str(),O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0600);if(fd<0){error=storage_error("Cannot stage collection file");ok=false;break;}
            metadata_seconds+=elapsed_seconds(metadata_begin);
            std::uint64_t remaining=bytes;while(remaining&&ok&&!interrupted()){
                const auto want=std::min<std::uint64_t>(remaining,buffer.size());const auto got=read_tar(buffer.data(),want);if(got!=want){error="Truncated collection file";ok=false;break;}
                std::size_t pos=0;while(pos<got){const auto write_begin=WorkerClock::now();const auto n=write(fd,buffer.data()+pos,got-pos);const int code=errno;write_seconds+=elapsed_seconds(write_begin);++write_calls;if(n<0&&code==EINTR)continue;if(n<=0){error=storage_error("Cannot save collection file",code);ok=false;break;}pos+=n;installed(payload+bytes-remaining+pos,files.size());}remaining-=got;read+=got;
            }
            const auto flush_begin=WorkerClock::now();if(fsync(fd)){error=storage_error("Cannot flush collection file");ok=false;}file_flush_seconds+=elapsed_seconds(flush_begin);const auto close_begin=WorkerClock::now();const int closed=close(fd);const int close_code=errno;close_seconds+=elapsed_seconds(close_begin);if(closed){error=storage_error("Cannot close collection file",close_code);ok=false;}
            if(!ok||interrupted()){std::remove(tmp.c_str());break;}
            const auto rename_begin=WorkerClock::now();const int renamed=std::rename(tmp.c_str(),destination.c_str());const int rename_code=errno;rename_seconds+=elapsed_seconds(rename_begin);if(renamed){error=storage_error("Cannot commit collection file",rename_code);ok=false;break;}
            for(auto dir=parent(destination);dir.size()>=stage_root.size();dir=parent(dir)){dirty_dirs.insert(dir);if(dir==stage_root)break;}
            const auto padding=(512-bytes%512)%512;if(padding&&read_tar(buffer.data(),padding)!=padding){error="Truncated USTAR padding";ok=false;break;}read+=padding;payload+=bytes;files.push_back({{"path",name},{"bytes",bytes}});installed(payload,files.size());
        }
        std::fclose(tar);if(interrupted())return false;if(!ok||!ended||files.empty()){if(error.empty())error="Empty or incomplete collection archive";return false;}
        if((pack.file_count&&pack.file_count!=files.size())||(pack.expanded_bytes&&pack.expanded_bytes!=payload)){error="Collection pack inventory does not match the bundled manifest";return false;}
        // Flush every installed file above, then each changed directory once,
        // deepest first, before the durable checkpoint permits deleting the tar.
        const auto directory_begin=WorkerClock::now();for(auto dir=dirty_dirs.rbegin();dir!=dirty_dirs.rend();++dir)if(!sync_directory(*dir)){error=storage_error("Cannot flush collection directory");return false;}const double directory_seconds=elapsed_seconds(directory_begin);
        const auto checkpoint_begin=WorkerClock::now();
        if(!atomic_text(marker(index),Json({{"sha256",pack.sha},{"files",files}}).dump())){error=storage_error("Cannot commit pack checkpoint");return false;}
        const double checkpoint_seconds=elapsed_seconds(checkpoint_begin);
        phase_receipt("extract-with-checkpoint",pack.id,payload,elapsed_seconds(begin));
#if defined(__FreeBSD__)
        hui::sys::log("[Museum] collection extraction %s / %zu files / %zu validated parents / file fsync %.3fs",pack.id.c_str(),files.size(),validated_parents.size(),file_flush_seconds);
        hui::sys::log("[Museum] collection extraction costs %s / read %.3fs (%llu calls) / write %.3fs (%llu calls) / metadata %.3fs / close %.3fs / rename %.3fs / status %.3fs / dirs %.3fs / checkpoint %.3fs",pack.id.c_str(),read_seconds,static_cast<unsigned long long>(read_calls),write_seconds,static_cast<unsigned long long>(write_calls),metadata_seconds,close_seconds,rename_seconds,status_seconds,directory_seconds,checkpoint_seconds);
#endif
        return true;
    }
    void run(){
        struct Finish {Impl*p;~Finish(){
#if defined(PM_COLLECTION_WRITER)
            if(p->writer){p->writer->stop();p->writer.reset();}
#endif
            p->running.store(false,std::memory_order_release);}}finish{this};
        std::fill(installed_pack_bytes.begin(),installed_pack_bytes.end(),0);std::fill(installed_pack_files.begin(),installed_pack_files.end(),0);
        worker_trace("entry (explicit 2 MiB stack)");
        {std::string error;update(Phase::verifying,"Checking collection archive index");if(!load_archive_index(error)){update(Phase::failed,"Invalid collection archive index",error);return;}}
        if(!bundled.empty()){update(Phase::verifying,"Checking installed collection");worker_trace("bundled inventory begin");const bool complete=media::packaged_images_complete(bundled);worker_trace(complete?"bundled inventory complete":"bundled inventory incomplete");if(complete){if(interrupted()){interrupted_status();return;}std::lock_guard<std::mutex>lock(mutex);active_root.clear();status.phase=Phase::ready;status.stage="Bundled collection ready";status.downloaded_bytes=status.total_bytes;status.installed_bytes=status.total_expanded_bytes;status.installed_files=status.total_files;return;}}
        if(interrupted()){interrupted_status();return;}
        if(!legacy_base.empty()&&ready_on_disk(legacy_ready)){std::lock_guard<std::mutex>lock(mutex);active_root=legacy_ready;status.phase=Phase::ready;status.stage="Existing collection ready";status.downloaded_bytes=status.total_bytes;status.installed_bytes=status.total_expanded_bytes;status.installed_files=status.total_files;return;}
        worker_trace("persistent directories begin");
        if(!mkdirs(base)||!mkdirs(base+"/downloads")){storage_failure("Cannot create collection storage",base,errno);return;}
        worker_trace("persistent directories ready; downloaded inventory begin");
        if(ready_on_disk()){std::lock_guard<std::mutex>lock(mutex);active_root=ready_root;status.phase=Phase::ready;status.stage="Collection ready";status.downloaded_bytes=status.total_bytes;status.installed_bytes=status.total_expanded_bytes;status.installed_files=status.total_files;return;}
        worker_trace("downloaded inventory incomplete");
        if(interrupted()){interrupted_status();return;}
        // Repair an incomplete same-version tree in private staging. Preserve
        // its checkpoints and all good files; the worker re-fetches only bad packs.
        if(directory(ready_root)&&!directory(stage_root)&&std::rename(ready_root.c_str(),stage_root.c_str())){update(Phase::failed,"Installation failed",storage_error("Cannot stage collection repair"));return;}
        if(!mkdirs(stage_root)){storage_failure("Cannot create safe staging directory",stage_root,errno);return;}
        worker_trace("staged inventory begin");
        std::uint64_t free=0;const auto present=archive_mode?0:std::min(expanded_bytes,staged_bytes(stage_root+"/assets/images"));std::uint64_t required=expanded_bytes-present+maximum_pack;
        if(archive_mode){required=32u<<20;for(std::size_t n=0;n<packs.size();++n){if(pack_done(n))continue;std::uint64_t partial=0;regular(base+"/downloads/"+packs[n].sha+".tar.part",&partial);required+=packs[n].bytes-std::min(packs[n].bytes,partial);}}
        worker_trace("storage preflight begin");const bool measured=available_bytes(base,free);worker_trace(measured?"storage preflight measured":"storage preflight unavailable",measured?0:errno);
        if(measured&&free<required){update(Phase::failed,"Not enough storage","Not enough free space in collection storage: "+std::to_string(required)+" additional bytes required");return;}
        if(!legacy_base.empty()){
#if !defined(PM_COLLECTION_WRITER)
            if(!storage_benchmark()){if(interrupted())interrupted_status();return;}
#endif
            std::string error;if(!import_legacy(error)){if(interrupted())interrupted_status();else update(Phase::failed,"Migration failed",error);return;}
        }
        worker_trace("curl initialization begin");
        static std::once_flag curl_once;static CURLcode curl_status=CURLE_FAILED_INIT;std::call_once(curl_once,[]{curl_status=curl_global_init(CURL_GLOBAL_DEFAULT);});if(curl_status!=CURLE_OK){update(Phase::failed,"Download unavailable","Cannot initialize network");return;}
        completed=0;
        for(std::size_t n=0;n<packs.size();++n){
            {std::lock_guard<std::mutex>lock(mutex);status.pack_index=n;status.downloaded_bytes=completed;}
            if(interrupted()){interrupted_status();return;}const auto&pack=packs[n];const auto path=base+"/downloads/"+pack.sha+".tar.part";
            if(pack_done(n)){account_checkpoint(n);completed+=pack.bytes;continue;}
            if(archive_mode){const auto promoted=stage_root+"/archives/"+pack.sha+".tar";std::uint64_t bytes=0;if(regular(promoted,&bytes)&&bytes==pack.bytes&&hash_pack(pack,promoted)){std::string error;if(!promote_archive(n,promoted,error)){update(Phase::failed,"Installation failed",error);return;}completed+=pack.bytes;continue;}if(interrupted()){interrupted_status();return;}}
            std::string error;if(!download(pack,path,error)){if(!error.empty())update(Phase::failed,"Download failed",error);else if(interrupted())interrupted_status();else update(Phase::failed,"Download failed","Download interrupted");return;}
            if(!hash_pack(pack,path)){if(interrupted())interrupted_status();else{std::remove(path.c_str());update(Phase::failed,"Verification failed","Collection pack checksum does not match the bundled manifest");}return;}
            if(archive_mode){if(!promote_archive(n,path,error)){if(interrupted())interrupted_status();else update(Phase::failed,"Installation failed",error);return;}}
            else if(!extract(pack,path,n,error)){if(interrupted())interrupted_status();else update(Phase::failed,"Installation failed",error);return;}
            completed+=pack.bytes;if(!archive_mode)std::remove(path.c_str());
        }
        if(interrupted()){interrupted_status();return;}
        if(archive_mode){const auto registry=read_bounded(bundled+"/assets/images/manifest.json",16u<<20,true);if(!registry.ok||digest_text(registry.bytes)!=image_manifest_sha){update(Phase::failed,"Installation failed","Bundled image registry checksum does not match the collection");return;}if(!mkdirs(stage_root+"/assets/images")||!atomic_text(stage_root+"/assets/images/manifest.json",registry.bytes)||!sync_directory(stage_root+"/assets")){storage_failure("Cannot activate bundled image registry",stage_root,errno);return;}}
        if(!regular(stage_root+"/assets/images/manifest.json")){update(Phase::failed,"Installation failed","Collection image manifest is missing");return;}
        if(!image_manifest_sha.empty()&&!archive_mode){
            Pack image_index;image_index.id="image index";image_index.sha=image_manifest_sha;regular(stage_root+"/assets/images/manifest.json",&image_index.bytes);
            if(!hash_pack(image_index,stage_root+"/assets/images/manifest.json")){if(interrupted())interrupted_status();else update(Phase::failed,"Verification failed","Collection image manifest checksum does not match");return;}
        }
        const auto index_sha=digest_text(read_small(stage_root+"/assets/images/manifest.json",16u<<20));
        if(!atomic_text(stage_root+"/.complete.json",Json({{"schema_version",1},{"manifest_sha256",manifest_sha},{"image_manifest_sha256",index_sha},{"pack_count",packs.size()}}).dump())||std::rename(stage_root.c_str(),ready_root.c_str())||!sync_directory(base)){update(Phase::failed,"Installation failed",storage_error("Cannot activate completed collection"));return;}
        std::lock_guard<std::mutex>lock(mutex);active_root=ready_root;status.phase=Phase::ready;status.stage="Collection ready";status.downloaded_bytes=status.total_bytes;status.installed_bytes=status.total_expanded_bytes;status.installed_files=status.total_files;status.bytes_per_second=0;
    }
};
CollectionInstaller::CollectionInstaller():impl_(new Impl){}
CollectionInstaller::~CollectionInstaller(){shutdown();}
bool CollectionInstaller::configure(const std::string& manifest_path,const std::string& data_directory,const std::string& bundled_root,bool allow_http_for_tests,const std::string&legacy_data_directory){
    shutdown();auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);std::lock_guard<std::mutex>lock(p.mutex);p.status={};p.configured=false;p.active_root.clear();p.packs.clear();
    const auto source=read_bounded(manifest_path,1u<<20,true);
    if(!source.ok){
        if(source.operation=="open"&&verified_missing_bundle(manifest_path,source.code)){p.status.diagnostic="Legacy bundled manifest confirmed absent: "+manifest_path;return false;}
        p.status.phase=Phase::failed;p.status.stage="Cannot read collection manifest";p.status.filesystem_errno=source.code;p.status.error="The bundled collection manifest could not be read";p.status.diagnostic=source.operation+" ["+manifest_path+"] errno="+std::to_string(source.code)+" ("+std::strerror(source.code)+"); legacy bypass refused";return false;
    }
    const auto&raw=source.bytes;auto j=Json::parse(raw,nullptr,false);
    const auto reject=[&](const char*why){p.status.phase=Phase::failed;p.status.error=why;p.status.stage="Invalid collection manifest";p.status.diagnostic=std::string(why)+" ["+manifest_path+"]";return false;};
    if(data_directory.empty()||data_directory.front()!='/'||data_directory=="/app0"||data_directory.rfind("/app0/",0)==0||data_directory.find("..")!=std::string::npos||data_directory.find('\\')!=std::string::npos)return reject("Persistent writable collection directory required");
    if(!legacy_data_directory.empty()&&(legacy_data_directory.front()!='/'||legacy_data_directory=="/app0"||legacy_data_directory.rfind("/app0/",0)==0||legacy_data_directory.find("..")!=std::string::npos||legacy_data_directory.find('\\')!=std::string::npos))return reject("Invalid legacy collection directory");
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
    p.status.total_expanded_bytes=p.expanded_bytes;for(const auto&pack:p.packs)p.status.total_files+=pack.file_count;
    if(j.contains("file_count")){if(!j["file_count"].is_number_unsigned())return reject("Invalid collection file count");const auto expected=j["file_count"].get<std::uint64_t>();if(p.status.total_files&&expected!=p.status.total_files)return reject("Inconsistent collection file count");p.status.total_files=expected;}
    p.installed_pack_bytes.assign(p.packs.size(),0);p.installed_pack_files.assign(p.packs.size(),0);
    p.image_manifest_sha.clear();if(j.contains("image_manifest_sha256")){if(!j["image_manifest_sha256"].is_string()||!hex_sha(j["image_manifest_sha256"].get<std::string>()))return reject("Invalid image manifest checksum");p.image_manifest_sha=j["image_manifest_sha256"].get<std::string>();}
    p.manifest_sha=digest_text(raw);if(p.manifest_sha.empty())return reject("Cannot identify bundled manifest");p.collection_id=j["collection_id"].get<std::string>();p.archive_index_path=parent(manifest_path)+"/collection-archive-index.json";p.archive_mode=false;p.base=data_directory+"/collection";const auto suffix=p.collection_id+"-"+p.manifest_sha.substr(0,24);p.stage_root=p.base+"/.stage-"+suffix;p.ready_root=p.base+"/"+suffix;p.legacy_base=legacy_data_directory.empty()||legacy_data_directory==data_directory?std::string():legacy_data_directory+"/collection";p.legacy_stage=p.legacy_base+"/.stage-"+suffix;p.legacy_ready=p.legacy_base+"/"+suffix;p.bundled=bundled_root;p.allow_http=allow_http_for_tests;p.configured=true;p.status.phase=Phase::idle;p.status.pack_count=p.packs.size();p.status.stage="Collection installation required";return true;
}
bool CollectionInstaller::start(){
    auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);if(!p.configured||p.running.load())return false;
    if(p.worker_joinable){pthread_join(p.worker,nullptr);p.worker_joinable=false;}
    {std::lock_guard<std::mutex>lock(p.mutex);if(p.status.phase==Phase::ready)return true;p.status.error.clear();}
    pthread_attr_t attributes;int code=pthread_attr_init(&attributes);
    if(!code){code=pthread_attr_setstacksize(&attributes,worker_stack_bytes);if(!code){p.command.store(0);p.running.store(true);code=pthread_create(&p.worker,&attributes,[](void*owner)->void*{static_cast<Impl*>(owner)->run();return nullptr;},&p);}pthread_attr_destroy(&attributes);}
    if(code){p.running.store(false);p.update(Phase::failed,"Installation worker unavailable","Cannot start the collection installer",0,"pthread worker initialization error="+std::to_string(code)+" ("+std::strerror(code)+")");worker_trace("worker initialization failed",code);return false;}
    p.worker_joinable=true;return true;
}
bool CollectionInstaller::retry(){return start();}
bool CollectionInstaller::remove_downloaded(){
    auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);
    if(!p.configured||p.running.load(std::memory_order_acquire))return false;
    if(p.worker_joinable){pthread_join(p.worker,nullptr);p.worker_joinable=false;}
    {
        std::lock_guard<std::mutex>lock(p.mutex);p.active_root.clear();p.status.phase=Phase::removing;p.status.stage="Removing downloaded data";
        p.status.error.clear();p.status.diagnostic.clear();p.status.filesystem_errno=0;p.status.bytes_per_second=0;
    }
    pthread_attr_t attributes;int code=pthread_attr_init(&attributes);
    if(!code){code=pthread_attr_setstacksize(&attributes,worker_stack_bytes);if(!code){p.command.store(0);p.running.store(true);code=pthread_create(&p.worker,&attributes,[](void*owner)->void*{static_cast<Impl*>(owner)->run_removal();return nullptr;},&p);}pthread_attr_destroy(&attributes);}
    if(code){p.running.store(false);p.update(Phase::failed,"Could not remove downloaded data","Cannot start the collection removal worker",0,"pthread worker initialization error="+std::to_string(code)+" ("+std::strerror(code)+")");return false;}
    p.worker_joinable=true;return true;
}
void CollectionInstaller::pause(){impl_->command.store(1,std::memory_order_release);}
void CollectionInstaller::cancel(){impl_->command.store(2,std::memory_order_release);}
void CollectionInstaller::shutdown(){if(!impl_)return;auto&p=*impl_;std::lock_guard<std::mutex>control(p.lifecycle);p.command.store(3,std::memory_order_release);if(p.worker_joinable){pthread_join(p.worker,nullptr);p.worker_joinable=false;}}
CollectionInstaller::Status CollectionInstaller::snapshot()const{std::lock_guard<std::mutex>lock(impl_->mutex);auto status=impl_->status;if(status.phase==Phase::downloading&&elapsed_seconds(impl_->last_progress_at)>1.)status.bytes_per_second=0;return status;}
bool CollectionInstaller::is_ready()const{return snapshot().phase==Phase::ready;}
std::string CollectionInstaller::cache_root()const{std::lock_guard<std::mutex>lock(impl_->mutex);return impl_->status.phase==Phase::ready?impl_->active_root:std::string();}
}
