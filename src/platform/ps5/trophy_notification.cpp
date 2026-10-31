// Pixel Museum - asynchronous, optional PS5 notification transport.
// SPDX-License-Identifier: GPL-3.0-or-later
// Protocol/API findings: Porpoise by Ruben/elripalda (GPL-3.0-or-later),
// src/porpoise_notify.cpp at61f38f6079a3011abba88e8f4f1cb0ddc0ed27a8,
// itself crediting PS5SX2/Spyros and LightningMods' payload SDK sample.
// Native OS transport: direct libSceNotification when available, otherwise
// the attributed tiny embedded relay via the local ELF loader127.0.0.1:9021.
#include "platform/ps5/trophy_notification.hpp"
#include <algorithm>
#include <array>
#include <cstddef>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <thread>
#include <cerrno>
#include <cstring>
#include <limits.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <unistd.h>

#ifndef MUSEUM_TROPHY_HOST_TEST
extern "C" {
int sceKernelLoadStartModule(const char*,std::size_t,const void*,std::uint32_t,void*,int*);
int sceKernelDlsym(int,const char*,void**);
}
#endif
namespace hui::ps5 {
namespace {
#include "build/trophy_notify_relay.inc"
using Sender=int(*)(int,bool,const char*);
std::string quoted(const std::string& s){std::string out="\"";for(unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=char(c);}else if(c<32){char b[7];std::snprintf(b,sizeof b,"\\u%04x",c);out+=b;}else out+=char(c);}return out+'"';}
Sender localSender(){
#ifdef MUSEUM_TROPHY_HOST_TEST
    return nullptr;
#else
    static Sender sender=nullptr;static std::once_flag once;
    std::call_once(once,[]{
    for(const char* dir:{"/system/common/lib/","/system/priv/lib/","/system_ex/common_ex/lib/","/system_ex/priv_ex/lib/"}){
        const std::string path=std::string(dir)+"libSceNotification.sprx";
        // These four paths are trusted literals. The system loader has its
        // own namespace; a title-side POSIX stat cannot decide availability.
        std::printf("[Museum] trophy native module load attempt %s\n",path.c_str());std::fflush(stdout);
        int result=0;int handle=sceKernelLoadStartModule(path.c_str(),0,nullptr,0,nullptr,&result);
        std::printf("[Museum] trophy native module %s handle=0x%x result=0x%x\n",path.c_str(),unsigned(handle),unsigned(result));std::fflush(stdout);if(handle<0)continue;
        void* symbol=nullptr;const int resolved=sceKernelDlsym(handle,"sceNotificationSend",&symbol);
        std::printf("[Museum] trophy native symbol result=0x%x available=%d\n",unsigned(resolved),symbol!=nullptr);
        if(resolved==0&&symbol){sender=reinterpret_cast<Sender>(symbol);break;}
    }});return sender;
#endif
}
std::string timestamp(){std::time_t now=std::time(nullptr);std::tm tm{};gmtime_r(&now,&tm);char out[32];std::strftime(out,sizeof out,"%Y-%m-%dT%H:%M:%S.000Z",&tm);return out;}
bool packRelay(const std::string&json,std::vector<std::uint8_t>&elf){
    constexpr char marker[]="PORPOISE-NOTIFY-RELAY-JSON-V1";constexpr std::size_t room=16384;
    if(json.empty()||json.front()!='{'||json.size()>=room)return false;
    for(std::size_t i=0;i+room<=kNotifyRelaySize;++i){
        if(std::memcmp(kNotifyRelay+i,marker,sizeof(marker)-1)!=0)continue;
        std::size_t j=i+sizeof(marker)-1;while(j<i+room&&kNotifyRelay[j]==0)++j;
        if(j!=i+room)continue;
        elf.assign(kNotifyRelay,kNotifyRelay+kNotifyRelaySize);
        std::memcpy(elf.data()+i,json.data(),json.size());elf[i+json.size()]=0;return true;
    }
    return false;
}
// BSD/PS5 IPv4 sockaddr wire bytes: length, family, network-order port/address.
// Used by the actual connect call and by the layout regression on Linux hosts.
constexpr std::array<std::uint8_t,16> relayAddressBytes(){return {16,2,0x23,0x3d,127,0,0,1,0,0,0,0,0,0,0,0};}
bool sendRelay(const std::string&json,const std::atomic<unsigned long long>&generation,unsigned long long expected){
#ifdef MUSEUM_TROPHY_HOST_TEST
    (void)json;(void)generation;(void)expected;return false;
#else
    int fd=-1;
    const auto failure=[&](const char*stage,int error){std::printf("[Museum] trophy relay failure stage=%s fd=%d errno=%d (%s)\n",stage,fd,error,std::strerror(error));std::fflush(stdout);return false;};
    std::vector<std::uint8_t>elf;if(!packRelay(json,elf))return failure("payload",EINVAL);
    fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return failure("socket",errno);
    struct Close{int fd;~Close(){::close(fd);}}close{fd};
#ifdef SO_NOSIGPIPE
    const int on=1;if(setsockopt(fd,SOL_SOCKET,SO_NOSIGPIPE,&on,sizeof(on))!=0){
        const int error=errno;
        std::printf("[Museum] trophy relay optional SO_NOSIGPIPE fd=%d errno=%d (%s); using MSG_NOSIGNAL\n",fd,error,std::strerror(error));std::fflush(stdout);
#ifndef MSG_NOSIGNAL
        return failure("SIGPIPE-protection",error);
#endif
    }
#endif
    // Proven console_curl_nonblocking option: title fcntl may answer EINVAL.
    const int nonblocking=1;
    if(setsockopt(fd,SOL_SOCKET,0x1200,&nonblocking,sizeof(nonblocking))!=0)return failure("SO_NBIO",errno);
    using Clock=std::chrono::steady_clock;
    const auto valid=[&]{return generation.load(std::memory_order_acquire)==expected;};
    const auto wait=[&](short events,Clock::time_point deadline){
        while(valid()&&Clock::now()<deadline){pollfd p{fd,events,0};const int r=poll(&p,1,50);
            if(r>0){if(p.revents&POLLNVAL)return failure("poll-invalid-fd",EBADF);if(p.revents&POLLERR){int error=0;socklen_t length=sizeof(error);if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&length)!=0)error=errno;return failure("poll-socket",error?error:EIO);}return (p.revents&(events|POLLHUP))!=0;}
            if(r<0&&errno!=EINTR)return failure("poll",errno);
        }return false;
    };
    static_assert(sizeof(sockaddr_in)==16&&offsetof(sockaddr_in,sin_len)==0&&offsetof(sockaddr_in,sin_family)==1&&offsetof(sockaddr_in,sin_port)==2&&offsetof(sockaddr_in,sin_addr)==4);
    static_assert(AF_INET==2);
    sockaddr_in address{};const auto address_bytes=relayAddressBytes();std::memcpy(&address,address_bytes.data(),address_bytes.size());address.sin_len=sizeof(address);
    if(connect(fd,reinterpret_cast<sockaddr*>(&address),sizeof(address))!=0){
        const int error=errno;
        if(error!=EINPROGRESS)return failure("connect",error);
        if(!wait(POLLOUT,Clock::now()+std::chrono::milliseconds(500)))return failure("connect-poll",valid()?ETIMEDOUT:ECANCELED);
        int pending_error=0;socklen_t length=sizeof(pending_error);
        if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&pending_error,&length)!=0)return failure("connect-SO_ERROR",errno);
        if(pending_error!=0)return failure("connect-result",pending_error);
    }
    std::printf("[Museum] trophy relay connected fd=%d BSDlen=%u endpoint=127.0.0.1:9021\n",fd,unsigned(address.sin_len));std::fflush(stdout);
    const auto deadline=Clock::now()+std::chrono::seconds(2);
    for(std::size_t sent=0;sent<elf.size();){
        if(!valid()||Clock::now()>=deadline)return failure("send-deadline",valid()?ETIMEDOUT:ECANCELED);
        int sendflags=0;
#ifdef MSG_NOSIGNAL
        sendflags|=MSG_NOSIGNAL;
#endif
        const auto n=::send(fd,elf.data()+sent,elf.size()-sent,sendflags);
        if(n>0){sent+=std::size_t(n);continue;}
        if(n<0&&errno==EINTR)continue;
        if(n<0&&(errno==EAGAIN||errno==EWOULDBLOCK)&&wait(POLLOUT,deadline))continue;
        return failure("send",n<0?errno:EPIPE);
    }
    std::printf("[Museum] trophy relay payload sent bytes=%zu\n",elf.size());std::fflush(stdout);
    if(shutdown(fd,SHUT_WR)!=0)return failure("shutdown",errno);
    const auto finish=Clock::now()+std::chrono::seconds(5);char buffer[256];std::size_t captured=0;
    constexpr std::size_t capture_limit=32768;
    while(valid()&&Clock::now()<finish){
        if(!wait(POLLIN,finish))break;
        const auto n=recv(fd,buffer,sizeof(buffer),0);if(n==0)return true;
        if(n>0&&captured<capture_limit){
            const auto count=std::min(std::size_t(n),capture_limit-captured);
            // Loader output is diagnostic text; neutralize control bytes and
            // never use it as a printf format string or unbounded allocation.
            for(std::size_t i=0;i<count;++i){const unsigned char c=buffer[i];if(c<32&&c!='\n'&&c!='\r'&&c!='\t')buffer[i]='?';}
            std::printf("[Museum] trophy relay stdout: ");std::fwrite(buffer,1,count,stdout);std::fflush(stdout);captured+=count;
        }
        if(n<0&&errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR)return failure("recv",errno);
    }
    return failure("loader-finish",valid()?ETIMEDOUT:ECANCELED);
#endif
}

}
std::string TrophyNotifications::payload(const museum::TrophyUnlock& u,const std::string& icon,const std::string& date,const std::string& id){
    const char* sound=u.rank==museum::TrophyRank::Platinum?"psfx_platinum_trophy_toast":"psfx_trophy_toast";
    const std::string uri="/user/data/pixel-museum-notifications/"+icon.substr(icon.find_last_of('/')+1);
    return "{\"rawData\":{\"viewTemplateType\":\"InteractiveToastTemplateB\",\"channelType\":\"Trophies\",\"useCaseId\":\"IDC\",\"soundEffect\":"+quoted(sound)+",\"toastOverwriteType\":\"No\",\"isImmediate\":true,\"priority\":100,\"viewData\":{\"icon\":{\"type\":\"Url\",\"parameters\":{\"url\":"+quoted(uri)+"}},\"message\":{\"body\":"+quoted(u.title)+"},\"subMessage\":{\"body\":"+quoted(u.description)+"}}},\"createdDateTime\":"+quoted(date)+",\"localNotificationId\":"+quoted(id)+"}";
}
#ifdef MUSEUM_TROPHY_HOST_TEST
std::vector<std::uint8_t> TrophyNotifications::testRelayAddress(){const auto bytes=relayAddressBytes();return {bytes.begin(),bytes.end()};}
bool TrophyNotifications::testRelayPayload(const std::string&json,std::vector<std::uint8_t>&elf){return packRelay(json,elf);}
#endif
TrophyNotifications::~TrophyNotifications(){stop();}
bool TrophyNotifications::start(std::string directory){
    std::lock_guard<std::mutex> lock(mutex_);if(running_)return true;
    while(directory.size()>1&&directory.back()=='/')directory.pop_back();
#ifndef MUSEUM_TROPHY_HOST_TEST
    if(directory!="/data/homebrew/PPSA70421/assets/trophies/fronts")return false;
#endif
    if(directory.empty()||directory.front()!='/')return false;root_=std::move(directory);stopping_=false;
    pthread_attr_t attr;if(pthread_attr_init(&attr)!=0)return false;pthread_attr_setstacksize(&attr,256u*1024u);
    const int rc=pthread_create(&thread_,&attr,entry,this);pthread_attr_destroy(&attr);running_=rc==0;
    std::printf("[Museum] trophy native worker start=%d icon-root=%s\n",rc,root_.c_str());return running_;
}
bool TrophyNotifications::validIcon(const std::string& path,std::string* reason)const{
    const auto fail=[&](const std::string& why){if(reason)*reason=why;return false;};
    const std::string prefix=root_+"/";if(path.rfind(prefix,0)!=0)return fail("Badge path outside approved image directory");
    const auto name=path.substr(prefix.size());
    if(name.size()<5||name.size()>96||name.substr(name.size()-4)!=".png"||name.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. ")!=std::string::npos||name.find("..")!=std::string::npos||name.find('/')!=std::string::npos)
        return fail("Badge must be a direct PNG child of the approved image directory");
    // Packaged fronts are verified by the asset manifest. Never open/stat a
    // global shell path from the title UI: their namespaces differ, and the
    // SDK's privileged *at imports are not a safe availability probe here.
    return true;
}
bool TrophyNotifications::submit(const museum::TrophyUnlock& u,const std::string& icon){
    std::lock_guard<std::mutex> lock(mutex_);if(u.id.empty()||u.title.empty()||seen_.count(u.id))return false;seen_.insert(u.id);
    std::string why;
    if(!running_||stopping_){fallback_.push_back({u,icon,"Native notification worker not running"});return true;}
    if(!validIcon(icon,&why)){fallback_.push_back({u,icon,why});return true;}
    if(queue_.size()>=24){fallback_.push_back({u,icon,"Native notification queue full"});return true;}
    queue_.push_back({u,icon});wake_.notify_one();return true;
}
std::vector<TrophyNotificationFallback> TrophyNotifications::pollFallback(){std::lock_guard<std::mutex> lock(mutex_);std::vector<TrophyNotificationFallback> out;out.swap(fallback_);return out;}
void TrophyNotifications::clearPending(){
    std::lock_guard<std::mutex> lock(mutex_);generation_.fetch_add(1,std::memory_order_release);
    queue_.clear();fallback_.clear();seen_.clear();wake_.notify_all();
}
void TrophyNotifications::stop(){
    {std::lock_guard<std::mutex> lock(mutex_);if(!running_)return;stopping_=true;generation_.fetch_add(1,std::memory_order_release);wake_.notify_all();}
    pthread_join(thread_,nullptr);std::lock_guard<std::mutex> lock(mutex_);running_=false;
}
void* TrophyNotifications::entry(void* self){static_cast<TrophyNotifications*>(self)->run();return nullptr;}
void TrophyNotifications::run(){
    using Clock=std::chrono::steady_clock;
#ifdef MUSEUM_TROPHY_HOST_TEST
    auto next=Clock::now();const auto gap=std::chrono::milliseconds(0);
#else
    auto next=Clock::now()+std::chrono::seconds(8);const auto gap=std::chrono::milliseconds(6500);
#endif
    Sender sender=localSender();bool available=sender!=nullptr;
#ifdef MUSEUM_TROPHY_HOST_TEST
    sender=test_sender_;available=sender!=nullptr;
#endif
    static std::atomic<unsigned> sequence{0};
    for(;;){Item item;unsigned long long generation=0;
        {std::unique_lock<std::mutex> lock(mutex_);wake_.wait(lock,[this]{return stopping_||!queue_.empty();});
            if(stopping_){for(const auto& q:queue_)fallback_.push_back({q.unlock,q.icon,"Application closing before native notification"});queue_.clear();return;}
            const auto waiting_generation=generation_.load(std::memory_order_acquire);
            // PS5 pthread_cond_timedwait can return an unexpected code that
            // libc++ turns into an abort in this exceptions-disabled title.
            // Match range_stream.cpp: plain wait plus short unlocked sleeps.
            while(Clock::now()<next&&!stopping_&&generation_.load(std::memory_order_acquire)==waiting_generation){
                lock.unlock();std::this_thread::sleep_for(std::chrono::milliseconds(5));lock.lock();
            }
            if(stopping_||generation_.load(std::memory_order_acquire)!=waiting_generation){next=Clock::now();continue;}
            if(queue_.empty())continue;
            item=std::move(queue_.front());queue_.pop_front();generation=generation_.load(std::memory_order_acquire);}
        if(generation!=generation_.load(std::memory_order_acquire))continue;
        bool sent=false;const auto json=payload(item.unlock,item.icon,timestamp(),std::to_string(100000000ull+(static_cast<unsigned long long>(std::time(nullptr))%800000ull)*1000ull+sequence.fetch_add(1)%1000));
        if(available){int result=-1;
            if(generation!=generation_.load(std::memory_order_acquire))continue;
            std::printf("[Museum] trophy native send begin %s PNG=%s bytes=%zu\n",item.unlock.id.c_str(),item.icon.c_str(),json.size());std::fflush(stdout);
            if(json.size()<16384)result=sender(0xFE,true,json.c_str());sent=result==0;
            std::printf("[Museum] trophy native send %s result=0x%x (API acceptance only, display unverified)\n",item.unlock.id.c_str(),unsigned(result));std::fflush(stdout);if(!sent)available=false;}
        if(!sent&&generation==generation_.load(std::memory_order_acquire)){
            std::printf("[Museum] trophy native relay begin %s via loopback:9021 PNG=%s\n",item.unlock.id.c_str(),item.icon.c_str());std::fflush(stdout);
            sent=sendRelay(json,generation_,generation);
            std::printf("[Museum] trophy native relay %s transport=%d (OS display/sound unverified)\n",item.unlock.id.c_str(),sent);std::fflush(stdout);
        }
        if(!sent){std::lock_guard<std::mutex> lock(mutex_);if(generation==generation_.load(std::memory_order_acquire))fallback_.push_back({item.unlock,item.icon,"Native trophy-style notification unsupported on this system"});}
        next=Clock::now()+(sent?gap:std::chrono::milliseconds(0));
    }
}
} // namespace hui::ps5
