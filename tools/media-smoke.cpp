// Pixel Museum - Exercise bounded HTTPS cache and decoded image results.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/media.hpp"
#include "platform/ps5/system.hpp"
#include <cstdio>
#include <string>
#include <sys/stat.h>

static int large_catalog() {
    // Populate local fixtures, so this regression makes no network requests.
    const std::string root="build/media-catalog-smoke-cache";
    mkdir(root.c_str(),0777);
    museum::media::RemoteCache cache;
    if(!cache.start(root)) return 10;
    for(unsigned item=0;item<520;++item) {
        const std::string url="https://fixture.invalid/museum-model-"+std::to_string(item);
        std::uint64_t hash=14695981039346656037ull;
        for(unsigned char c:url) { hash^=c;hash*=1099511628211ull; }
        char name[24];std::snprintf(name,sizeof(name),"%016llx.bin",static_cast<unsigned long long>(hash));
        FILE* fixture=std::fopen((root+"/"+name).c_str(),"wb");
        if(!fixture) return 11;
        std::fputc(1,fixture);std::fclose(fixture);
        auto result=cache.request(url,false);
        for(unsigned wait=0;wait<200 && result.state==museum::media::State::loading;++wait) {
            hui::sys::sleep_us(1000);result=cache.get(url);
        }
        if(result.state!=museum::media::State::ready) {
            std::fprintf(stderr,"catalogue item %u did not become ready: state=%d\n",item,int(result.state));return 12;
        }
    }
    cache.stop();
    std::puts("520 distinct model requests loaded through the bounded metadata LRU");return 0;
}
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    if(std::string(argv[1])=="--catalogue") return large_catalog();
    museum::media::RemoteCache cache;
    if(!cache.start("build/media-smoke-cache")) return 3;
    if(cache.request("file:///etc/passwd").state!=museum::media::State::failed) return 4;
    if(cache.request("http://example.com/image.png").state!=museum::media::State::failed) return 5;
    auto result=cache.request(argv[1]);
    for(unsigned i=0;i<120 && result.state==museum::media::State::loading;++i) {
        hui::sys::sleep_us(250000); result=cache.get(argv[1]);
    }
    std::printf("state=%d size=%dx%d error=%s\n",int(result.state),result.width,result.height,result.error.c_str());
    cache.stop();
    return result.state==museum::media::State::ready && result.width>0 && result.width<=1600 && result.height<=1600 ? 0:1;
}
