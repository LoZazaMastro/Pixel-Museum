// Data-only eleventh-group prose/media checks on the production Screen.
#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_eleventh_scoped(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*message){if(!ok)std::fprintf(stderr,"Eleventh scoped check failed: %s\n",message);return ok;};
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;
 struct Target{const char*id;const char*feature;int paragraph;bool endpoint;};
 const Target targets[]={{"workbook-10-19-vanquish","",0,true},{"workbook-10-19-vanquish","",2,true},{"workbook-10-19-vanquish","",3,true},{"workbook-12-08-yakuza","",6,true},{"wikipedia-60979422","",2,true},{"workbook-04-07-atlus","",3,true},{"i-am-alive","",0,false},{"i-am-alive","",1,false},{"i-am-alive","",2,false}};
 const auto capture=[&](const std::string&name){for(int n=0;n<30;++n)s.update(1.f/60);s.draw(width,height,framebuffer);s.draw(width,height,framebuffer);if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char>pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/"+name+"-4k.png").c_str(),width,height,4,pixels.data(),width*4)!=0&&glGetError()==GL_NO_ERROR;};
 for(bool dark:{false,true}){s.dark_theme_=dark;s.theme_mix_.snap(dark?1:0);
  for(const auto&t:targets){s.select(t.id);s.preview(1);s.fade_=1;s.entry_snapshot_=false;s.story_open_.snap(1);const auto&e=*s.current();int feature=-1;
   if(*t.feature){for(size_t n=0;n<e.editorial_features.size();++n)if(e.editorial_features[n].id==t.feature)feature=int(n);if(!require(feature>=0,"current feature identity exists"))return false;}
   const auto&body=feature<0?e.body:e.editorial_features[size_t(feature)].body;
   if(!require(e.id==t.id&&t.paragraph<int(body.size()),"current exact entry/source paragraph exists"))return false;
   const auto c=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&v){return v.feature==feature&&(v.paragraph==t.paragraph||std::find(v.continuation.begin(),v.continuation.end(),t.paragraph)!=v.continuation.end());});
   if(!require(c!=s.story_cards_.end()&&c->lead.empty(),"requested complete source appears on a real card without ellipsis lead"))return false;
   const int card=int(c-s.story_cards_.begin());s.story_focus_=card;s.story_position_.snap(float(card));s.scroll_.snap(0);const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(20);
   do{s.update(1.f/60);if(story_photo_ready(s))break;std::this_thread::sleep_for(std::chrono::milliseconds(10));}while(std::chrono::steady_clock::now()<until);
   if(!require(story_photo_ready(s),"current illustration is ready before capture"))return false;
   const auto name=std::string("eleventh-")+(dark?"dark-":"light-")+t.id+"-"+(feature<0?"main":t.feature)+"-p"+std::to_string(t.paragraph);
   if(!require(capture(name+"-start"),"start frame4K GL0"))return false;
   if(t.endpoint){hui::InputFrame input;input.connected=true;input.stick2_y=1;hui::ui::Feedback f;for(int n=0;n<int(s.scroll_max_/680*60)+100;++n){f.clear();s.handle(input,f);s.update(1.f/60);}s.page_.clear();s.draw_detail();const auto&layout=s.story_text_[size_t(card)];const auto&last=layout.rows().back();
    if(!require(!s.story_expanded_&&s.story_focus_==card&&std::abs(s.scroll_.target-s.scroll_max_)<.1f&&404+layout.title_height+28+last.baseline-s.scroll_.value<=824.1f,"right stick reaches final complete line without R3 or card changes"))return false;
    if(!require(capture(name+"-end"),"source endpoint4K GL0"))return false;
   }
   std::printf("PASS eleventh %s current %s feature%d p%d/card%d image%d endpoint%d /4K GL0\n",dark?"dark":"light",t.id,feature,t.paragraph,card,c->image,t.endpoint);
  }
 }
 std::puts("PASS eleventh scoped:6changed prose endpoints+3semantic media mappings, both themes,30actual4K captures GL0. No native compile.");return true;
}
}
