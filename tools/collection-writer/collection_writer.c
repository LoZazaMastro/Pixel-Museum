/* Restricted, single-session collection writer in the payload process class.
 * SPDX-License-Identifier: GPL-3.0-or-later */
#include "platform/collection_writer_protocol.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <poll.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>
#ifndef PMCW_HOST_TEST
#include <sys/syscall.h>
#endif

/* Adapted from the user-supplied Stremio native/download_writer/posix_at.hpp
 * (GPL-3.0-or-later). Payload SDK bare *_at stubs leave FreeBSD's positive
 * errno/carry unnormalized: never mistake EACCES for a file descriptor. */
#ifndef PMCW_HOST_TEST
_Static_assert(SYS_openat==499&&SYS_unlinkat==503,"Unexpected payload syscall ABI");
static long normalized_at(long number,long first,long second,long third,long fourth){
    register long fourth_argument __asm__("r10")=fourth;unsigned char failed;
    __asm__ volatile("syscall\n\tsetc %1"
        : "+a"(number),"=qm"(failed),"+d"(third)
        : "D"(first),"S"(second),"r"(fourth_argument)
        : "rcx","r11","memory","cc");
    if(!failed)return number;
    errno=number>0&&number<=INT_MAX?(int)number:EIO;return -1;
}
#endif
static int writer_openat(int directory,const char*path,int flags,mode_t permissions){
#ifdef PMCW_HOST_TEST
    return openat(directory,path,flags,permissions);
#else
    return (int)normalized_at(499,directory,(long)path,flags,permissions);
#endif
}
static int writer_unlinkat(int directory,const char*path,int flags){
#ifdef PMCW_HOST_TEST
    return unlinkat(directory,path,flags);
#else
    return (int)normalized_at(503,directory,(long)path,flags,0);
#endif
}

__attribute__((used)) volatile unsigned char g_collection_writer_config[PMCW_CONFIG_CAPACITY]=PMCW_CONFIG_MARKER;
static unsigned char buffer[PMCW_MAX_DATA];
static char hashes[PMCW_MAX_PACKS][65];
static uint64_t sizes[PMCW_MAX_PACKS];
static uint32_t pack_count,mode;
static char root[256],downloads[300],marker[400];
static int current=-1;
static int root_fd=-1,downloads_fd=-1;
static uint64_t offset,limit;
static int marker_created;
static int stdio_mode;
static const char*init_stage="config";
static char init_path[400];
static void stage(const char*operation,const char*path){init_stage=operation;snprintf(init_path,sizeof(init_path),"%s",path?path:"");}
static void init_failure(const char*category){const int error=errno;fprintf(stderr,"[CollectionWriter] %s errno=%d stage=%s path=%s uid=%u euid=%u gid=%u egid=%u\n",category,error,init_stage,init_path,(unsigned)getuid(),(unsigned)geteuid(),(unsigned)getgid(),(unsigned)getegid());}

static int exact_read(int socket,void*data,size_t size){
    unsigned char*p=data;
    while(size){struct pollfd ready={socket,POLLIN,0};int waited;do{waited=poll(&ready,1,30000);}while(waited<0&&errno==EINTR);if(waited<=0){if(!waited)errno=ETIMEDOUT;return -1;}ssize_t n=stdio_mode?read(socket,p,size):recv(socket,p,size,0);if(n<0&&errno==EINTR)continue;if(n<=0){if(!n)errno=EPIPE;return -1;}p+=n;size-=(size_t)n;}
    return 0;
}
static int write_all(int fd,const void*data,size_t size){
    const unsigned char*p=data;
    while(size){ssize_t n=write(fd,p,size);if(n<0&&errno==EINTR)continue;if(n<=0){if(!n)errno=EIO;return -1;}p+=n;size-=(size_t)n;}
    return 0;
}
static int ack(int socket,int error){
    unsigned char data[PMCW_ACK_BYTES]={0};memcpy(data,PMCW_ACK_MAGIC,4);pmcw_put32(data+4,(uint32_t)error);pmcw_put64(data+8,offset);pmcw_put64(data+16,(uint64_t)getpid());
    const int output=stdio_mode?STDOUT_FILENO:socket;
    size_t sent=0;while(sent<sizeof(data)){struct pollfd ready={output,POLLOUT,0};int waited;do{waited=poll(&ready,1,30000);}while(waited<0&&errno==EINTR);if(waited<=0){if(!waited)errno=ETIMEDOUT;return -1;}ssize_t n=stdio_mode?write(output,data+sent,sizeof(data)-sent):send(output,data+sent,sizeof(data)-sent,0);if(n<0&&errno==EINTR)continue;if(n<=0)return -1;sent+=(size_t)n;}return 0;
}
static int directory(const char*path){
    struct stat st;
    stage("mkdir",path);
    if(mkdir(path,0770)&&errno!=EEXIST)return -1;
    stage("lstat-directory",path);
    if(lstat(path,&st)||!S_ISDIR(st.st_mode)){errno=ENOTDIR;return -1;}
#ifndef PMCW_HOST_TEST
    /* elfldr retains the application's real UID, but its payload EGID can
     * differ from the title's group. Share by app owner + helper real group,
     * not by a guessed group zero or globally writable directory. */
    stage("chown-shared-owner",path);
    if(chown(path,getuid(),getgid()))return -1;
#endif
    stage("chmod-directory",path);
    return chmod(path,0770);
}
static int finish_current(void){
    if(current<0)return 0;
    int result=0,saved=0;
    if(fsync(current)){result=-1;saved=errno;}
    if(close(current)&&!result){result=-1;saved=errno;}
    current=-1;
    if(!result&&fsync(downloads_fd)){result=-1;saved=errno;}
    if(result)errno=saved;return result;
}
static int open_pack(uint64_t index){
    if(index>=pack_count){errno=EINVAL;return -1;}
    if(finish_current())return -1;
    char basename[80];snprintf(basename,sizeof(basename),"%s.tar.part",hashes[index]);
    int fd=writer_openat(downloads_fd,basename,O_WRONLY|O_CREAT|O_NOFOLLOW,0660);if(fd<0)return -1;
    struct stat st;
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_nlink!=1||st.st_size<0||(uint64_t)st.st_size>sizes[index]){int e=errno?errno:EINVAL;close(fd);errno=e;return -1;}
#ifndef PMCW_HOST_TEST
    if(fchown(fd,getuid(),getgid())){int e=errno;close(fd);errno=e;return -1;}
#endif
    if(fchmod(fd,0660)||lseek(fd,st.st_size,SEEK_SET)<0){int e=errno;close(fd);errno=e;return -1;}
    current=fd;offset=(uint64_t)st.st_size;limit=sizes[index];return 0;
}
static int config(unsigned char nonce[32],uint32_t*port){
    const unsigned char*c=(const unsigned char*)g_collection_writer_config;
    if(memcmp(c,PMCW_MAGIC,8)){errno=EINVAL;return -1;}
    *port=pmcw_get32(c+8);mode=pmcw_get32(c+12);pack_count=pmcw_get32(c+48);memcpy(nonce,c+16,32);
    if((*port&&*port<1024)||*port>65535||mode>1||!pack_count||pack_count>PMCW_MAX_PACKS){errno=EINVAL;return -1;}
    unsigned any=0;for(unsigned i=0;i<32;++i)any|=nonce[i];if(!any){errno=EINVAL;return -1;}
    for(uint32_t i=0;i<pack_count;++i){
        const unsigned char*r=c+PMCW_CONFIG_HEADER+i*PMCW_CONFIG_RECORD;
        for(unsigned j=0;j<64;++j)if(!((r[j]>='0'&&r[j]<='9')||(r[j]>='a'&&r[j]<='f'))){errno=EINVAL;return -1;}
        memcpy(hashes[i],r,64);hashes[i][64]=0;sizes[i]=pmcw_get64(r+64);
        if(!sizes[i]||sizes[i]>PMCW_MAX_PACK_BYTES){errno=EINVAL;return -1;}
        for(uint32_t j=0;j<i;++j)if(!strcmp(hashes[i],hashes[j])){errno=EINVAL;return -1;}
    }
    char hex[65];for(unsigned i=0;i<32;++i)snprintf(hex+2*i,3,"%02x",nonce[i]);
#ifdef PMCW_HOST_TEST
    const char*test_root=getenv("PMCW_TEST_ROOT");if(!test_root||strlen(test_root)>220||mode!=1){errno=EINVAL;return -1;}
    snprintf(root,sizeof(root),"%s",test_root);
#else
    if(mode)snprintf(root,sizeof(root),"/data/pixel-museum-writer-probe-%s",hex);
    else snprintf(root,sizeof(root),"/data/pixelmuseum/collection");
    if(!mode&&directory("/data/pixelmuseum"))return -1;
#endif
    if(directory(root))return -1;
    snprintf(downloads,sizeof(downloads),"%s/downloads",root);if(directory(downloads))return -1;
    stage("open-root",root);root_fd=open(root,O_RDONLY|O_DIRECTORY|O_NOFOLLOW);if(root_fd<0)return -1;
    stage("open-downloads",downloads);downloads_fd=writer_openat(root_fd,"downloads",O_RDONLY|O_DIRECTORY|O_NOFOLLOW,0);if(downloads_fd<0){close(root_fd);root_fd=-1;return -1;}
    snprintf(marker,sizeof(marker),"%s/.writer-session-%s",root,hex);return 0;
}
static int publish_marker(const unsigned char nonce[32]){
    stage("open-marker",marker);
    int fd=writer_openat(root_fd,strrchr(marker,'/')+1,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0660);if(fd<0)return -1;
    marker_created=1;int rc=0,saved=0;
#ifndef PMCW_HOST_TEST
    stage("chown-marker",marker);if(fchown(fd,getuid(),getgid())){rc=-1;saved=errno;}
#endif
    stage("write-sync-marker",marker);
    if(!rc&&(fchmod(fd,0660)||write_all(fd,nonce,32)||fsync(fd))){rc=-1;saved=errno;}
    if(close(fd)&&!rc){rc=-1;saved=errno;}
    stage("sync-root",root);if(!rc&&fsync(root_fd)){rc=-1;saved=errno;}
    if(rc)errno=saved;return rc;
}
static void cleanup(void){
    (void)finish_current();
    if(marker_created)(void)writer_unlinkat(root_fd,strrchr(marker,'/')+1,0);
    if(mode==1){
        for(uint32_t i=0;i<pack_count;++i){char basename[80];snprintf(basename,sizeof(basename),"%s.tar.part",hashes[i]);(void)writer_unlinkat(downloads_fd,basename,0);}
        (void)writer_unlinkat(root_fd,"downloads",AT_REMOVEDIR);(void)rmdir(root);
    }
    if(downloads_fd>=0){close(downloads_fd);downloads_fd=-1;}if(root_fd>=0){close(root_fd);root_fd=-1;}
}
int main(void){
    signal(SIGPIPE,SIG_IGN);unsigned char nonce[32];uint32_t port=0;
    if(config(nonce,&port)){init_failure("config");return 1;}
    stdio_mode=port==0;int client=STDIN_FILENO;
    if(stdio_mode){if(publish_marker(nonce)){init_failure("marker");cleanup();return 3;}}
    else{
    int listener=socket(AF_INET,SOCK_STREAM,0);if(listener<0){cleanup();return 2;}
    struct sockaddr_in address;memset(&address,0,sizeof(address));
#ifndef PMCW_HOST_TEST
    address.sin_len=sizeof(address);
#endif
    address.sin_family=AF_INET;address.sin_port=htons((uint16_t)port);address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
    if(bind(listener,(struct sockaddr*)&address,sizeof(address))||listen(listener,1)||publish_marker(nonce)){fprintf(stderr,"[CollectionWriter] listen/marker errno=%d\n",errno);close(listener);cleanup();return 3;}
    struct pollfd pending={listener,POLLIN,0};int waited;do{waited=poll(&pending,1,30000);}while(waited<0&&errno==EINTR);
    if(waited<=0){close(listener);cleanup();return 4;}
    struct sockaddr_in peer;socklen_t peer_size=sizeof(peer);client=accept(listener,(struct sockaddr*)&peer,&peer_size);close(listener);
    if(client<0||peer.sin_addr.s_addr!=htonl(INADDR_LOOPBACK)){if(client>=0)close(client);cleanup();return 5;}
    struct timeval timeout={30,0};(void)setsockopt(client,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));(void)setsockopt(client,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
    }
    unsigned char hello[PMCW_HELLO_BYTES];
    if(exact_read(client,hello,sizeof(hello))||memcmp(hello,PMCW_MAGIC,8)||memcmp(hello+8,nonce,32)){(void)ack(client,EACCES);close(client);cleanup();return 6;}
    if(ack(client,0)){close(client);cleanup();return 7;}
    uint64_t budget=0,accepted=0;for(uint32_t i=0;i<pack_count;++i)budget+=sizes[i];budget*=2;
    const time_t started=time(NULL);int result=0;
    for(unsigned commands=0;commands<2000000u;++commands){
        unsigned char request[PMCW_REQUEST_BYTES];if(exact_read(client,request,sizeof(request)))break;
        if(time(NULL)-started>6*60*60||memcmp(request,PMCW_REQUEST_MAGIC,4)){(void)ack(client,EPROTO);result=8;break;}
        uint32_t command=pmcw_get32(request+4);uint64_t value=pmcw_get64(request+8);int error=0;
        if(command==PMCW_OPEN){if(open_pack(value))error=errno;}
        else if(command==PMCW_DATA){
            if(current<0||!value||value>PMCW_MAX_DATA||value>limit-offset||value>budget-accepted){(void)ack(client,EINVAL);result=9;break;}
            /* TCP segmentation must not become tiny filesystem writes. A DATA
             * frame is bounded at 2 MiB and is assembled before any write. A
             * truncated frame leaves the previously acknowledged prefix intact. */
            if(exact_read(client,buffer,(size_t)value))error=errno;
            else{size_t at=0;while(at<(size_t)value){ssize_t done=write(current,buffer+at,(size_t)value-at);if(done<0&&errno==EINTR)continue;if(done<=0){error=done<0?errno:EIO;break;}at+=(size_t)done;offset+=(uint64_t)done;accepted+=(uint64_t)done;}}
        }
        else if(command==PMCW_FINISH){if(value)error=EINVAL;else if(finish_current())error=errno;}
        else if(command==PMCW_QUIT){if(value)error=EINVAL;else if(finish_current())error=errno;(void)ack(client,error);result=error?10:0;break;}
        else error=EINVAL;
        if(ack(client,error)||error){result=11;break;}
    }
    close(client);cleanup();return result;
}
