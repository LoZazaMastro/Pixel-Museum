// Pixel Museum - bounded reads from verified collection USTAR files.
#pragma once
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <sys/stat.h>
namespace museum::media::detail {
class CollectionArchive {
public:
 struct Slice {std::string archive;std::uint64_t offset=0,bytes=0,archive_bytes=0;};
 static constexpr std::size_t maximum_bytes=32u<<20;
 std::map<std::string,Slice> slices;
 static bool sha(const std::string&s){return s.size()==64&&s.find_first_not_of("0123456789abcdef")==std::string::npos;}
 static bool safe(const std::string&s){
  if(s.rfind("assets/images/",0)!=0||s.find('\\')!=std::string::npos||s.find(':')!=std::string::npos||s.back()=='/')return false;
  std::size_t start=0;while(start<s.size()){const auto end=s.find('/',start);const auto part=s.substr(start,end==std::string::npos?end:end-start);if(part.empty()||part=="."||part=="..")return false;if(end==std::string::npos)break;start=end+1;}return true;
 }
 bool load(const std::string&index,const std::string&root){
  slices.clear();errno=0;FILE*f=std::fopen(index.c_str(),"rb");if(!f)return errno==ENOENT;
  struct stat st{};if(fstat(fileno(f),&st)||!S_ISREG(st.st_mode)||st.st_size<=0||std::uint64_t(st.st_size)>maximum_bytes){std::fclose(f);return false;}
  std::string text(std::size_t(st.st_size),'\0');const bool read=std::fread(text.data(),1,text.size(),f)==text.size();std::fclose(f);if(!read)return false;
  const auto j=nlohmann::json::parse(text,nullptr,false);using J=nlohmann::json;
  const auto uint=[](const J&v){return v.is_number_unsigned();};
  if(!j.is_object()||!j.contains("schema_version")||!j["schema_version"].is_number_integer()||j["schema_version"]!=1||!j.contains("collection_id")||!j["collection_id"].is_string()||j["collection_id"].get<std::string>().empty()||!j.contains("image_manifest_sha256")||!j["image_manifest_sha256"].is_string()||!sha(j["image_manifest_sha256"].get<std::string>())||!j.contains("packs")||!j["packs"].is_array()||j["packs"].empty()||j["packs"].size()>128)return false;
  std::set<std::string>paths,ids,hashes;std::map<std::string,Slice> pending;
  for(const auto&p:j["packs"]){
   if(!p.is_object()||!p.contains("id")||!p["id"].is_string()||!ids.insert(p["id"].get<std::string>()).second||!p.contains("sha256")||!p["sha256"].is_string()||!sha(p["sha256"].get<std::string>())||!hashes.insert(p["sha256"].get<std::string>()).second||!p.contains("bytes")||!uint(p["bytes"])||!p.contains("files")||!p["files"].is_array())return false;
   const auto total=p["bytes"].get<std::uint64_t>();if(total<1024||total>std::uint64_t(LONG_MAX)||total%512)return false;
   const auto archive=root+"/archives/"+p["sha256"].get<std::string>()+".tar";struct stat info{};const bool available=stat(archive.c_str(),&info)==0&&S_ISREG(info.st_mode)&&info.st_size>=0&&std::uint64_t(info.st_size)==total;
   std::uint64_t previous_end=0;
   for(const auto&v:p["files"]){
    if(!v.is_object()||!v.contains("path")||!v["path"].is_string()||!v.contains("offset")||!uint(v["offset"])||!v.contains("bytes")||!uint(v["bytes"]))return false;
    const auto path=v["path"].get<std::string>();const auto offset=v["offset"].get<std::uint64_t>(),bytes=v["bytes"].get<std::uint64_t>();
    if(!safe(path)||!paths.insert(path).second||paths.size()>100000||offset<512||offset%512||offset<previous_end||offset>total||bytes>total-offset)return false;
    previous_end=offset+bytes;
    if(available)pending[root+"/"+path]={archive,offset,bytes,total};
   }
  }
  slices=std::move(pending);return true;
 }
 bool contains(const std::string&path)const{return slices.count(path)!=0;}
 bool read(const std::string&path,std::string&body,std::size_t limit=maximum_bytes)const{
  body.clear();const auto it=slices.find(path);if(it==slices.end())return false;const auto&s=it->second;
  if(!s.bytes||s.bytes>std::min(limit,maximum_bytes)||s.offset>std::uint64_t(LONG_MAX))return false;
  FILE*f=std::fopen(s.archive.c_str(),"rb");if(!f)return false;struct stat st{};
  if(fstat(fileno(f),&st)||!S_ISREG(st.st_mode)||st.st_size<0||std::uint64_t(st.st_size)!=s.archive_bytes||std::fseek(f,long(s.offset),SEEK_SET)){std::fclose(f);return false;}
  body.resize(std::size_t(s.bytes));const bool ok=std::fread(body.data(),1,body.size(),f)==body.size();std::fclose(f);if(!ok)body.clear();return ok;
 }
};
}
