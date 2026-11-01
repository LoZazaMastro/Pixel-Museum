// Pixel Museum - no arbitrary paths or commands cross the restricted writer channel.
#include "platform/collection_writer.hpp"
#include "platform/collection_writer_protocol.h"
#include <algorithm>
#include <cerrno>
#include <cstdio>
#include <cstring>
#if defined(__FreeBSD__) || defined(MUSEUM_COLLECTION_WRITER_TEST)
#include <chrono>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>
#if defined(__FreeBSD__)
#include <openssl/rand.h>
#endif
namespace museum {
namespace {
using Clock=std::chrono::steady_clock;
#if defined(__FreeBSD__)
#include "build/collection_writer.inc"
#endif
bool valid(const std::vector<CollectionWriter::Pack>&packs){
 if(packs.empty()||packs.size()>PMCW_MAX_PACKS)return false;
 for(std::size_t n=0;n<packs.size();++n){const auto&p=packs[n];if(p.sha.size()!=64||p.sha.find_first_not_of("0123456789abcdef")!=std::string::npos||!p.bytes||p.bytes>PMCW_MAX_PACK_BYTES)return false;for(std::size_t m=0;m<n;++m)if(packs[m].sha==p.sha)return false;}return true;
}
bool validated_elf(const std::vector<unsigned char>&elf){
 if(elf.size()<64||elf.size()>(16u<<20)||std::memcmp(elf.data(),"\177ELF",4)||elf[4]!=2||elf[5]!=1)return false;
 const auto u16=[&](std::size_t n){return unsigned(elf[n])|(unsigned(elf[n+1])<<8);};
 const auto u32=[&](std::size_t n){std::uint32_t v=0;for(unsigned k=0;k<4;++k)v|=std::uint32_t(elf[n+k])<<(k*8);return v;};
 const auto u64=[&](std::size_t n){std::uint64_t v=0;for(unsigned k=0;k<8;++k)v|=std::uint64_t(elf[n+k])<<(k*8);return v;};
 const auto bounded=[&](std::uint64_t offset,std::uint64_t bytes){return offset<=elf.size()&&bytes<=elf.size()-offset;};
 const auto shoff=u64(40),phoff=u64(32);const auto shnum=u16(60),phnum=u16(56);
 if(u16(18)!=62||u16(58)!=64||!shnum||shnum>4096||!bounded(shoff,std::uint64_t(shnum)*64)||shoff+std::uint64_t(shnum)*64!=elf.size()||u16(54)!=56||!phnum||!bounded(phoff,std::uint64_t(phnum)*56))return false;
 for(unsigned n=0;n<phnum;++n){const auto at=std::size_t(phoff)+n*56;if(!bounded(u64(at+8),u64(at+32)))return false;}
 for(unsigned n=0;n<shnum;++n){const auto at=std::size_t(shoff)+n*64;if(u32(at+4)!=8&&!bounded(u64(at+24),u64(at+32)))return false;}return true;
}
bool patch(std::vector<unsigned char>&elf,unsigned port,const std::array<unsigned char,32>&nonce,const std::vector<CollectionWriter::Pack>&packs,unsigned mode){
 if(!valid(packs)||(port&&(port<49152||port>65535))||mode>1||!validated_elf(elf))return false;
 constexpr char marker[]=PMCW_CONFIG_MARKER;std::size_t position=SIZE_MAX;
 for(std::size_t n=0;n+PMCW_CONFIG_CAPACITY<=elf.size();++n){if(std::memcmp(elf.data()+n,marker,sizeof(marker)-1))continue;if(position!=SIZE_MAX)return false;position=n;}
 if(position==SIZE_MAX)return false;
 auto*p=elf.data()+position;std::fill(p,p+PMCW_CONFIG_CAPACITY,0);std::memcpy(p,PMCW_MAGIC,8);pmcw_put32(p+8,port);pmcw_put32(p+12,mode);std::memcpy(p+16,nonce.data(),nonce.size());pmcw_put32(p+48,std::uint32_t(packs.size()));
 for(std::size_t n=0;n<packs.size();++n){auto*record=p+PMCW_CONFIG_HEADER+n*PMCW_CONFIG_RECORD;std::memcpy(record,packs[n].sha.data(),64);pmcw_put64(record+64,packs[n].bytes);}return true;
}
bool wait_socket(int fd,short event,Clock::time_point deadline){
 while(Clock::now()<deadline){pollfd p{fd,event,0};const int result=poll(&p,1,100);if(result<0){if(errno==EINTR)continue;return false;}if(!result)continue;if(p.revents&POLLNVAL){errno=EBADF;return false;}if(p.revents&POLLERR){int code=0;socklen_t length=sizeof(code);if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&code,&length))return false;errno=code?code:EIO;return false;}if(p.revents&(event|POLLHUP))return true;}errno=ETIMEDOUT;return false;
}
bool transfer(int fd,void*data,std::size_t size,bool sending,int seconds){
 auto*p=static_cast<unsigned char*>(data);const auto deadline=Clock::now()+std::chrono::seconds(seconds);
 for(std::size_t position=0;position<size;){if(!wait_socket(fd,sending?POLLOUT:POLLIN,deadline))return false;int flags=0;
#ifdef MSG_NOSIGNAL
 if(sending)flags|=MSG_NOSIGNAL;
#endif
 const auto count=sending?send(fd,p+position,size-position,flags):recv(fd,p+position,size-position,0);if(count>0){position+=std::size_t(count);continue;}if(count<0&&(errno==EINTR||errno==EAGAIN||errno==EWOULDBLOCK))continue;if(!count)errno=EPIPE;return false;}return true;
}
int connect_loopback(unsigned port){
 int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return -1;
 const auto fail=[&]{const int code=errno;close(fd);errno=code;return -1;};
#ifdef SO_NOSIGPIPE
 const int on=1;(void)setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&on,sizeof(on));
#endif
#if defined(__FreeBSD__)
 const int on_nbio=1;if(setsockopt(fd,SOL_SOCKET,0x1200,&on_nbio,sizeof(on_nbio)))return fail();
#else
 const int flags=fcntl(fd,F_GETFL,0);if(flags<0||fcntl(fd,F_SETFL,flags|O_NONBLOCK))return fail();
#endif
 timeval timeout{120,0};(void)setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));(void)setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
 sockaddr_in address{};
#if defined(__FreeBSD__)
 static_assert(sizeof(address)==16&&offsetof(sockaddr_in,sin_len)==0&&offsetof(sockaddr_in,sin_port)==2);address.sin_len=sizeof(address);
#endif
 address.sin_family=AF_INET;auto*wire=reinterpret_cast<unsigned char*>(&address.sin_port);wire[0]=unsigned(port>>8);wire[1]=unsigned(port);auto*ip=reinterpret_cast<unsigned char*>(&address.sin_addr);ip[0]=127;ip[3]=1;
 if(connect(fd,reinterpret_cast<sockaddr*>(&address),sizeof(address))){if(errno!=EINPROGRESS)return fail();if(!wait_socket(fd,POLLOUT,Clock::now()+std::chrono::seconds(2)))return fail();int code=0;socklen_t length=sizeof(code);if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&code,&length))return fail();if(code){errno=code;return fail();}}return fd;
}
bool marker_matches(const std::string&path,const std::array<unsigned char,32>&nonce){
 int fd=::open(path.c_str(),O_RDONLY|O_NOFOLLOW|O_NONBLOCK);if(fd<0)return false;struct stat info{};std::array<unsigned char,32>body{};bool ok=fstat(fd,&info)==0&&S_ISREG(info.st_mode)&&info.st_size==32;std::size_t got=0;while(ok&&got<body.size()){const auto n=read(fd,body.data()+got,body.size()-got);if(n<0&&errno==EINTR)continue;if(n<=0){ok=false;break;}got+=std::size_t(n);}const int code=errno;close(fd);errno=code;return ok&&body==nonce;
}
}
bool CollectionWriter::failure(const char*operation,int code,std::string*error){errno=code?code:EIO;error_=std::string(operation)+": "+std::strerror(errno);if(error)*error=error_;return false;}
bool CollectionWriter::ack(std::uint64_t&offset,std::string&error,int seconds){
 unsigned char bytes[PMCW_ACK_BYTES]{};if(!transfer(fd_,bytes,sizeof(bytes),false,seconds))return failure("Collection writer response",errno,&error);
 if(std::memcmp(bytes,PMCW_ACK_MAGIC,4)){
  // Log only the fixed eight-byte framing prefix, never the authentication
  // nonce or an unbounded loader/helper output stream. Do not skip banners.
  char hex[17]{},text[9]{};for(unsigned n=0;n<8;++n){std::snprintf(hex+n*2,3,"%02x",unsigned(bytes[n]));text[n]=bytes[n]>=32&&bytes[n]<127?char(bytes[n]):'.';}
  std::printf("[Museum] collection writer invalid ACK framing first8=%s ascii=%s authenticated=%d\n",hex,text,authenticated_?1:0);std::fflush(stdout);
  return failure("Invalid collection writer response",EPROTO,&error);
 }
 const auto response_pid=pmcw_get64(bytes+16);if(!response_pid||(pid_&&response_pid!=pid_))return failure("Collection writer identity changed",EPROTO,&error);
 const auto code=pmcw_get32(bytes+4);if(!pid_){std::printf("[Museum] collection writer HELLO ACK status=%u offset=%llu pid=%llu\n",unsigned(code),static_cast<unsigned long long>(pmcw_get64(bytes+8)),static_cast<unsigned long long>(response_pid));std::fflush(stdout);}if(code){const auto diagnostic=pmcw_get64(bytes+8);std::printf("[Museum] collection writer storage errno=%u stage=%u detail=%u\n",unsigned(code),unsigned(diagnostic>>32),unsigned(diagnostic&0xffffffffu));std::fflush(stdout);return failure("Collection writer storage",int(code),&error);}pid_=response_pid;offset=pmcw_get64(bytes+8);return true;
}
bool CollectionWriter::connect_session(unsigned port,const std::array<unsigned char,32>&nonce,const std::string&marker,std::string&error){
 if(port){const auto deadline=Clock::now()+std::chrono::seconds(15);do{fd_=connect_loopback(port);if(fd_>=0)break;poll(nullptr,0,100);}while(Clock::now()<deadline);}
 if(fd_<0)return failure("Collection writer unavailable",errno,&error);
 unsigned char hello[PMCW_HELLO_BYTES]{};std::memcpy(hello,PMCW_MAGIC,8);std::memcpy(hello+8,nonce.data(),nonce.size());std::uint64_t offset=0;
 if(!transfer(fd_,hello,sizeof(hello),true,5)||!ack(offset,error,5)){if(error.empty())failure("Collection writer authentication",errno,&error);close(fd_);fd_=-1;return false;}
 if(!marker_matches(marker,nonce)){close(fd_);fd_=-1;return failure("Collection writer storage is not visible to this app",EACCES,&error);}authenticated_=true;return true;
}
bool CollectionWriter::request(unsigned command,std::uint64_t value,std::uint64_t&offset,std::string&error){
 if(fd_<0||!authenticated_)return failure("Collection writer is not connected",ENOTCONN,&error);unsigned char bytes[PMCW_REQUEST_BYTES]{};std::memcpy(bytes,PMCW_REQUEST_MAGIC,4);pmcw_put32(bytes+4,command);pmcw_put64(bytes+8,value);if(!transfer(fd_,bytes,sizeof(bytes),true,5))return failure("Collection writer request",errno,&error);return ack(offset,error);
}
bool CollectionWriter::start(const std::vector<Pack>&packs,std::string&error){
 stop();error.clear();error_.clear();if(!valid(packs))return failure("Invalid collection writer pack list",EINVAL,&error);
#if defined(__FreeBSD__)
 std::array<unsigned char,34>random{};if(RAND_bytes(random.data(),int(random.size()))!=1)return failure("Cannot authenticate collection writer",EIO,&error);std::array<unsigned char,32>nonce{};std::copy_n(random.begin(),32,nonce.begin());constexpr unsigned port=0;
 std::vector<unsigned char>elf(kCollectionWriterElf,kCollectionWriterElf+kCollectionWriterElfSize);if(!patch(elf,port,nonce,packs,0))return failure("Cannot configure collection writer",EINVAL,&error);
 // elfldr consumes exactly the validated section-table end, then hands
 // this still-open connection to the helper as stdin/stdout. Never half-close.
 fd_=connect_loopback(9021);if(fd_<0)return failure("Local payload loader is unavailable",errno,&error);
 if(!transfer(fd_,elf.data(),elf.size(),true,10)){const int code=errno;close(fd_);fd_=-1;return failure("Cannot launch collection writer",code,&error);}
 char hex[65]{};for(std::size_t n=0;n<nonce.size();++n)std::snprintf(hex+n*2,3,"%02x",unsigned(nonce[n]));packs_=packs;return connect_session(port,nonce,std::string("/data/pixelmuseum/collection/.writer-session-")+hex,error);
#else
 (void)packs;return failure("Native collection writer is unavailable",ENOSYS,&error);
#endif
}
bool CollectionWriter::open(std::size_t index,std::uint64_t&offset,std::string&error){
 if(index>=packs_.size()||opened_)return failure("Invalid collection writer pack",EINVAL,&error);std::uint64_t actual=0;if(!request(PMCW_OPEN,index,actual,error))return false;if(actual>packs_[index].bytes)return failure("Invalid collection writer resume offset",EPROTO,&error);offset=offset_=actual;expected_=packs_[index].bytes;opened_=true;return true;
}
std::ptrdiff_t CollectionWriter::write(const void*data,std::size_t bytes){
 if(!opened_||!data||!bytes||bytes>PMCW_MAX_DATA||offset_>expected_||bytes>expected_-offset_){failure("Invalid collection writer block",EINVAL);return -1;}unsigned char header[PMCW_REQUEST_BYTES]{};std::memcpy(header,PMCW_REQUEST_MAGIC,4);pmcw_put32(header+4,PMCW_DATA);pmcw_put64(header+8,bytes);std::string error;std::uint64_t offset=0;
 if(!transfer(fd_,header,sizeof(header),true,5)||!transfer(fd_,const_cast<void*>(data),bytes,true,120)){failure("Collection writer transfer",errno);return -1;}if(!ack(offset,error)||offset!=offset_+bytes){if(error.empty())failure("Invalid collection writer write offset",EPROTO);return -1;}offset_=offset;return std::ptrdiff_t(bytes);
}
bool CollectionWriter::finish(std::string&error){if(!opened_)return failure("No collection writer pack is open",EINVAL,&error);std::uint64_t offset=0;if(!request(PMCW_FINISH,0,offset,error))return false;opened_=false;if(offset!=offset_)return failure("Invalid collection writer durable offset",EPROTO,&error);return true;}
bool CollectionWriter::remove_downloaded(std::string&error){
 if(opened_)return failure("A collection pack is still open",EBUSY,&error);
 std::uint64_t removed=0;if(!request(PMCW_REMOVE,0,removed,error))return false;
 if(removed)return failure("Invalid collection removal acknowledgement",EPROTO,&error);return true;
}
void CollectionWriter::stop(){if(fd_>=0){if(authenticated_){unsigned char bytes[PMCW_REQUEST_BYTES]{};std::memcpy(bytes,PMCW_REQUEST_MAGIC,4);pmcw_put32(bytes+4,PMCW_QUIT);(void)transfer(fd_,bytes,sizeof(bytes),true,2);}shutdown(fd_,SHUT_RDWR);close(fd_);}fd_=-1;authenticated_=opened_=false;pid_=offset_=expected_=0;packs_.clear();}
CollectionWriter::~CollectionWriter(){stop();}
#ifdef MUSEUM_COLLECTION_WRITER_TEST
bool CollectionWriter::attach_for_test(unsigned port,const std::array<unsigned char,32>&nonce,const std::string&marker,const std::vector<Pack>&packs,std::string&error){stop();if(!valid(packs))return failure("Invalid test packs",EINVAL,&error);packs_=packs;return connect_session(port,nonce,marker,error);}
bool CollectionWriter::attach_fd_for_test(int fd,const std::array<unsigned char,32>&nonce,const std::string&marker,const std::vector<Pack>&packs,std::string&error){stop();if(!valid(packs))return failure("Invalid test packs",EINVAL,&error);fd_=fd;const int flags=fcntl(fd_,F_GETFL,0);if(flags<0||fcntl(fd_,F_SETFL,flags|O_NONBLOCK))return failure("Test channel flags",errno,&error);packs_=packs;return connect_session(0,nonce,marker,error);}
bool CollectionWriter::patch_for_test(std::vector<unsigned char>&elf,unsigned port,const std::array<unsigned char,32>&nonce,const std::vector<Pack>&packs,unsigned mode){return patch(elf,port,nonce,packs,mode);}
#endif
}
#else
namespace museum {
CollectionWriter::~CollectionWriter()=default;bool CollectionWriter::start(const std::vector<Pack>&,std::string&error){error_=error="Native collection writer is unavailable";errno=ENOSYS;return false;}bool CollectionWriter::open(std::size_t,std::uint64_t&,std::string&error){return start({},error);}std::ptrdiff_t CollectionWriter::write(const void*,std::size_t){errno=ENOSYS;return -1;}bool CollectionWriter::finish(std::string&error){return start({},error);}bool CollectionWriter::remove_downloaded(std::string&error){return start({},error);}void CollectionWriter::stop(){}
}
#endif
