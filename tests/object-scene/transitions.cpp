// Actual original-master transition and source-read admission regression.
#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include "third_party/nlohmann/json.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <thread>
int main(){
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint major,minor;assert(eglInitialize(d,&major,&minor)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto c=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,c));hui::gfx::set_glsl_prefix("#version 450 core\n");
 std::ifstream f("models/index.json");nlohmann::json index;f>>index;
 {
  museum::ObjectScene scene;
  for(unsigned round=0;round<3;++round){const std::string id=round==1?"playstation":"game-boy";nlohmann::json source;for(const auto&r:index["models"])if(r["exhibit_id"]==id)source=r;assert(!source.is_null());const auto path=source["asset_file"].get<std::string>();const auto groups=source.value("include_groups",std::vector<std::string>{});
   scene.request(path,groups);
   if(round){assert(scene.timings().pending_gpu_deletes>0);std::this_thread::sleep_for(std::chrono::milliseconds(30));assert(scene.stage()=="Reading the original model");assert(scene.timings().encoded_model_bytes==0);scene.cancel();scene.request("/superseded-missing.glb");scene.cancel();scene.request(path,groups);}
   for(unsigned n=0;n<20000&&!scene.ready();++n){scene.upload_pending();if(!scene.error().empty())break;std::this_thread::sleep_for(std::chrono::milliseconds(1));}
   if(!scene.ready()){std::fprintf(stderr,"%s failed: %s\n",id.c_str(),scene.error().c_str());return 2;}
   assert(scene.timings().pending_gpu_deletes==0);assert(scene.stats().srgb_textures+scene.stats().linear_textures==(round==1?13u:11u));assert(scene.render(-.35f,1024,576,.13f,false,2));assert(glGetError()==GL_NO_ERROR);
   std::printf("PASS transition %u %s: %.2fms request-to-ready, original artwork/geometry, zero GL errors\n",round,id.c_str(),scene.timings().load_ready_ms);
  }
 }
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,c);eglTerminate(d);
}
