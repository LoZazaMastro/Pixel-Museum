#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_timeline_symbols(Screen&s,unsigned framebuffer,int width,int height){
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=false;s.panel_.snap(0);s.history_focus_=false;s.detail_=false;s.story_open_.snap(0);
 Entry base;base.id="game-boy";base.year=1989;base.summary="Host-only typography fixture, never production catalogue data.";base.soundtrack.tracks.resize(1);
 s.catalog_.entries.clear();for(const auto&title:{"Game Boy","Super Mario Bros. and the next dimension of play","A deliberately extended title to exercise three stable lines while a neighbouring exhibition moves smoothly into focus"}){auto e=base;e.title=title;s.catalog_.entries.push_back(e);}s.visible_={0,1,2};s.focus_=1;
 for(bool dark:{false,true})for(float position:{0.f,1.f,2.f,1.35f}){
  s.dark_theme_=dark;s.theme_mix_.snap(dark?1:0);for(int frame=0;frame<75;++frame)s.update(1.f/60);s.timeline_.snap(position);for(int frame=0;frame<3;++frame)s.draw(width,height,framebuffer);
  for(int n=0;n<3;++n){const auto&title=s.catalog_.entries[size_t(n)].title;float reference=30;while(float(s.fonts_.regular.font->wrap(title,reference,450).size())*reference*1.18f>74&&reference>16)--reference;const auto lines=hui::ui::paragraph_lines(s.fonts_.regular,title,reference,450);const float hover=std::clamp(1.f-std::abs(float(n)-position),0.f,1.f);const float size=reference*(.72f+.28f*hover),baseline=883-float(lines.lines.size()-1)*size*1.18f,top=baseline-s.fonts_.regular.font->ascent(size),icon_y=top-27;
   if(top-(icon_y+15)<11.99f||icon_y-15<744){std::fprintf(stderr,"Timeline symbol clearance/clipping failed\n");return false;}}
  if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);const auto name=std::string("build/previews/timeline-symbols-")+(dark?"dark":"light")+(position==0?"-normal-focused":position==1?"-focused":position==2?"-extended-focused":"-moving")+"-4k.png";if(!stbi_write_png(name.c_str(),width,height,4,pixels.data(),width*4)||glGetError()!=GL_NO_ERROR)return false;
 }
 std::puts("PASS actual timeline symbols: stable1/2/3line fixtures, selected/moving/unselected, both icons,12px minimum gap, unclipped, light/dark4KGL0.");return true;
}
inline bool ScreenInspection::verify_timeline_pause(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*note){if(!ok)std::fprintf(stderr,"Timeline/pause FAILED: %s\n",note);return ok;};
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=false;s.panel_.snap(0);
 const auto settle=[&](){for(int n=0;n<75;++n)s.update(1.f/60);};
 const auto capture=[&](const std::string&name){settle();if(!s.experience_active_){const auto*e=s.current();if(e&&!e->images.empty()){const auto&url=e->images[e->preferred_image].url;s.cache_.request(url);const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);while(!s.cache_.get(url).texture&&std::chrono::steady_clock::now()<deadline){s.update(1.f/60);s.draw(width,height,framebuffer);std::this_thread::sleep_for(std::chrono::milliseconds(10));}if(!require(bool(s.cache_.get(url).texture),"current preferred photo texture ready before capture"))return false;}}for(int n=0;n<35;++n){s.update(1.f/60);s.draw(width,height,framebuffer);std::this_thread::sleep_for(std::chrono::milliseconds(4));}if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char>p(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,p.data());stbi_flip_vertically_on_write(1);return stbi_write_png(("build/previews/timeline-pause-"+name+"-4k.png").c_str(),width,height,4,p.data(),width*4)&&glGetError()==GL_NO_ERROR;};
 const auto press=[&](hui::Action action){hui::InputFrame i;i.connected=true;i.pressed=hui::action_bit(action);hui::ui::Feedback f;s.handle(i,f);};
 for(bool dark:{false,true}){
  s.dark_theme_=dark;s.theme_mix_.snap(dark?1:0);s.select("super-mario-bros");s.preview(0);settle();
  const auto game=s.current()->id;s.focus_history(true);const int year=s.current()->year;
  for(size_t n=0;n<s.history_catalog_.entries.size();++n)if(s.history_catalog_.entries[n].year==year)s.history_focus_index_=int(n);
  s.focus_history(false);if(!require(s.current()->id==game,"same culture year restores exact gaming stop"))return false;
  if(!require(capture(dark?"dark-games":"light-games"),"gaming rail frame GL0"))return false;
  s.focus_history(true);settle();s.history_position_.snap(float(s.history_focus_index_));
  if(!require(capture(dark?"dark-culture":"light-culture"),"culture rail frame GL0"))return false;
  s.history_focus_index_=0;const int day=chronology_day(*s.current());s.focus_history(false);
  const int nearest=std::abs(chronology_day(*s.current())-day);
  for(const int n:s.visible_)if(!require(std::abs(chronology_day(s.catalog_.entries[size_t(n)])-day)>=nearest,"changed year returns nearest gaming date"))return false;
  int pong=-1;for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].entry_id=="pong")pong=int(n);
  if(!require(pong>=0,"Pong experience exists"))return false;s.open_experience(pong,{64,350,548,370});s.experience_open_.snap(1);settle();
  press(hui::Action::menu);if(!require(s.experience_paused_,"Options opens pause"))return false;settle();
  const auto picture=[&](){hui::gfx::DrawList d;s.study_->draw(d,s.fonts_,{0,0,1920,960},hui::gfx::Color::rgb(0xb6a2cf));std::string bytes;for(const auto&v:d.instances())bytes.append(reinterpret_cast<const char*>(&v),sizeof(v));return bytes;};
  const auto before=picture();for(int n=0;n<120;++n)s.update(1.f/120);
  if(!require(picture()==before&&!s.motion_controls(),"paused simulation frozen and motion disabled"))return false;
  if(!require(capture(dark?"dark-options-pause":"light-options-pause"),"actual pause overlay frame GL0"))return false;
  press(hui::Action::confirm);if(!require(!s.experience_paused_&&s.experience_active_,"Continue resumes same experience"))return false;settle();
  press(hui::Action::west);if(!require(s.experience_active_,"Square does not exit gameplay"))return false;
  press(hui::Action::back);if(!require(s.experience_active_,"Circle does not bypass pause menu"))return false;
  press(hui::Action::menu);hui::InputFrame down;down.connected=true;down.nav=hui::Direction::down;hui::ui::Feedback feedback;s.handle(down,feedback);press(hui::Action::confirm);
  if(!require(!s.experience_active_,"Options then Exit closes experience"))return false;settle();
  int pixels=-1;for(size_t n=0;n<study_catalog().size();++n)if(study_catalog()[n].id=="pixels")pixels=int(n);
  if(!require(pixels>=0,"pixel workshop exists"))return false;s.open_experience(pixels,{64,350,548,370});s.experience_open_.snap(1);s.workshop_.set_cursor(6,6);press(hui::Action::menu);
  const auto pixel_picture=[&](){hui::gfx::DrawList d;s.workshop_.draw(d,s.fonts_,{0,0,1920,960},hui::gfx::Color::rgb(0xb6a2cf),true);std::string bytes;for(const auto&v:d.instances())bytes.append(reinterpret_cast<const char*>(&v),sizeof(v));return bytes;};
  const auto pixel_before=pixel_picture();for(int n=0;n<120;++n)s.update(1.f/120);if(!require(pixel_picture()==pixel_before,"pixel workshop cursor animation freezes while paused"))return false;
  s.study_.reset();s.experience_paused_=false;s.experience_pause_open_.snap(0);s.experience_open_.snap(1);s.tactile_repeat_=0;
  hui::InputFrame touch;touch.connected=true;touch.touch.available=true;touch.touch.count=1;touch.touch.points[0].x=.6f;touch.touch.points[0].y=.6f;hui::ui::Feedback touch_feedback;s.handle(touch,touch_feedback);
  if(!require(touch_feedback.tactile.size()==1,"legacy accepted touch cursor emits exactly one pulse"))return false;
  touch_feedback.clear();s.handle(touch,touch_feedback);if(!require(touch_feedback.tactile.empty(),"unchanged legacy touch cursor silent"))return false;
  s.experience_active_=s.experience_paused_=false;s.experience_open_.snap(0);s.experience_pause_open_.snap(0);
  s.open_search(feedback);const auto accent=s.search_prompt_.style.theme.primary;
  if(!require(accent.r>accent.g&&accent.g>accent.b,"search keyboard accent is orange in both themes"))return false;
  if(!require(capture(dark?"dark-orange-keyboard":"light-orange-keyboard"),"actual orange keyboard frame GL0"))return false;
  s.search_prompt_.dismiss();s.search_open_.snap(0);s.year_guide_=false;

 }
 std::puts("PASS actual timeline exact-return and changed-year matching; both theme rails; Options Continue/Exit; paused simulation frozen; Square retained; six actual4Kframes GL0.");return true;
}
}
