// Current ninth-group media/prose captures, never a product-flow modification.
#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_ninth_scoped(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*message){if(!ok)std::fprintf(stderr,"Ninth scoped check failed: %s\n",message);return ok;};
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.dark_theme_=true;s.theme_mix_.snap(1);
 const auto capture=[&](const std::string&name){for(int n=0;n<30;++n)s.update(1.f/60);s.draw(width,height,framebuffer);s.draw(width,height,framebuffer);if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char>pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/"+name+"-4k.png").c_str(),width,height,4,pixels.data(),width*4)!=0&&glGetError()==GL_NO_ERROR;};
 const std::pair<const char*,int>targets[]={{"workbook-08-13-gyromite",2},{"workbook-04-07-atlus",3},{"mega-drive",0},{"mega-drive",1},{"mega-drive",2},{"workbook-06-19-treasure",2},{"workbook-06-19-treasure",3},{"daily-01-09",2}};
 for(const auto&[id,p]:targets){s.select(id);s.preview(1);s.fade_=1;s.entry_snapshot_=false;s.story_open_.snap(1);
  const auto&e=*s.current();if(!require(e.id==id&&p<int(e.body.size()),"current catalogue target identity and source paragraph resolve"))return false;const auto c=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&v){return v.feature<0&&(v.paragraph==p||std::find(v.continuation.begin(),v.continuation.end(),p)!=v.continuation.end());});
  if(!require(c!=s.story_cards_.end()&&c->lead.empty(),"requested current source paragraph has a complete real card"))return false;
  const int card=int(c-s.story_cards_.begin());s.story_focus_=card;s.story_position_.snap(float(card));s.scroll_.snap(0);
  const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(20);do{s.update(1.f/60);if(story_photo_ready(s))break;std::this_thread::sleep_for(std::chrono::milliseconds(10));}while(std::chrono::steady_clock::now()<until);
  if(!require(story_photo_ready(s),"current scoped image is decoded before capture"))return false;
  const auto name=std::string("ninth-")+id+"-p"+std::to_string(p);if(!require(capture(name+"-start"),"scoped narrative capture4K GL0"))return false;
  if(std::string(id)=="mega-drive"){hui::InputFrame i;i.connected=true;i.stick2_y=1;hui::ui::Feedback f;for(int n=0;n<int(s.scroll_max_/680*60)+100;++n){f.clear();s.handle(i,f);s.update(1.f/60);}s.page_.clear();s.draw_detail();
   const auto&layout=s.story_text_[size_t(card)];const auto&last=layout.rows().back();if(!require(!s.story_expanded_&&s.story_focus_==card&&std::abs(s.scroll_.target-s.scroll_max_)<.1f&&404+layout.title_height+28+last.baseline-s.scroll_.value<=824.1f,"new Mega Drive source reaches its final complete line through right-stick input"))return false;
   if(!require(capture(name+"-end"),"Mega Drive source endpoint4K GL0"))return false;
  }
  std::printf("PASS ninth current narrative %s p%d/card%d image%d / explicit current composition /4K GL0\n",id,p,card,c->image);
 }
 s.select("workbook-07-28-lua");s.preview(0);s.fade_=1;s.entry_snapshot_=false;s.image_index_=s.current()->preferred_image;s.open_photo({950,220,826,478});s.gallery_open_.snap(1);
 for(bool dark:{false,true}){s.dark_theme_=dark;s.theme_mix_.snap(dark?1:0);for(int n=0;n<90;++n){s.update(1.f/60);std::this_thread::sleep_for(std::chrono::milliseconds(2));}if(!require(capture(std::string("ninth-lua-official-logo-")+(dark?"dark":"light")),"correct official Lua logo gallery renders in both4Kthemes GL0"))return false;}
 std::puts("PASS ninth scoped:8narrative frames+3MegaDrive endpoints+2LuaRGBAlogo themes,13actual4K captures GL0.");return true;
}
}
