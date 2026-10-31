// Exact original-master cache parity and corruption/source-version rollback.
#include "museum/object_scene.cpp"
#include <fstream>
#include <cassert>
#include <filesystem>
int main(int argc,char**argv){
 std::ifstream f("models/index.json");nlohmann::json index;f>>index;std::atomic<std::uint64_t> serial{1};unsigned checked=0;
 auto same=[](const museum::ImageUpload&a,const museum::ImageUpload&b){assert(a.source.rgba==b.source.rgba&&a.source.opaque==b.source.opaque&&a.source.alpha_known==b.source.alpha_known&&a.packed_base==b.packed_base&&a.packed_components==b.packed_components&&a.packed_channels==b.packed_channels);for(unsigned role=0;role<2;++role){assert(a.levels[role].size()==b.levels[role].size());for(std::size_t n=0;n<a.levels[role].size();++n){const auto&x=a.levels[role][n],&y=b.levels[role][n];assert(x.width==y.width&&x.height==y.height&&x.bytes==y.bytes);}}assert(a.packed_levels.size()==b.packed_levels.size());for(std::size_t n=0;n<a.packed_levels.size();++n)assert(a.packed_levels[n].bytes==b.packed_levels[n].bytes);};
 std::vector<std::string> ids;for(int n=1;n<argc;++n)ids.emplace_back(argv[n]);if(ids.empty())ids={"game-boy","playstation"};
 for(const auto&id:ids){nlohmann::json source;for(const auto&r:index["models"])if(r["exhibit_id"]==id)source=r;museum::Reader reader;reader.defer_images=true;reader.include_groups=source.value("include_groups",std::vector<std::string>{});assert(reader.read(source["asset_file"]));double cached_ms=0,original_ms=0;
  for(std::size_t n=0;n<reader.model.images.size();++n){if(!reader.model.images[n].roles)continue;museum::ImageUpload cached,original;cached.source=reader.model.images[n];cached.encoded=reader.encoded_file;cached.serial=1;cached.index=n;original.source=cached.source;original.encoded=cached.encoded;original.serial=1;original.index=n;original.use_cache=false;
   assert(museum::prepare_mips(original,serial)&&museum::prepare_mips(cached,serial)&&cached.cache_hit);same(original,cached);assert(original.uniform_roles==cached.uniform_roles);cached_ms+=cached.cache_decode_ms+cached.prepare_ms;original_ms+=original.decode_ms+original.prepare_ms;++checked;
  }
  std::printf("PASS %s all sourceRGBA+mips+packedbytes equal; original CPU%.2fms / cacheCPU%.2fms\n",id.c_str(),original_ms,cached_ms);
 }
 const std::string model="build/material-fixtures/packed-orm-10497-9987.glb",cache="build/material-fixtures/packed-orm-10497-9987.artwork.pmc";std::ifstream file(cache,std::ios::binary);std::string bytes((std::istreambuf_iterator<char>(file)),{});assert(bytes.size()>20);file.close();
 auto write=[&](const std::string&b){std::ofstream out(cache,std::ios::binary|std::ios::trunc);out.write(b.data(),static_cast<std::streamsize>(b.size()));};
 auto run=[&](bool hit){museum::Reader r;r.defer_images=true;assert(r.read(model));museum::ImageUpload job;job.source=r.model.images[0];job.encoded=r.encoded_file;job.serial=1;job.index=0;assert(museum::prepare_mips(job,serial)&&job.cache_hit==hit&&job.error.empty());};
 run(true);const auto length=museum::u32(reinterpret_cast<const unsigned char*>(bytes.data()+8));auto header=nlohmann::json::parse(bytes.substr(20,length));
 auto rewrite=[&](const nlohmann::json&metadata){const auto text=metadata.dump();const auto size=static_cast<std::uint32_t>(text.size());std::string revised="PMAC0001";for(unsigned n=0;n<4;++n)revised.push_back(static_cast<char>(size>>(n*8)));const auto hash=museum::encoded_fingerprint(reinterpret_cast<const unsigned char*>(text.data()),text.size());for(unsigned n=0;n<8;++n)revised.push_back(static_cast<char>(hash>>(n*8)));revised+=text;revised+=bytes.substr(20+length);write(revised);};
 auto changed=header;changed["version"]=2;rewrite(changed);run(false);
 changed=header;changed["atlases"][0]["source_fingerprint"]=changed["atlases"][0]["source_fingerprint"].get<std::uint64_t>()^1u;rewrite(changed);run(false);
 auto corrupt=bytes;corrupt[20+length/2]^=0x01;write(corrupt);run(false);
 corrupt=bytes;corrupt[20+length+10]^=0x37;write(corrupt);run(false);
 corrupt=bytes;corrupt.back()^=0x19;write(corrupt);run(false);
 write(bytes.substr(0,bytes.size()/2));run(false);write(bytes);run(true);
 std::puts("PASS cache version/source mismatch, corrupt compressed bytes and truncated payload fall back to original PNG; valid cache resumes");
 std::printf("PASS %u original full-resolution canonical atlases byte-for-byte\n",checked);
}
