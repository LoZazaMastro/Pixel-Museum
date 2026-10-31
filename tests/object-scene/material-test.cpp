// Pixel Museum - actual renderer neutral-material pixel tests. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include "third_party/nlohmann/json.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <array>
#include <chrono>
#include <thread>
#include <filesystem>
#include <fstream>
namespace {bool reject_compact=false;unsigned rejected_compact=0;}
extern "C" void __real_glTexStorage2D(GLenum,GLsizei,GLenum,GLsizei,GLsizei);
extern "C" void __wrap_glTexStorage2D(GLenum target,GLsizei levels,GLenum format,GLsizei w,GLsizei h){
 if(reject_compact&&(format==GL_R8||format==GL_RG8)){++rejected_compact;__real_glTexStorage2D(target,levels,GL_ZERO,w,h);return;}
 __real_glTexStorage2D(target,levels,format,w,h);
}
int main(int argc,char**argv){
 const bool asynchronous=argc>1;reject_compact=argc>1&&std::string(argv[1])=="--async-compact-failure";
 FILE*f=std::fopen("build/material-fixtures/manifest.json","rb");assert(f);std::fseek(f,0,SEEK_END);auto size=std::ftell(f);std::rewind(f);std::string bytes(size,'\0');assert(std::fread(bytes.data(),1,bytes.size(),f)==bytes.size());std::fclose(f);
 auto manifest=nlohmann::json::parse(bytes);auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);auto display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint major,minor;assert(eglInitialize(display,&major,&minor)&&eglBindAPI(EGL_OPENGL_API));
 const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto context=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,context));hui::gfx::set_glsl_prefix("#version 450 core\n");
 std::array<unsigned char,4> normal{},mirrored{};unsigned count=0,cache_comparisons=0;
 {
 museum::ObjectScene scene;
 for(const auto&fixture:manifest["cases"]){auto name=fixture["file"].get<std::string>();bool loaded=false;
 if(asynchronous){scene.request("build/material-fixtures/"+name);for(unsigned tries=0;tries<10000;++tries){scene.upload_pending();if(scene.ready()){loaded=true;break;}if(!scene.error().empty())break;std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(scene.timings().max_upload_bytes<=(2u<<20));}
 else loaded=scene.load("build/material-fixtures/"+name);if(!fixture["expected_error"].is_null()){assert(!loaded);assert(scene.error().find(fixture["expected_error"].get<std::string>())!=std::string::npos);std::printf("%s: explicit rejection PASS\n",name.c_str());++count;continue;}if(!loaded){std::fprintf(stderr,"%s: %s\n",name.c_str(),scene.error().c_str());return 2;}if(!fixture["expected_note"].is_null())assert(scene.material_notes().find(fixture["expected_note"].get<std::string>())!=std::string::npos);else assert(scene.material_notes().empty());auto texture=scene.render(0,256,256,0);assert(texture);GLuint fbo;glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,texture,0);std::array<unsigned char,4> pixel{};glReadPixels(128,128,1,1,GL_RGBA,GL_UNSIGNED_BYTE,pixel.data());glBindFramebuffer(GL_FRAMEBUFFER,0);glDeleteFramebuffers(1,&fbo);assert(glGetError()==GL_NO_ERROR);assert(pixel[3]==255);
 std::printf("%s: RGB %u,%u,%u",name.c_str(),pixel[0],pixel[1],pixel[2]);
 if(!fixture["expected_rgb"].is_null()){for(unsigned c=0;c<3;++c){auto expected=fixture["expected_rgb"][c].get<int>();if(std::abs(int(pixel[c])-expected)>3){std::fprintf(stderr,"\n%s channel %u: got %u expected %d\n",name.c_str(),c,pixel[c],expected);return 3;}}}
 if(reject_compact&&name=="packed-orm-10497-9987.glb"){
  std::ifstream cache("build/material-fixtures/packed-orm-10497-9987.artwork.pmc",std::ios::binary);std::array<char,8>magic{};cache.read(magic.data(),8);
  if(std::string(magic.data(),magic.size())=="PMAC0002")assert(scene.timings().compact_cache_fallbacks==1&&scene.timings().artwork_cache_hits==1);
 }
 const auto stats=scene.stats();const nlohmann::json actual={{"srgb_textures",stats.srgb_textures},{"linear_textures",stats.linear_textures},{"dual_role_texture_bytes",stats.dual_role_texture_bytes},{"tangent_vertices",stats.tangent_vertices}};
 for(auto it=fixture["expected_stats"].begin();it!=fixture["expected_stats"].end();++it)assert(actual[it.key()]==it.value());
 if(name=="unlit-linear-factor.glb")assert(stats.sampler_objects==1);
 if(name=="srgb-linear-filter.glb")assert(stats.sampler_objects==2);
 if(name=="normal-authored.glb")normal=pixel;if(name=="normal-mirrored.glb")mirrored=pixel;
 // Compare the entire actual rendered image against the original RGBA path,
 // including minified mips, authored wrap modes and shared-image role unions.
 if(asynchronous&&(name.rfind("packed-",0)==0||name.rfind("union-",0)==0||name.rfind("uniform-",0)==0||name.rfind("notuniform-",0)==0)){
  auto read_pixels=[](GLuint t){GLuint f;glGenFramebuffers(1,&f);glBindFramebuffer(GL_FRAMEBUFFER,f);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,t,0);std::vector<unsigned char> out(256*256*4);glReadPixels(0,0,256,256,GL_RGBA,GL_UNSIGNED_BYTE,out.data());glBindFramebuffer(GL_FRAMEBUFFER,0);glDeleteFramebuffers(1,&f);return out;};
  if(std::filesystem::exists("build/material-fixtures/"+name.substr(0,name.size()-4)+".artwork.pmc")){assert(scene.timings().artwork_cache_hits==1);++cache_comparisons;}
  const auto packed=read_pixels(texture);museum::ObjectScene reference;assert(reference.load("build/material-fixtures/"+name));const auto rgba=read_pixels(reference.render(0,256,256,0));unsigned delta=0;for(std::size_t n=0;n<rgba.size();++n)delta=std::max(delta,unsigned(std::abs(int(rgba[n])-int(packed[n]))));assert(delta<=1);assert(glGetError()==GL_NO_ERROR);
  const auto packed_bytes=scene.timings().estimated_gpu_bytes,rgba_bytes=reference.timings().estimated_gpu_bytes;
  if(name.rfind("uniform-",0)==0){
   assert(scene.timings().uniform_texture_views==1&&scene.timings().uniform_saved_logical_bytes>0&&packed_bytes<rgba_bytes&&delta==0);
   // Magnification/minification and off-axis derivatives all produce the
   // same actual shader pixels as the untouched full-resolution source map.
   for(float zoom:{.3f,2.5f})for(float angle:{0.f,.43f}){
    const auto optimized=read_pixels(scene.render(angle,256,256,.13f,false,zoom));
    const auto original=read_pixels(reference.render(angle,256,256,.13f,false,zoom));
    assert(optimized==original&&glGetError()==GL_NO_ERROR);
   }
  }
  else if(name.rfind("notuniform-",0)==0){assert(scene.timings().uniform_texture_views==0);}
  else if(!reject_compact&&name.rfind("packed-",0)==0)assert(packed_bytes<rgba_bytes);
  else assert(packed_bytes==rgba_bytes);
 }
 std::puts(" PASS");++count;
 }
 for(unsigned c=0;c<3;++c)assert(std::abs(int(normal[c])-int(mirrored[c]))<=2);
 }
 if(asynchronous){
  museum::ObjectScene transitioning;assert(transitioning.load("build/material-fixtures/packed-orm-10497-9987.glb"));
  transitioning.request("/must-not-be-read-before-gpu-retirement.glb");assert(transitioning.timings().pending_gpu_deletes>0);
  std::this_thread::sleep_for(std::chrono::milliseconds(30));assert(transitioning.stage()=="Reading the original model");assert(transitioning.error().empty());
  transitioning.cancel();transitioning.request("build/material-fixtures/packed-ao-10497-9987.glb");
  for(unsigned n=0;n<5000&&!transitioning.ready();++n){transitioning.upload_pending();std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  assert(transitioning.ready()&&transitioning.error().empty()&&glGetError()==GL_NO_ERROR);
  std::puts("PASS: source-read admission waits for GPU retirement; cancellation/re-request resumes newest model");
 }
 if(asynchronous){
  // Prepare from one immutable open descriptor, then reject a changed source
  // before any image is decoded or published. This only mutates a fixture copy.
  const std::string changed="build/material-fixtures/changed-after-read.glb";
  std::filesystem::copy_file("build/material-fixtures/packed-orm-10497-9987.glb",changed,std::filesystem::copy_options::overwrite_existing);
  museum::ObjectScene modified;modified.request(changed);
  for(unsigned tries=0;tries<5000&&modified.stage()=="Reading the original model";++tries)std::this_thread::sleep_for(std::chrono::milliseconds(1));
  assert(modified.loading());
  {std::fstream file(changed,std::ios::binary|std::ios::in|std::ios::out);assert(file);file.seekp(-16,std::ios::end);char byte=73;file.write(&byte,1);}
  for(unsigned tries=0;tries<5000&&modified.error().empty();++tries){modified.upload_pending();std::this_thread::sleep_for(std::chrono::milliseconds(1));}
  assert(!modified.ready()&&modified.error().find("changed")!=std::string::npos);assert(glGetError()==GL_NO_ERROR);
  std::puts("PASS: in-place encoded source mutation rejected before atlas publication");
 }
 if(reject_compact)assert(rejected_compact>0);
 if(cache_comparisons)std::printf("PASS: %u cache-backed full-image shader comparisons against originalRGBA\n",cache_comparisons);
 eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,context);eglTerminate(display);std::printf("PASS: %u neutral pixel/material checks; mirrored tangent frame preserved.\n",count);
}
