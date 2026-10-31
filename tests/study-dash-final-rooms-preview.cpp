#include "museum/study_motion.cpp"
#include "museum/study_controls.hpp"
#include "gfx/renderer.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <cassert>
#include <array>
#include <limits>
#include <cmath>
#include <cstring>
#include <cstdio>
#include <string>
#include <vector>
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Weverything"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#pragma clang diagnostic pop
std::uint64_t signature(museum::Study&study,hui::ui::Fonts&fonts){hui::gfx::DrawList list;study.draw(list,fonts,{80,170,1760,760},hui::gfx::Color::rgb(0x985b42));std::uint64_t hash=1469598103934665603ull;for(const auto&item:list.instances())for(float value:item.rect){std::uint32_t bits=0;std::memcpy(&bits,&value,sizeof(bits));hash=(hash^bits)*1099511628211ull;}return hash;}
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string b(ftell(f),'\0');rewind(f);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
namespace museum {namespace {struct DashInspection {static std::unique_ptr<Study> scene(unsigned room){auto s=std::make_unique<Dash>();s->enter(room);return s;}};}}
std::unique_ptr<museum::Study> make(const std::string&,unsigned room){return museum::DashInspection::scene(room);}
void check_mechanics(hui::ui::Fonts&);
int main(){auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto c=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,c));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;const char*names[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned i=0;i<4;++i){assert(faces[i].load(read(names[i])));*refs[i]={&faces[i],renderer.batch().create_font_texture(faces[i])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;const char*keys[]={"dash"};for(unsigned stage=0;stage<2;++stage)for(const char*key:keys){auto study=make(key,stage+3);assert(study&&study->help()[0]);hui::ui::Feedback feedback;hui::gfx::DrawList list;list.rounded_rect({0,0,1920,1080},0,hui::gfx::Color::rgb(0x091116));study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0xbeaccc));museum::draw_study_controls(list,fonts,"dash",{65,985,1790,70},hui::gfx::Color::rgb(0xe8e8d9),hui::gfx::Color::rgb(0x091116),true);renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);assert(stbi_write_png((std::string("build/previews/dash-redesigned-room-")+std::to_string(stage+4)+".png").c_str(),3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::printf("%s 3840x2160 / %zu drawing instances / GL0\n",key,list.instances().size());}
renderer.release();target.destroy();} eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,c);eglTerminate(d);}
