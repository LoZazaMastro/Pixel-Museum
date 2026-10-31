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
int main(int argc,char**argv){auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint major,minor;assert(eglInitialize(d,&major,&minor)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto c=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,c));
 {hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.start("build/photo-test-cache"));
 const std::string a="https://offline.test/square-a",b="https://offline.test/square-b",m0="https://offline.test/medium-0",m1="https://offline.test/medium-1",m2="https://offline.test/medium-2";
 auto wait=[&](const std::string&url){cache.request(url);for(unsigned i=0;i<5000;++i){cache.upload_pending(renderer);if(cache.get(url).texture)return;std::this_thread::sleep_for(std::chrono::milliseconds(2));}assert(false&&"cache image did not become resident");};
 cache.set_visible({a});cache.request(a);
 for(unsigned i=0;i<5000&&cache.get(a).state!=museum::media::State::ready;++i)std::this_thread::sleep_for(std::chrono::milliseconds(2));
 assert(cache.get(a).width==4096&&!cache.get(a).texture);
 cache.upload_pending(renderer);assert(!cache.get(a).texture); // A 64 MiB image cannot finish in the first 2 MiB tick.
 GLint pending=0;glGetIntegerv(GL_TEXTURE_BINDING_2D,&pending);assert(pending&&glIsTexture(static_cast<GLuint>(pending)));
 cache.release_textures();assert(!glIsTexture(static_cast<GLuint>(pending))); // Cancel/recreate must also delete the private, incomplete texture.
 for(unsigned tick=0;tick<31;++tick){cache.upload_pending(renderer);assert(!cache.get(a).texture);}
 cache.upload_pending(renderer);assert(cache.get(a).texture); // Exactly 32 bounded ticks for the actual 64 MiB fixture.
 wait(a);const auto first=cache.get(a);assert(first.width==4096&&first.height==4096&&first.source_width==4096);
 glBindTexture(GL_TEXTURE_2D,first.texture);std::vector<std::uint8_t> retained(std::size_t(4096)*4096*4);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,retained.data());
 for(const auto offset:{std::size_t(0),retained.size()-4})assert(retained[offset]==120&&retained[offset+1]==40&&retained[offset+2]==80&&retained[offset+3]==255); // First and final rows really reached GL storage.
 wait(m0);wait(m1);assert(cache.get(a).texture==first.texture&&cache.get(m0).texture&&cache.get(m1).texture);
 cache.set_visible({a,m1});wait(m2);assert(cache.get(a).texture==first.texture&&cache.get(m1).texture&&cache.get(m2).texture&&!cache.get(m0).texture);
 // Model pressure retires only nonvisible GL resources; originals survive on disk.
 const auto m2texture=cache.get(m2).texture;assert(m2texture);cache.set_visible({a,m1});assert(cache.set_model_pressure(true)>0);assert(!glIsTexture(m2texture));assert(cache.get(a).texture==first.texture&&cache.get(m1).texture);
 cache.request(m2);for(unsigned n=0;n<80;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(2));}assert(!cache.get(m2).texture);assert(cache.get(a).texture==first.texture);
 cache.set_model_pressure(false);cache.set_visible({a,m1,m2});wait(m2);assert(cache.get(m2).width==2048&&cache.get(m2).texture);cache.set_visible({a,m1});
 cache.request(b);for(unsigned i=0;i<500;++i){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(2));}assert(cache.get(a).texture==first.texture&&!cache.get(b).texture);const unsigned previous=requests;for(unsigned i=0;i<100;++i)assert(cache.request(b).state==museum::media::State::idle);std::this_thread::sleep_for(std::chrono::milliseconds(50));assert(requests==previous);
 cache.set_visible({b});wait(b);assert(cache.get(b).texture&&!cache.get(a).texture);assert(glGetError()==GL_NO_ERROR);cache.stop();cache.release_textures();}
 {
  const std::string package="build/photo-package-test";std::filesystem::create_directories(package+"/assets/images");
  std::filesystem::copy_file("build/photo-fixtures/small.png",package+"/assets/images/preview.png",std::filesystem::copy_options::overwrite_existing);
  std::filesystem::copy_file("build/photo-fixtures/medium.png",package+"/assets/images/full.png",std::filesystem::copy_options::overwrite_existing);
  std::ofstream manifest(package+"/assets/images/manifest.json");manifest<<R"({"images":{"https://local.test/photo":"assets/images/full.png"},"previews":{"https://local.test/photo":"assets/images/preview.png"},"metadata":{"https://local.test/photo":{"sha256":"abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"},"https://local.test/alias":{"sha256":"ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789"},"https://local.test/bad":{"sha256":"bad"}}})";manifest.close();
  hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.images_from_package(package));assert(cache.image_identity("https://local.test/photo")==cache.image_identity("https://local.test/alias"));assert(cache.image_identity("https://local.test/photo")=="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789");assert(cache.image_identity("https://local.test/bad")=="https://local.test/bad");assert(cache.image_identity("https://local.test/missing")=="https://local.test/missing");assert(cache.start("build/photo-package-cache"));const auto before=requests.load();
  cache.prefetch_images({"https://local.test/photo"});
  for(unsigned n=0;n<2000&&!cache.get("https://local.test/photo").texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(2));}
  assert(cache.get("https://local.test/photo").width==200); // warm preview comes from the package
  const auto preview_texture=cache.get("https://local.test/photo").texture;
  cache.set_visible({"https://local.test/photo"});cache.request("https://local.test/photo");
  for(unsigned n=0;n<2000&&(cache.get("https://local.test/photo").width!=2048||cache.get("https://local.test/photo").texture==preview_texture);++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(2));}
  assert(cache.get("https://local.test/photo").width==2048&&cache.get("https://local.test/photo").texture);
  cache.request("https://local.test/missing");
  for(unsigned n=0;n<500&&cache.get("https://local.test/missing").state!=museum::media::State::failed;++n)std::this_thread::sleep_for(std::chrono::milliseconds(2));
  assert(cache.get("https://local.test/missing").state==museum::media::State::failed&&requests==before); // no HTTP fallback
  cache.stop();cache.release_textures();puts("PASS: packaged preview warmup, full photo upgrade, missing asset fails locally, zero HTTP requests");
 }

 {
  // Hold the real worker in its HTTP adapter, then fill all16 queue slots.
  // A new active request arrives AFTER set_visible and must be admitted first.
  const auto stamp=std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
  hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.start("build/photo-priority-queue-"+stamp));
  cache.request("https://offline.test/queue-gate");
  for(unsigned n=0;n<2000&&!gate_entered;++n)std::this_thread::sleep_for(std::chrono::milliseconds(1));assert(gate_entered);
  for(unsigned n=0;n<16;++n)assert(cache.request("https://offline.test/queue-old-"+std::to_string(n)).state==museum::media::State::loading);
  const std::string active="https://offline.test/queue-active";cache.set_visible({active});assert(cache.request(active).state==museum::media::State::loading);gate_release=true;
  for(unsigned n=0;n<2000&&!cache.get(active).texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(cache.get(active).texture);
  {std::lock_guard<std::mutex> lock(order_mutex);assert(request_order.size()>=2&&request_order[0].find("queue-gate")!=std::string::npos&&request_order[1]==active);}
  cache.stop();cache.release_textures();puts("PASS: newly visible request overtakes16 obsolete queued jobs after set_visible; real worker order verified");
 }
 {
  const std::string package="build/photo-priority-package";std::filesystem::create_directories(package+"/assets/images");
  const auto copy=[&](const char*source,const char*name){std::filesystem::copy_file(source,package+"/assets/images/"+name,std::filesystem::copy_options::overwrite_existing);};
  copy("build/photo-fixtures/square.png","full.png");copy("build/photo-fixtures/small.png","preview.png");copy("build/photo-fixtures/medium.png","fallback.png");
  std::ofstream(package+"/assets/images/bad.png")<<"not an image";
  const char*real_path=std::getenv("MUSEUM_PHOTO_PROBE");if(real_path)copy(real_path,"actual.jpg");
  std::ofstream manifest(package+"/assets/images/manifest.json");manifest<<R"({"images":{"https://local.test/priority-hidden":"assets/images/full.png","https://local.test/priority-active":"assets/images/full.png","https://local.test/priority-fallback":"assets/images/fallback.png","https://local.test/priority-real":"assets/images/actual.jpg","https://local.test/priority-neighbour":"assets/images/fallback.png"},"previews":{"https://local.test/priority-active":"assets/images/preview.png","https://local.test/priority-fallback":"assets/images/bad.png","https://local.test/priority-neighbour":"assets/images/preview.png"}})";manifest.close();
  const std::string hidden="https://local.test/priority-hidden",active="https://local.test/priority-active",fallback="https://local.test/priority-fallback";
  hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.images_from_package(package));assert(cache.start("build/photo-priority-package-cache"));const auto requests_before=requests.load();
  cache.request(hidden);for(unsigned n=0;n<4000&&cache.get(hidden).state!=museum::media::State::ready;++n)std::this_thread::sleep_for(std::chrono::milliseconds(1));assert(cache.get(hidden).state==museum::media::State::ready);
  cache.upload_pending(renderer);assert(!cache.get(hidden).texture);GLint old=0;glGetIntegerv(GL_TEXTURE_BINDING_2D,&old);assert(old);glObjectLabel(GL_TEXTURE,GLuint(old),-1,"obsolete-private-photo");
  wide_transfers=0;const auto started=std::chrono::steady_clock::now();cache.set_visible({active});cache.request(active);
  for(unsigned n=0;n<4000&&!cache.get(active).texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(cache.get(active).texture&&wide_transfers==0);
  const auto preview=cache.get(active).texture;glBindTexture(GL_TEXTURE_2D,preview);GLint actual_width=0;glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&actual_width);assert(actual_width==200);
  char label[64]{};GLsizei length=0;if(glIsTexture(GLuint(old)))glGetObjectLabel(GL_TEXTURE,GLuint(old),sizeof(label),&length,label);assert(std::string(label,std::size_t(length))!="obsolete-private-photo");
  std::printf("Cold active packaged preview: %.2fms host; stale4K transfer count0 after focus change\n",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count());
  for(unsigned n=0;n<4000&&cache.get(active).texture==preview;++n){cache.upload_pending(renderer);if(cache.get(active).texture==preview)assert(glIsTexture(preview));std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  const auto full=cache.get(active);assert(full.texture&&full.texture!=preview&&full.width==4096&&full.height==4096&&full.source_width==4096&&wide_transfers==32&&!glIsTexture(preview));
  glBindTexture(GL_TEXTURE_2D,full.texture);std::vector<std::uint8_t> pixels(std::size_t(4096)*4096*4);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());for(std::size_t n=0;n<pixels.size();n+=4)assert(pixels[n]==120&&pixels[n+1]==40&&pixels[n+2]==80&&pixels[n+3]==255);
  const std::string neighbour="https://local.test/priority-neighbour";cache.prefetch_images({neighbour});
  for(unsigned n=0;n<4000&&cache.get(neighbour).state!=museum::media::State::ready;++n)std::this_thread::sleep_for(std::chrono::milliseconds(1));assert(cache.get(neighbour).state==museum::media::State::ready&&!cache.get(neighbour).texture);
  cache.set_visible({fallback});cache.request(fallback);cache.upload_pending(renderer);assert(cache.get(neighbour).state==museum::media::State::idle);for(unsigned n=0;n<4000&&!cache.get(fallback).texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(cache.get(fallback).texture&&cache.get(fallback).width==2048); // corrupt optional preview falls back to untouched master
  for(unsigned n=0;n<4000&&!cache.get(neighbour).texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(cache.get(neighbour).texture&&cache.get(neighbour).width==200);
  puts("PASS: priority-deferred neighbour preview resumes after active master; memory/LRU deferral remains separate");
  if(real_path){
   const std::string real="https://local.test/priority-real";cache.set_visible({real});const auto begin=std::chrono::steady_clock::now();cache.request(real);
   for(unsigned n=0;n<4000&&cache.get(real).state!=museum::media::State::ready;++n)std::this_thread::sleep_for(std::chrono::milliseconds(1));assert(cache.get(real).state==museum::media::State::ready);
   const auto decoded=std::chrono::steady_clock::now();unsigned ticks=0;
   while(!cache.get(real).texture&&ticks<100){cache.upload_pending(renderer);++ticks;if(!cache.get(real).texture)std::this_thread::sleep_for(std::chrono::milliseconds(16));}
   const auto photo=cache.get(real);assert(photo.texture);std::printf("Actual local JPEG %dx%d: decode/read %.2fms, complete transfer %u bounded ticks / first master %.2fms host\n",photo.source_width,photo.source_height,std::chrono::duration<double,std::milli>(decoded-begin).count(),ticks,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count());
  }
  assert(requests==requests_before&&glGetError()==GL_NO_ERROR);cache.stop();cache.release_textures();puts("PASS: cold packaged preview preempts stale64MiB upload; automatic full4K promotion retains preview until all32 bounded chunks, every RGBA texel exact; corrupt preview master fallback; zero HTTP");
 }
 {
  const std::string package="build/photo-failed-master-package",url="https://local.test/failed-master";
  std::filesystem::create_directories(package+"/assets/images");
  std::filesystem::copy_file("build/photo-fixtures/small.png",package+"/assets/images/preview.png",std::filesystem::copy_options::overwrite_existing);
  std::ofstream(package+"/assets/images/full.png")<<"corrupt installed master";
  std::ofstream(package+"/assets/images/manifest.json")<<R"({"images":{"https://local.test/failed-master":"assets/images/full.png"},"previews":{"https://local.test/failed-master":"assets/images/preview.png"}})";
  hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.images_from_package(package)&&cache.start("build/photo-failed-master-cache"));const auto before=requests.load();
  cache.prefetch_images({url});
  for(unsigned n=0;n<4000&&!cache.get(url).texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  const auto preview=cache.get(url);assert(preview.texture&&preview.width==200&&preview.height==100);
  cache.set_visible({url});cache.request(url);
  for(unsigned n=0;n<4000&&cache.get(url).error.empty();++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  const auto failed=cache.get(url);assert(failed.state==museum::media::State::ready&&!failed.error.empty()&&failed.texture==preview.texture&&failed.width==preview.width&&failed.height==preview.height&&failed.source_width==preview.source_width&&failed.source_height==preview.source_height&&glIsTexture(preview.texture));
  // Make a valid master available: ordinary navigation must not spin/retry it.
  std::filesystem::copy_file("build/photo-fixtures/medium.png",package+"/assets/images/full.png",std::filesystem::copy_options::overwrite_existing);
  for(unsigned n=0;n<100;++n){cache.request(url);cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));assert(cache.get(url).texture==preview.texture&&cache.get(url).width==200&&!cache.get(url).error.empty());}
  cache.retry(url);
  for(unsigned n=0;n<4000&&cache.get(url).texture==preview.texture;++n){cache.upload_pending(renderer);const auto shown=cache.get(url);if(shown.texture==preview.texture)assert(shown.width==200&&shown.height==100&&glIsTexture(preview.texture));std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  assert(cache.get(url).texture&&cache.get(url).texture!=preview.texture&&cache.get(url).width==2048&&cache.get(url).error.empty()&&requests==before);
  cache.stop();cache.release_textures();puts("PASS: failed master retains entire READY preview and valid geometry; navigation suppresses retry; explicit retry promotes valid replacement atomically");
 }

 {
  // Long articles revisit evicted masters while another 64 MiB master is
  // focused. A neighbour's small installed preview fits even when its master
  // does not fit beside the focused photo in the 96 MiB resident budget.
  const std::string package="build/photo-long-article-package";
  std::filesystem::create_directories(package+"/assets/images");
  std::filesystem::copy_file("build/photo-fixtures/square.png",package+"/assets/images/full.png",std::filesystem::copy_options::overwrite_existing);
  std::filesystem::copy_file("build/photo-fixtures/small.png",package+"/assets/images/preview.png",std::filesystem::copy_options::overwrite_existing);
  std::ofstream(package+"/assets/images/manifest.json")<<R"({"images":{"https://local.test/long-a":"assets/images/full.png","https://local.test/long-b":"assets/images/full.png"},"previews":{"https://local.test/long-a":"assets/images/preview.png","https://local.test/long-b":"assets/images/preview.png"}})";
  const std::string a="https://local.test/long-a",b="https://local.test/long-b";
  hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.images_from_package(package)&&cache.start("build/photo-long-article-cache"));const auto before=requests.load();
  const auto focus=[&](const std::string&url){cache.set_visible({url});cache.request(url);for(unsigned n=0;n<8000;++n){cache.upload_pending(renderer);const auto asset=cache.get(url);if(asset.texture&&asset.width==4096&&asset.state==museum::media::State::ready)return;std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(false&&"long article focused master missing");};
  focus(a);focus(b);assert(!cache.get(a).texture);const auto active=cache.get(b).texture;
  cache.set_visible({b,a});
  for(unsigned n=0;n<1000&&!cache.get(a).texture;++n){cache.request(a);cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  assert(cache.get(a).texture&&cache.get(a).width==200&&"evicted neighbouring master must reload its fitting packaged preview");
  assert(cache.get(b).texture==active&&cache.get(b).width==4096);
  for(unsigned n=0;n<100;++n){cache.request(a);cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));assert(cache.get(a).texture&&cache.get(b).texture==active);}
  focus(a);assert(cache.get(a).width==4096&&requests==before&&glGetError()==GL_NO_ERROR);
  cache.stop();cache.release_textures();puts("PASS: evicted long-article neighbour returns as installed preview beside focused64MiB master, remains visible, promotes when focused, zero HTTP");
 }
 for(int i=1;i<argc;++i){
  const std::string package="build/photo-actual-source-package-"+std::to_string(i),url="https://local.test/actual-source";
  std::filesystem::create_directories(package+"/assets/images");
  std::filesystem::copy_file(argv[i],package+"/assets/images/full.bin",std::filesystem::copy_options::overwrite_existing);
  std::filesystem::copy_file("build/photo-fixtures/small.png",package+"/assets/images/preview.png",std::filesystem::copy_options::overwrite_existing);
  std::ofstream(package+"/assets/images/manifest.json")<<R"({"images":{"https://local.test/actual-source":"assets/images/full.bin"},"previews":{"https://local.test/actual-source":"assets/images/preview.png"}})";
  hui::gfx::Renderer renderer;museum::media::RemoteCache cache;assert(cache.images_from_package(package)&&cache.start("build/photo-actual-source-cache-"+std::to_string(i)));const auto before=requests.load();
  cache.prefetch_images({url});
  for(unsigned n=0;n<4000&&!cache.get(url).texture;++n){cache.upload_pending(renderer);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  const auto preview=cache.get(url);assert(preview.texture&&preview.width==200);
  cache.set_visible({url});cache.request(url);
  for(unsigned n=0;n<16000&&cache.get(url).texture==preview.texture;++n){cache.upload_pending(renderer);const auto shown=cache.get(url);assert(shown.texture&&shown.width>0&&shown.height>0);if(shown.texture==preview.texture)assert(shown.width==200&&shown.height==100&&glIsTexture(preview.texture));std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  const auto photo=cache.get(url);assert(photo.texture&&photo.texture!=preview.texture&&photo.state==museum::media::State::ready&&photo.error.empty()&&photo.width<=4096&&photo.height<=4096&&photo.source_width>4096&&requests==before);
  std::printf("PASS actual packaged source %dx%d -> GL %dx%d, preview retained until complete bounded promotion, zero HTTP\n",photo.source_width,photo.source_height,photo.width,photo.height);
  assert(glGetError()==GL_NO_ERROR);cache.stop();cache.release_textures();
 }
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,c);eglTerminate(d);puts("PASS: real worker,64MiB active photo survives96MiB pressure, lower-priority LRU eviction, background deferral without redecoding, current photo switch");}
