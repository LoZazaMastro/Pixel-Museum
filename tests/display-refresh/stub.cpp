// Exercise actual Display request/fallback lifecycle; no hardware/FPS claim.
#include "platform/ps5/display_egl.hpp"
#include <GL/glcorearb.h>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdint>
#include <string>
#include <vector>
namespace {
struct State {bool initialized=false,can_request120=true,reject4k=false,query=true;int accepted=120,width=1920,height=1080,request=0,interval=-1,requested120=0,requested60=0;EGLint error=EGL_SUCCESS;std::vector<std::string>events;} state;
void reset(){state=State{};}
}
namespace hui::sys {void log(const char*format,...){va_list args;va_start(args,format);std::vprintf(format,args);va_end(args);std::putchar('\n');}}
extern "C" {
EGLDisplay eglGetDisplay(EGLNativeDisplayType){return reinterpret_cast<EGLDisplay>(std::uintptr_t(1));}
EGLint eglGetError(){const auto error=state.error;state.error=EGL_SUCCESS;return error;}
EGLBoolean eglInitialize(EGLDisplay,EGLint*major,EGLint*minor){assert(!state.initialized);state.initialized=true;state.events.push_back("init");*major=1;*minor=5;return EGL_TRUE;}
EGLBoolean eglBindAPI(EGLenum){return EGL_TRUE;}
EGLBoolean eglChooseConfig(EGLDisplay,const EGLint*,EGLConfig*config,EGLint,EGLint*count){*config=reinterpret_cast<EGLConfig>(std::uintptr_t(2));*count=1;return EGL_TRUE;}
EGLSurface eglCreateWindowSurface(EGLDisplay,EGLConfig,EGLNativeWindowType,const EGLint*){return reinterpret_cast<EGLSurface>(std::uintptr_t(3));}
EGLContext eglCreateContext(EGLDisplay,EGLConfig,EGLContext,const EGLint*){return reinterpret_cast<EGLContext>(std::uintptr_t(4));}
EGLBoolean eglMakeCurrent(EGLDisplay,EGLSurface,EGLSurface,EGLContext){return EGL_TRUE;}
EGLBoolean eglQuerySurface(EGLDisplay,EGLSurface,EGLint field,EGLint*out){*out=field==EGL_WIDTH?state.width:state.height;return EGL_TRUE;}
EGLBoolean eglSwapInterval(EGLDisplay,EGLint interval){state.interval=interval;return EGL_TRUE;}
EGLBoolean eglSwapBuffers(EGLDisplay,EGLSurface){state.events.push_back("swap");return EGL_TRUE;}
EGLBoolean eglDestroyContext(EGLDisplay,EGLContext){return EGL_TRUE;}
EGLBoolean eglDestroySurface(EGLDisplay,EGLSurface){return EGL_TRUE;}
EGLBoolean eglTerminate(EGLDisplay){state.initialized=false;return EGL_TRUE;}
void glGetIntegerv(GLenum field,GLint*out){*out=field==GL_MAJOR_VERSION?4:6;}
const GLubyte*glGetString(GLenum){return reinterpret_cast<const GLubyte*>("4.6 test lifecycle");}
#if EXPECT_DYNAMIC
EGLBoolean eglSetDisplayModePS5(EGLDisplay,EGLint width,EGLint height){assert(!state.initialized);state.events.push_back("size");if(state.reject4k&&width==3840){state.error=EGL_BAD_PARAMETER;return EGL_FALSE;}state.width=width;state.height=height;return EGL_TRUE;}
EGLBoolean eglSetDisplayRefreshPS5(EGLDisplay,EGLint rate){assert(!state.initialized);state.events.push_back("refresh");if(rate==120){++state.requested120;if(!state.can_request120){state.error=EGL_BAD_PARAMETER;return EGL_FALSE;}}else ++state.requested60;state.request=rate;return EGL_TRUE;}
EGLBoolean eglGetDisplayModePS5(EGLDisplay,EGLint*w,EGLint*h,EGLint*rate){state.events.push_back("query");if(!state.query)return EGL_FALSE;*w=state.width;*h=state.height;*rate=state.request==120?state.accepted:60;return EGL_TRUE;}
#endif
}
int main(){
 assert(hui::ps5::Display::supports_display_modes()==bool(EXPECT_DYNAMIC));
#if EXPECT_DYNAMIC
 for(unsigned scenario=0;scenario<5;++scenario){reset();state.accepted=scenario==1?60:120;state.can_request120=scenario!=2;state.query=scenario!=3;state.reject4k=scenario==4;
  hui::ps5::Display display;assert(display.open(3840,2160,120));
  assert(state.events.size()>=3&&state.events[0]=="size"&&state.events[state.events.size()-1]=="init");
  assert(state.requested120==1&&state.requested60==(scenario==2?1:0)&&state.interval==1);
  assert(display.width()==(scenario==4?1920:3840)&&display.height()==(scenario==4?1080:2160));
  assert(display.refresh_hz()==60); // No assumed acceptance before presentation.
  assert(display.swap());const int expected=scenario==1||scenario==2||scenario==3?60:120;
  assert(display.refresh_hz()==expected&&state.events.back()=="query");
  display.close();assert(!state.initialized&&display.refresh_hz()==60&&!display.swap());
 }
 std::puts("PASS dynamic Display: startup60 defaults do not cap accepted120; display60/APIreject/querymissing fallbacks, size fallback, pre-initialize mode requests, synchronized swap and close/reset.");
#else
 reset();hui::ps5::Display display;assert(display.open(3840,2160,120));assert(state.events.size()==1&&state.events[0]=="init"&&state.requested120==0&&state.interval==1);assert(display.width()==1920&&display.height()==1080&&display.refresh_hz()==60);assert(display.swap()&&display.refresh_hz()==60);display.close();
 std::puts("PASS legacy Display: fixed SDK keeps conservative60, synchronized presentation and no unsupported runtime API calls.");
#endif
}
