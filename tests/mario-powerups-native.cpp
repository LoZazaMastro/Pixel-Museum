// Reuse the established native EGL/font harness, retaining its old captures.
#define main prior_motion_layout_main
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wreturn-type"
#include "tests/motion-layout-preview.cpp"
#pragma clang diagnostic pop
#undef main
#include <filesystem>
namespace museum {namespace {struct MarioInspection {
 static void place(Jump&s,unsigned stage){hui::InputFrame i;i.connected=true;hui::ui::Feedback f;
  if(stage==1||stage==2){s.p_={205,490};s.vy_=-650;s.grounded_=false;for(int n=0;n<10;++n){s.handle(i,f);s.update(.01f);}for(unsigned n=0;n<(stage==1?2u:10u);++n)s.update(.1f);return;}
  if(stage==3||stage==4||stage==5||stage==10||stage==11){s.mushroom_active_=true;s.mushroom_emerge_=.5f;s.mushroom_={105,550};s.handle(i,f);s.update(.001f);assert(s.large_);}
  if(stage==4){i.held=hui::action_bit(hui::Action::down);s.handle(i,f);}
  if(stage==5){s.p_={300,500};s.vy_=-650;s.grounded_=false;s.update(.02f);s.update(.06f);}
  if(stage==6){s.p_={380,490};s.vy_=-650;s.grounded_=false;s.handle(i,f);s.update(.02f);s.update(.1f);}
  if(stage==7||stage==8){s.p_={1141,445};i.held=hui::action_bit(hui::Action::down);for(int n=0;n<30;++n){s.handle(i,f);s.update(.01f);}assert(s.pipe_from_==1);if(stage==8){i.held=0;for(int n=0;n<140;++n){s.handle(i,f);s.update(.01f);}assert(s.secret_);}}
  if(stage==9){s.secret_=true;s.p_={1126,535};i.stick_x=1;s.handle(i,f);s.update(.02f);s.update(.1f);assert(s.pipe_from_==3);}
  if(stage==10||stage==11){s.p_={Jump::enemy_x(0,s.time_+.001f),520};s.immune_=0;s.handle(i,f);s.update(.001f);assert(!s.large_);if(stage==11){s.immune_=0;s.update(.001f);assert(s.falls_==1&&s.p_.x==105);}}
 }
};}}
int main(){
 auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));auto display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint major,minor;assert(eglInitialize(display,&major,&minor)&&eglBindAPI(EGL_OPENGL_API));
 const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};auto context=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);assert(eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,context));hui::gfx::set_glsl_prefix("#version 450 core\n");
 {hui::gfx::Renderer renderer;assert(renderer.init());hui::gfx::Canvas target;assert(target.create(3840,2160,1));std::array<hui::gfx::Font,4>faces;hui::ui::Fonts fonts;
  const char*names[]={"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"};hui::ui::FontRef*refs[]={&fonts.regular,&fonts.semibold,&fonts.display,&fonts.mono};for(unsigned n=0;n<4;++n){assert(faces[n].load(read(names[n])));*refs[n]={&faces[n],renderer.batch().create_font_texture(faces[n])};}fonts.pixel=fonts.mono;fonts.hand=fonts.regular;
  const char*scenes[]={"start-small","mushroom-emerging","mushroom-moving","grown-double-height","grown-crouched","brick-four-fragments","question-coin-rises","pipe-entry-hidden","secret-room","pipe-exit-hidden","damage-shrinks","death-at-start"};
  const std::string folder="build/previews/mario-powerups-refined/";std::filesystem::create_directories(folder);
  for(unsigned stage=0;stage<12;++stage){museum::Jump study;museum::MarioInspection::place(study,stage);hui::gfx::DrawList list;const hui::gfx::Color base{.035f,.055f,.065f,1},accent=hui::gfx::Color::rgb(0xc391a0);list.rounded_rect({0,0,1920,1080},0,base);study.draw(list,fonts,{0,0,1920,960},accent);museum::draw_study_controls(list,fonts,"jump",{64,990,1792,88},hui::gfx::Color::rgb(0xf1efe7),base,true);
   renderer.begin();renderer.draw(list);renderer.present(target.framebuffer(),3840,2160);glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<unsigned char>pixels(3840u*2160*4);glReadPixels(0,0,3840,2160,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);assert(stbi_write_png((folder+scenes[stage]+"-4k.png").c_str(),3840,2160,4,pixels.data(),3840*4));assert(glGetError()==GL_NO_ERROR);std::printf("Mario native %s3840x2160 GL0\n",scenes[stage]);
  }renderer.release();target.destroy();
 }eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,context);eglTerminate(display);
}
