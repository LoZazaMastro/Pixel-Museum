// Isolated lossless derived-artwork cache benchmark; no production cache format.
#include "museum/object_scene.cpp"
#include <fstream>
#include <cassert>
#include <sys/resource.h>
extern "C" std::size_t ZSTD_compressBound(std::size_t);
extern "C" std::size_t ZSTD_compress(void*,std::size_t,const void*,std::size_t,int);
extern "C" std::size_t ZSTD_decompress(void*,std::size_t,const void*,std::size_t);
extern "C" unsigned ZSTD_isError(std::size_t);
int main(int argc,char**argv){
 std::ifstream indexfile("models/index.json");nlohmann::json index;indexfile>>index;
 nlohmann::json report={{"scope","Host-only exact current decoded channel/mip payload, zstd level1, in-memory decompression. No production cache, no GPU format/API changes, no PS5 latency claim."},{"models",nlohmann::json::array()}};
 std::vector<std::string> ids;for(int n=1;n<argc;++n)ids.emplace_back(argv[n]);if(ids.empty())ids={"game-boy","playstation"};
 for(const auto&id:ids){
  nlohmann::json source;for(const auto&r:index["models"])if(r["exhibit_id"]==id)source=r;assert(!source.is_null());
  museum::Reader reader;reader.defer_images=true;reader.include_groups=source.value("include_groups",std::vector<std::string>{});assert(reader.read(source["asset_file"]));assert(reader.bytes.empty());std::atomic<std::uint64_t> serial{1};
  std::size_t total_raw=0,total_compressed=0,max_raw=0,max_compressed=0;double total_png=0,total_mips=0,total_compress=0,total_decode=0;unsigned views=0;
  auto rows=nlohmann::json::array();
  for(std::size_t n=0;n<reader.model.images.size();++n){if(!reader.model.images[n].roles)continue;
   museum::ImageUpload job;job.source=std::move(reader.model.images[n]);job.encoded=reader.encoded_file;job.serial=1;job.use_cache=false;assert(museum::prepare_mips(job,serial));total_png+=job.decode_ms;total_mips+=job.prepare_ms;
   for(unsigned role=0;role<2;++role){if(!(job.source.roles&(1u<<role)))continue;const bool packed=role==1&&job.packed_components;
    std::vector<unsigned char> raw=packed?job.packed_base:job.source.rgba;for(const auto&m:packed?job.packed_levels:job.levels[role])raw.insert(raw.end(),m.bytes.begin(),m.bytes.end());
    std::vector<unsigned char> compressed(ZSTD_compressBound(raw.size()));auto started=std::chrono::steady_clock::now();auto size=ZSTD_compress(compressed.data(),compressed.size(),raw.data(),raw.size(),1);assert(!ZSTD_isError(size));double encode_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count();compressed.resize(size);
    std::vector<unsigned char> decoded(raw.size());double decode_ms=0;for(unsigned repeat=0;repeat<3;++repeat){started=std::chrono::steady_clock::now();const auto restored=ZSTD_decompress(decoded.data(),decoded.size(),compressed.data(),compressed.size());assert(!ZSTD_isError(restored)&&restored==raw.size());decode_ms+=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count();assert(decoded==raw);}decode_ms/=3;
    total_raw+=raw.size();total_compressed+=size;total_compress+=encode_ms;total_decode+=decode_ms;max_raw=std::max(max_raw,raw.size());max_compressed=std::max(max_compressed,size);++views;
    rows.push_back({{"atlas",n},{"role",role==0?"sRGB colour":"linear material"},{"components",packed?job.packed_components:4},{"width",job.source.width},{"height",job.source.height},{"raw_bytes",raw.size()},{"compressed_bytes",size},{"compress_ms",encode_ms},{"decompress_ms",decode_ms},{"exact_every_byte_roundtrip",true}});
    std::printf("%s atlas%zu role%u: %.2fMiB?%.2fMiB zstd encode%.2fms / decode%.2fms exactbytes PASS\n",id.c_str(),n,role,double(raw.size())/(1u<<20),double(size)/(1u<<20),encode_ms,decode_ms);std::fflush(stdout);
   }
  }
  report["models"].push_back({{"id",id},{"source_sha256",source["sha256"]},{"views",views},{"raw_cache_bytes",total_raw},{"zstd_cache_bytes",total_compressed},{"source_png_decode_ms",total_png},{"mip_and_pack_ms",total_mips},{"zstd_encode_ms",total_compress},{"zstd_decode_ms",total_decode},{"max_single_raw_atlas_bytes",max_raw},{"max_single_compressed_atlas_bytes",max_compressed},{"conservative_compressed_plus_decoded_atlas_bytes",max_raw+max_compressed},{"gpu_transfer_bytes_unchanged",total_raw},{"minimum_2mib_upload_ticks",(total_raw+(2u<<20)-1)/(2u<<20)},{"atlas_rows",rows}});
 }
 struct rusage usage{};if(getrusage(RUSAGE_SELF,&usage)==0)report["process_peak_rss_bytes"]=static_cast<std::uint64_t>(usage.ru_maxrss)*1024;
 const char*destination=std::getenv("MUSEUM_BENCH_OUTPUT");std::ofstream output(destination?destination:"build/research/derived-model-cache-benchmark.json");output<<report.dump(2)<<'\n';
}
