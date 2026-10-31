// Actual GL upload scheduler: measured fast path, slow-driver backoff and bytes.
#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <chrono>
#include <thread>
#include <vector>
#include <cstdio>
#include <algorithm>
namespace {unsigned calls=0;bool slow=false;GLuint atlas=0;std::size_t largest_chunk=0;}
extern "C" void __real_glTexSubImage2D(GLenum,GLint,GLint,GLint,GLsizei,GLsizei,GLenum,GLenum,const void*);
extern "C" void __wrap_glTexSubImage2D(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,GLenum format,GLenum type,const void*data){
 ++calls;largest_chunk=std::max(largest_chunk,std::size_t(w)*h*4);GLint name=0;glGetIntegerv(GL_TEXTURE_BINDING_2D,&name);atlas=GLuint(name);
 if(slow)std::this_thread::sleep_for(std::chrono::milliseconds(4));
 __real_glTexSubImage2D(target,level,x,y,w,h,format,type,data);
}
int main(){
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);auto display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint a,b;assert(eglInitialize(display,&a,&b)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto context=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,context));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {
 museum::ObjectScene scene;scene.request("build/material-fixtures/upload-adaptive4k.glb");unsigned slow_frames=0;bool grew=false,backed_off=false;std::size_t greatest=0;
 for(unsigned frame=0;frame<10000&&!scene.ready();++frame){
  // Establish measured fast transfers before simulating a suddenly slow driver.
  slow=calls>=24&&slow_frames<8;const unsigned before=calls;scene.upload_pending(1.5,true);const auto t=scene.timings();greatest=std::max(greatest,t.last_upload_bytes);grew|=t.upload_budget_bytes>(2u<<20);
  if(slow&&calls>before){assert(calls-before==1);++slow_frames;if(slow_frames>=3)backed_off|=t.upload_budget_bytes==(2u<<20);}
  assert(t.last_upload_bytes<=t.upload_budget_bytes&&t.upload_budget_bytes<=(16u<<20));assert(scene.error().empty());std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
 assert(scene.ready()&&slow_frames==8&&backed_off&&grew&&largest_chunk<=(512u<<10));assert(glGetError()==GL_NO_ERROR);
 glBindTexture(GL_TEXTURE_2D,atlas);std::vector<unsigned char> bytes(4096u*4096u*4u);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,bytes.data());for(std::size_t n=0;n<bytes.size();n+=4){assert(bytes[n]==38&&bytes[n+1]==62&&bytes[n+2]==117&&bytes[n+3]==255);}assert(glGetError()==GL_NO_ERROR);
 std::printf("PASS actual adaptive upload: fast cap grows, eight4ms driver frames perform one chunk only and back off to2MiB; chunk<=512KiB, tick<=16MiB; every4K GPU base texel unchanged. Maximum transferred tick%zuKiB.\n",greatest>>10);
 }
 eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,context);eglTerminate(display);
}
