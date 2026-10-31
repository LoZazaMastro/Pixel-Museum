#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::preview_console_cutouts(Screen&s,unsigned framebuffer,int width,int height,int mode){
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.year_guide_=false;s.panel_.snap(0);s.year_panel_.snap(0);s.reduced_=true;s.preview(0);
 auto capture=[&](const std::string&name){
  s.draw(width,height,framebuffer);std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);
  const auto path="build/previews/"+name+"-4k.png";return stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4)&&glGetError()==GL_NO_ERROR;
 };
 if(mode==1){
  const char*cutout_id=std::getenv("MUSEUM_CUTOUT_ENTRY");s.select(cutout_id?cutout_id:"workbook-03-21-game-boy-advance");const auto*entry=s.current();if(!entry||entry->images.empty()||entry->images[0].url.find(".png")==std::string::npos)return false;
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);while(!s.cache_.get(entry->images[0].url).texture&&std::chrono::steady_clock::now()<deadline){s.update(1.f/120);std::this_thread::sleep_for(std::chrono::milliseconds(5));}
  const auto photo=s.cache_.get(entry->images[0].url);if(!photo.texture)return false;
  glBindTexture(GL_TEXTURE_2D,photo.texture);std::vector<unsigned char>rgba(size_t(photo.width)*photo.height*4);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba.data());size_t empty=0,opaque=0;for(size_t n=3;n<rgba.size();n+=4){empty+=rgba[n]==0;opaque+=rgba[n]==255;}if(!empty||!opaque||glGetError()!=GL_NO_ERROR)return false;
  for(bool dark:{false,true}){s.dark_theme_=dark;s.theme_mix_.snap(dark?1.f:0.f);for(int n=0;n<40;++n)s.update(1.f/120);if(!capture(std::string(cutout_id?cutout_id:"gba")+(dark?"-transparent-native-dark":"-transparent-native-light")))return false;}
  std::printf("PASS actual %s native hero / decoded texture %dx%d / alpha empty%zu opaque%zu / dark+light4K GL0\n",cutout_id?cutout_id:"GBA",photo.width,photo.height,empty,opaque);return true;
 }
 const char*id=mode==2?"nintendo-64":mode==3?"wii":"playstation-5";
 auto entry=std::find_if(s.catalog_.entries.begin(),s.catalog_.entries.end(),[&](const auto&e){return e.id==id;});if(entry==s.catalog_.entries.end()||entry->models.empty())return false;const auto original=entry->models[0];
 std::vector<std::string>clean=original.include_groups;
 if(mode==3)clean={"node:wii:console","node:wii:button1","node:wii:button2","node:wii:buttons3","node:stand:pCube2"};
 if(mode==4)clean={"node:Sketchfab Model.001_100","node:Object_2.001_101","node:Object_3.001_102","node:Object_4.001_103","node:Object_5.001_104","node:Object_7.001_106","node:Object_8.001_107"};
 for(int variant=0;variant<2;++variant){
  s.object_.cancel();for(size_t k=0;k<s.prepared_objects_.size();++k){s.prepared_objects_[k].cancel();s.prepared_paths_[k].clear();}entry->models[0]=original;if(variant)entry->models[0].include_groups=clean;
  if(mode==2&&variant)entry->models[0].asset_file="../research/console-authored-group-cleanup/nintendo-64-no-rear-cords.glb";
  s.dark_theme_=true;s.theme_mix_.snap(1);s.select(id);freeze_object(s);
  const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(90);while(!s.object_texture_&&std::chrono::steady_clock::now()<deadline){s.update(1.f/120);std::this_thread::sleep_for(std::chrono::milliseconds(2));if(!s.object_.error().empty()){std::fprintf(stderr,"%s error %s\n",id,s.object_.error().c_str());return false;}}
  if(!s.object_texture_)return false;
  const int angles=mode==2?4:2;
  for(int angle=0;angle<angles;++angle){s.object_angle_=original.initial_angle+float(angle)*(mode==2?1.57079633f:3.14159265f);s.object_render_clock_=1;
   for(int frame=0;frame<40;++frame){s.update(1.f/120);s.draw(width,height,framebuffer);}const auto t=s.object_.timings();if(t.render_width!=3840||t.render_height!=1920||!t.coverage_post_aa||glGetError()!=GL_NO_ERROR)return false;
   const std::string label=std::string(id)+(variant?"-clean":"-original")+"-angle"+std::to_string(angle);
   if(!capture(label))return false;std::printf("PASS %s variant%d angle%d actual4K stage / %.2fms ready / GL0\n",id,variant,angle,t.load_ready_ms);
  }
 }entry->models[0]=original;return true;
}
}
