#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::preview_ps1_presentations(Screen&s,unsigned framebuffer,int width,int height){
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.year_guide_=false;s.panel_.snap(0);s.year_panel_.snap(0);s.dark_theme_=true;s.theme_mix_.snap(1);s.reduced_=true;s.preview(0);
 auto entry=std::find_if(s.catalog_.entries.begin(),s.catalog_.entries.end(),[](const auto&e){return e.id=="playstation";});if(entry==s.catalog_.entries.end()||entry->models.empty())return false;
 const auto original=entry->models[0];
 const std::vector<std::vector<std::string>>groups={original.include_groups,{"node:Ps1_body_18","node:ps_controller.001_4"},{"node:Ps1_body_18","node:ps_controller.002_5"}};
 const char*labels[]={"current-cables","body-one-controller","body-front-controller"};
 for(size_t n=0;n<groups.size();++n){
  s.object_.cancel();for(size_t k=0;k<s.prepared_objects_.size();++k){s.prepared_objects_[k].cancel();s.prepared_paths_[k].clear();}
  entry->models[0].include_groups=groups[n];s.select("playstation");freeze_object(s);
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(90);
  while(!s.object_texture_&&std::chrono::steady_clock::now()<deadline){s.update(1.f/120);std::this_thread::sleep_for(std::chrono::milliseconds(2));if(!s.object_.error().empty()){std::fprintf(stderr,"PS1 proposal failed: %s\n",s.object_.error().c_str());return false;}}
  if(!s.object_texture_)return false;
  for(int frame=0;frame<40;++frame){s.update(1.f/120);s.draw(width,height,framebuffer);}
  const auto t=s.object_.timings();if(t.render_width!=1920||t.render_height!=960||!t.coverage_post_aa||glGetError()!=GL_NO_ERROR)return false;
  std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);
  const auto out=std::string("build/previews/ps1-presentation-")+labels[n]+"-4k.png";if(!stbi_write_png(out.c_str(),width,height,4,pixels.data(),width*4)||glGetError()!=GL_NO_ERROR)return false;
  std::printf("PASS PS1 proposal %s / actual%zuMiB / ready%.2fms /4KGL0\n",labels[n],t.estimated_gpu_bytes>>20,t.load_ready_ms);
 }
 entry->models[0]=original;return true;
}
}
