#pragma once
#include <chrono>
namespace museum {
inline bool ScreenInspection::verify_story_reading(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool value,const char*message){if(!value)std::fprintf(stderr,"Story reading check failed: %s\n",message);return value;};
 s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.data_.clear();s.select("wikipedia-79613463");s.preview(1);s.story_open_.snap(1);
 if(!require(s.current()&&s.current()->id=="wikipedia-79613463","actual MarioKartWorld348 article exists"))return false;
 for(const auto&card:s.story_cards_)if(!require(card.kind!=Screen::StoryCard::sources,"per-article credits cards are absent"))return false;
 // A long source fixture exercises real paragraph rendering and controller
 // scrolling, rather than only checking a string retained in the catalogue.
 auto&fixture=s.catalog_.entries[size_t(s.visible_[size_t(s.focus_)])];const Entry original=fixture;
 fixture.images.clear();fixture.videos.clear();fixture.models.clear();fixture.editorial_features.clear();fixture.soundtrack={};fixture.soundtrack_rooms.clear();
 std::string body="Dr. A. preserved Super Mario Bros. (1985) as part of the original source. ";
 for(int n=0;n<330;++n)body+="Complete source wording remains available to read. ";
 body+="FINAL SOURCE SENTENCE stays readable without changing cards.";
 fixture.body={body};fixture.story_headings={"An intact source paragraph"};s.prepare_story();s.detail_=true;s.story_open_.snap(1);s.story_position_.snap(0);s.scroll_.snap(0);s.page_.clear();s.draw_detail();
 if(!require(!s.story_expanded_&&s.scroll_max_>1000&&s.story_cards_[0].lead.empty(),"long narrative renders complete source directly, without a generated ellipsis lead or Read expansion"))return false;
 hui::InputFrame input;input.connected=true;input.stick2_y=1;hui::ui::Feedback feedback;
 for(int n=0;n<int(s.scroll_max_/680*60)+100;++n){s.handle(input,feedback);s.update(1.f/60);feedback.clear();}
 s.page_.clear();s.draw_detail();
 if(!require(!s.story_expanded_&&s.story_focus_==0&&std::abs(s.scroll_.target-s.scroll_max_)<.01f&&fixture.body[0]==body,"right stick reaches the end without R3, scene changes or source mutations"))return false;
 const auto&card=s.story_cards_[0];float heading_size=64;while(s.fonts_.semibold.font->wrap(card.title,heading_size,1440).size()>3&&heading_size>28)--heading_size;
 const float top=404+float(s.fonts_.semibold.font->wrap(card.title,heading_size,1440).size())*heading_size*1.15f+28;
 const auto lines=hui::ui::paragraph_lines(s.fonts_.regular,body,34,1440,std::numeric_limits<int>::max());
 hui::gfx::DrawList expected;hui::ui::text(expected,s.fonts_.regular,lines.lines.back(),184,top+float(lines.lines.size()-1)*50-s.scroll_.value,34,hui::gfx::Color::rgb(0xffffff));
 bool found=false;const auto&want=expected.instances();const auto&actual=s.page_.instances();
 for(size_t n=0;n+want.size()<=actual.size()&&!found;++n){bool same=true;for(size_t k=0;k<want.size()&&same;++k)for(unsigned q=0;q<4;++q)if(std::abs(actual[n+k].rect[q]-want[k].rect[q])>.02f||std::abs(actual[n+k].extra[q]-want[k].extra[q])>.0001f){same=false;break;}if(same)found=true;}
 const float final_y=top+float(lines.lines.size()-1)*50-s.scroll_.value;
 const bool visible=final_y>top-28&&final_y<824;
 museum::Model accessory;accessory.title="Original credited GamePad source title";accessory.display_caption="Wii U GamePad";fixture.models={accessory};s.prepare_story();const bool caption_ok=s.story_cards_[0].kind==Screen::StoryCard::object&&s.story_cards_[0].title=="Wii U GamePad"&&fixture.models[0].title==accessory.title;fixture.models[0].display_caption.clear();s.prepare_story();const bool legacy_ok=s.story_cards_[0].title=="An object made for play";
 fixture=original;s.prepare_story();
 if(!require(caption_ok&&legacy_ok,"explicit accessory display caption is visible without replacing original source identity or legacy captions"))return false;
 if(!require(found&&visible,"actual glyph geometry contains the final full source line inside the visible clipping window"))return false;
 std::printf("PASS actualScreen full prose: %zu wrapped lines, last baseline%.1f, right-stick-only scroll, noR3/ellipsis/source loss; GL0.\n",lines.lines.size(),final_y);
 // Current edited paragraphs, not only the synthetic long-prose fixture.
 for(const char*id:{"workbook-03-28-kingdom-hearts","workbook-03-09-super-mario-rpg"}){
  s.select(id);const auto*entry=s.current();
  if(!require(entry&&entry->id==id&&entry->body.size()>3,"current edited long paragraph exists"))return false;
  const auto source=entry->body;
  const auto card=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[](const auto&c){return c.feature<0&&(c.paragraph==3||std::find(c.continuation.begin(),c.continuation.end(),3)!=c.continuation.end());});
  if(!require(card!=s.story_cards_.end(),"edited paragraph3 is composed into a readable card"))return false;
  const int focus=int(card-s.story_cards_.begin());s.story_focus_=focus;s.story_position_.snap(float(focus));s.story_open_.snap(1);s.scroll_.snap(0);s.page_.clear();s.draw_detail();
  if(!require(!s.story_expanded_&&s.scroll_max_>0,"edited paragraph scrolls directly without Read expansion"))return false;
  const float maximum=s.scroll_max_;
  for(int n=0;n<int(maximum/680*60)+100;++n){s.handle(input,feedback);s.update(1.f/60);feedback.clear();}
  s.page_.clear();s.draw_detail();
  if(!require(s.current()->id==id&&s.story_focus_==focus&&!s.story_expanded_&&std::abs(s.scroll_.target-s.scroll_max_)<.01f&&s.current()->body==source,"real right stick reaches edited paragraph end without changing source or cards"))return false;
  const auto&layout=s.story_text_[size_t(focus)];const auto&lastrow=layout.rows().back();
  const auto&active=s.story_cards_[size_t(focus)];const bool media=active.image>=0||active.kind==Screen::StoryCard::film;
  const float tx=media?(active.kind==Screen::StoryCard::narrative&&focus%2==0?1214.f:144.f):184.f;
  const float top=404+layout.title_height+28,baseline=top+lastrow.baseline-s.scroll_.value;
  hui::gfx::DrawList expected_line;hui::ui::text(expected_line,s.fonts_.regular,lastrow.text,tx,baseline,lastrow.size,hui::gfx::Color::rgb(0xffffff));
  bool last_found=false;const auto&want_line=expected_line.instances();const auto&got=s.page_.instances();
  for(size_t n=0;n+want_line.size()<=got.size()&&!last_found;++n){bool same=true;for(size_t k=0;k<want_line.size()&&same;++k)for(unsigned q=0;q<4;++q)if(std::abs(got[n+k].rect[q]-want_line[k].rect[q])>.02f||std::abs(got[n+k].extra[q]-want_line[k].extra[q])>.0001f){same=false;break;}if(same)last_found=true;}
  if(!require(last_found&&!want_line.empty()&&baseline>=top-28&&baseline<824,"edited paragraph final source line has visible actual glyph geometry"))return false;
  s.draw(width,height,framebuffer);if(!require(glGetError()==GL_NO_ERROR,"edited paragraph scroll endpoint renders GL0"))return false;
  std::printf("PASS actualScreen current edited %s body3: %zu complete rows, right-stick end, final baseline%.1f, source unchanged/noR3/noellipsis/GL0.\n",id,layout.rows().size(),baseline);
 }
 for(const char*id:{"nintendo-64","workbook-03-02-nintendo-ds-lite"}){
  s.select(id);const auto*entry=s.current();if(!require(entry&&entry->id==id&&entry->explicit_story_media_only,"real hardware preserves explicit-only media policy through runtime projection and native parser"))return false;
  if(!require(entry->images.size()>1&&entry->images[0].story_paragraph==-1&&entry->images[1].story_paragraph==0,"real cover remains unmapped while hardware illustration belongs to paragraph zero"))return false;
  for(size_t p=0;p<entry->body.size();++p){const auto card=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[&](const auto&c){return c.feature<0&&c.paragraph==int(p);});if(!require(card!=s.story_cards_.end()&&card->image==int(p+1)&&card->continuation.empty(),"real hardware paragraph retains its exact intended photograph without cover substitution or unexpected scene merging"))return false;}
  s.story_open_.snap(1);s.story_position_.snap(0);s.draw(width,height,framebuffer);if(!require(glGetError()==GL_NO_ERROR,"explicit mapped hardware cards render without GL errors"))return false;
  std::printf("PASS actualScreen %s: %zu independent source paragraphs use intended photographs1..%zu; cover0 stays outside story.\n",id,entry->body.size(),entry->body.size());
 }
 return true;
}
}
