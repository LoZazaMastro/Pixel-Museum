#include "museum/study.hpp"
#include "museum/study_controls.hpp"
#include "ui/glyphs.hpp"
#include "gfx/renderer.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include <vector>
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Weverything"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#pragma clang diagnostic pop
void check_flight_mechanics();
std::unique_ptr<museum::Study> flight_preview(int chamber);
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string b(ftell(f),'\0');rewind(f);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
int main(){
 check_flight_mechanics();
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));
 const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto context=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,context));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;
  const char*paths[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned n=0;n<4;++n){assert(faces[n].load(read(paths[n])));*refs[n]={&faces[n],renderer.batch().create_font_texture(faces[n])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;
  for(int chamber=0;chamber<3;++chamber){auto study=flight_preview(chamber);hui::gfx::DrawList list;study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0x758d80));list.rounded_rect({0,960,1920,120},0,hui::gfx::Color::rgb(0x0b100e));museum::draw_study_controls(list,fonts,"wireframe",{60,988,1800,85},hui::gfx::Color::rgb(0xf1efe7),hui::gfx::Color::rgb(0x0b100e),true);
  renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);char path[128];std::snprintf(path,sizeof(path),"build/previews/study-flight-stage%d-4k.png",chamber+1);assert(stbi_write_png(path,3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::puts("Flight4K real-GL render with glyph footer PASS (not PS5 performance measured)");}renderer.release();target.destroy();}
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,context);eglTerminate(d);
}
