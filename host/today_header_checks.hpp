#pragma once
namespace museum {
inline bool ScreenInspection::verify_today_header(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*why){if(!ok)std::fprintf(stderr,"Today header: %s\n",why);return ok;};
 s.language_="it";s.apply_language();s.preview(0);s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;
 s.settings_=s.credits_=s.chapters_=s.detail_=s.year_guide_=false;s.panel_.snap(0);s.year_panel_.snap(0);s.fade_=1;s.history_transition_=false;
 s.date_year_=2026;s.date_month_=9;s.date_day_=11;s.notice_time_=0;
 if(!require(s.today_date_label().find("2026")!=std::string::npos,"date includes current year"))return false;
 const auto save=[&](const char*name){s.draw(width,height,framebuffer);if(glGetError()!=GL_NO_ERROR)return false;std::vector<unsigned char>pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);return stbi_write_png(name,width,height,4,pixels.data(),width*4)!=0;};
 const auto original=s.catalog_.entries;
 for(auto&e:s.catalog_.entries){e.month=1;e.day=1;e.calendar_month=1;e.calendar_day=1;}
 s.history_focus_=false;s.time_=1;
 if(!require(s.today_entries(false).empty(),"no matches remains empty"))return false;
 if(!require(save("build/previews/today-header-it-no-match.png"),"no-match actual render"))return false;
 s.catalog_.entries.front().month=9;s.catalog_.entries.front().day=11;s.catalog_.entries.front().precision="day";s.catalog_.entries.front().calendar_only=false;s.catalog_.entries.front().linked_exhibit_id.clear();
 if(!require(s.today_entries(false).size()==1,"one matching event"))return false;
 if(!require(save("build/previews/today-header-it-one-match.png"),"single actual render"))return false;
 s.catalog_.entries[1].month=9;s.catalog_.entries[1].day=11;s.catalog_.entries[1].precision="day";s.catalog_.entries[1].calendar_only=false;s.catalog_.entries[1].linked_exhibit_id.clear();
 if(!require(s.today_entries(false).size()==2,"two matching events"))return false;
 s.time_=1;if(!require(save("build/previews/today-header-it-multiple-first.png"),"first rotation actual render"))return false;
 s.time_=5.5f;if(!require(save("build/previews/today-header-it-multiple-second.png"),"second rotation actual render"))return false;
 s.time_=4.5f;if(!require(save("build/previews/today-header-it-multiple-fade.png"),"rotation boundary actual render"))return false;
 s.catalog_.entries=original;
 int longest=0;size_t length=0;for(size_t i=0;i<s.history_catalog_.entries.size();++i){size_t count=0;for(const auto&v:s.history_catalog_.entries[i].body)count+=v.size();if(count>length){length=count;longest=int(i);}}
 s.history_focus_=true;s.history_focus_index_=longest;s.history_position_.snap(float(longest));s.history_transition_=false;s.fade_=1;s.time_=1;s.scroll_.snap(0);
 if(!require(save("build/previews/today-header-it-long-culture-top.png"),"long culture top actual render"))return false;
 const auto&e=s.history_catalog_.entries[size_t(longest)];float size=46;while(s.fonts_.semibold.font->wrap(e.title,size,770).size()>2&&size>28)size-=1;
 const float year=date_label(e,false).empty()?414.f:459.f;
 const auto title_lines=hui::ui::paragraph_lines(s.fonts_.semibold,e.title,size,770);
 const float top=year+62+float(title_lines.lines.size())*size*1.15f+20;
 std::string body;for(const auto&v:e.body){if(!body.empty())body+="\n\n";body+=v;}if(body.empty())body=e.summary;
 const auto lines=hui::ui::paragraph_lines(s.fonts_.regular,body,24,760);
 const float viewport=std::max(1.f,862-top),expected=std::max(0.f,float(lines.lines.size())*34-viewport);
 if(!require(std::abs(s.scroll_max_-expected)<.1f,"culture scroll uses viewport shortened by exactly two34px lines"))return false;
 if(!require(s.scroll_max_>68,"long culture retains scrollable full content"))return false;
 s.scroll_.snap(s.scroll_max_);if(!require(save("build/previews/today-header-it-long-culture-bottom.png"),"last culture paragraph reachable actual render"))return false;
 std::printf("PASS actual today header0/1/2 matches and timed fade; culture viewport bottom862/leading34/full scroll %.1f, all renders GL0.\n",s.scroll_max_);return true;
}
}
