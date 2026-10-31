// Actual native font/fallback and GL coverage, distinct from shaping support.
#pragma once
#include "third_party/nlohmann/json.hpp"
namespace museum {
inline bool ScreenInspection::verify_unicode_fonts(Screen&s,unsigned framebuffer,int width,int height){
 std::string bytes;if(!hui::save::read_file("build/research/font-coverage.json",&bytes))return false;
 const auto audit=nlohmann::json::parse(bytes);if(audit.at("ordinary_glyph_status")!="pass"||audit.at("stale_subset_inputs")!=false)return false;
 const auto points=audit.at("ordinary_codepoints").get<std::vector<std::uint32_t>>();
 const auto visible=audit.at("visible_ordinary_codepoints").get<std::vector<std::uint32_t>>();
 const auto utf8=[](std::uint32_t cp){std::string value;if(cp<0x80)value+=char(cp);else if(cp<0x800){value+=char(0xc0|(cp>>6));value+=char(0x80|(cp&63));}else if(cp<0x10000){value+=char(0xe0|(cp>>12));value+=char(0x80|((cp>>6)&63));value+=char(0x80|(cp&63));}else{value+=char(0xf0|(cp>>18));value+=char(0x80|((cp>>12)&63));value+=char(0x80|((cp>>6)&63));value+=char(0x80|(cp&63));}return value;};
 const std::array<hui::ui::FontRef,4>faces{s.fonts_.regular,s.fonts_.semibold,s.fonts_.display,s.fonts_.mono};
 GLint maximum_texture=0;glGetIntegerv(GL_MAX_TEXTURE_SIZE,&maximum_texture);
 if(s.cjk_.atlas_width()>maximum_texture||s.cjk_.atlas_height()>maximum_texture)return false;
 for(const auto&face:faces){
  for(auto cp:points)if(!face.font->has_glyph(cp)){std::fprintf(stderr,"Missing actual runtime glyphU+%04X\n",cp);return false;}
  std::vector<hui::gfx::GlyphQuad>question;face.font->layout("?",0,0,34,hui::gfx::Align::left,question);
  for(auto cp:visible){std::vector<hui::gfx::GlyphQuad>quads;face.font->layout(utf8(cp),0,0,34,hui::gfx::Align::left,quads);if(quads.empty()){std::fprintf(stderr,"No visible glyph geometryU+%04X\n",cp);return false;}const auto&a=quads[0];const auto&q=question[0];if(a.texture==q.texture&&a.u0==q.u0&&a.v0==q.v0&&a.u1==q.u1&&a.v1==q.v1){std::fprintf(stderr,"Question-mark substitutionU+%04X\n",cp);return false;}}
  if(std::abs(face.measure("A\xc2\xa0" "B",34)-face.measure("A B",34))>.01f)return false;
 }
 // Exercise actual glyphs near the lower end of a rectangular fallback atlas,
 // not only the earlier rows used by the fixed IPA/Japanese demonstration.
 std::vector<std::pair<float,std::uint32_t>>edge_glyphs;
 for(auto cp:visible)if(cp>=0x3000&&cp<=0x9fff&&s.cjk_.has_glyph(cp)){
  std::vector<hui::gfx::GlyphQuad>quads;s.cjk_.layout(utf8(cp),0,0,40,hui::gfx::Align::left,quads);
  if(quads.size()==1)edge_glyphs.emplace_back(quads[0].v1,cp);
 }
 std::sort(edge_glyphs.begin(),edge_glyphs.end(),[](const auto&a,const auto&b){return a.first>b.first;});
 if(edge_glyphs.size()<12)return false;edge_glyphs.resize(12);
 for(bool dark:{false,true}){
  hui::gfx::DrawList layer;const auto bg=hui::gfx::Color::rgb(dark?0x0b100e:0xf1efe7),ink=hui::gfx::Color::rgb(dark?0xf1efe7:0x202521);
  layer.rounded_rect({0,0,1920,1080},0,bg);hui::ui::text(layer,s.fonts_.mono,"ACTUAL CURRENT JAPANESE GLYPHS / RECTANGULAR ATLAS EDGE",100,65,20,ink);
  for(std::size_t face=0;face<faces.size();++face)for(std::size_t col=0;col<edge_glyphs.size();++col){
   const float x=150+float(col)*135,y=200+float(face)*225;const auto cp=edge_glyphs[col].second;
   hui::ui::text(layer,faces[face],utf8(cp),x,y,40,ink);
   char label[32];std::snprintf(label,sizeof(label),"U+%04X",cp);hui::ui::text(layer,s.fonts_.mono,label,x,y+55,14,ink.with_alpha(.65f));
  }
  s.renderer_.begin();s.renderer_.draw(layer);s.renderer_.present(framebuffer,width,height);glBindFramebuffer(GL_FRAMEBUFFER,framebuffer);
  std::vector<unsigned char>pixels(size_t(width)*height*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());if(glGetError()!=GL_NO_ERROR)return false;
  for(std::size_t face=0;face<faces.size();++face)for(std::size_t col=0;col<edge_glyphs.size();++col){
   const float x=150+float(col)*135,y=200+float(face)*225;unsigned visible_pixels=0;
   for(int py=int((y-60)*height/1080);py<int((y+15)*height/1080);++py)for(int px=int((x-15)*width/1920);px<int((x+85)*width/1920);++px){
    const auto offset=(size_t(height-1-py)*width+px)*4;
    if(std::abs(int(pixels[offset])-int(pixels[0]))>20||std::abs(int(pixels[offset+1])-int(pixels[1]))>20||std::abs(int(pixels[offset+2])-int(pixels[2]))>20)++visible_pixels;
   }
   if(visible_pixels<4){std::fprintf(stderr,"Blank rectangular-atlas glyph U+%04X / face%zu\n",edge_glyphs[col].second,face);return false;}
  }
  const std::string path=std::string("build/previews/unicode-atlas-extended-")+(dark?"dark":"light")+"-4k.png";stbi_flip_vertically_on_write(1);if(!stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4))return false;
 }
 std::printf("PASS rectangular font atlas %ux%u / %zu R8 bytes / hostGL maximum%d / 12lower-edge Japanese glyphs4faces2themes actualpixelsGL0; physicalPS5 limit not measured.\n",unsigned(s.cjk_.atlas_width()),unsigned(s.cjk_.atlas_height()),s.cjk_.atlas().size(),maximum_texture);
 const char*labels[]={"Inter Regular","Inter SemiBold","Montserrat Medium","DejaVu Sans Mono"};
 const char*lines[]={"【公式】植松伸夫TV · イー・アル・カンフー · バーチャファイター2","Алексей Пажитнов · Lumière [lymjɛːʁ] · Benigni [roˈbɛrto beˈniɲɲi]","𝒬𝓊𝒾𝑒𝓉𝓈𝒸𝒽𝑒𝒷𝒶𝓁𝓁 · 🎮 🕹 🚢 · 𝗙𝗨𝗟𝗟 𝗢𝗦𝗧"};
 for(bool dark:{false,true}){
  hui::gfx::DrawList layer;const auto background=hui::gfx::Color::rgb(dark?0x0b100e:0xf1efe7),ink=hui::gfx::Color::rgb(dark?0xf1efe7:0x202521);
  layer.rounded_rect({0,0,1920,1080},0,background);hui::ui::text(layer,s.fonts_.mono,"PIXEL MUSEUM / ACTUAL FONT COVERAGE",100,75,20,ink);
  for(size_t face=0;face<faces.size();++face){const float y=145+float(face)*225;hui::ui::text(layer,s.fonts_.mono,labels[face],100,y,19,ink.with_alpha(.6f));for(unsigned line=0;line<3;++line)hui::ui::text(layer,faces[face],lines[line],100,y+50+float(line)*47,34,ink);}
  s.renderer_.begin();s.renderer_.draw(layer);s.renderer_.present(framebuffer,width,height);glBindFramebuffer(GL_FRAMEBUFFER,framebuffer);std::vector<unsigned char>pixels(size_t(width)*height*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());if(glGetError()!=GL_NO_ERROR)return false;
  stbi_flip_vertically_on_write(1);const std::string path=std::string("build/previews/unicode-fonts-")+(dark?"dark":"light")+"-4k.png";if(!stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4))return false;
 }
 if(std::getenv("MUSEUM_SCRIPT_PROTOTYPE")){
  std::string run_data;if(!hui::save::read_file("build/research/offline-script-shaping/script-runs.json",&run_data))return false;
  const auto prototype=nlohmann::json::parse(run_data);
  for(bool dark:{false,true}){
   hui::gfx::DrawList layer;const auto bg=hui::gfx::Color::rgb(dark?0x0b100e:0xf1efe7),ink=hui::gfx::Color::rgb(dark?0xf1efe7:0x202521);layer.rounded_rect({0,0,1920,1080},0,bg);hui::ui::text(layer,s.fonts_.mono,"OFFLINE HARFBUZZ / ORIGINAL UTF8 / ACTUAL RUNTIME",100,60,18,ink);
   unsigned n=0;for(const auto&run:prototype["runs"]){if(!run["original_full_phrase"].get<bool>())continue;const auto cp=run["private_glyph"].get<std::uint32_t>();const auto original=run["text"].get<std::string>();if(!s.cjk_.has_glyph(cp))return false;for(const auto&face:faces){if(!face.font->has_text(original))return false;std::vector<hui::gfx::GlyphQuad>geometry;face.font->layout(original,0,0,34,hui::gfx::Align::left,geometry);if(geometry.size()!=1||geometry[0].texture!=s.cjk_ref_.texture)return false;}const float y=135+float(n)*100;hui::ui::text(layer,s.fonts_.mono,run["script"].get<std::string>()+" / "+std::to_string(run["shaped_glyphs"].size())+" shaped glyphs",100,y,17,ink.with_alpha(.6f));hui::ui::text(layer,s.fonts_.regular,original,470,y+13,48,ink);++n;}
   if(n!=9)return false;s.renderer_.begin();s.renderer_.draw(layer);s.renderer_.present(framebuffer,width,height);glBindFramebuffer(GL_FRAMEBUFFER,framebuffer);std::vector<unsigned char>pixels(size_t(width)*height*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());if(glGetError()!=GL_NO_ERROR)return false;
   const std::string path=std::string("build/previews/script-runs-runtime-")+(dark?"dark":"light")+"-4k.png";stbi_flip_vertically_on_write(1);if(!stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4))return false;
  }
  const auto article=std::find_if(s.history_catalog_.entries.begin(),s.history_catalog_.entries.end(),[](const auto&e){return e.id=="history-2003-iraq-war";});if(article==s.history_catalog_.entries.end()||article->body.empty())return false;
  const auto original_body=article->body;s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.fade_=1;s.history_transition_=false;s.entry_snapshot_=false;s.history_focus_=true;s.history_focus_index_=int(article-s.history_catalog_.entries.begin());s.history_position_.snap(float(s.history_focus_index_));s.history_emphasis_.snap(1);s.prepare_story();s.detail_=false;s.story_focus_=0;s.story_open_.snap(0);s.story_position_.snap(0);s.scroll_.snap(0);s.draw(width,height,framebuffer);
  if(s.page_.instances().size()<100)return false;
  glBindFramebuffer(GL_FRAMEBUFFER,framebuffer);std::vector<unsigned char>pixels(size_t(width)*height*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());if(article->body!=original_body||!s.fonts_.regular.font->has_text(original_body[0])||glGetError()!=GL_NO_ERROR)return false;
  stbi_flip_vertically_on_write(1);if(!stbi_write_png("build/previews/unicode-iraq-original-story-4k.png",width,height,4,pixels.data(),width*4))return false;
  std::puts("PASS9 exact static source phrases: originalUTF8 native matcher across4faces, actualIraqstory unchanged, genuineHarfBuzz forms and both4KthemesGL0. Not a general dynamic shaping engine.");
 }
 std::printf("PASS actualScreen Unicode: %zu current ordinary points/%zu visible glyphs across4faces, genuine atlas geometry (noquestionmark aliases), NBSPadvance, both4KthemesGL0. Complexshaping not claimed.\n",points.size(),visible.size());return true;
}
}
