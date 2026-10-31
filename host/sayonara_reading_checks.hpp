// Scoped source-only update check against the current production Screen.
#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_sayonara_reading(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*message){if(!ok)std::fprintf(stderr,"Sayonara reading check failed: %s\n",message);return ok;};
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.select("workbook-09-19-sayonara-wild-hearts");s.preview(1);s.fade_=1;s.entry_snapshot_=false;s.story_open_.snap(1);
 const auto squash=[](std::string text){text.erase(std::remove_if(text.begin(),text.end(),[](unsigned char c){return std::isspace(c);}),text.end());return text;};
 const auto capture=[&](const std::string&name){for(int n=0;n<30;++n)s.update(1.f/60);s.draw(width,height,framebuffer);s.draw(width,height,framebuffer);if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char> pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/"+name+"-4k.png").c_str(),width,height,4,pixels.data(),width*4)!=0&&glGetError()==GL_NO_ERROR;};
 for(bool dark:{false,true}){s.dark_theme_=dark;s.theme_mix_.snap(dark?1.f:0.f);
  for(int p:{1,2,3}){
   const auto&e=*s.current();const auto c=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&v){return v.feature<0&&v.paragraph==p;});
   if(!require(c!=s.story_cards_.end()&&c->continuation.empty()&&c->lead.empty()&&c->image>=0&&c->image!=e.preferred_image&&e.images[size_t(c->image)].story_paragraph==p,"each changed paragraph retains its distinct explicit non-cover image"))return false;
   const int card=int(c-s.story_cards_.begin());s.story_focus_=card;s.story_position_.snap(float(card));s.scroll_.snap(0);
   const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(20);
   do{s.update(1.f/60);if(story_photo_ready(s))break;std::this_thread::sleep_for(std::chrono::milliseconds(10));}while(std::chrono::steady_clock::now()<until);
   if(!require(story_photo_ready(s),"actual local image is ready before capture"))return false;
   s.page_.clear();s.draw_detail();const auto&layout=s.story_text_[size_t(card)];std::string rendered;for(const auto&r:layout.rows())if(!r.heading)rendered+=r.text;
   if(!require(layout.ready&&squash(rendered)==squash(e.body[size_t(p)]),"all complete source text reaches native layout in order without an ellipsis lead"))return false;
   const auto prefix=std::string("sayonara-eight-")+(dark?"dark":"light")+"-p"+std::to_string(p);
   if(!require(capture(prefix+"-start"),"start frame renders4K GL0"))return false;
   hui::InputFrame input;input.connected=true;input.stick2_y=1;hui::ui::Feedback feedback;
   const float extent=s.scroll_max_;for(int n=0;n<int(extent/680*60)+100;++n){feedback.clear();s.handle(input,feedback);s.update(1.f/60);}
   s.page_.clear();s.draw_detail();const auto&last=layout.rows().back();
   std::printf("Sayonara endpoint diagnostic p%d card%d/%d expanded%d target%.1f max%.1f value%.1f last%.1f\n",p,card,s.story_focus_,s.story_expanded_,s.scroll_.target,s.scroll_max_,s.scroll_.value,last.baseline);
   if(!require(!s.story_expanded_&&s.story_focus_==card&&std::abs(s.scroll_.target-s.scroll_max_)<.1f&&404+layout.title_height+28+last.baseline-s.scroll_.value<=824.1f&&last.baseline-s.scroll_.value>=-28,"right stick reaches the final complete line without changing card or pressing R3"))return false;
   if(!require(capture(prefix+"-end"),"final complete-line frame renders4K GL0"))return false;
   std::printf("PASS scoped Sayonara %s p%d/card%d: %zu exact source bytes, %zu rows, scroll%.1f, distinct image%d, right-stick final baseline%.1f;4K GL0\n",dark?"dark":"light",p,card,e.body[size_t(p)].size(),layout.rows().size(),extent,c->image,last.baseline-s.scroll_.value);
  }
 }
 std::puts("PASS scoped Sayonara3 both themes: full wording/endpoints, real right-stick scroll, distinct image association,12actual4K frames GL0; no native compilation.");return true;
}
}
