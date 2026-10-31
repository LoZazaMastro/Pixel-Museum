#include "museum/object_scene.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <cstdio>
static bool reject_compact=false;
static void budget_storage(GLenum target,GLsizei levels,GLenum internal,GLsizei w,GLsizei h){glTexStorage2D(target,levels,reject_compact&&internal==GL_RG8?GLenum(0):internal,w,h);}
#define glTexStorage2D budget_storage
#include "museum/object_scene.cpp"
#undef glTexStorage2D
namespace museum {
struct ObjectSceneBudgetInspection {
 static void run(){
  std::atomic<std::uint64_t> revision{1};
  for(int mode=0;mode<5;++mode){
   ObjectScene object;assert(object.init());auto&p=*object.impl_;p.images.resize(1);p.linear_images.resize(1);p.image_storage.resize(1);p.linear_storage.resize(1);
   auto job=std::make_unique<ImageUpload>();job->serial=1;job->use_cache=false;job->source.width=job->source.height=4;job->source.roles=mode==0||mode==2?3:2;job->source.data_channels=mode==0||mode==2?7:6;job->texture_limit=2;job->source.rgba.resize(64);
   for(unsigned n=0;n<64;++n)job->source.rgba[n]=mode==2?123:std::uint8_t((n*37)%256);
   const auto original=job->source.rgba;assert(prepare_mips(*job,revision));
   const bool uniform=mode==2;const auto colour=job->levels[0].empty()?std::vector<std::uint8_t>{}:job->levels[0][0].bytes;const auto data=job->levels[1][0].bytes;const auto packed=job->packed_levels.empty()?std::vector<std::uint8_t>{}:job->packed_levels[0].bytes;
   if(mode==0)assert(colour!=data);
   if(mode==3)reject_compact=true;
   if(mode==4){job->direct_payload=true;reject_compact=true;}
   p.active_image=std::move(job);p.upload_budget_ms=1000;std::size_t budget=1u<<20;const bool ok=p.upload_image_step(budget,SceneClock::now());
   if(mode==4){assert(!ok&&p.active_image->compact_reprepare&&p.active_image->texture_limit==2);reject_compact=false;continue;}
   assert(ok&&p.error.empty());assert(p.active_image->source.width==4&&p.active_image->source.height==4&&p.active_image->source.rgba==original);
   for(unsigned role=0;role<2;++role){if(!(p.active_image->source.roles&(1u<<role)))continue;
    glBindTexture(GL_TEXTURE_2D,role?p.linear_images[0]:p.images[0]);GLint w=0,h=0,maxlevel=0;glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&w);glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_HEIGHT,&h);glGetTexParameteriv(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,&maxlevel);
    assert(w==(uniform?1:2)&&h==w&&maxlevel==(uniform?0:1));
    if(uniform){std::array<unsigned char,4>pixel{};glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,pixel.data());for(auto b:pixel)assert(b==123);}
    else if(role==1&&mode==1){std::vector<unsigned char>pixels(8);glGetTexImage(GL_TEXTURE_2D,0,GL_RG,GL_UNSIGNED_BYTE,pixels.data());assert(pixels==packed);}
    else{std::vector<unsigned char>pixels(16);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());assert(pixels==(role?data:colour));}
   }
   if(!uniform)for(unsigned role=0;role<2;++role){if(!(p.active_image->source.roles&(1u<<role)))continue;
    glBindTexture(GL_TEXTURE_2D,role?p.linear_images[0]:p.images[0]);glPixelStorei(GL_PACK_ALIGNMENT,1);
    const bool compact=role==1&&mode==1;const auto&expected=compact?p.active_image->packed_levels[1].bytes:p.active_image->levels[role][1].bytes;
    std::vector<unsigned char>tail(expected.size());glGetTexImage(GL_TEXTURE_2D,1,compact?GL_RG:GL_RGBA,GL_UNSIGNED_BYTE,tail.data());assert(tail==expected);
   }
   Model estimate;estimate.texture_limit=2;Pixels image;image.width=image.height=4;image.roles=p.active_image->source.roles;estimate.images.push_back(image);assert(p.gpu_bytes<=model_residency(estimate));
   assert(glGetError()==GL_NO_ERROR);reject_compact=false;
  }
  Model heavy;for(int n=0;n<6;++n){Pixels im;im.width=im.height=4096;im.roles=2;heavy.images.push_back(im);}const auto full=model_residency(heavy);assert(full>(768u<<20));heavy.texture_limit=2048;const auto reduced=model_residency(heavy);assert(reduced<full/3&&reduced<=(257u<<20));
  std::puts("PASS texturebudget realGL: originalrgba/sourceidentity unchanged; distinct sRGB/data mip1; RG8samepackedbytes; uniform1x1; compactunsupported RGBAfallbacksame2x2 and directpayloadrepreparepolicy; selectedmipresidencyupperbound");
 }
};}
int main(){const auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);auto display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(display,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto gl=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,gl));hui::gfx::set_glsl_prefix("#version 450 core\n");museum::ObjectSceneBudgetInspection::run();}
