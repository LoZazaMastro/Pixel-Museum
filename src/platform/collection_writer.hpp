// Pixel Museum - authenticated loopback transport to the restricted cache writer.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>
namespace museum {
class CollectionWriter {
public:
 struct Pack {std::string sha;std::uint64_t bytes=0;};
 CollectionWriter()=default;~CollectionWriter();
 CollectionWriter(const CollectionWriter&)=delete;CollectionWriter&operator=(const CollectionWriter&)=delete;
 bool start(const std::vector<Pack>&packs,std::string&error);
 bool open(std::size_t index,std::uint64_t&offset,std::string&error);
 std::ptrdiff_t write(const void*data,std::size_t bytes);
 bool finish(std::string&error);
 bool remove_downloaded(std::string&error);
 void stop();
 const std::string&last_error()const{return error_;}
#ifdef MUSEUM_COLLECTION_WRITER_TEST
 bool attach_for_test(unsigned port,const std::array<unsigned char,32>&nonce,const std::string&marker,const std::vector<Pack>&packs,std::string&error);
 bool attach_fd_for_test(int fd,const std::array<unsigned char,32>&nonce,const std::string&marker,const std::vector<Pack>&packs,std::string&error);
 static bool patch_for_test(std::vector<unsigned char>&elf,unsigned port,const std::array<unsigned char,32>&nonce,const std::vector<Pack>&packs,unsigned mode=1);
#endif
private:
 int fd_=-1;bool authenticated_=false,opened_=false;std::uint64_t pid_=0,offset_=0,expected_=0;std::vector<Pack>packs_;std::string error_;
 bool failure(const char*operation,int code,std::string*error=nullptr);
 bool connect_session(unsigned port,const std::array<unsigned char,32>&nonce,const std::string&marker,std::string&error);
 bool request(unsigned command,std::uint64_t value,std::uint64_t&offset,std::string&error);
 bool ack(std::uint64_t&offset,std::string&error,int timeout_seconds=120);
};
}
