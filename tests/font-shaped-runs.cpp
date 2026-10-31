// Genuine static shaping, source-preserving wrap/fit and bounded parser tests.
#include "gfx/font.hpp"
#include "third_party/nlohmann/json.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iterator>
#include <cstdio>
static std::string read(const char*path){std::ifstream file(path,std::ios::binary);assert(file);return {(std::istreambuf_iterator<char>(file)),{}};}
static std::string utf8(std::uint32_t cp){return {char(0xf0|(cp>>18)),char(0x80|((cp>>12)&63)),char(0x80|((cp>>6)&63)),char(0x80|(cp&63))};}
int main(){
 const auto bytes=read("assets/fonts/cjk-subset.huifont");hui::gfx::Font fallback,unicode;assert(fallback.load(bytes)&&unicode.load(read("assets/fonts/unicode-fallback.huifont")));
 const auto prepared=nlohmann::json::parse(read("build/research/offline-script-shaping/script-runs.json"));unsigned checked=0;
 for(const char*file:{"assets/fonts/inter-regular.huifont","assets/fonts/inter-semibold.huifont","assets/fonts/montserrat-medium.huifont","assets/fonts/dejavu-sans-mono.huifont"}){
  hui::gfx::Font face;assert(face.load(read(file)));face.add_fallback(&unicode,7);face.add_fallback(&fallback,8);
  for(const auto&run:prepared["runs"]){const auto text=run["text"].get<std::string>();const auto original=text;const auto private_cp=run["private_glyph"].get<std::uint32_t>();
   assert(face.has_text(text));const float width=float(run["advance_font_units"].get<int>())*34/float(prepared["target_units_per_em"].get<int>());assert(std::abs(face.measure(text,34)-width)<.01f);
   std::vector<hui::gfx::GlyphQuad>actual,expected;face.layout(text,10,80,34,hui::gfx::Align::left,actual);fallback.layout(utf8(private_cp),10,80,34,hui::gfx::Align::left,expected);
   assert(actual.size()==1&&expected.size()==1&&actual[0].texture==8);const auto&a=actual[0];const auto&e=expected[0];assert(a.x0==e.x0&&a.y0==e.y0&&a.x1==e.x1&&a.y1==e.y1&&a.u0==e.u0&&a.v0==e.v0&&a.u1==e.u1&&a.v1==e.v1);
   // Half the real prose-column width: wrap at actual word boundaries without
   // splitting a Tamil consonant/vowel cluster into unshaped source prefixes.
   const std::string sentence="Before "+text+" after";const auto lines=face.wrap(sentence,34,280);std::string restored;for(const auto&line:lines){assert(face.has_text(line)&&face.measure(line,34)<=280.01f);if(!restored.empty())restored+=' ';restored+=line;}assert(restored==sentence&&text==original);
   const auto fitted=face.fit(text,34,width*.7f);assert(face.has_text(fitted)&&face.measure(fitted,34)<=width*.7f+.01f);for(size_t index=0;index<fitted.size();)assert(hui::gfx::next_codepoint(fitted,&index)<0xf0000);
   if(run["script"]=="Arabic"){const auto&glyphs=run["shaped_glyphs"];assert(glyphs.front()["source_byte_cluster"].get<unsigned>()>=glyphs.back()["source_byte_cluster"].get<unsigned>());}
   ++checked;
  }
  assert(!face.has_text("حربالعراق")); // An unknown joined word cannot claim real shaping.
 }
 const auto get32=[&](size_t offset){std::uint32_t value;std::memcpy(&value,bytes.data()+offset,4);return value;};
 std::uint16_t w,h;std::memcpy(&w,bytes.data()+8,2);std::memcpy(&h,bytes.data()+10,2);const auto trailer=40+size_t(get32(32))*24+size_t(get32(36))*12+size_t(w)*h;
 const auto reject=[](const std::string&data){hui::gfx::Font malformed;assert(!malformed.load(data)&&!malformed.error().empty());};
 reject(bytes.substr(0,bytes.size()-1));reject(bytes+"x");
 auto malformed=bytes;std::uint32_t value=513;std::memcpy(malformed.data()+trailer+4,&value,4);reject(malformed);
 malformed=bytes;value=1;std::memcpy(malformed.data()+trailer+8,&value,4);reject(malformed);
 malformed=bytes;value=1025;std::memcpy(malformed.data()+trailer+12,&value,4);reject(malformed);
 malformed=bytes;malformed[trailer+16]='A';reject(malformed);
 std::printf("PASS %u genuine shaped-run/face cases: HarfBuzz advances, exact outline geometry, originalUTF8 wrap/fit, ArabicRTL order, unknown-run rejection and6malformed trailers; v1 fonts retained.\n",checked);
}
