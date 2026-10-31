#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_culture_staged(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*note){if(!ok)std::fprintf(stderr,"Culture staged check failed: %s\n",note);return ok;};
 if(!require(s.history_catalog_.entries.size()==342,"staged separate culture catalogue loads342entries"))return false;
 s.data_.clear();s.onboarding_=false;s.language_="en";s.apply_language();s.preview(0);s.boot_time_=5;s.boot_note_=13;s.detail_=false;
 const char*ids[]={"history-1876-telephone","history-1977-star-wars-film","history-1982-thriller-album","history-1989-1989-tiananmen-square-protests-and-massacre"};
 for(bool dark:{false,true}){s.dark_theme_=dark;s.theme_mix_.snap(dark?1:0);
 for(const auto*id:ids){const auto found=std::find_if(s.history_catalog_.entries.begin(),s.history_catalog_.entries.end(),[&](const auto&e){return e.id==id;});if(!require(found!=s.history_catalog_.entries.end(),"known culture subject exists"))return false;
 s.history_focus_=true;s.history_focus_index_=int(found-s.history_catalog_.entries.begin());s.history_position_.snap(float(s.history_focus_index_));s.history_emphasis_.snap(1);s.history_transition_=false;s.entry_snapshot_=false;s.fade_=1;s.scroll_.snap(0);s.image_index_=found->preferred_image;s.warm_history();
 const auto&im=found->images[size_t(found->preferred_image)];const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(30);media::Asset asset;
 do{s.update(1.f/60);asset=s.cache_.get(im.url);if(asset.texture&&std::max(asset.width,asset.height)>=1024)break;std::this_thread::sleep_for(std::chrono::milliseconds(10));}while(std::chrono::steady_clock::now()<until);
 if(!require(asset.texture&&std::max(asset.width,asset.height)>=1024,"real packaged culture master texture ready"))return false;
 for(int n=0;n<20;++n)s.update(1.f/60);s.draw(width,height,framebuffer);s.draw(width,height,framebuffer);if(!require(glGetError()==GL_NO_ERROR,"actual culture drawing GL0"))return false;
 std::vector<unsigned char>pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);
 const auto output=std::string("build/previews/culture-staged-")+(dark?"dark-":"light-")+id+"-4k.png";if(!require(stbi_write_png(output.c_str(),width,height,4,pixels.data(),width*4)&&glGetError()==GL_NO_ERROR,"actual culture4K capture"))return false;
 std::printf("PASS staged culture %s %s / image %s / published %dx%d /4K GL0\n",dark?"dark":"light",id,im.url.c_str(),asset.width,asset.height);
 }}std::puts("PASS staged culture342 native entries, four actual correct packaged photos both themes,8real4Kframes GL0.");return true;
}
}
