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
namespace museum {namespace {struct MotionInspection {
 static void place(Study&study,const std::string&,unsigned stage){
  auto&s=static_cast<Momentum&>(study);hui::ui::Feedback feedback;bool first=false,second=false,third=false,highjump=false,enemyjump=false;int hurt_frames=0;
  for(int frame=0;frame<120*45;++frame){hui::InputFrame input;input.connected=true;input.stick_x=1;input.stick_y=stage!=5&&s.x_>600&&s.x_<800?1.f:0.f;bool jump=false;
   if(stage==7&&!highjump&&s.x_>1700&&s.v_>440)input.stick_x=-1;
   if(stage==6&&s.x_>2950&&s.x_<3210&&s.v_>650)input.stick_x=-1;
   if(!first&&s.x_>1080&&s.grounded_){first=true;jump=true;}
   if(stage==7&&!highjump&&s.x_>1800&&s.x_<1940&&s.v_<470&&s.grounded_){highjump=true;jump=true;}
   if(stage==7&&!enemyjump&&s.x_>3040&&s.x_<3140&&s.grounded_){enemyjump=true;jump=true;}
   if(!second&&s.x_>(stage==6?3210:3360)&&s.x_<3470&&s.grounded_){second=true;jump=true;}
   if(stage==6&&!third&&s.x_>3870&&s.x_<4250&&s.grounded_){third=true;jump=true;}
   if(jump)input.pressed=input.held=hui::action_bit(Action::confirm);
   s.handle(input,feedback);s.update(1.f/120);
   for(const auto&ring:s.loose_)if(ring.life>0){++hurt_frames;break;}
   const bool ready=stage==0?s.x_>=550:stage==1?s.x_>=1770:stage==2?s.loop_>=1.2f:stage==3?s.x_>=4700:stage==4?s.x_>=5990:stage==5?hurt_frames>=18&&int(s.time_*10)%2==0:stage==6?s.x_>4700&&s.y_>Momentum::ceiling(s.x_)+26:s.x_>2230&&s.grounded_&&std::abs(s.y_+26-355)<1;
   if(ready){std::printf("actual-input-preview stage%u x%.2f y%.2f v%.2f loop%.2f falls%d\n",stage,s.x_,s.y_,s.v_,s.loop_,s.falls_);assert(s.falls_==0);return;}
  }assert(false&&"Real-input preview stage unreachable");
 }};}}
std::uint64_t signature(museum::Study&study,hui::ui::Fonts&fonts){hui::gfx::DrawList list;study.draw(list,fonts,{80,170,1760,760},hui::gfx::Color::rgb(0x985b42));std::uint64_t hash=1469598103934665603ull;for(const auto&item:list.instances())for(float value:item.rect){std::uint32_t bits=0;std::memcpy(&bits,&value,sizeof(bits));hash=(hash^bits)*1099511628211ull;}return hash;}
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string b(ftell(f),'\0');rewind(f);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
std::unique_ptr<museum::Study> make(const std::string&key){return museum::make_study_motion(key);}
void check_mechanics(hui::ui::Fonts&);
int main(){auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto c=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,c));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;const char*names[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned i=0;i<4;++i){assert(faces[i].load(read(names[i])));*refs[i]={&faces[i],renderer.batch().create_font_texture(faces[i])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;const char*keys[]={"momentum"};for(unsigned stage=0;stage<8;++stage)for(const char*key:keys){auto study=make(key);assert(study&&study->help()[0]);hui::ui::Feedback feedback;hui::InputFrame input;input.connected=true;museum::MotionInspection::place(*study,key,stage);hui::gfx::DrawList list;list.rounded_rect({0,0,1920,1080},0,hui::gfx::Color::rgb(0x091116));study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0xbeaccc));museum::draw_study_controls(list,fonts,key,{65,985,1790,70},hui::gfx::Color::rgb(0xe8e8d9),hui::gfx::Color::rgb(0x091116),true);renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);assert(stbi_write_png((std::string("build/previews/sonic1-refined-")+key+"-"+std::to_string(stage)+"-4k.png").c_str(),3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::printf("%s 3840x2160 / %zu drawing instances / GL0\n",key,list.instances().size());}
renderer.release();target.destroy();} eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,c);eglTerminate(d);}
