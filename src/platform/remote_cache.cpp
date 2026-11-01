// Pixel Museum - Bounded asynchronous HTTPS image and document cache.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/media.hpp"
#include "gfx/renderer.hpp"
#include "yt/http.hpp"
#include "platform/image_quality.hpp"
#include "platform/media_retry.hpp"
#include "platform/ps5/system.hpp"
#include "core/save_file.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include "platform/collection_archive.hpp"
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <deque>
#include <dirent.h>
#include <map>
#include <mutex>
#include <pthread.h>
#include <sys/stat.h>
#include <vector>
namespace museum::media {
namespace {
constexpr std::size_t kImageBytes = 12u << 20;
constexpr std::size_t kDocumentBytes = 160u << 20;
constexpr std::size_t kDiskBytes = 384u << 20;
constexpr std::size_t kResidentImageBytes = 96u << 20;
constexpr std::size_t kPendingImageBytes = 64u << 20;
using Milliseconds = detail::ImageRetry::Milliseconds;
Milliseconds clock_ms() {
    return static_cast<Milliseconds>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count());
}
std::string origin_for(const std::string&url) {
    const auto end=url.find('/',8);
    std::string origin=url.substr(0,end);
    for(char&c:origin)if(c>='A'&&c<='Z')c=static_cast<char>(c-'A'+'a');
    return origin;
}
std::string name_for(const std::string &url) {
    std::uint64_t value = 14695981039346656037ull;
    for (unsigned char c : url) { value ^= c; value *= 1099511628211ull; }
    char name[24]; std::snprintf(name, sizeof(name), "%016llx.bin", static_cast<unsigned long long>(value));
    return name;
}
bool directory(const std::string &path) {
    for (std::size_t i = 1; i <= path.size(); ++i)
        if (i == path.size() || path[i] == '/')
            mkdir(path.substr(0, i).c_str(), 0777);
    struct stat info{}; return stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode);
}
void prune(const std::string &root) {
    struct File { std::string path; std::uint64_t bytes; long long modified; };
    std::vector<File> files; std::uint64_t total = 0;
    DIR *dir = opendir(root.c_str()); if (!dir) return;
    while (dirent *item = readdir(dir)) {
        const std::string name = item->d_name;
        if (name.size() != 20 || name.substr(16) != ".bin") continue;
        const std::string path = root + "/" + name; struct stat s{};
        if (stat(path.c_str(), &s) != 0 || !S_ISREG(s.st_mode)) continue;
        files.push_back({path, static_cast<std::uint64_t>(s.st_size), static_cast<long long>(s.st_mtime)});
        total += static_cast<std::uint64_t>(s.st_size);
    }
    closedir(dir);
    std::sort(files.begin(), files.end(), [](const File &a, const File &b) { return a.modified < b.modified; });
    for (const auto &f : files) { if (total <= kDiskBytes) break; if (std::remove(f.path.c_str()) == 0) total -= f.bytes; }
}
}
struct RemoteCache::Impl {
    struct Entry { Asset asset; bool image = true, deferred=false, preview=false, resident_preview=false, preview_failed=false, priority_deferred=false; std::vector<std::uint8_t> pixels; std::uint64_t used = 0; detail::ImageRetry retry; GLuint uploading=0; int upload_row=0, texture_width=0, texture_height=0; };
    static Asset displayed_asset(const Entry&e){
        Asset result=e.asset;
        if(result.texture&&e.texture_width>0&&e.texture_height>0){result.width=e.texture_width;result.height=e.texture_height;}
        return result;
    }
    mutable std::mutex mutex; std::condition_variable wake;
    std::map<std::string, Entry> entries; std::deque<std::string> queue;
    std::string root; pthread_t thread{}; bool running = false, stopping = false;
    std::uint64_t tick = 0;
    bool model_pressure=false;
    detail::CollectionArchive archives;
    bool packaged_only=false;std::map<std::string,std::string> packaged,previews,image_hashes;
    std::vector<std::string> warm;
    std::deque<std::string> prefetch,bulk;
    std::vector<std::string> clear_urls;
    ImageDownload download;
    unsigned disk_generation=0;
    bool clear_pending=false;
    std::string image_path(const std::string&url,bool offline=false)const{return root+(offline?"/offline/":"/photos/")+name_for(url);}
    bool saved_image(const std::string&url)const{
        struct stat info{};
        for(const auto&path:{image_path(url,true),image_path(url),root+"/"+name_for(url)})
            if(stat(path.c_str(),&info)==0&&info.st_size>0)return true;
        return false;
    }
    bool disk_image(const std::string&url,bool offline,unsigned generation){
        const auto destination=image_path(url,offline);
        std::string body;
        struct stat info{};
        for(const auto&path:{image_path(url,true),destination,image_path(url),root+"/"+name_for(url)}){
            if(stat(path.c_str(),&info)!=0||info.st_size<=0||std::size_t(info.st_size)>=detail::kPhotoLocalBytes)continue;
            if(!offline||path==destination)return true;
            FILE*f=std::fopen(path.c_str(),"rb");if(!f)continue;
            body.resize(std::size_t(info.st_size));const auto got=std::fread(body.data(),1,body.size(),f);std::fclose(f);
            if(got!=body.size())body.clear();else break;
        }
        if(body.empty()){
            yt::http::Request request;request.url=url;request.max_bytes=kImageBytes;request.timeout_s=18;
            request.headers.push_back({"User-Agent","PixelMuseum/0.1 (PS5 historical collection)"});
            auto response=yt::http::perform(request);
            if(!response.http_ok()||response.body.empty()||response.body.size()>=kImageBytes)return false;
            body=std::move(response.body);
            int w=0,h=0,sw=0,sh=0;std::vector<std::uint8_t> pixels;std::string error;
            if(!detail::prepare_photo(body,&w,&h,&sw,&sh,&pixels,&error))return false;
        }
        std::lock_guard<std::mutex> lock(mutex);
        if(stopping||generation!=disk_generation)return false;
        const std::string temporary=destination+".part";
        FILE*f=std::fopen(temporary.c_str(),"wb");if(!f)return false;
        const bool written=std::fwrite(body.data(),1,body.size(),f)==body.size();
        const bool closed=std::fclose(f)==0;
        if(!written||!closed||std::rename(temporary.c_str(),destination.c_str())!=0){std::remove(temporary.c_str());return false;}
        return true;
    }
    void erase_images(const std::vector<std::string>&urls){
        // Only image directories and image URL hashes; never models, preferences or video data.
        for(const auto&folder:{root+"/photos",root+"/offline"}){
            DIR*dir=opendir(folder.c_str());if(!dir)continue;
            while(auto*item=readdir(dir)){const std::string name=item->d_name;
                if((name.size()==20&&name.substr(16)==".bin")||(name.size()==25&&name.substr(16)==".bin.part"))
                    std::remove((folder+"/"+name).c_str());
            }closedir(dir);
        }
        for(const auto&url:urls)std::remove((root+"/"+name_for(url)).c_str());
    }
    std::vector<std::string> visible;
    std::map<std::string,Milliseconds> host_cooldowns;
    Milliseconds next_automatic = 0;
    Milliseconds host_due(const std::string&url) const {
        const auto found=host_cooldowns.find(origin_for(url));
        return found==host_cooldowns.end()?0:found->second;
    }
    void cool_host(const std::string&url,Milliseconds due,Milliseconds now) {
        for(auto it=host_cooldowns.begin();it!=host_cooldowns.end();)
            if(it->second<=now)it=host_cooldowns.erase(it);else ++it;
        const auto origin=origin_for(url);
        if(!host_cooldowns.count(origin)&&host_cooldowns.size()>=64) {
            auto oldest=std::min_element(host_cooldowns.begin(),host_cooldowns.end(),
                [](const auto&a,const auto&b){return a.second<b.second;});
            host_cooldowns.erase(oldest);
        }
        auto&existing=host_cooldowns[origin];existing=std::max(existing,due);
    }
    // Only declared visible photos are eligible; an empty pin list is not a
    // licence to retry the entire visited collection. No GL or frame polling.
    bool next_work(std::string&url,bool&image,bool&preview,int&kind,std::unique_lock<std::mutex>&lock) {
        for(;;) {
            if(stopping)return false;
            if(clear_pending){kind=3;return true;}
            const auto now=clock_ms();Milliseconds earliest=detail::ImageRetry::never;
            for(auto it=queue.begin();it!=queue.end();++it) {
                const auto&entry=entries.at(*it);
                if(model_pressure&&entry.image&&std::find(visible.begin(),visible.end(),*it)==visible.end())continue;
                const auto due=entry.image?host_due(*it):0;
                if(due<=now) {url=std::move(*it);queue.erase(it);image=entries.at(url).image;preview=entries.at(url).preview;return true;}
                earliest=std::min(earliest,due);
            }
            for(const auto&visible_url:visible) {
                const auto found=entries.find(visible_url);if(found==entries.end())continue;
                auto&e=found->second;
                if(!e.image||e.asset.state!=State::failed||e.retry.due==detail::ImageRetry::never)continue;
                const auto due=std::max({e.retry.due,host_due(visible_url),next_automatic});
                if(e.retry.eligible(e.image,true,now)&&due<=now) {
                    url=visible_url;image=true;e.asset.state=State::loading;
                    next_automatic=detail::ImageRetry::after(now,1000);
                    hui::sys::log("[Museum] photo retry %s attempt %u/3",name_for(url).c_str(),e.retry.failures);
                    return true;
                }
                earliest=std::min(earliest,due);
            }
            if(packaged_only)for(const auto&candidate:warm){
                if(model_pressure&&std::find(visible.begin(),visible.end(),candidate)==visible.end())continue;
                if(!previews.count(candidate))continue;
                auto found=entries.find(candidate);
                if(found==entries.end()){if(entries.size()>=512)continue;found=entries.emplace(candidate,Entry{}).first;}
                auto&e=found->second;
                if(e.asset.state!=State::idle)continue;
                if(e.deferred){if(!e.priority_deferred||primary_pending())continue;e.deferred=false;e.priority_deferred=false;}
                e.image=true;e.preview=true;e.asset.state=State::loading;e.used=++tick;
                url=candidate;image=true;preview=true;return true;
            }
            if(!prefetch.empty()){url=std::move(prefetch.front());prefetch.pop_front();kind=1;return true;}
            if(download.active&&!bulk.empty()){url=std::move(bulk.front());bulk.pop_front();kind=2;return true;}
            if(earliest==detail::ImageRetry::never)wake.wait(lock);
            else wake.wait_for(lock,std::chrono::milliseconds(earliest>now?earliest-now:1));
        }
    }
    std::size_t pending_bytes() const {std::size_t total=0;for(const auto&[url,e]:entries){(void)url;total+=e.pixels.size();}return total;}
    std::size_t priority(const std::string&url) const {const auto it=std::find(visible.begin(),visible.end(),url);return it==visible.end()?visible.size():static_cast<std::size_t>(it-visible.begin());}
    bool primary_pending() const {
        if(visible.empty())return false;
        const auto it=entries.find(visible.front());if(it==entries.end())return true;
        const auto&e=it->second;
        return e.asset.state!=State::failed&&(!e.asset.texture||e.asset.state==State::loading||!e.pixels.empty()||e.uploading);
    }
    // This also applies when a request arrives after set_visible(). Admit a
    // newly focused photo by deferring a lower-priority queued image, never
    // an in-flight job/document or an already visible higher-priority request.
    bool enqueue(const std::string&url) {
        if(std::find(queue.begin(),queue.end(),url)!=queue.end())return true;
        const auto rank=priority(url);
        if(queue.size()>=16){
            auto victim=queue.end();
            for(auto it=queue.begin();it!=queue.end();++it)if(entries.at(*it).image&&priority(*it)>rank&&(victim==queue.end()||priority(*it)>priority(*victim)))victim=it;
            if(victim==queue.end())return false;
            auto&e=entries.at(*victim);e.asset.state=e.asset.texture?State::ready:State::idle;e.deferred=true;e.priority_deferred=true;queue.erase(victim);
        }
        const auto place=std::find_if(queue.begin(),queue.end(),[&](const auto&queued){return priority(queued)>rank;});
        queue.insert(place,url);wake.notify_one();return true;
    }
    bool can_revisit(const std::string&url,const Entry&e) const {
        if(!e.deferred||visible.empty())return true;
        const auto rank=priority(url);if(rank==visible.size()||(rank>0&&primary_pending()))return false;
        // Eviction leaves the master's dimensions behind. They must not bar
        // a visible neighbour's much smaller installed preview from returning.
        // Its actual decoded size is still checked by the upload residency gate.
        if(!e.asset.texture&&packaged_only&&!e.preview_failed&&previews.count(url))return true;
        std::size_t bytes=static_cast<std::size_t>(e.asset.width)*e.asset.height*4;
        for(const auto&[key,item]:entries)if(item.asset.texture&&priority(key)<rank)bytes+=static_cast<std::size_t>(item.asset.width)*item.asset.height*4;
        return bytes<=kResidentImageBytes;
    }
    static void *entry(void *p) { static_cast<Impl *>(p)->run(); return nullptr; }
    void run() {
        prune(root);prune(root+"/photos");
        for (;;) {
            std::string url; bool image = false,preview=false;int kind=0;unsigned generation=0;
            std::vector<std::string> removing;
            { std::unique_lock<std::mutex> lock(mutex);
              if(!next_work(url,image,preview,kind,lock))return;
              generation=disk_generation;if(kind==3){removing=std::move(clear_urls);clear_pending=false;} }
            if(kind==3){erase_images(removing);std::lock_guard<std::mutex> lock(mutex);download.clearing=false;continue;}
            if(kind==1||kind==2){
                const bool ok=disk_image(url,kind==2,generation);
                if(kind==1)prune(root+"/photos");
                std::lock_guard<std::mutex> lock(mutex);
                if(kind==2&&generation==disk_generation&&download.active){++download.completed;if(!ok)++download.failed;if(bulk.empty())download.active=false;}
                continue;
            }
            Asset result; result.path = image?image_path(url):root+"/"+name_for(url);
            if(image&&packaged_only){const auto&files=preview?previews:packaged;const auto found=files.find(url);
                if(found!=files.end())result.path=found->second;
                else{result.state=State::failed;result.error="This image is not included in the installed collection";}}
            if(image&&!packaged_only){struct stat existing{};for(const auto&path:{image_path(url,true),result.path,root+"/"+name_for(url)})
                if(stat(path.c_str(),&existing)==0&&existing.st_size>0){result.path=path;break;}}
            // Installed originals may exceed the network download budget. Both
            // paths still share bounded source decoding and retained GPU limits.
            const std::size_t byte_limit=image?kImageBytes:kDocumentBytes;
            const std::size_t local_byte_limit=image?detail::kPhotoLocalBytes:kDocumentBytes;
            std::string body;
            long failed_http_status=0;
            struct stat info{};
            if(image&&packaged_only&&archives.contains(result.path)){archives.read(result.path,body,local_byte_limit);}
            else if (stat(result.path.c_str(), &info) == 0 && info.st_size > 0 && static_cast<std::size_t>(info.st_size) < local_byte_limit) {
                FILE *file=std::fopen(result.path.c_str(),"rb");
                if (file) {
                    body.resize(static_cast<std::size_t>(info.st_size));
                    const auto got=std::fread(body.data(),1,body.size(),file); std::fclose(file);
                    if (got!=body.size()) body.clear();
                    else hui::sys::log("[Museum] media disk cache %s",name_for(url).c_str());
                }
            }
            if(body.empty()&&image&&packaged_only){result.state=State::failed;result.error="The installed image could not be read";}
            if (body.empty()&&!(image&&packaged_only)) {
                yt::http::Request request; request.url = url; request.max_bytes = byte_limit; request.timeout_s = image?18:45;
                request.headers.push_back({"User-Agent","PixelMuseum/0.1 (PS5 historical collection)"});
                auto response = yt::http::perform(request);
                if (!response.http_ok() || response.body.empty() || response.body.size() >= byte_limit) {
                    result.state = State::failed;
                    if(!response.http_ok()&&response.error.empty())failed_http_status=response.status;
                    result.error = response.error.empty() ? "Media server returned HTTP " + std::to_string(response.status) : response.error;
                } else {
                    body = std::move(response.body);
                    const std::string temporary = result.path + ".part";
                    FILE *file = std::fopen(temporary.c_str(), "wb");
                    if (file) { const auto written = std::fwrite(body.data(), 1, body.size(), file); std::fclose(file);
                        if (written == body.size()) std::rename(temporary.c_str(), result.path.c_str()); else std::remove(temporary.c_str()); }
                    prune(image?root+"/photos":root);
                }
            }
            std::vector<std::uint8_t> pixels;
            if (result.state != State::failed) {
                if (image && !detail::prepare_photo(body, &result.width, &result.height, &result.source_width, &result.source_height, &pixels, &result.error)) {
                    result.state = State::failed;if(!(image&&packaged_only))std::remove(result.path.c_str());
                } else result.state = State::ready;

            }
            if(image&&result.state==State::ready)hui::sys::log("[Museum] photo %s source %dx%d / retained %dx%d / %zu KiB RGBA",name_for(url).c_str(),result.source_width,result.source_height,result.width,result.height,pixels.size()>>10);
            if (result.state==State::failed) hui::sys::log("[Museum] media failed %s: %s",name_for(url).c_str(),result.error.c_str());
            { std::unique_lock<std::mutex> lock(mutex);
              const auto hidden_under_pressure=[&]{return image&&model_pressure&&std::find(visible.begin(),visible.end(),url)==visible.end();};
              wake.wait(lock,[&]{return stopping||hidden_under_pressure()||pending_bytes()+pixels.size()<=kPendingImageBytes;});if(stopping)return;
              if(hidden_under_pressure()){auto&e=entries[url];e.asset.state=State::idle;e.deferred=true;continue;}
              auto &e=entries[url];
              if(image&&!preview&&result.state==State::failed&&e.asset.texture){
                  // A failed master must not replace a resident preview's
                  // dimensions with zero: the UI would draw zero-width geometry.
                  // Keep all visible metadata and suppress repeated promotion.
                  e.asset.state=State::ready;e.asset.error=std::move(result.error);
                  e.preview=false;e.deferred=false;e.priority_deferred=false;e.retry.reset();
                  wake.notify_all();continue;
              }
              result.texture=e.asset.texture;e.asset=std::move(result);e.pixels=std::move(pixels);e.deferred=false;e.priority_deferred=false;e.preview=preview;
              if(image&&preview&&e.asset.state==State::failed){
                  // A damaged optional preview must not hide a valid installed
                  // master, nor retry the same preview indefinitely.
                  e.preview_failed=true;e.preview=false;e.asset.state=State::idle;
                  if(enqueue(url))e.asset.state=State::loading;
                  wake.notify_all();continue;
              }
              const auto now=clock_ms();
              if(image&&e.asset.state==State::failed&&detail::ImageRetry::transient(failed_http_status)) {
                  e.retry.failed(failed_http_status,now);
                  const auto delay=e.retry.due==detail::ImageRetry::never?60000:e.retry.due-now;
                  cool_host(url,detail::ImageRetry::after(now,delay),now);
                  hui::sys::log("[Museum] photo HTTP %ld %s: %s / host cooldown %llu ms",failed_http_status,name_for(url).c_str(),
                      e.retry.due==detail::ImageRetry::never?"automatic retries exhausted":"retry only while visible",
                      static_cast<unsigned long long>(delay));
              } else e.retry.reset(); }
        }
    }
};
RemoteCache::RemoteCache() : impl_(std::make_unique<Impl>()) {}
RemoteCache::~RemoteCache() { stop(); }
bool packaged_images_complete(const std::string&root){
    const auto safe=[](const std::string&path){return path.rfind("assets/images/",0)==0&&path.find("..") == std::string::npos&&path.find('\\')==std::string::npos&&path.find(':')==std::string::npos;};
    std::string bytes;
    if(!hui::save::read_file(root+"/assets/images/manifest.json",&bytes,16u<<20))return false;
    const auto manifest=nlohmann::json::parse(bytes,nullptr,false);
    if(!manifest.is_object()||!manifest.contains("images")||!manifest["images"].is_object()||manifest["images"].empty())return false;
    std::map<std::string,std::uint64_t> sizes;
    std::string index_bytes;
    if(hui::save::read_file(root+"/content/collection-files.json",&index_bytes,16u<<20)){
        const auto index=nlohmann::json::parse(index_bytes,nullptr,false);
        if(!index.is_object()||index.value("schema_version",0)!=1||!index.contains("files")||!index["files"].is_array()||index["files"].empty())return false;
        for(const auto&file:index["files"]){
            if(!file.is_object()||!file.contains("path")||!file["path"].is_string()||!file.contains("bytes")||!file["bytes"].is_number_unsigned())return false;
            const auto path=file["path"].get<std::string>();const auto expected=file["bytes"].get<std::uint64_t>();
            if(!safe(path)||expected==0||!sizes.emplace(path,expected).second)return false;
            struct stat st{};if(stat((root+"/"+path).c_str(),&st)!=0||!S_ISREG(st.st_mode)||st.st_size<=0||static_cast<std::uint64_t>(st.st_size)!=expected)return false;
        }
    }
    for(const char*key:{"images","previews"}){
        if(!manifest.contains(key)){if(std::string(key)=="images")return false;continue;}
        if(!manifest[key].is_object())return false;
        for(auto it=manifest[key].begin();it!=manifest[key].end();++it){
            if(!it.value().is_string())return false;const auto path=it.value().get<std::string>();if(!safe(path))return false;
            if(!sizes.empty()){if(!sizes.count(path))return false;}
            else{struct stat st{};if(stat((root+"/"+path).c_str(),&st)!=0||!S_ISREG(st.st_mode)||st.st_size<=0)return false;}
        }
    }
    return true;
}
bool RemoteCache::images_from_package(const std::string&root,const std::string&collection_root){
    if(impl_->running)return false;
    impl_->packaged_only=true;impl_->packaged.clear();impl_->previews.clear();impl_->image_hashes.clear();impl_->archives.slices.clear();std::string bytes;
    const auto& image_root=collection_root.empty()?root:collection_root;
    if(!impl_->archives.load(root+"/content/collection-archive-index.json",image_root))return false;
    if(!hui::save::read_file(image_root+"/assets/images/manifest.json",&bytes,16u<<20))return false;
    const auto manifest=nlohmann::json::parse(bytes,nullptr,false);if(!manifest.is_object())return false;
    impl_->packaged.clear();impl_->previews.clear();impl_->image_hashes.clear();
    // A collection may be installed after an initial failed request. Registration
    // happens with the worker stopped; allow those images to load on restart.
    for(auto&[url,e]:impl_->entries){(void)url;if(e.image&&e.asset.state==State::failed&&!e.asset.texture&&!e.uploading){e.asset=Asset{};e.retry.reset();e.preview_failed=false;e.preview=false;e.deferred=false;}}
    const auto read=[&](const char*key,std::map<std::string,std::string>&out){
        if(!manifest.contains(key)||!manifest[key].is_object())return;
        for(auto it=manifest[key].begin();it!=manifest[key].end();++it){if(!it.value().is_string())continue;const auto path=it.value().get<std::string>();
            if(path.rfind("assets/images/",0)==0&&path.find("..") == std::string::npos&&path.find('\\')==std::string::npos&&path.find(':')==std::string::npos)out[it.key()]=image_root+"/"+path;}
    };read("images",impl_->packaged);read("previews",impl_->previews);
    if(manifest.contains("metadata")&&manifest["metadata"].is_object())for(auto it=manifest["metadata"].begin();it!=manifest["metadata"].end();++it){
        const auto&value=it.value();if(!value.is_object()||!value.contains("sha256")||!value["sha256"].is_string())continue;
        auto hash=value["sha256"].get<std::string>();if(hash.size()!=64||!std::all_of(hash.begin(),hash.end(),[](unsigned char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F');}))continue;
        for(auto&c:hash)if(c>='A'&&c<='F')c=char(c-'A'+'a');impl_->image_hashes[it.key()]=std::move(hash);
    }
    // Pin fronts share the bounded asynchronous image cache, but keep their
    // own manifest so editorial packaging cannot overwrite or fetch them.
    std::string pins;
    if(hui::save::read_file(root+"/assets/trophies/fronts/index.json",&pins,1u<<20)){
        const auto index=nlohmann::json::parse(pins,nullptr,false);
        if(index.is_object())for(auto it=index.begin();it!=index.end();++it){
            if(!it.value().is_string()||it.key().rfind("museum-pin:",0)!=0)continue;
            const auto path=it.value().get<std::string>();
            if(path.rfind("assets/trophies/fronts/",0)==0&&path.find("..") == std::string::npos&&
               path.find('\\')==std::string::npos&&path.find(':')==std::string::npos)
                impl_->packaged[it.key()]=root+"/"+path;
        }
    }
    return !impl_->packaged.empty();
}
std::string RemoteCache::image_identity(const std::string&url) const {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    if(const auto it=impl_->image_hashes.find(url);it!=impl_->image_hashes.end())return it->second;
    if(const auto it=impl_->packaged.find(url);it!=impl_->packaged.end())return it->second;
    return url;
}
bool RemoteCache::start(const std::string &root) {
    if (impl_->running) return true;
    if (!directory(root)) return false;
    impl_->root = root;directory(root+"/photos");directory(root+"/offline"); impl_->stopping = false;
    pthread_attr_t attr; pthread_attr_init(&attr); pthread_attr_setstacksize(&attr, 1u << 20);
    const int rc = pthread_create(&impl_->thread, &attr, &Impl::entry, impl_.get()); pthread_attr_destroy(&attr);
    impl_->running = rc == 0; return impl_->running;
}
void RemoteCache::stop() {
    if (!impl_->running) return;
    { std::lock_guard<std::mutex> lock(impl_->mutex); impl_->stopping = true; impl_->wake.notify_one(); }
    pthread_join(impl_->thread, nullptr); impl_->running = false;
}
Asset RemoteCache::request(const std::string &url, bool image) {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    auto found = impl_->entries.find(url);
    if (found != impl_->entries.end()) {
        found->second.used = ++impl_->tick;
        // Document metadata may outlive its file when the bounded disk cache
        // evicts an old model. Revisit it through the worker rather than hand
        // the scene loader a permanently missing path.
        if (!found->second.image && found->second.asset.state==State::ready) {
            struct stat info{};
            if (stat(found->second.asset.path.c_str(),&info)!=0 || info.st_size<=0)
                found->second.asset.state=State::idle;
        }
        // Neighbour cards retain their small previews. Only the focused photo
        // promotes to its master; otherwise a large neighbour repeatedly decodes
        // a master that cannot fit beside the protected focused texture.
        if(image&&(impl_->visible.empty()||impl_->priority(url)==0)&&found->second.resident_preview&&found->second.asset.state==State::ready&&found->second.asset.texture&&!found->second.uploading&&found->second.pixels.empty()&&found->second.asset.error.empty()&&impl_->can_revisit(url,found->second)){found->second.asset.state=State::idle;found->second.preview=false;found->second.deferred=false;}
        if (found->second.asset.state==State::idle && impl_->can_revisit(url,found->second) && impl_->running){
            if(image&&!found->second.asset.texture&&!found->second.preview_failed&&impl_->packaged_only&&impl_->previews.count(url))found->second.preview=true;
            if(impl_->enqueue(url))found->second.asset.state=State::loading;
        }
        return Impl::displayed_asset(found->second);
    }
    Asset failure; failure.state = State::failed;
    if ((url.rfind("https://", 0) != 0&&!impl_->packaged.count(url)) || url.size() > 4096) { failure.error = "Exhibit media requires HTTPS or registered packaged artwork"; return failure; }
    if (!impl_->running) { failure.state = State::idle; return failure; }
    if (impl_->entries.size() >= 512) {
        // A large catalogue must not stop loading after the first 512 visited
        // URLs. Only recycle inactive records: GL texture deletion stays on the
        // frame thread, and queued/in-flight work retains its map entry.
        auto oldest=impl_->entries.end();
        for(auto i=impl_->entries.begin();i!=impl_->entries.end();++i)
            if(i->second.asset.state!=State::loading && !i->second.asset.texture && i->second.pixels.empty()
               && (oldest==impl_->entries.end() || i->second.used<oldest->second.used)) oldest=i;
        if(oldest==impl_->entries.end()) { failure.state=State::idle; return failure; }
        impl_->entries.erase(oldest);
    }
    auto &e = impl_->entries[url]; e.image = image; e.used = ++impl_->tick;
    // Cold selections get a real packaged preview before the full master.
    // The master still decodes asynchronously and replaces it only when every
    // original-resolution row has reached private GL storage.
    e.preview=image&&impl_->packaged_only&&impl_->previews.count(url);
    e.asset.state=impl_->enqueue(url)?State::loading:State::idle;return e.asset;
}
Asset RemoteCache::get(const std::string &url) const {
    std::lock_guard<std::mutex> lock(impl_->mutex); const auto it = impl_->entries.find(url);
    return it == impl_->entries.end() ? Asset{} : Impl::displayed_asset(it->second);
}
void RemoteCache::retry(const std::string &url) {
    { std::lock_guard<std::mutex> lock(impl_->mutex);
      auto it=impl_->entries.find(url); if(it==impl_->entries.end() || it->second.asset.state==State::loading || !it->second.pixels.empty()) return;
      it->second.asset.state=State::idle; it->second.asset.error.clear(); it->second.retry.reset(); }
    request(url);
}
void RemoteCache::set_visible(const std::vector<std::string>&urls) {
    std::vector<std::string> next;
    for(const auto&url:urls)if(next.size()<24&&std::find(next.begin(),next.end(),url)==next.end())next.push_back(url);
    std::lock_guard<std::mutex> lock(impl_->mutex);
    if(next==impl_->visible)return;
    impl_->visible=std::move(next);
    std::stable_sort(impl_->queue.begin(),impl_->queue.end(),[&](const auto&a,const auto&b){return impl_->priority(a)<impl_->priority(b);});
    impl_->wake.notify_one();
}
std::size_t RemoteCache::set_model_pressure(bool enabled) {
    std::lock_guard<std::mutex> lock(impl_->mutex);const bool changed=impl_->model_pressure!=enabled;impl_->model_pressure=enabled;std::size_t released=0;
    if(enabled)for(auto&[url,e]:impl_->entries){
        if(std::find(impl_->visible.begin(),impl_->visible.end(),url)!=impl_->visible.end())continue;
        if(e.uploading){glDeleteTextures(1,&e.uploading);e.uploading=0;e.upload_row=0;}
        if(e.asset.texture){released+=std::size_t(e.texture_width)*e.texture_height*4;GLuint name=e.asset.texture;glDeleteTextures(1,&name);e.asset.texture=0;e.texture_width=e.texture_height=0;}
        if(e.image&&(!e.pixels.empty()||e.asset.state==State::ready)){e.pixels.clear();e.pixels.shrink_to_fit();e.asset.state=State::idle;e.deferred=true;}
    }
    if(changed||enabled)impl_->wake.notify_all();
    if(released)hui::sys::log("[Museum] large model pressure released %zu MiB nonvisible photos; original disk images retained",released>>20);
    return released;
}
void RemoteCache::upload_pending(hui::gfx::Renderer &renderer) {
    (void)renderer;
    std::lock_guard<std::mutex> lock(impl_->mutex);
    // Finish one bounded transfer before allocating another texture. A 4K
    // photograph must not submit its entire 64 MiB payload in a single frame.
    // Keep an existing preview visible until all rows of its replacement exist.
    constexpr std::size_t transfer_bytes=2u<<20;
    if(!impl_->visible.empty()){
        const auto primary=impl_->entries.find(impl_->visible.front());
        if(primary!=impl_->entries.end()){
            auto&e=primary->second;
            if(e.resident_preview&&e.asset.state==State::ready&&!e.uploading&&e.pixels.empty()&&e.asset.error.empty()&&impl_->enqueue(primary->first)){e.preview=false;e.deferred=false;e.asset.state=State::loading;}
        }
    }
    // An obsolete private 4K upload must not pin all64MiB of staging and hold
    // the one worker ahead of a newly focused preview/master. Only incomplete
    // lower-priority work is discarded; completed photo textures remain intact.
    if(impl_->primary_pending())for(auto&[url,e]:impl_->entries){
        if(impl_->priority(url)==0||(!e.uploading&&e.pixels.empty()))continue;
        if(e.uploading){glDeleteTextures(1,&e.uploading);e.uploading=0;e.upload_row=0;}
        e.pixels.clear();e.pixels.shrink_to_fit();e.asset.state=e.asset.texture?State::ready:State::idle;e.deferred=true;e.priority_deferred=true;
        impl_->wake.notify_all();
    }
    unsigned count=0;
    while(count<1) {
        auto selected=impl_->entries.end();
        for(auto it=impl_->entries.begin();it!=impl_->entries.end();++it)if((it->second.uploading||!it->second.pixels.empty())&&(!impl_->model_pressure||std::find(impl_->visible.begin(),impl_->visible.end(),it->first)!=impl_->visible.end())) {
            const auto rank=impl_->priority(it->first);
            if(selected==impl_->entries.end()||rank<impl_->priority(selected->first)||(rank==impl_->priority(selected->first)&&((it->second.uploading&&!selected->second.uploading)||(bool(it->second.uploading)==bool(selected->second.uploading)&&it->second.used>selected->second.used))))selected=it;
        }
        if(selected==impl_->entries.end())break;
        auto&e=selected->second;const auto incoming=e.pixels.size();bool room=true;
        for(;;) {
            std::size_t resident=0,bytes=0;auto victim=impl_->entries.end();
            const auto rank=impl_->priority(selected->first);
            for(auto it=impl_->entries.begin();it!=impl_->entries.end();++it)if(it->second.asset.texture&&it!=selected) {
                ++resident;bytes+=static_cast<std::size_t>(it->second.texture_width)*it->second.texture_height*4;
                // Active higher/equal-priority photos survive background uploads.
                const auto other_rank=impl_->priority(it->first);
                if(!impl_->visible.empty()&&other_rank<impl_->visible.size()&&other_rank<=rank)continue;
                if(victim==impl_->entries.end()||other_rank>impl_->priority(victim->first)||(other_rank==impl_->priority(victim->first)&&it->second.used<victim->second.used))victim=it;
            }
            if(resident<24&&bytes+incoming<=kResidentImageBytes)break;
            if(victim==impl_->entries.end()){room=false;break;}
            GLuint old=victim->second.asset.texture;glDeleteTextures(1,&old);victim->second.asset.texture=0;victim->second.texture_width=0;victim->second.texture_height=0;victim->second.asset.state=State::idle;victim->second.deferred=true;
        }
        if(!room) { if(e.uploading)glDeleteTextures(1,&e.uploading);e.uploading=0;e.upload_row=0;e.pixels.clear();e.pixels.shrink_to_fit();e.asset.state=State::idle;e.deferred=true;impl_->wake.notify_all();continue; }
        const auto previous_error=glGetError();if(previous_error!=GL_NO_ERROR)hui::sys::log("[Museum] GL error before photo upload: %u",unsigned(previous_error));
        if(!e.uploading){
            glGenTextures(1,&e.uploading);glBindTexture(GL_TEXTURE_2D,e.uploading);
            glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,e.asset.width,e.asset.height,0,GL_RGBA,GL_UNSIGNED_BYTE,nullptr);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,0);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
        }else glBindTexture(GL_TEXTURE_2D,e.uploading);
        const auto stride=static_cast<std::size_t>(e.asset.width)*4;
        const auto rows=std::min(e.asset.height-e.upload_row,static_cast<int>(std::max(std::size_t(1),transfer_bytes/stride)));
        glPixelStorei(GL_UNPACK_ALIGNMENT,4);
        glTexSubImage2D(GL_TEXTURE_2D,0,0,e.upload_row,e.asset.width,rows,GL_RGBA,GL_UNSIGNED_BYTE,e.pixels.data()+stride*e.upload_row);
        const auto upload_error=glGetError();
        if(upload_error!=GL_NO_ERROR){
            if(e.uploading)glDeleteTextures(1,&e.uploading);e.uploading=0;e.upload_row=0;
            e.asset.state=e.asset.texture?State::ready:State::failed;e.asset.error="The exhibit image could not be uploaded";
            hui::sys::log("[Museum] photo upload failed %dx%d / GL %u",e.asset.width,e.asset.height,unsigned(upload_error));
        }else{
            e.upload_row+=rows;
            if(e.upload_row<e.asset.height)return;
            if(e.asset.texture){GLuint old=e.asset.texture;glDeleteTextures(1,&old);}
            e.asset.texture=e.uploading;e.uploading=0;e.upload_row=0;e.texture_width=e.asset.width;e.texture_height=e.asset.height;e.resident_preview=e.preview;e.asset.state=State::ready;
        }
        e.pixels.clear();e.pixels.shrink_to_fit();e.deferred=false;impl_->wake.notify_all();++count;
    }
}
void RemoteCache::release_textures() {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    for (auto &[url,e] : impl_->entries) { (void)url; if(e.uploading){glDeleteTextures(1,&e.uploading);e.uploading=0;e.upload_row=0;} if (e.asset.texture) { GLuint t = e.asset.texture; glDeleteTextures(1,&t); e.asset.texture = 0;e.texture_width=0;e.texture_height=0; e.asset.state=State::idle;e.deferred=false; } }
    impl_->wake.notify_all();
}
void RemoteCache::prefetch_images(const std::vector<std::string>&urls){
    std::lock_guard<std::mutex> lock(impl_->mutex);impl_->prefetch.clear();
    if(impl_->packaged_only){impl_->warm=urls;impl_->wake.notify_one();return;}
    for(const auto&url:urls)if(url.rfind("https://",0)==0&&url.size()<=4096
        &&std::find(impl_->prefetch.begin(),impl_->prefetch.end(),url)==impl_->prefetch.end())impl_->prefetch.push_back(url);
    impl_->wake.notify_one();
}
void RemoteCache::download_images(const std::vector<std::string>&urls){
    std::lock_guard<std::mutex> lock(impl_->mutex);++impl_->disk_generation;impl_->bulk.clear();
    for(const auto&url:urls)if(url.rfind("https://",0)==0&&url.size()<=4096)impl_->bulk.push_back(url);
    std::sort(impl_->bulk.begin(),impl_->bulk.end());impl_->bulk.erase(std::unique(impl_->bulk.begin(),impl_->bulk.end()),impl_->bulk.end());
    impl_->download={ !impl_->bulk.empty(),false,impl_->bulk.size(),0,0 };impl_->wake.notify_one();
}
void RemoteCache::cancel_download(){
    std::lock_guard<std::mutex> lock(impl_->mutex);++impl_->disk_generation;impl_->bulk.clear();impl_->download.active=false;impl_->wake.notify_one();
}
void RemoteCache::clear_images(const std::vector<std::string>&urls){
    std::lock_guard<std::mutex> lock(impl_->mutex);++impl_->disk_generation;impl_->bulk.clear();impl_->prefetch.clear();
    impl_->download={};impl_->download.clearing=true;impl_->clear_urls=urls;impl_->clear_pending=true;impl_->wake.notify_one();
}
ImageDownload RemoteCache::image_download()const{std::lock_guard<std::mutex> lock(impl_->mutex);return impl_->download;}
} // namespace museum::media
