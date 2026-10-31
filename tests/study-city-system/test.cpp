#include "museum/study_city_system.hpp"
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
void check_city_system_mechanics();
std::unique_ptr<museum::Study> city_system_preview();
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string b(ftell(f),'\0');rewind(f);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
int main(){
 check_city_system_mechanics();assert(!museum::make_study_city_system("not-a-city"));
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));
 const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto context=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,context));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;
  const char*paths[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned n=0;n<4;++n){assert(faces[n].load(read(paths[n])));*refs[n]={&faces[n],renderer.batch().create_font_texture(faces[n])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;
  auto study=museum::make_study_city_system("city-system");hui::ui::Feedback feedback;
  for(unsigned n=0;n<18000;++n){hui::InputFrame i;i.connected=true;i.stick_x=std::sin(float(n)*.013f);i.stick_y=std::cos(float(n)*.017f);if(n%173==0)i.pressed=hui::action_bit(hui::Action::confirm);if(n%541==0)i.pressed|=hui::action_bit(hui::Action::north);if(n%1601==0)i.pressed|=hui::action_bit(hui::Action::west);if(n%1301==0)i.focus_lost=true;if(n%90<16){i.touch.available=true;i.touch.count=1;i.touch.points[0]={float(n%101)/100,float(n%67)/66,0};}study->handle(i,feedback);study->update(n%101==0?std::numeric_limits<float>::quiet_NaN():1.f/120);const int note=study->take_note();assert(note==-1||(note>=48&&note<=84));assert(std::isfinite(feedback.rumble_strength)&&feedback.rumble_strength<=1);feedback.clear();
   if(n%600==0){hui::gfx::DrawList list;study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0x985b42));assert(list.instances().size()<1500);for(const auto&item:list.instances())for(float v:item.rect)assert(std::isfinite(v));}}
  study=city_system_preview();hui::gfx::DrawList list;study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0x758d80));list.rounded_rect({0,960,1920,120},0,hui::gfx::Color::rgb(0x0b100e));
  using B=hui::ui::Button;const hui::ui::Hint controls[]={{B::left_stick,"Choose"},{B::cross,"Build / continue"},{B::triangle,"Road / green"},{B::touchpad,"Draw"},{B::square,"Restart"},{B::circle,"Back"}};hui::ui::HintLayout layout;layout.size=29;layout.text_size=21;layout.cy=1018;hui::ui::draw_hints(list,fonts,hui::ui::GlyphStyle::mono(hui::gfx::Color::rgb(0xf1efe7),hui::gfx::Color::rgb(0x0b100e)),controls,6,70,false,layout);
  renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);assert(stbi_write_png("build/previews/study-city-system-4k.png",3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::puts("city-system:18000 finite simulation frames;4K real-GL render with glyph footer PASS (not PS5 performance measured)");renderer.release();target.destroy();}
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,context);eglTerminate(d);
}
