#include "museum/catalog.hpp"
#include "core/save_file.hpp"
#include "gfx/font.hpp"
#include "museum/timeline_hero.hpp"
#include <cassert>
#include <algorithm>
#include <cstdio>
#include <set>
#include <string>
int main(){
 museum::Catalog c;if(!c.load("build/runtime-preview/content/catalog.json"))return 2;
 hui::gfx::Font title,body,cjk;std::string data;
 if(!hui::save::read_file("assets/fonts/inter-semibold.huifont",&data,16u<<20)||!title.load(data))return 3;
 if(!hui::save::read_file("assets/fonts/inter-regular.huifont",&data,16u<<20)||!body.load(data))return 4;
 if(!hui::save::read_file("assets/fonts/cjk-subset.huifont",&data,16u<<20)||!cjk.load(data))return 5;
 title.add_fallback(&cjk,1);body.add_fallback(&cjk,1);
 const std::set<std::string> ids={"wikipedia-63956111","wikipedia-71748594","wikipedia-76197150","miyamoto-order-of-culture-2026"};
 for(const auto&e:c.entries)if(ids.count(e.id)){
  float ts=68;while(title.wrap(e.title,ts,770).size()>2&&ts>28)ts-=2;
  const auto tl=title.wrap(e.title,ts,770);const float oldafter=448+float(tl.size())*ts*1.13f;
  float bs=28;while(oldafter+16+float(body.wrap(e.summary,bs,710).size())*bs*1.4f>719&&bs>20)--bs;
  const auto sl=body.wrap(e.summary,bs,710);const float oldbottom=oldafter+16+float(sl.size()-1)*bs*1.4f+body.descent(bs);
  std::printf("%s %s\nBEFORE title%.0f/%zu summary%.0f/%zu actualbottom%.2f clip766\n",e.id.c_str(),e.title.c_str(),ts,tl.size(),bs,sl.size(),oldbottom);
  const auto fit=museum::timeline_hero_text(title,body,e.title,e.summary);
  assert(fit.fits&&fit.compact&&fit.title_size>=44&&fit.summary_size>=20);
  assert(fit.last_glyph_bottom<=744&&fit.title_baseline-title.ascent(fit.title_size)==448-title.ascent(68));
  const auto summary=body.wrap(e.summary,fit.summary_size,fit.summary_width);
  assert(summary.size()<99);
  const auto clean=[](std::string_view text){std::string out;for(unsigned char ch:text)if(ch!=' '&&ch!='\n'&&ch!='\r'&&ch!='\t')out+=char(ch);return out;};
  std::string joined;for(const auto&line:summary)joined+=line;
  assert(clean(joined)==clean(e.summary));
  std::printf("JOINT title%.0f/%zu summary%.0f/%zu baseline%.2f bottom%.2f fulltextPASS\n",fit.title_size,title.wrap(e.title,fit.title_size,770).size(),fit.summary_size,summary.size(),fit.title_baseline,fit.last_glyph_bottom);

 }
}
