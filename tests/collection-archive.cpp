#define JSON_NOEXCEPTION 1
#include "platform/collection_archive.hpp"
#include "yt/image.hpp"
#include <cassert>
#include <fstream>
#include <iterator>
#include <cstdio>
using museum::media::detail::CollectionArchive;
std::string file(const std::string&p){std::ifstream f(p,std::ios::binary);return {std::istreambuf_iterator<char>(f),{}};}
int main(int argc,char**argv){
 if(argc==3){CollectionArchive archive;assert(archive.load(argv[1],argv[2]));std::printf("PASS production index validated; available archive slices=%zu\n",archive.slices.size());return 0;}
 const std::string base="build/collection-delivery-20261031/archive-fixture",root=base+"/collection",path=root+"/assets/images/original.png";
 CollectionArchive archive;assert(archive.load(base+"/absent.json",root)&&archive.slices.empty());assert(archive.load(base+"/index.json",root)&&archive.slices.size()==1);assert(!archive.contains(root+"/assets/images/physical.png"));
 std::string body;assert(archive.read(path,body)&&body==file("build/photo-fixtures/small.png"));int width=0,height=0;std::vector<std::uint8_t>pixels;std::string error;assert(yt::decode_image(body,&width,&height,&pixels,&error)&&width==200&&height==100);assert(!archive.read(path,body,1)&&body.empty());
 auto j=nlohmann::json::parse(file(base+"/index.json"));
 const auto invalid=[&](auto value){const auto p=base+"/bad.json";{std::ofstream f(p);f<<value.dump();}assert(!archive.load(p,root)&&archive.slices.empty());};
 auto bad=j;bad["packs"][0]["files"][0]["path"]="assets/images/../secret";invalid(bad);
 bad=j;bad["packs"][0]["files"][0]["offset"]=std::uint64_t(1)<<63;invalid(bad);
 bad=j;bad["packs"][0]["files"][0]["bytes"]=-1;invalid(bad);
 bad=j;bad["packs"][0]["files"].push_back(bad["packs"][0]["files"][0]);invalid(bad);
 bad=j;bad["schema_version"]=2;invalid(bad);
 {std::ofstream f(base+"/bad.json");f<<"{";}assert(!archive.load(base+"/bad.json",root));
 assert(archive.load(base+"/index.json",root));const auto slice=archive.slices.at(path);const auto original_tar=file(slice.archive);{std::ofstream f(slice.archive,std::ios::binary|std::ios::app);f<<'x';}assert(!archive.read(path,body)&&body.empty());assert(archive.load(base+"/index.json",root)&&archive.slices.empty());{std::ofstream f(slice.archive,std::ios::binary|std::ios::trunc);f<<original_tar;}
 std::puts("PASS: original archive bytes and200x100decode; physical/missing fallback; size recheck; local cap; traversal,duplicate,overflow,negative,malformed/version rejected");
}
