#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include "third_party/nlohmann/json.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <fstream>
#include <thread>
#include <chrono>
#include <cstdio>
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
int main(int argc,char**argv){
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));assert(get);
 auto display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(display,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));
 const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};
 auto gl=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,gl));hui::gfx::set_glsl_prefix("#version 450 core\n");
 nlohmann::json index;std::ifstream("models/index.json")>>index;
 const std::vector<std::string>ids=argc>1?std::vector<std::string>{argv[1]}:std::vector<std::string>{"playstation","nintendo-64","game-boy"};
 for(const auto&id:ids){
  const auto row=std::find_if(index["models"].begin(),index["models"].end(),[&](const auto&v){return v.value("exhibit_id","")==id;});assert(row!=index["models"].end());
  const auto groups=(*row).value("include_groups",std::vector<std::string>{});if(argc==1)assert(!groups.empty());
  museum::ObjectScene scene;scene.request(argc>2?argv[2]:(*row)["asset_file"].get<std::string>(),groups);auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(120);
  while(!scene.ready()&&std::chrono::steady_clock::now()<deadline){scene.upload_pending(2,true);if(!scene.error().empty()){std::fprintf(stderr,"%s: %s\n",id.c_str(),scene.error().c_str());return 1;}std::this_thread::sleep_for(std::chrono::milliseconds(1));}assert(scene.ready());
  for(int angle=0;angle<2;++angle){auto texture=scene.render((*row).value("initial_angle",0.f)+angle*.8f,3840,1920,(*row).value("initial_tilt",.13f),(*row).value("source_z_up",false),(*row).value("initial_zoom",1.f));assert(texture);glBindTexture(GL_TEXTURE_2D,texture);std::vector<unsigned char>pixels(3840u*1920*4);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());size_t visible=0;for(size_t n=3;n<pixels.size();n+=4)if(pixels[n])++visible;assert(visible>10000&&visible<3840u*1920);stbi_flip_vertically_on_write(1);const auto path=std::string("build/previews/current-console-only-")+id+"-"+std::to_string(angle)+"-4k.png";assert(stbi_write_png(path.c_str(),3840,1920,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::printf("PASS %s angle%d %zu visible3840x1920GL0, groups%zu\n",id.c_str(),angle,visible,groups.size());std::fflush(stdout);}
  scene.release();
 }
 eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);
}
