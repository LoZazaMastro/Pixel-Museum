// Full-resolution GPU-only resolve and detail/alpha regression checks.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
// Fail even if an otherwise valid-looking result took the forbidden slow path.
extern "C" void APIENTRY glBlitFramebuffer(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum){std::fputs("Unexpected framebuffer blit\n",stderr);std::abort();}
extern "C" void APIENTRY glRenderbufferStorageMultisample(GLenum,GLsizei,GLenum,GLsizei,GLsizei){std::fputs("Unexpected multisample allocation\n",stderr);std::abort();}
int main(){
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint major,minor;assert(eglInitialize(d,&major,&minor)&&eglBindAPI(EGL_OPENGL_API));const EGLint attributes[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto c=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attributes);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,c));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {
 museum::ObjectScene scene;
 for(unsigned test=0;test<2;++test){const char*path=test?"build/material-fixtures/post-aa-sharp-artwork.glb":"build/material-fixtures/unlit-linear-factor.glb";assert(scene.load(path));constexpr int width=3840,height=2160;const auto texture=scene.render(.27f,width,height,.23f);assert(texture);glBindTexture(GL_TEXTURE_2D,texture);GLint w=0,h=0;glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&w);glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_HEIGHT,&h);assert(w==width&&h==height);const auto timing=scene.timings();assert(timing.render_samples==1&&timing.coverage_post_aa);GLuint target=0;glGenFramebuffers(1,&target);glBindFramebuffer(GL_FRAMEBUFFER,target);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,texture,0);std::vector<unsigned char>pixels(size_t(width)*height*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());size_t visible=0,partial=0,opaque=0;
 for(size_t n=0;n<pixels.size();n+=4){const auto alpha=pixels[n+3];if(!alpha)continue;++visible;if(alpha<255)++partial;else ++opaque;if(!test){for(unsigned channel=0;channel<3;++channel)assert(std::abs(int(pixels[n+channel])-118)<=2);}else if(alpha==255){assert(pixels[n+1]<=2);const bool red=pixels[n]>=253&&pixels[n+2]<=2,blue=pixels[n]<=2&&pixels[n+2]>=253;assert(red||blue);}}
 assert(visible>100000&&partial>100&&opaque>100000);std::printf("4K postAA%s: %zu visible / %zu antialiased silhouette / %zu exact opaque pixels; no blit or MSAA\n",test?" sharp artwork":" neutral alpha",visible,partial,opaque);glBindFramebuffer(GL_FRAMEBUFFER,0);glDeleteFramebuffers(1,&target);assert(glGetError()==GL_NO_ERROR);
 }
 }
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,c);eglTerminate(d);
}
