#pragma once
#include "third_party/stb/stb_image_write.h"
namespace museum {
inline bool ScreenInspection::verify_arcade_cage_visual(Screen&s,unsigned framebuffer,int width,int height){
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.connection_panel_=false;
 s.gallery_=s.screening_=s.fullscreen_=s.year_guide_=s.chapters_=false;s.panel_.snap(0);s.year_panel_.snap(0);s.history_focus_=false;s.detail_=false;s.story_open_.snap(0);
 const auto capture=[&](const char*name){s.draw(width,height,framebuffer);if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char>pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png((std::string("build/previews/arcade-current-")+name+".png").c_str(),width,height,4,pixels.data(),width*4)!=0;};
 const auto open=[&](const char*id){int index=-1;for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].id==id)index=int(n);if(index<0)return false;s.open_experience(index,{64,350,548,370});s.experience_open_.snap(1);s.experience_intro_.snap(0);s.experience_introduction_=false;s.experience_paused_=false;s.experience_pause_open_.snap(0);return true;};
 if(!open("maze")||!capture("maze-cage-start"))return false;
 hui::InputFrame input;input.connected=true;hui::ui::Feedback feedback;
 for(int n=0;n<100;++n){feedback.clear();s.handle(input,feedback);s.update(1.f/60);}
 if(!capture("maze-cage-release"))return false;
 for(const char*id:{"formation","bricks","gravity","paddle"})if(!open(id)||!capture(id))return false;
 input.secondary.connected=true;s.handle(input,feedback);if(!capture("paddle-two-players"))return false;
 if(!open("gravity"))return false;input.secondary.connected=false;input.pressed=hui::action_bit(hui::Action::menu);s.handle(input,feedback);s.experience_pause_open_.snap(1);
 if(!capture("gravity-paused-no-legend"))return false;
 std::printf("ARCADE_CAGE_VISUAL_PASS eight actual Screen captures %dx%d GL0\n",width,height);return true;
}
}
