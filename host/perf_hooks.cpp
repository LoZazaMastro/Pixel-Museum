// Linker wrappers observe production calls; test measurements opt out explicitly.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "host/perf_hooks.hpp"
#include <GL/gl.h>
#include <GL/glext.h>
namespace museum::host {
namespace { TransferCounts counts; bool enabled=false; }
void reset_transfers(){counts={};}
void count_transfers(bool value){enabled=value;}
TransferCounts transfers(){return counts;}
}
extern "C" {
void __real_glBlitFramebuffer(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum);
void __real_glReadPixels(GLint,GLint,GLsizei,GLsizei,GLenum,GLenum,void*);
void __real_glGetTexImage(GLenum,GLint,GLenum,GLenum,void*);
void __real_glCopyImageSubData(GLuint,GLenum,GLint,GLint,GLint,GLint,GLuint,GLenum,GLint,GLint,GLint,GLint,GLsizei,GLsizei,GLsizei);
void __wrap_glBlitFramebuffer(GLint a,GLint b,GLint c,GLint d,GLint e,GLint f,GLint g,GLint h,GLbitfield mask,GLenum filter){
    if(museum::host::enabled)++museum::host::counts.blits;
    __real_glBlitFramebuffer(a,b,c,d,e,f,g,h,mask,filter);
}
void __wrap_glReadPixels(GLint x,GLint y,GLsizei w,GLsizei h,GLenum format,GLenum type,void*data){
    if(museum::host::enabled)++museum::host::counts.read_pixels;
    __real_glReadPixels(x,y,w,h,format,type,data);
}
void __wrap_glGetTexImage(GLenum target,GLint level,GLenum format,GLenum type,void*data){
    if(museum::host::enabled)++museum::host::counts.get_texture;
    __real_glGetTexImage(target,level,format,type,data);
}
void __wrap_glCopyImageSubData(GLuint a,GLenum b,GLint c,GLint d,GLint e,GLint f,GLuint g,GLenum h,GLint i,GLint j,GLint k,GLint l,GLsizei w,GLsizei height,GLsizei depth){
    if(museum::host::enabled)++museum::host::counts.copy_images;
    __real_glCopyImageSubData(a,b,c,d,e,f,g,h,i,j,k,l,w,height,depth);
}
}
