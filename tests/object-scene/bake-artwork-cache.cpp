// Offline-only producer for the renderer's versioned lossless artwork cache.
#include "museum/object_scene.cpp"
#include <fstream>
#include <cassert>
extern "C" std::size_t ZSTD_compressBound(std::size_t);
struct ZSTD_CCtx_s;
extern "C" ZSTD_CCtx_s* ZSTD_createCCtx();
extern "C" std::size_t ZSTD_freeCCtx(ZSTD_CCtx_s*);
extern "C" std::size_t ZSTD_CCtx_setParameter(ZSTD_CCtx_s*,int,int);
extern "C" std::size_t ZSTD_compress2(ZSTD_CCtx_s*,void*,std::size_t,const void*,std::size_t);
int main(int argc,char**argv){
 std::ifstream input("models/index.json");nlohmann::json index;input>>index;
 bool v2=false;std::string source_id;std::vector<std::string> paths;for(int n=1;n<argc;++n){const std::string arg=argv[n];if(arg=="--v2")v2=true;else if(arg.rfind("--source-id=",0)==0)source_id=arg.substr(12);else paths.push_back(arg);}if(paths.empty())paths={"models/game-boy.glb","models/playstation.glb"};
 auto*context=ZSTD_createCCtx();assert(context);
 // Stable public zstd parameters: compressionLevel100/checksumFlag201.
 assert(!museum::ZSTD_isError(ZSTD_CCtx_setParameter(context,100,1)));
 assert(!museum::ZSTD_isError(ZSTD_CCtx_setParameter(context,201,1)));
 for(const auto&path:paths){
  nlohmann::json source;for(const auto&r:index["models"])if(r["asset_file"]==path||(!source_id.empty()&&r["exhibit_id"]==source_id))source=r;if(!source_id.empty())assert(source.is_object());
  museum::Reader reader;reader.defer_images=true;if(source.is_object())reader.include_groups=source.value("include_groups",std::vector<std::string>{});if(!reader.read(path)){std::fprintf(stderr,"%s\n",reader.error.c_str());return 2;}
  const std::string destination=path.substr(0,path.size()-4)+".artwork.pmc",payloadfile=destination+".payload.part",temporary=destination+".part";
  FILE*payload=std::fopen(payloadfile.c_str(),"wb");assert(payload);std::uint64_t offset=0,total_raw=0;
  nlohmann::json metadata={{"version",museum::kArtworkCacheVersion},{"frame_checksum","xxh64-low32"},{"source_bytes",reader.encoded_file->bytes},{"source_sha256",source.is_object()?source.value("sha256",""):"fixture"},{"mip_algorithm","RGBA8 original source, linear-light sRGB mips, existing weighted data mips; v1"},{"atlases",nlohmann::json::array()}};
  if(v2){std::ifstream original(path,std::ios::binary);std::string data((std::istreambuf_iterator<char>(original)),{});assert(data.size()==reader.encoded_file->bytes);metadata["source_sha256"]=museum::object_source_sha256_hex(data.data(),data.size());if(!source_id.empty())assert(metadata["source_sha256"]==source["sha256"]);metadata["version"]=2;metadata["mip_algorithm"]="exact-existing-RGBA8-mips-and-current-packed-views-v2";}
  std::atomic<std::uint64_t> serial{1};
  for(std::size_t n=0;n<reader.model.images.size();++n){if(!reader.model.images[n].roles)continue;
   museum::ImageUpload job;job.source=std::move(reader.model.images[n]);job.encoded=reader.encoded_file;job.serial=1;job.use_cache=false;assert(museum::prepare_mips(job,serial));
   nlohmann::json atlas={{"index",n},{"width",job.source.width},{"height",job.source.height},{"roles",job.source.roles},{"data_channels",job.source.data_channels},{"source_fingerprint",job.source.encoded_fingerprint},{"views",nlohmann::json::array()}};
   if(v2)atlas["source_opaque"]=job.source.opaque;
   for(unsigned role=0;role<2;++role){if(!(job.source.roles&(1u<<role)))continue;
    nlohmann::json view={{"role",role},{"levels",nlohmann::json::array()}};
    const bool compact=v2&&role==1&&job.source.roles==2&&job.packed_components;
    const bool constant=v2&&job.source.roles!=3&&job.uniform_roles[role];
    if(v2){view["format"]=compact?(job.packed_components==1?"r8":"rg8"):"rgba8";view["constant"]=constant;}
    auto write=[&](int w,int h,const std::vector<std::uint8_t>&bytes){
     std::vector<unsigned char> compressed(ZSTD_compressBound(bytes.size()));const auto size=ZSTD_compress2(context,compressed.data(),compressed.size(),bytes.data(),bytes.size());assert(!museum::ZSTD_isError(size));assert(std::fwrite(compressed.data(),1,size,payload)==size);
     view["levels"].push_back({{"width",w},{"height",h},{"offset",offset},{"compressed_bytes",size}});offset+=size;total_raw+=bytes.size();
    };
    if(constant){const auto&pixels=compact?job.packed_base:job.source.rgba;const std::size_t count=compact?job.packed_components:4;write(1,1,std::vector<std::uint8_t>(pixels.begin(),pixels.begin()+count));}
    else if(compact){write(job.source.width,job.source.height,job.packed_base);for(const auto&m:job.packed_levels)write(m.width,m.height,m.bytes);}
    else{write(job.source.width,job.source.height,job.source.rgba);for(const auto&m:job.levels[role])write(m.width,m.height,m.bytes);}atlas["views"].push_back(view);
   }
   metadata["atlases"].push_back(atlas);
  }
  assert(std::fclose(payload)==0);std::string header=metadata.dump();assert(header.size()<(128u<<10));FILE*out=std::fopen(temporary.c_str(),"wb");assert(out);assert(std::fwrite(v2?"PMAC0002":"PMAC0001",1,8,out)==8);const std::uint32_t size=static_cast<std::uint32_t>(header.size());unsigned char little[4]{static_cast<unsigned char>(size),static_cast<unsigned char>(size>>8),static_cast<unsigned char>(size>>16),static_cast<unsigned char>(size>>24)};assert(std::fwrite(little,1,4,out)==4);const auto header_hash=museum::encoded_fingerprint(reinterpret_cast<const unsigned char*>(header.data()),header.size());unsigned char hash_bytes[8];for(unsigned n=0;n<8;++n)hash_bytes[n]=static_cast<unsigned char>(header_hash>>(n*8));assert(std::fwrite(hash_bytes,1,8,out)==8);assert(std::fwrite(header.data(),1,header.size(),out)==header.size());
  payload=std::fopen(payloadfile.c_str(),"rb");assert(payload);std::vector<unsigned char> block(1u<<20);for(;;){const auto got=std::fread(block.data(),1,block.size(),payload);if(got)assert(std::fwrite(block.data(),1,got,out)==got);if(got<block.size()){assert(!std::ferror(payload));break;}}
  assert(std::fclose(payload)==0&&std::fclose(out)==0);assert(std::rename(temporary.c_str(),destination.c_str())==0);std::remove(payloadfile.c_str());std::printf("BAKED %s: %llu rawRGBA+mipbytes / %llu compressedbytes / %zu canonicalatlases\n",destination.c_str(),static_cast<unsigned long long>(total_raw),static_cast<unsigned long long>(offset),metadata["atlases"].size());
 }
 assert(!museum::ZSTD_isError(ZSTD_freeCCtx(context)));
}
