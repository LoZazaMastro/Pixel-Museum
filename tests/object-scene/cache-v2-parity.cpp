// Compare exact v2 upload bytes against original pixels/mips, then reject bad
// source/header/frame metadata without committing a partially decoded job.
#include "museum/object_scene.cpp"
#include <cassert>
#include <fstream>
#include <filesystem>
int main(int argc,char**argv){
 assert(museum::object_source_sha256_hex("",0)=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
 assert(museum::object_source_sha256_hex("abc",3)=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
 const std::string long_message(1000000,'a');assert(museum::object_source_sha256_hex(long_message.data(),long_message.size())=="cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
 std::atomic<std::uint64_t> revision{1};unsigned checked=0;std::size_t saved=0;
 for(int arg=1;arg<argc;++arg){
  museum::Reader reader;reader.defer_images=true;assert(reader.read(argv[arg]));assert(reader.encoded_file->source_sha256.size()==64);
  for(std::size_t n=0;n<reader.model.images.size();++n){if(!reader.model.images[n].roles)continue;
   museum::ImageUpload original,cached;original.source=reader.model.images[n];original.encoded=reader.encoded_file;original.serial=1;original.index=n;original.use_cache=false;cached.source=original.source;cached.encoded=original.encoded;cached.serial=1;cached.index=n;
   assert(museum::prepare_mips(original,revision)&&museum::prepare_mips(cached,revision)&&cached.cache_hit);
   assert(original.source.opaque==cached.source.opaque&&original.source.alpha_known==cached.source.alpha_known&&original.uniform_roles==cached.uniform_roles);
   assert(original.packed_components==cached.packed_components&&original.packed_channels==cached.packed_channels);
   assert(original.packed_base==cached.packed_base&&original.packed_levels.size()==cached.packed_levels.size());
   for(std::size_t m=0;m<original.packed_levels.size();++m)assert(original.packed_levels[m].bytes==cached.packed_levels[m].bytes&&original.packed_levels[m].width==cached.packed_levels[m].width&&original.packed_levels[m].height==cached.packed_levels[m].height);
   if(cached.packed_components&&cached.direct_payload){assert(cached.source.rgba.empty()&&cached.levels[1].empty());saved+=original.source.rgba.size();for(const auto&m:original.levels[1])saved+=m.bytes.size();}
   else for(unsigned role=0;role<2;++role)if(original.source.roles&(1u<<role)){
    if(cached.uniform_roles[role]&&cached.direct_payload){assert(cached.source.rgba.size()==4&&std::equal(cached.source.rgba.begin(),cached.source.rgba.end(),original.source.rgba.begin())&&cached.levels[role].empty());}
    else{assert(cached.source.rgba==original.source.rgba&&cached.levels[role].size()==original.levels[role].size());for(std::size_t m=0;m<original.levels[role].size();++m)assert(cached.levels[role][m].bytes==original.levels[role][m].bytes);}
   }
   ++checked;
  }
 }
 const std::string path="build/material-fixtures/packed-orm-10497-9987.glb",cache="build/material-fixtures/packed-orm-10497-9987.artwork.pmc";
 std::ifstream input(cache,std::ios::binary);const std::string bytes((std::istreambuf_iterator<char>(input)),{});assert(bytes.size()>20&&bytes.substr(0,8)=="PMAC0002");
 const auto length=museum::u32(reinterpret_cast<const unsigned char*>(bytes.data()+8));const auto header=nlohmann::json::parse(bytes.substr(20,length));
 const auto write=[&](const std::string&value){std::ofstream out(cache,std::ios::binary|std::ios::trunc);out.write(value.data(),value.size());};
 const auto run=[&](bool hit){museum::Reader r;r.defer_images=true;assert(r.read(path));museum::ImageUpload job;job.source=r.model.images[0];job.encoded=r.encoded_file;job.index=0;job.serial=1;assert(museum::prepare_mips(job,revision)&&job.cache_hit==hit&&job.error.empty());if(!hit)assert(!job.direct_payload&&!job.source.rgba.empty());};
 const auto rewrite=[&](const nlohmann::json&metadata){const auto text=metadata.dump();const auto count=std::uint32_t(text.size());std::string value="PMAC0002";for(unsigned n=0;n<4;++n)value.push_back(static_cast<char>(count>>(n*8)));const auto hash=museum::encoded_fingerprint(reinterpret_cast<const unsigned char*>(text.data()),text.size());for(unsigned n=0;n<8;++n)value.push_back(static_cast<char>(hash>>(n*8)));value+=text;value+=bytes.substr(20+length);write(value);};
 run(true);unsigned rejected=0;
 const auto reject=[&](const nlohmann::json&changed){rewrite(changed);run(false);++rejected;};
 auto changed=header;changed["version"]=1;reject(changed);
 changed=header;changed["source_sha256"]=std::string(64,'0');reject(changed);
 changed=header;changed["mip_algorithm"]="different";reject(changed);
 changed=header;changed["atlases"][0]["roles"]=1;reject(changed);
 changed=header;changed["atlases"][0]["data_channels"]=1;reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["format"]="rgb565";reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["format"]="rgba8";reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["constant"]=true;reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["levels"].erase(changed["atlases"][0]["views"][0]["levels"].end()-1);reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["levels"][0]["offset"]=~std::uint64_t(0);reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["levels"][0]["width"]=8192;reject(changed);
 changed=header;changed["atlases"][0]["views"][0]["levels"][0]["compressed_bytes"]=~std::uint64_t(0);reject(changed);
 for(auto at:{std::size_t(10),std::size_t(20+length/2),std::size_t(20+length+8),bytes.size()-1}){auto broken=bytes;broken[at]^=67;write(broken);run(false);++rejected;}
 write(bytes.substr(0,bytes.size()/2));run(false);++rejected;write(bytes);run(true);
 museum::Reader r;r.defer_images=true;assert(r.read(path));museum::ImageUpload cancelled;cancelled.source=r.model.images[0];cancelled.encoded=r.encoded_file;cancelled.serial=0;cancelled.index=0;
 assert(!museum::read_artwork_cache(cancelled,revision)&&cancelled.source.rgba.empty()&&cancelled.packed_base.empty()&&!cancelled.direct_payload);
 std::printf("PASS v2 exact current upload bytes for%u atlases; %zu originalRGBA+mip staging bytes not retained; %u malformed/source/format/mip/endian/frame cases fallback; cancelled job commits nothing; SHA256 standard vectors PASS\n",checked,saved,rejected);
}
