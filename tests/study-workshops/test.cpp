#include "museum/study_workshops.hpp"
#include "museum/study_controls.hpp"
#include "gfx/renderer.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <limits>
#include <string>
#include <vector>
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Weverything"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#pragma clang diagnostic pop
void check_workshop_mechanics();
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string b(ftell(f),'\0');rewind(f);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
int main(){
 check_workshop_mechanics();
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));
 const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto context=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,context));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;
  const char*paths[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned n=0;n<4;++n){assert(faces[n].load(read(paths[n])));*refs[n]={&faces[n],renderer.batch().create_font_texture(faces[n])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;
  const char*keys[]={"cartridge-rules","pocket-budget","adaptive-pulse","jump-lab","pixels"};for(const char*key:keys){auto study=museum::make_study_workshops(key);assert(study&&study->help()[0]);hui::ui::Feedback feedback;
   for(unsigned n=0;n<12000;++n){hui::InputFrame input;input.connected=true;input.stick_x=std::sin(float(n)*.013f);input.trigger_r=float(n%180)/179;input.nav=hui::Direction(1+(n/45)%4);input.nav_from_stick=n%2;input.held=n%100<70?hui::action_bit(hui::Action::confirm):0;if(n%103==0)input.pressed=hui::action_bit(hui::Action::confirm);if(n%331==0)input.pressed|=hui::action_bit(hui::Action::page_next);if(n%521==0){input.touch.available=true;input.touch.count=1;input.touch.points[0]={float(n%101)/100,float(n%67)/66,0};}if(n%1601==0)input.pressed|=hui::action_bit(hui::Action::west);if(n%1301==0)input.focus_lost=true;
    study->handle(input,feedback);study->update(n%101==0?std::numeric_limits<float>::quiet_NaN():1.f/120);int note=study->take_note();assert(note==-1||(note>=48&&note<=84));assert(std::isfinite(feedback.rumble_strength)&&feedback.rumble_strength<=1);feedback.clear();
    if(n%400==0){hui::gfx::DrawList list;study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0x985b42));assert(list.instances().size()<1500);for(const auto&item:list.instances())for(float x:item.rect)assert(std::isfinite(x));}}
   study->reset();hui::InputFrame idle;idle.connected=true;for(int n=0;n<120;++n){study->handle(idle,feedback);study->update(1.f/120);}
   hui::gfx::DrawList list;study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0x985b42));list.rounded_rect({0,960,1920,120},0,hui::gfx::Color::rgb(0x0b100e));museum::draw_study_controls(list,fonts,key,{64,990,1792,88},hui::gfx::Color::rgb(0xf1efe7),hui::gfx::Color::rgb(0x0b100e),true);
   renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);assert(stbi_write_png((std::string("build/previews/workshop-")+key+"-4k.png").c_str(),3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::printf("%s: 12000 bounded 120Hz simulation frames / 4K rendering / bottom glyph hints PASS\n",key);}
  renderer.release();target.destroy();}
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,context);eglTerminate(d);
}
