// Native manifest regression: unavailable lstat must not bypass first-run setup.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_installer.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cassert>
#include <cerrno>
#include <chrono>
#include <cstdarg>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <pthread.h>
#include <string>
#include <thread>
#include <sys/stat.h>
#include <unistd.h>
namespace {std::string denied,unconfirmed;unsigned lstat_calls=0,worker_calls=0;bool thread_failure=false;}
extern "C" int __real_open(const char*,int,...);
extern "C" int __wrap_open(const char*path,int flags,...){
    mode_t mode=0;if(flags&O_CREAT){va_list args;va_start(args,flags);mode=va_arg(args,int);va_end(args);}
    if(path==denied){errno=EACCES;return -1;}if(path==unconfirmed){errno=ENOENT;return -1;}
    return flags&O_CREAT?__real_open(path,flags,mode):__real_open(path,flags);
}
extern "C" int __wrap_lstat(const char*,struct stat*){++lstat_calls;errno=ENOSYS;return -1;}
extern "C" int __real_pthread_create(pthread_t*,const pthread_attr_t*,void*(*)(void*),void*);
extern "C" int __wrap_pthread_create(pthread_t*thread,const pthread_attr_t*attributes,void*(*entry)(void*),void*owner){
    assert(attributes);size_t stack=0;assert(!pthread_attr_getstacksize(attributes,&stack));assert(stack>=2u<<20);++worker_calls;
    return thread_failure?EAGAIN:__real_pthread_create(thread,attributes,entry,owner);
}
namespace museum::media {bool packaged_images_complete(const std::string&root){volatile unsigned char workspace[128u<<10];for(size_t n=0;n<sizeof(workspace);n+=4096)workspace[n]=1;return root=="test-bundled-complete";}}
int main(){
    char pattern[]="/tmp/pm-installer-fs-XXXXXX";char*temporary=mkdtemp(pattern);assert(temporary);const std::string root=temporary,path=root+"/collection-packs.json";
    const auto write=[&](const std::string&name,const std::string&value){std::ofstream stream(name);stream<<value;stream.close();assert(stream);};
    using C=museum::CollectionInstaller;using P=C::Phase;C installer;
    const nlohmann::json manifest={{"schema_version",1},{"collection_id","fixture"},{"packs",nlohmann::json::array({{{"id","one"},{"url","https://example.invalid/one.tar"},{"bytes",10240u},{"sha256",std::string(64,'0')},{"format","tar"}}})}};
    write(path,manifest.dump());assert(installer.configure(path,root+"/data"));assert(installer.snapshot().phase==P::idle);assert(!lstat_calls);
    assert(installer.configure(path,root+"/data","test-bundled-complete"));assert(installer.start());const auto start=std::chrono::steady_clock::now();while(!installer.is_ready()){assert(std::chrono::steady_clock::now()-start<std::chrono::seconds(2));std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(worker_calls==1);
    assert(installer.configure(path,root+"/data"));thread_failure=true;assert(!installer.start());auto failure=installer.snapshot();assert(failure.phase==P::failed&&failure.diagnostic.find("pthread")!=std::string::npos);thread_failure=false;
    denied=path;assert(!installer.configure(path,root+"/data"));auto s=installer.snapshot();assert(s.phase==P::failed&&s.filesystem_errno==EACCES);assert(s.diagnostic.find(path)!=std::string::npos&&s.diagnostic.find("open")!=std::string::npos);assert(!installer.start());denied.clear();
    unconfirmed=path;assert(!installer.configure(path,root+"/data"));s=installer.snapshot();assert(s.phase==P::failed&&s.filesystem_errno==ENOENT);unconfirmed.clear();
    write(path,"");assert(!installer.configure(path,root+"/data"));assert(installer.snapshot().phase==P::failed);
    write(path,"{");assert(!installer.configure(path,root+"/data"));assert(installer.snapshot().phase==P::failed);
    write(path,std::string((1u<<20)+1,'x'));assert(!installer.configure(path,root+"/data"));s=installer.snapshot();assert(s.phase==P::failed&&s.filesystem_errno==EFBIG);
    assert(!installer.configure(root,root+"/data"));s=installer.snapshot();assert(s.phase==P::failed&&s.filesystem_errno==EISDIR);
    assert(!installer.configure(root+"/absent.json",root+"/data"));assert(installer.snapshot().phase==P::unconfigured);
    assert(!installer.configure(root+"/unavailable/absent.json",root+"/data"));assert(installer.snapshot().phase==P::failed);
    assert(!lstat_calls);unlink(path.c_str());rmdir(root.c_str());
    std::cout<<"PASS: explicit 2 MiB worker with 128 KiB stack workload, thread creation failure, lstat unavailable, valid manifest, EACCES, contradictory ENOENT, empty/malformed/oversize/directory, verified legacy absence, unavailable parent\n";
}
