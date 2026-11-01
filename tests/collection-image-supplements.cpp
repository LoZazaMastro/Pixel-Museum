// Pixel Museum - optional bundled artwork with the real offline image worker.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/media.hpp"
#include "gfx/renderer.hpp"
#include "yt/http.hpp"
#include "third_party/nlohmann/json.hpp"
#include <atomic>
#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <thread>
#include <cstdio>
namespace fs=std::filesystem;
using J=nlohmann::json;
namespace {std::atomic<unsigned> requests{0};void write(const std::string&p,const std::string&b){fs::create_directories(fs::path(p).parent_path());std::ofstream f(p,std::ios::binary);f.write(b.data(),b.size());}}
namespace yt::http {Response perform(const Request&){++requests;return {};}}
namespace hui::gfx {Renderer::~Renderer()=default;GlBatch::~GlBatch()=default;Backdrop::~Backdrop()=default;Canvas::~Canvas()=default;
std::uint32_t GlBatch::create_texture(int w,int h,const std::uint8_t*p){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,p);return t;}}
int main(){
 const std::string base="build/collection-image-supplements-test",root=base+"/app",collection=base+"/collection";
 fs::remove_all(base);
 const std::string url="https://collection.test/existing",new_url="https://collection.test/new";
 const std::string old_hash(64,'a'),new_hash(64,'b');
 const std::string registry=root+"/content/collection-image-supplements.json";
 const std::string image="assets/image-supplements/new.ppm";
 const std::string old_image="assets/images/old.ppm";
 write(collection+"/"+old_image,"P6\n2 1\n255\n"+std::string(6,'\x31'));
 write(root+"/"+image,"P6\n3 2\n255\n"+std::string(18,'\x72'));
 write(root+"/assets/trophies/fronts/pin.ppm","P6\n2 1\n255\n"+std::string(6,'\x41'));
 write(root+"/assets/trophies/fronts/index.json",J{{"museum-pin:test","assets/trophies/fronts/pin.ppm"}}.dump());
 write(collection+"/assets/images/manifest.json",J{{"images",{{url,old_image}}},{"previews",{{url,old_image}}},{"metadata",{{url,{{"sha256",old_hash}}}}}}.dump());
 auto register_ok=[&]{museum::media::RemoteCache cache;return cache.images_from_package(root,collection);};
 assert(register_ok()); // Optional absent: old full/external packages still work.
 const J valid={{"schema_version",1},{"images",{{url,image},{new_url,image}}},{"metadata",{{url,{{"sha256",std::string(64,'B')}}}}}};
 write(registry,"{");assert(!register_ok());
 for(const std::string&path:{std::string("assets/images/old.ppm"),std::string("assets/image-supplements/../old.ppm"),std::string("assets/image-supplements/a/./b.ppm"),std::string("assets/image-supplements//new.ppm"),std::string("assets/image-supplements/new.ppm/")}){
  auto bad=valid;bad["images"][url]=path;write(registry,bad.dump());assert(!register_ok());
 }
 {auto bad=valid;bad["schema_version"]=2;write(registry,bad.dump());assert(!register_ok());}
 {auto bad=valid;bad["metadata"][url]["sha256"]="not-a-hash";write(registry,bad.dump());assert(!register_ok());}
 {auto bad=valid;bad["images"]["museum-pin:test"]=image;write(registry,bad.dump());assert(!register_ok());}
 for(const std::string&name:{std::string("missing.ppm"),std::string("empty.ppm"),std::string("large.ppm"),std::string("directory"),std::string("symlink.ppm")}){
  if(name=="empty.ppm"||name=="large.ppm")write(root+"/assets/image-supplements/"+name,"");
  if(name=="large.ppm")fs::resize_file(root+"/assets/image-supplements/"+name,(32u<<20)+1);
  if(name=="directory")fs::create_directories(root+"/assets/image-supplements/"+name);
  if(name=="symlink.ppm")fs::create_symlink("new.ppm",root+"/assets/image-supplements/"+name);
  auto bad=valid;bad["images"][url]="assets/image-supplements/"+name;write(registry,bad.dump());assert(!register_ok());
 }
 write(registry,valid.dump());
 museum::media::RemoteCache cache;assert(cache.images_from_package(root,collection));
 assert(cache.image_identity(url)==new_hash);assert(cache.image_identity(new_url)==root+"/"+image);
 assert(cache.start(base+"/cache"));
 for(const auto&key:{url,new_url,std::string("museum-pin:test")}){
  cache.request(key);for(unsigned i=0;i<2000&&cache.get(key).state!=museum::media::State::ready;++i)std::this_thread::sleep_for(std::chrono::milliseconds(1));
  const auto a=cache.get(key);assert(a.state==museum::media::State::ready);
  if(key=="museum-pin:test"){assert(a.path==root+"/assets/trophies/fronts/pin.ppm");assert(a.source_width==2);}
  else{assert(a.path==root+"/"+image);assert(a.source_width==3&&a.source_height==2);}
 }
 cache.stop();assert(requests==0);
 std::puts("PASS optional absent; malformed/version/path/file/size/symlink/hash rejection; real worker new+override; old preview/hash replaced; bundled-root resolution; pin preserved; HTTP0");
}
