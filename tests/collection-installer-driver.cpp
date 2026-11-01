// Actual worker exercised by the local HTTP integration harness.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_installer.hpp"
#include "museum/collection_sha256.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cassert>
#include <chrono>
#include <thread>
#include <iostream>
#include <fstream>
#include <unistd.h>
#include <sys/statvfs.h>
#include <cerrno>
#ifdef MUSEUM_COLLECTION_WRITER_TEST
extern thread_local bool pm_writer_test_sink;
#endif
namespace {bool low_space=false,full_storage=false,slow_migration=false,checkpoint_full=false;std::vector<std::size_t>download_writes;}
extern "C" int __real_statvfs(const char*,struct statvfs*);
extern "C" int __wrap_statvfs(const char*path,struct statvfs*info){if(low_space){*info={};info->f_frsize=4096;return 0;}return __real_statvfs(path,info);}
extern "C" ssize_t __real_write(int,const void*,size_t);
extern "C" ssize_t __wrap_write(int fd,const void*bytes,size_t count){if(full_storage){errno=ENOSPC;return -1;}if(slow_migration)usleep(20000);const int saved=errno;char name[4096];const auto n=readlink(("/proc/self/fd/"+std::to_string(fd)).c_str(),name,sizeof(name));if(n>0){const std::string path(name,n);if(checkpoint_full&&path.find("/.pack-")!=std::string::npos&&path.find(".json.tmp")!=std::string::npos){errno=ENOSPC;return -1;}if(path.size()>=9&&path.substr(path.size()-9)==".tar.part"){
#ifdef MUSEUM_COLLECTION_WRITER_TEST
 assert(pm_writer_test_sink&&"Native installer attempted a direct download write");
#endif
 download_writes.push_back(count);}}errno=saved;return __real_write(fd,bytes,count);}
namespace museum::media {
// This test isolates the installer; the actual cache helper has its own worker test.
bool packaged_images_complete(const std::string& root){return root=="test-bundled-complete";}
}
int main(int argc,char**argv){
    using C=museum::CollectionInstaller;using Phase=C::Phase;
    museum::CollectionSha256 empty;assert(empty.finish()=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    museum::CollectionSha256 abc;abc.update("a",1);abc.update("bc",2);assert(abc.finish()=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    museum::CollectionSha256 million;std::string a(1000,'a');for(unsigned n=0;n<1000;++n)million.update(a.data(),a.size());assert(million.finish()=="cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
    assert(argc>=4);const std::string mode=argv[3];low_space=mode=="space-low";full_storage=mode=="space-write";slow_migration=mode=="pause-migrate"||mode=="crash-migrate";C installer;
    checkpoint_full=mode=="archive-checkpoint-full";const std::string bundle=argc>5?argv[5]:(mode=="bundled"?"test-bundled-complete":"");
#ifdef MUSEUM_COLLECTION_WRITER_TEST
    setenv("PM_WRITER_TEST_ROOT",argv[2],1);
#endif
    std::uint64_t first_pack_bytes=0;if(mode=="crash-second"){std::ifstream file(argv[1]);nlohmann::json manifest;file>>manifest;first_pack_bytes=manifest["packs"][0]["bytes"].get<std::uint64_t>();}
    const bool configured=installer.configure(argv[1],argv[2],bundle,true,argc>4?argv[4]:"");
    if(mode=="invalid"){assert(!configured);std::cout<<"invalid manifest rejected\n";return 0;}
    assert(configured&&installer.start());bool acted=false,was_paused=false,retried=false;std::uint64_t paused_bytes=0;
    const auto begin=std::chrono::steady_clock::now();
    for(;;){
        const auto s=installer.snapshot();assert(s.downloaded_bytes<=s.total_bytes);
        assert(s.installed_bytes<=s.total_expanded_bytes);if(s.total_files)assert(s.installed_files<=s.total_files);
        if(s.phase!=Phase::ready)assert(installer.cache_root().empty());
        if(mode=="pause"&&!acted&&s.phase==Phase::downloading&&s.downloaded_bytes>65536){installer.pause();acted=true;}
        if(mode=="pause-migrate"&&!acted&&s.stage=="Migrating collection"&&s.installed_bytes>65536){installer.pause();acted=true;}
        if(mode=="crash-migrate"&&s.stage=="Migrating collection"&&s.installed_bytes>65536)_exit(0);
        if((mode=="pause"||mode=="pause-migrate")&&s.phase==Phase::paused&&!was_paused){paused_bytes=s.downloaded_bytes;std::this_thread::sleep_for(std::chrono::milliseconds(30));assert(installer.snapshot().downloaded_bytes==paused_bytes);was_paused=true;}
        if((mode=="pause"||mode=="pause-migrate")&&was_paused&&!retried)retried=installer.retry();
        if(mode=="retry"&&s.phase==Phase::failed&&!retried){assert(s.downloaded_bytes>0);retried=installer.retry();}
        if(mode=="cancel"&&!acted&&s.phase==Phase::downloading&&s.downloaded_bytes>65536){installer.cancel();acted=true;}
        // Cross the explicit 2 MiB raw buffer before simulating power loss,
        // so this case specifically verifies Range from a real disk prefix.
        if(mode=="crash-second"&&s.pack_index==1&&s.phase==Phase::downloading&&s.downloaded_bytes>first_pack_bytes+(2u<<20)+65536)_exit(0);
        if(s.phase==Phase::ready){assert(mode!="fail"&&mode!="cancel"&&mode!="crash-second");assert(installer.is_ready());assert((mode=="bundled")==installer.cache_root().empty());std::cout<<nlohmann::json({{"ready",true},{"root",installer.cache_root()},{"bytes",s.downloaded_bytes},{"retried",retried},{"paused",was_paused},{"raw_download_write_sizes",download_writes}}).dump()<<'\n';return 0;}
        if(((mode=="fail"||mode=="space-low"||mode=="space-write"||mode=="archive-checkpoint-full")&&s.phase==Phase::failed)||(mode=="cancel"&&s.phase==Phase::cancelled)){assert(!installer.is_ready());if(mode.rfind("space-",0)==0)assert(s.error.find("space")!=std::string::npos);std::cout<<nlohmann::json({{"ready",false},{"error",s.error},{"stage",s.stage}}).dump()<<'\n';return 0;}
        assert(std::chrono::steady_clock::now()-begin<std::chrono::seconds(20));
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
}
