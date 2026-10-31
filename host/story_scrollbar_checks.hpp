// Real Screen regression: scrollbar geometry follows the clipped prose viewport.
#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_story_scrollbar(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*message){if(!ok)std::fprintf(stderr,"Scrollbar check failed: %s\n",message);return ok;};
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.entry_snapshot_=false;s.fade_=1;
 const auto choose=[&](const char*id,int wanted_side,bool overflowing){
  s.select(id);s.preview(1);s.story_open_.snap(1);s.entry_snapshot_=false;s.fade_=1;
  for(size_t n=0;n<s.story_cards_.size();++n){
   const auto&c=s.story_cards_[n];if(c.paragraph<0||c.feature>=0||c.image<0)continue;
   const bool reverse=c.kind==Screen::StoryCard::narrative&&n%2==0;
   if(wanted_side>=0&&int(reverse)!=wanted_side)continue;
   s.story_focus_=int(n);s.story_position_.snap(float(n));s.scroll_.snap(0);s.page_.clear();s.draw_detail();
   if((s.scroll_max_>1)==overflowing)return true;
  }
  return false;
 };
 const auto geometry=[&](float*thumb_y=nullptr){
  const auto&c=s.story_cards_[size_t(s.story_focus_)];const auto&t=s.story_text_[size_t(s.story_focus_)];
  const bool reverse=c.kind==Screen::StoryCard::narrative&&s.story_focus_%2==0;
  const float x=(reverse?1214.f:144.f)+560+14,top=404+t.title_height+(c.title.empty()?0:28)-28;
  const float height=824-top;int count=0;float y=0,h=0;
  for(const auto&i:s.page_.instances())if(std::abs(i.rect[0]-x)<.02f&&std::abs(i.rect[2]-6)<.02f){
   ++count;if(i.rect[3]<height-.1f){y=i.rect[1];h=i.rect[3];}
  }
  if(s.scroll_max_<=0)return count==0;
  if(count!=2||h<31.9f||y<top-.02f||y+h>824.02f)return false;
  if(thumb_y)*thumb_y=y;
  if(s.scroll_.value<.01f)return std::abs(y-top)<.02f;
  if(std::abs(s.scroll_.value-s.scroll_max_)<.01f)return std::abs(y+h-824)<.02f;
  return y>top&&y+h<824;
 };
 const auto capture=[&](const std::string&name){
  s.draw(width,height,framebuffer);s.draw(width,height,framebuffer);if(glGetError()!=GL_NO_ERROR)return false;
  std::vector<unsigned char> pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
  stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/story-scrollbar-"+name+".png").c_str(),width,height,4,pixels.data(),width*4)!=0&&glGetError()==GL_NO_ERROR;
 };
 for(bool dark:{false,true}){s.dark_theme_=dark;s.theme_mix_.snap(dark?1:0);
  for(int side:{0,1}){
   bool found=false;for(const char*id:{"workbook-10-30-grim-fandango","workbook-11-19-half-life","workbook-03-28-kingdom-hearts"})if(choose(id,side,true)){found=true;break;}
   if(!require(found,"actual scrolling game card exists on each side"))return false;
   const auto source=s.current()->body;const int card=s.story_focus_;const float maximum=s.scroll_max_;
   const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);
   while(!story_photo_ready(s)&&std::chrono::steady_clock::now()<deadline){s.update(1.f/60);std::this_thread::sleep_for(std::chrono::milliseconds(10));}
   if(!require(story_photo_ready(s),"actual local illustration becomes resident within10seconds"))return false;
   float previous=-1;
   for(int stage=0;stage<3;++stage){
    s.scroll_.snap(maximum*stage*.5f);s.page_.clear();s.draw_detail();float y=0;
    if(!require(geometry(&y)&&y>previous,"track stays in viewport and thumb moves top/middle/bottom"))return false;previous=y;
    const std::string name=std::string(dark?"dark":"light")+"-"+(side?"right":"left")+"-"+std::to_string(stage);
    if(!require(capture(name),"actual scrollbar frame renders GL0"))return false;
   }
   s.scroll_.snap(0);hui::InputFrame input;input.connected=true;input.stick2_y=1;hui::ui::Feedback feedback;
   for(int n=0;n<int(maximum/680*60)+100;++n){s.handle(input,feedback);s.update(1.f/60);feedback.clear();}
   s.page_.clear();s.draw_detail();if(!require(geometry()&&s.story_focus_==card&&std::abs(s.scroll_.target-s.scroll_max_)<.01f&&s.current()->body==source,"right-stick input reaches bottom with unchanged source/card and bottom-aligned thumb"))return false;
   std::printf("PASS scrollbar %s %s card%d extent%.1f viewport end824; start/mid/end + real right-stick GL0\n",dark?"dark":"light",s.current()->id.c_str(),card,maximum);
  }
  bool short_card=false;for(const char*id:{"wikipedia-28420914","wikipedia-24309673","wikipedia-3021662","wikipedia-48825904"})if(choose(id,-1,false)){short_card=true;break;}
  if(!require(short_card,"actual short game paragraph fits without scrolling"))return false;
  if(!require(geometry(),"short paragraph has no redundant track or thumb"))return false;
 }
 std::puts("PASS scrollbar actual source cards both columns/themes, proportional thumb, endpoints, short-content suppression; no catalogue/wording mutation.");return true;
}
}
