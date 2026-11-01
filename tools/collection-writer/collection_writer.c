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
#include <stddef.h>
#include <dirent.h>
#include <sys/syscall.h>

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
    const char*denied=getenv("PMCW_TEST_UNLINK_DENY_NAME");
    if(denied&&!strcmp(path,denied)){errno=EACCES;return -1;}
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
static int collection_removed;
/* elfldr connects both stdout and stderr to the binary protocol socket.
 * Default to a silent channel even before configuration has been validated. */
static int stdio_mode=1;
/* Binary-only removal diagnostics: high32=stage, low32=bounded detail. */
static uint32_t removal_stage,removal_detail;
static const char*init_stage="config";
static char init_path[400];
static void stage(const char*operation,const char*path){init_stage=operation;snprintf(init_path,sizeof(init_path),"%s",path?path:"");}
static void init_failure(const char*category){const int error=errno;if(!stdio_mode)fprintf(stderr,"[CollectionWriter] %s errno=%d stage=%s path=%s uid=%u euid=%u gid=%u egid=%u\n",category,error,init_stage,init_path,(unsigned)getuid(),(unsigned)geteuid(),(unsigned)getgid(),(unsigned)getegid());errno=error;}

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
    unsigned char data[PMCW_ACK_BYTES]={0};memcpy(data,PMCW_ACK_MAGIC,4);pmcw_put32(data+4,(uint32_t)error);pmcw_put64(data+8,error&&removal_stage?((uint64_t)removal_stage<<32)|removal_detail:offset);pmcw_put64(data+16,(uint64_t)getpid());
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
/* All destructive work stays in the existing restricted payload process.
 * App eboots cannot safely execute the payload SDK's raw syscall stubs. */
struct removal_work {uint64_t entries;time_t deadline;};
static char removal_targets[18][512];
static int target_parent(const char*path,int*descriptor,char leaf[256]){
    removal_stage=10;removal_detail=path?(uint32_t)strlen(path):0;
    if(!path||path[0]!='/'||strlen(path)>=512||strchr(path,'\\')){errno=EINVAL;return -1;}
    int fd=open("/",O_RDONLY|O_DIRECTORY|O_NOFOLLOW);if(fd<0)return -1;
    const char*part=path+1;
    for(;;){
        const char*slash=strchr(part,'/');const size_t length=slash?(size_t)(slash-part):strlen(part);
        if(!length||length>=256){close(fd);errno=EINVAL;return -1;}
        memcpy(leaf,part,length);leaf[length]=0;
        if(!strcmp(leaf,".")||!strcmp(leaf,"..")){close(fd);errno=EINVAL;return -1;}
        if(!slash){*descriptor=fd;return 0;}
        int next=writer_openat(fd,leaf,O_RDONLY|O_DIRECTORY|O_NOFOLLOW,0);
        if(next<0){const int code=errno;close(fd);errno=code;return code==ENOENT?1:-1;}
        close(fd);fd=next;part=slash+1;
    }
}
static int removal_probe_at(int parent,const char*leaf){
    removal_stage=20;removal_detail=0;int fd=writer_openat(parent,leaf,O_RDONLY|O_DIRECTORY|O_NOFOLLOW,0);
    if(fd<0)return errno==ENOENT?0:-1;return close(fd);
}
static int removal_probe(const char*path){
    int parent=-1;char leaf[256];const int found=target_parent(path,&parent,leaf);if(found)return found>0?0:-1;
    const int result=removal_probe_at(parent,leaf),code=errno;close(parent);errno=code;return result;
}
/* Native controls proved fdopendir/readdir on a duplicate descriptor; the
 * public/raw getdents entry points return EINVAL on this PS5 filesystem. */
static DIR*removal_stream(int fd){
    removal_stage=30;removal_detail=0;int copy=dup(fd);if(copy<0)return NULL;
    removal_stage=31;removal_detail=0;DIR*stream=fdopendir(copy);
    if(!stream){const int code=errno?errno:EIO;close(copy);errno=code;}return stream;
}
static int remove_contents(int fd,unsigned depth,struct removal_work*work){
    if(depth>64){errno=EOVERFLOW;return -1;}
    DIR*stream=removal_stream(fd);if(!stream)return -1;int result=0,code=0;
    for(;;){
        if(time(NULL)>work->deadline){result=-1;code=ETIMEDOUT;break;}
        removal_stage=32;removal_detail=depth;errno=0;struct dirent*entry=readdir(stream);
        if(!entry){if(errno==EINTR)continue;if(errno){result=-1;code=errno;}break;}
        if(!entry->d_ino)continue;char name[256];const size_t length=strnlen(entry->d_name,sizeof(name));
        removal_stage=35;removal_detail=(uint32_t)length;
        if(!length||length>=sizeof(name)||strchr(entry->d_name,'/')){result=-1;code=EINVAL;break;}
        memcpy(name,entry->d_name,length+1);if(!strcmp(name,".")||!strcmp(name,".."))continue;
        if(++work->entries>1000000){result=-1;code=EOVERFLOW;break;}
        removal_stage=36;removal_detail=depth;int child=writer_openat(fd,name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW,0);
        if(child<0){
            const int error=errno;if(error==ENOENT)continue;if(error!=ENOTDIR&&error!=ELOOP){result=-1;code=error;break;}
            removal_stage=40;removal_detail=depth;if(writer_unlinkat(fd,name,0)&&errno!=ENOENT){result=-1;code=errno;break;}
        }else{
            const int removed=remove_contents(child,depth+1,work),error=errno;const int closed=close(child);
            if(removed){result=-1;code=error;break;}if(closed){result=-1;code=errno;break;}
            removal_stage=41;removal_detail=depth;if(writer_unlinkat(fd,name,AT_REMOVEDIR)&&errno!=ENOENT){result=-1;code=errno;break;}
        }
    }
    if(closedir(stream)&&!result){removal_stage=39;result=-1;code=errno?errno:EIO;}errno=code;return result;
}
static int remove_target_at(int parent,const char*leaf,struct removal_work*work){
    int fd=writer_openat(parent,leaf,O_RDONLY|O_DIRECTORY|O_NOFOLLOW,0);
    if(fd<0)return errno==ENOENT?0:-1;
    int result=remove_contents(fd,0,work),code=errno;
    if(close(fd)&&!result){result=-1;code=errno;}
    if(!result){removal_stage=42;removal_detail=0;if(writer_unlinkat(parent,leaf,AT_REMOVEDIR)&&errno!=ENOENT){result=-1;code=errno;}}
    if(!result){removal_stage=50;removal_detail=0;if(fsync(parent)){result=-1;code=errno;}}
    errno=code;return result;
}
static int add_removal_target(unsigned*count,const char*path){
    if(*count>=18||!path||strlen(path)>=sizeof(removal_targets[0])){errno=EOVERFLOW;return -1;}
    for(unsigned n=0;n<*count;++n)if(!strcmp(removal_targets[n],path))return 0;
    snprintf(removal_targets[(*count)++],sizeof(removal_targets[0]),"%s",path);return 0;
}
#ifndef PMCW_HOST_TEST
static int sandbox_removal_targets(unsigned*count){
    int fd=open("/mnt/sandbox",O_RDONLY|O_DIRECTORY|O_NOFOLLOW);if(fd<0)return errno==ENOENT?0:-1;
    DIR*stream=removal_stream(fd);if(!stream){const int code=errno;close(fd);errno=code;return -1;}
    int result=0,code=0;unsigned checked=0;
    for(;;){
        removal_stage=32;removal_detail=0;errno=0;struct dirent*entry=readdir(stream);
        if(!entry){if(errno==EINTR)continue;if(errno){result=-1;code=errno;}break;}
        if(++checked>10000){result=-1;code=EOVERFLOW;break;}
        const char*name=entry->d_name;const size_t length=strnlen(name,256);const char prefix[]="PPSA70421_";
        if(length>=256){result=-1;code=EIO;break;}if(strncmp(name,prefix,sizeof(prefix)-1))continue;
        const char*suffix=name+sizeof(prefix)-1;const size_t digits=length-(sizeof(prefix)-1);
        if(!digits||digits>6)continue;size_t n=0;while(n<digits&&suffix[n]>='0'&&suffix[n]<='9')++n;if(n!=digits)continue;
        char path[512];snprintf(path,sizeof(path),"/mnt/sandbox/%s/download0/pixelmuseum/collection",name);
        if(add_removal_target(count,path)){result=-1;code=errno;break;}
    }
    if(closedir(stream)&&!result){result=-1;code=errno?errno:EIO;}
    if(close(fd)&&!result){result=-1;code=errno;}errno=code;return result;
}
#endif
/* Retain parent capabilities before dropping the loader identity. The global
 * sandbox ancestor is not searchable by UID1; each owned mount parent is. */
struct removal_plan {unsigned count;int parent[18];char leaf[18][256];};
static int close_removal_plan(struct removal_plan*plan){
    int code=0;for(unsigned n=0;n<plan->count;++n)if(plan->parent[n]>=0){if(close(plan->parent[n])&&!code)code=errno?errno:EIO;plan->parent[n]=-1;}
    if(code){errno=code;return -1;}return 0;
}
static int prepare_removal_parents(struct removal_plan*plan,unsigned count){
    plan->count=count;for(unsigned n=0;n<count;++n)plan->parent[n]=-1;
    for(unsigned n=0;n<count;++n){
        const int found=target_parent(removal_targets[n],&plan->parent[n],plan->leaf[n]);
        if(found<0){const int code=errno;close_removal_plan(plan);errno=code;return -1;}
    }
    return 0;
}
static int check_removal_plan(const struct removal_plan*plan){
    for(unsigned n=0;n<plan->count;++n)if(plan->parent[n]>=0&&removal_probe_at(plan->parent[n],plan->leaf[n]))return -1;
    return 0;
}
/* elfldr preserves the title's real UID while using a different effective
 * identity. Use the actual app owner for its private0700 collection folders;
 * this one-shot REMOVE path never changes existing ownership or modes. */
static int removal_owner_identity(void){
    const uid_t owner=getuid();const gid_t group=getgid();
    removal_stage=60;removal_detail=(uint32_t)group;errno=0;int result=setegid(group);
    if(result){if(!errno)errno=result>0?result:EIO;return -1;}
    if(getegid()!=group){errno=EACCES;return -1;}
    removal_stage=61;removal_detail=(uint32_t)owner;errno=0;result=seteuid(owner);
    if(result){if(!errno)errno=result>0?result:EIO;return -1;}
    if(getuid()!=owner||geteuid()!=owner||getgid()!=group||getegid()!=group){errno=EACCES;return -1;}
    return 0;
}
static int remove_downloaded(void){
    if(current>=0){errno=EBUSY;return -1;}
    unsigned count=0;if(add_removal_target(&count,root))return -1;
#ifdef PMCW_HOST_TEST
    const char*legacy=getenv("PMCW_TEST_LEGACY_ROOT");if(legacy&&*legacy&&add_removal_target(&count,legacy))return -1;
#else
    if(!mode&&(add_removal_target(&count,"/download0/pixelmuseum/collection")||sandbox_removal_targets(&count)))return -1;
#endif
    struct removal_plan plan;if(prepare_removal_parents(&plan,count))return -1;
    if(removal_owner_identity()||check_removal_plan(&plan)){const int code=errno;close_removal_plan(&plan);errno=code;return -1;}
    if(downloads_fd>=0){close(downloads_fd);downloads_fd=-1;}if(root_fd>=0){close(root_fd);root_fd=-1;}
    if(!stdio_mode){fprintf(stderr,"[CollectionWriter] removal begin roots=%u\n",count);fflush(stderr);}
    struct removal_work work={0,time(NULL)+90};
    for(unsigned n=0;n<count;++n)if(plan.parent[n]>=0&&remove_target_at(plan.parent[n],plan.leaf[n],&work)){const int code=errno;close_removal_plan(&plan);if(!stdio_mode){fprintf(stderr,"[CollectionWriter] removal failed target=%u errno=%d entries=%llu\n",n,code,(unsigned long long)work.entries);fflush(stderr);}errno=code;return -1;}
    if(close_removal_plan(&plan))return -1;
    marker_created=0;collection_removed=1;offset=0;
    if(!stdio_mode){fprintf(stderr,"[CollectionWriter] removal complete entries=%llu\n",(unsigned long long)work.entries);fflush(stderr);}return 0;
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
static int config_as_owner(unsigned char nonce[32],uint32_t*port){
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
    if(removal_probe(root)||directory(root))return -1;
    snprintf(downloads,sizeof(downloads),"%s/downloads",root);if(directory(downloads))return -1;
    stage("open-root",root);root_fd=open(root,O_RDONLY|O_DIRECTORY|O_NOFOLLOW);if(root_fd<0)return -1;
    stage("open-downloads",downloads);downloads_fd=writer_openat(root_fd,"downloads",O_RDONLY|O_DIRECTORY|O_NOFOLLOW,0);if(downloads_fd<0){close(root_fd);root_fd=-1;return -1;}
    snprintf(marker,sizeof(marker),"%s/.writer-session-%s",root,hex);return 0;
}
static int config(unsigned char nonce[32],uint32_t*port){
    const uid_t real_uid=getuid(),previous_uid=geteuid();const gid_t real_gid=getgid(),previous_gid=getegid();
    int result=removal_owner_identity(),code=errno;
    if(!result){result=config_as_owner(nonce,port);code=errno;}
    /* Appmkdirs can recreate the owned roots0700. Open/normalize only those
     * existing writer roots as their owner, then retain the proven loader
     * identity for HELLO/downloads and preopening sandbox parent handles. */
    errno=0;int restored=seteuid(previous_uid),restore_error=restored?(errno?errno:restored>0?restored:EIO):0;
    errno=0;restored=setegid(previous_gid);if(restored&&!restore_error)restore_error=errno?errno:restored>0?restored:EIO;
    if(restore_error||getuid()!=real_uid||getgid()!=real_gid||geteuid()!=previous_uid||getegid()!=previous_gid){stage("restore-writer-identity",root);errno=restore_error?restore_error:EACCES;return -1;}
    errno=code;return result;
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
    if(collection_removed)return;
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
        else if(command==PMCW_REMOVE){removal_stage=1;removal_detail=(uint32_t)value;if(value)error=EINVAL;else if(remove_downloaded())error=errno;(void)ack(client,error);result=error?12:0;break;}
        else if(command==PMCW_QUIT){if(value)error=EINVAL;else if(finish_current())error=errno;(void)ack(client,error);result=error?10:0;break;}
        else error=EINVAL;
        if(ack(client,error)||error){result=11;break;}
    }
    close(client);cleanup();return result;
}
