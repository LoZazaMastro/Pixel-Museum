#include "platform/collection_writer.hpp"
#include "platform/collection_writer_protocol.h"
#include <cassert>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include <cstdio>
std::vector<unsigned char>bytes(const std::string&p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
int main(){
 using W=museum::CollectionWriter;char tmp[]="/tmp/pmcw-client-XXXXXX";assert(mkdtemp(tmp));const std::string base=tmp;std::array<unsigned char,32>nonce{};for(unsigned n=0;n<32;++n)nonce[n]=n+1;const unsigned port=49152+(getpid()%16000);const std::vector<W::Pack>packs={{std::string(64,'a'),(2u<<20)+19}};auto elf=bytes("build/collection-writer/collection_writer_host");assert(W::patch_for_test(elf,port,nonce,packs));assert(!W::patch_for_test(elf,port,nonce,packs));
 const auto launch=[&](unsigned number){auto code=bytes("build/collection-writer/collection_writer_host");assert(W::patch_for_test(code,port+number,nonce,packs));const auto executable=base+"/helper"+std::to_string(number);{std::ofstream f(executable,std::ios::binary);f.write(reinterpret_cast<const char*>(code.data()),code.size());}assert(chmod(executable.c_str(),0700)==0);const auto child=fork();assert(child>=0);if(!child){setenv("PMCW_TEST_ROOT",(base+"/root"+std::to_string(number)).c_str(),1);execl(executable.c_str(),executable.c_str(),static_cast<char*>(nullptr));_exit(127);}return child;};
 char hex[65]{};for(std::size_t n=0;n<nonce.size();++n)std::snprintf(hex+n*2,3,"%02x",unsigned(nonce[n]));
 const auto marker=[&](unsigned number){return base+"/root"+std::to_string(number)+"/.writer-session-"+hex;};
 auto child=launch(0);W writer;std::string error;assert(writer.attach_for_test(port,nonce,marker(0),packs,error));std::uint64_t offset=999;assert(writer.open(0,offset,error)&&offset==0);std::vector<unsigned char>payload(2u<<20,0x5a);assert(writer.write(payload.data(),payload.size())==std::ptrdiff_t(payload.size()));assert(writer.finish(error));assert(writer.open(0,offset,error)&&offset==payload.size());const char tail[]="1234567890123456789";assert(writer.write(tail,19)==19);assert(writer.write(tail,1)==-1);assert(writer.finish(error));const auto saved=bytes(base+"/root0/downloads/"+packs[0].sha+".tar.part");assert(saved.size()==packs[0].bytes&&std::equal(payload.begin(),payload.end(),saved.begin())&&std::memcmp(saved.data()+payload.size(),tail,19)==0);writer.stop();int status=0;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
 child=launch(1);auto wrong=nonce;wrong[0]^=1;assert(!writer.attach_for_test(port+1,wrong,marker(1),packs,error));writer.stop();assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)!=0);
 child=launch(2);assert(!writer.attach_for_test(port+2,nonce,base+"/wrong-marker",packs,error));writer.stop();assert(waitpid(child,&status,0)==child&&WIFEXITED(status));

 auto native_elf=bytes("build/collection-writer/collection_writer.elf");assert(W::patch_for_test(native_elf,0,nonce,packs,0));
 auto invalid_elf=bytes("build/collection-writer/collection_writer_host");invalid_elf.push_back(0);assert(!W::patch_for_test(invalid_elf,0,nonce,packs));
 auto stdio_elf=bytes("build/collection-writer/collection_writer_host");assert(W::patch_for_test(stdio_elf,0,nonce,packs));const auto stdio_exe=base+"/helper-stdio";{std::ofstream f(stdio_exe,std::ios::binary);f.write(reinterpret_cast<const char*>(stdio_elf.data()),stdio_elf.size());}assert(chmod(stdio_exe.c_str(),0700)==0);int channel[2];assert(socketpair(AF_UNIX,SOCK_STREAM,0,channel)==0);child=fork();assert(child>=0);if(!child){close(channel[0]);assert(dup2(channel[1],0)==0&&dup2(channel[1],1)==1);close(channel[1]);setenv("PMCW_TEST_ROOT",(base+"/root3").c_str(),1);execl(stdio_exe.c_str(),stdio_exe.c_str(),static_cast<char*>(nullptr));_exit(127);}close(channel[1]);
 if(!writer.attach_fd_for_test(channel[0],nonce,marker(3),packs,error)){std::fprintf(stderr,"STDIO attach failed: %s\n",error.c_str());assert(false);}assert(writer.open(0,offset,error)&&offset==0);assert(writer.write(payload.data(),payload.size())==std::ptrdiff_t(payload.size()));assert(writer.finish(error));assert(writer.open(0,offset,error)&&offset==payload.size());assert(writer.finish(error));writer.stop();assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
 std::puts("PASS STDIO same-channel private RPC,partialdurability,resume,sectiontableendbounds; nohalfclose required");
 std::filesystem::remove_all(base);std::puts("PASS real C helper/client: config patch,authenticated loopback,namespace marker,2MiB DATA,partial FINISH durable,reopen exactoffset,full bytes,rangeguard,QUIT,wrongnonce andwrongnamespace refused");
}
