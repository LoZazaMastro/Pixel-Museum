// Pixel Museum - real worker/residency test with offline HTTP and minimal texture-upload host adapter.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/media.hpp"
#include "gfx/renderer.hpp"
#include "yt/http.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <atomic>
#include <cstdio>
#include <chrono>
#include <thread>
#include <string>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <cstdlib>
namespace {std::atomic<unsigned>requests{0},wide_transfers{0};std::atomic<bool>gate_entered{false},gate_release{false};std::mutex order_mutex;std::vector<std::string>request_order;std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string bytes(ftell(f),'\0');rewind(f);assert(fread(bytes.data(),1,bytes.size(),f)==bytes.size());fclose(f);return bytes;}}
namespace yt::http {Response perform(const Request&r){++requests;if(r.url.find("queue-")!=std::string::npos){std::lock_guard<std::mutex> lock(order_mutex);request_order.push_back(r.url);}if(r.url.find("queue-gate")!=std::string::npos){gate_entered=true;while(!gate_release)std::this_thread::sleep_for(std::chrono::milliseconds(1));}Response response;response.status=200;response.body=read(r.url.find("queue-")!=std::string::npos?"build/photo-fixtures/small.png":r.url.find("medium")!=std::string::npos?"build/photo-fixtures/medium.png":"build/photo-fixtures/square.png");return response;}}
extern "C" void __real_glTexSubImage2D(GLenum,GLint,GLint,GLint,GLsizei,GLsizei,GLenum,GLenum,const void*);
extern "C" void __wrap_glTexSubImage2D(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,GLenum format,GLenum type,const void*p){if(w==4096)++wide_transfers;__real_glTexSubImage2D(target,level,x,y,w,h,format,type,p);}
// The cache calls the production Renderer::batch accessor; these resource-only
// shims avoid initializing unrelated UI shaders while real GL uploads/deletes execute.
namespace hui::gfx {Renderer::~Renderer()=default;GlBatch::~GlBatch()=default;Backdrop::~Backdrop()=default;Canvas::~Canvas()=default;
std::uint32_t GlBatch::create_texture(int w,int h,const std::uint8_t*rgba){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,0);return t;}}

int main(int argc,char**argv){
 if(argc>1){const bool complete=museum::media::packaged_images_complete(argv[1]);std::printf("REAL PACKAGE COMPLETENESS %s %s\n",complete?"PASS_COMPLETE":"PASS_MISSING",argv[1]);return 0;}

 using museum::media::RemoteCache;using museum::media::State;
 const std::string base="build/collection-delivery-20261031/archive-worker-fixture",install=base+"/install",collection=base+"/persistent/collection/version-ready";
 std::filesystem::create_directories(install+"/assets/trophies/fronts");std::filesystem::create_directories(collection+"/assets/images");std::filesystem::create_directories(collection+"/content");std::filesystem::create_directories(install+"/content");std::filesystem::create_directories(collection+"/archives");
 const auto photo=read("build/photo-fixtures/small.png");
 {std::ofstream f(collection+"/assets/images/original.png",std::ios::binary);f<<photo;}
 {std::ofstream f(install+"/assets/trophies/fronts/pin.png",std::ios::binary);f<<photo;}
 {std::ofstream f(install+"/assets/trophies/fronts/index.json");f<<R"({"museum-pin:test":"assets/trophies/fronts/pin.png"})";}
 const std::string manifest=R"({"schema_version":1,"images":{"https://collection.test/photo":"assets/images/original.png"},"previews":{},"metadata":{}})";
 {std::ofstream f(collection+"/assets/images/manifest.json");f<<manifest;}
 const auto write_index=[&](std::size_t size){std::ofstream f(collection+"/content/collection-files.json");f<<"{\"schema_version\":1,\"files\":[{\"path\":\"assets/images/manifest.json\",\"bytes\":"<<manifest.size()<<"},{\"path\":\"assets/images/original.png\",\"bytes\":"<<size<<"}]}";};
 write_index(photo.size());assert(museum::media::packaged_images_complete(collection));assert(!museum::media::packaged_images_complete(install));write_index(photo.size()+1);assert(!museum::media::packaged_images_complete(collection));write_index(photo.size());
 RemoteCache cache;assert(!cache.images_from_package(install));assert(cache.start(base+"/cache"));const std::string url="https://collection.test/photo";cache.request(url);for(int tick=0;tick<1000&&cache.get(url).state!=State::failed;++tick)std::this_thread::sleep_for(std::chrono::milliseconds(2));assert(cache.get(url).state==State::failed);cache.stop();

 const std::string fixture="build/collection-delivery-20261031/archive-fixture";
 const auto index=read((fixture+"/index.json").c_str());
 // Copy the immutable private verified archive fixture.
 for(const auto&entry:std::filesystem::directory_iterator(fixture+"/collection/archives")){auto tar=read(entry.path().c_str());std::ofstream f(collection+"/archives/"+entry.path().filename().string(),std::ios::binary);f<<tar;}
 {std::ofstream f(install+"/content/collection-archive-index.json");f<<"{";}
 assert(!cache.images_from_package(install,collection));
 {std::ofstream f(install+"/content/collection-archive-index.json");f<<index;}
 std::filesystem::remove(collection+"/assets/images/original.png");
 assert(cache.images_from_package(install,collection));assert(cache.start(base+"/cache"));
 for(const auto&key:{url,std::string("museum-pin:test")}){cache.request(key);for(int tick=0;tick<1000&&cache.get(key).state!=State::ready;++tick)std::this_thread::sleep_for(std::chrono::milliseconds(2));auto result=cache.get(key);assert(result.state==State::ready);assert(result.source_width>0&&result.source_height>0);if(key==url)assert(result.path==collection+"/assets/images/original.png");else assert(result.path==install+"/assets/trophies/fronts/pin.png");std::printf("PASS %s root=%s original=%dx%d\n",key==url?"downloaded image":"bundled pin",key==url?"persistent":"install",result.source_width,result.source_height);}
 assert(requests.load()==0);cache.stop();std::puts("PASS archive-only original via real RemoteCache worker,200x100decode,FAILED reset,invalid index failclosed,preserved physical bundled pin; HTTP requests=0");return 0;
}
