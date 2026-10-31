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
 auto&s=static_cast<Momentum&>(study);hui::ui::Feedback f;const int hz=120;float jump_delay=0,stuck=0,lastx=s.x_,charge_time=0;int prepare=0,taps=0,tube_mask=0;
 const float targets[]={300,1200,3300,3900,5500,6700,9470,5660,9568};
 const float target=targets[stage];
  for(int frame=0;frame<hz*90;++frame){hui::InputFrame i;i.connected=true;i.stick_x=1;if(s.x_/1.6f>2100&&s.x_/1.6f<2600&&s.grounded_&&std::abs(s.v_)>300)i.stick_y=1;jump_delay-=1.f/hz;bool jump=false;
   if(s.grounded_&&jump_delay<=0){const float look=std::max(50.f,std::abs(s.v_)*.14f);const float floor=Momentum::land_floor(s.x_+look,s.y_+26,50,55);
    if(floor>1e7f||floor<s.y_+26-15||stuck>.18f)jump=true;
    for(unsigned n=0;n<22;++n)if(!s.enemy_down_[n]){const auto e=s.enemy(n);if(e.x>s.x_&&e.x-s.x_<look+55&&std::abs(e.y-s.y_)<75)jump=true;}
    for(const auto&p:s.native_spikes)if(p.x*1.6f>s.x_&&p.x*1.6f-s.x_<look+70&&std::abs(p.y*1.6f-s.y_)<80)jump=true;
    if(s.x_>320&&s.x_<480)jump=true;
   }
   if(s.x_/1.6f>3400&&s.x_/1.6f<3700){jump=false;if(s.v_>380)i.stick_x=-1;}
   if(s.x_/1.6f>5200&&s.x_/1.6f<5660){jump=false;i.stick_y=1;}
   if((s.x_/1.6f>6080&&s.x_/1.6f<6420)||(s.x_/1.6f>6600&&s.x_/1.6f<6930)){jump=false;i.stick_y=1;}
   if(!prepare&&s.x_/1.6f>5100&&s.x_/1.6f<5400&&s.grounded_&&s.v_<650)prepare=1;
   if(prepare==1){jump=false;i.stick_y=0;i.stick_x=s.v_>10?-1:0;if(std::abs(s.v_)<15)prepare=2;}
   if(prepare==2){jump=false;i.stick_y=1;i.stick_x=0;charge_time+=1.f/hz;if(charge_time>.11f){i.pressed=i.held=hui::action_bit(Action::confirm);charge_time=0;if(++taps>=5)prepare=3;}}
   else if(prepare==3){jump=false;i.stick_y=0;i.stick_x=1;prepare=4;}
   if(jump){i.pressed=i.held=hui::action_bit(Action::confirm);jump_delay=.3f;}
   const float before_x=s.x_,before_y=s.y_;const int before_falls=s.falls_,before_rings=s.rings_;
   s.handle(i,f);s.update(1.f/hz);if(std::abs(s.x_-lastx)<.1f)stuck+=1.f/hz;else stuck=0;lastx=s.x_;
   assert(std::isfinite(s.x_)&&std::isfinite(s.y_)&&std::isfinite(s.v_)&&std::isfinite(s.vy_));
   if(s.tube_distance_>=0)tube_mask|=1<<s.tube_number_;
   if(s.falls_>before_falls)printf("DEATH %dHz native x%.1f y%.1f rings%d time%.2f\n",hz,before_x/1.6f,before_y/1.6f,before_rings,s.time_);
   const bool ready=stage==4?s.loop_>1.f:stage==5?s.tube_number_==1&&s.tube_distance_>100:stage==7?s.loop_done_&&s.x_/1.6f>5660:stage==8?s.finished_:s.x_/1.6f>=target;
   if(ready){std::printf("ACTUAL INPUT stage%u native x%.1f y%.1f falls%d loopdone%d tube%.1f\n",stage,s.x_/1.6f,s.y_/1.6f,s.falls_,s.loop_done_,s.tube_distance_);return;}
}assert(false);}};}}
std::uint64_t signature(museum::Study&study,hui::ui::Fonts&fonts){hui::gfx::DrawList list;study.draw(list,fonts,{80,170,1760,760},hui::gfx::Color::rgb(0x985b42));std::uint64_t hash=1469598103934665603ull;for(const auto&item:list.instances())for(float value:item.rect){std::uint32_t bits=0;std::memcpy(&bits,&value,sizeof(bits));hash=(hash^bits)*1099511628211ull;}return hash;}
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string b(ftell(f),'\0');rewind(f);assert(fread(b.data(),1,b.size(),f)==b.size());fclose(f);return b;}
std::unique_ptr<museum::Study> make(const std::string&key){return museum::make_study_motion(key);}
void check_mechanics(hui::ui::Fonts&);
int main(){auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto d=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint ma,mi;assert(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_API));const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto c=eglCreateContext(d,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,c));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;const char*names[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned i=0;i<4;++i){assert(faces[i].load(read(names[i])));*refs[i]={&faces[i],renderer.batch().create_font_texture(faces[i])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;const char*keys[]={"momentum"};for(unsigned stage=0;stage<9;++stage)for(const char*key:keys){auto study=make(key);assert(study&&study->help()[0]);hui::ui::Feedback feedback;hui::InputFrame input;input.connected=true;museum::MotionInspection::place(*study,key,stage);hui::gfx::DrawList list;list.rounded_rect({0,0,1920,1080},0,hui::gfx::Color::rgb(0x091116));study->draw(list,fonts,{0,0,1920,960},hui::gfx::Color::rgb(0xbeaccc));museum::draw_study_controls(list,fonts,key,{65,985,1790,70},hui::gfx::Color::rgb(0xe8e8d9),hui::gfx::Color::rgb(0x091116),true);renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);assert(stbi_write_png((std::string("build/previews/sonic-native-")+key+"-"+std::to_string(stage)+"-4k.png").c_str(),3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::printf("%s 3840x2160 / %zu drawing instances / GL0\n",key,list.instances().size());}
renderer.release();target.destroy();} eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,c);eglTerminate(d);}
