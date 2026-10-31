// Offline research only: compare exact existing payloads with current RG8/R8
// upload bytes. Does not write/modify a runtime sidecar or renderer.
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <vector>
extern "C" std::size_t ZSTD_decompress(void*,std::size_t,const void*,std::size_t);
extern "C" unsigned ZSTD_isError(std::size_t);
extern "C" std::size_t ZSTD_compressBound(std::size_t);
struct ZSTD_CCtx_s;
extern "C" ZSTD_CCtx_s* ZSTD_createCCtx();
extern "C" std::size_t ZSTD_freeCCtx(ZSTD_CCtx_s*);
extern "C" std::size_t ZSTD_CCtx_setParameter(ZSTD_CCtx_s*,int,int);
extern "C" std::size_t ZSTD_compress2(ZSTD_CCtx_s*,void*,std::size_t,const void*,std::size_t);
using Json=nlohmann::json;
using Clock=std::chrono::steady_clock;
double ms(Clock::time_point started){return std::chrono::duration<double,std::milli>(Clock::now()-started).count();}
std::uint32_t u32(const unsigned char*p){return std::uint32_t(p[0])|std::uint32_t(p[1])<<8|std::uint32_t(p[2])<<16|std::uint32_t(p[3])<<24;}
volatile std::size_t sink=0;
int main(int argc,char**argv){
 auto*context=ZSTD_createCCtx();assert(context);
 assert(!ZSTD_isError(ZSTD_CCtx_setParameter(context,100,1))&&!ZSTD_isError(ZSTD_CCtx_setParameter(context,201,1)));
 Json output={{"publication_status","RESEARCH_ONLY_NO_PRODUCTION_FORMAT"},{"models",Json::array()}};
 for(int arg=1;arg<argc;++arg){
  std::ifstream stream(argv[arg],std::ios::binary);std::array<unsigned char,20>prefix{};stream.read(reinterpret_cast<char*>(prefix.data()),20);
  assert(stream&&std::memcmp(prefix.data(),"PMAC0001",8)==0);std::string text(u32(prefix.data()+8),'\0');stream.read(text.data(),text.size());const auto header=Json::parse(text);
  const auto payload=20+text.size();Json model={{"path",argv[arg]},{"source_sha256",header["source_sha256"]},{"atlases",Json::array()}};
  for(const auto&atlas:header["atlases"]){
   const unsigned mask=atlas["data_channels"];const unsigned components=unsigned(bool(mask&1))+unsigned(bool(mask&2))+unsigned(bool(mask&4));
   if(atlas["roles"]!=2||components<1||components>2)continue;
   Json row={{"index",atlas["index"]},{"dimensions",Json::array({atlas["width"],atlas["height"]})},{"components",components},{"source_raw_bytes",0},{"v1_compressed_bytes",0},{"v2_packed_raw_bytes",0},{"v2_compressed_bytes",0},{"levels",Json::array()}};
   bool uniform=true;std::array<unsigned char,4>first{};bool have_first=false;
   for(const auto&level:atlas["views"][0]["levels"]){
    const std::size_t raw_bytes=level["width"].get<std::size_t>()*level["height"].get<std::size_t>()*4;
    std::vector<unsigned char>compressed(level["compressed_bytes"].get<std::size_t>());stream.seekg(payload+level["offset"].get<std::size_t>());stream.read(reinterpret_cast<char*>(compressed.data()),compressed.size());assert(stream);
    std::vector<unsigned char>raw(raw_bytes);assert(ZSTD_decompress(raw.data(),raw.size(),compressed.data(),compressed.size())==raw.size());
    if(!have_first){std::copy_n(raw.begin(),4,first.begin());have_first=true;}
    for(std::size_t n=0;uniform&&n<raw.size();n+=4)if(std::memcmp(raw.data()+n,first.data(),4))uniform=false;
    std::vector<unsigned char>packed(raw.size()/4*components);std::size_t target=0;
    for(std::size_t n=0;n<raw.size();n+=4)for(unsigned channel=0;channel<3;++channel)if(mask&(1u<<channel))packed[target++]=raw[n+channel];
    std::vector<unsigned char>encoded(ZSTD_compressBound(packed.size()));const auto size=ZSTD_compress2(context,encoded.data(),encoded.size(),packed.data(),packed.size());assert(!ZSTD_isError(size));encoded.resize(size);
    std::vector<unsigned char>decoded(packed.size());assert(ZSTD_decompress(decoded.data(),decoded.size(),encoded.data(),encoded.size())==decoded.size()&&decoded==packed);
    double old_ms=0,new_ms=0;
    for(int sample=0;sample<5;++sample){
     auto start=Clock::now();std::vector<unsigned char>old_raw(raw.size());assert(ZSTD_decompress(old_raw.data(),old_raw.size(),compressed.data(),compressed.size())==old_raw.size());
     std::vector<unsigned char>old_packed(packed.size());target=0;for(std::size_t n=0;n<old_raw.size();n+=4)for(unsigned channel=0;channel<3;++channel)if(mask&(1u<<channel))old_packed[target++]=old_raw[n+channel];
     old_ms+=ms(start);assert(old_packed==packed);sink+=old_packed[0];
     start=Clock::now();std::vector<unsigned char>new_packed(packed.size());assert(ZSTD_decompress(new_packed.data(),new_packed.size(),encoded.data(),encoded.size())==new_packed.size());new_ms+=ms(start);assert(new_packed==packed);sink+=new_packed[0];
    }
    const auto add=[&](const char*key,std::size_t n){row[key]=row[key].get<std::size_t>()+n;};add("source_raw_bytes",raw.size());add("v1_compressed_bytes",compressed.size());add("v2_packed_raw_bytes",packed.size());add("v2_compressed_bytes",encoded.size());
    row["levels"].push_back({{"width",level["width"]},{"height",level["height"]},{"old_decode_and_pack_mean_ms",old_ms/5},{"new_direct_packed_decode_mean_ms",new_ms/5},{"exact_current_upload_bytes",true}});
   }
   row["all_original_RGBA_and_mips_uniform"]=uniform;
   if(uniform){row["constant_exact_RGBA"]=first;row["constant_packed_bytes"]=components;row["constant_can_replace_all_levels_after_offline_byte_proof"]=true;}
   model["atlases"].push_back(row);
  }
  output["models"].push_back(model);
 }
 assert(!ZSTD_isError(ZSTD_freeCCtx(context)));std::puts(output.dump(2).c_str());return sink==123456;
}
