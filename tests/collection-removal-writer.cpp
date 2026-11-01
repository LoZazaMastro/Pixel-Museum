// Native-removal transport contract, exercised with the real separate C helper.
// All paths are temporary fixtures. No console or production collection access.
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "platform/collection_writer.hpp"
#include "platform/collection_writer_protocol.h"
#include <array>
#include <cassert>
#include <cerrno>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <poll.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

namespace fs=std::filesystem;
using Writer=museum::CollectionWriter;
namespace {
std::vector<unsigned char>read_bytes(const fs::path&path){std::ifstream f(path,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
void put(const fs::path&path,const std::string&body="fixture"){fs::create_directories(path.parent_path());std::ofstream f(path);f<<body;assert(f);}
struct Session {
    fs::path base,current,legacy,bundle;
    Writer writer;
    pid_t child=-1;
    int raw=-1;
    std::array<unsigned char,32>nonce{};
    const std::vector<Writer::Pack>packs{{std::string(64,'a'),10240}};
    Session(const fs::path&root,const char*name):base(root/name),current(base/"current/collection"),legacy(base/"legacy/collection"),bundle(base/"bundle"){
        fs::create_directories(base);for(unsigned n=0;n<nonce.size();++n)nonce[n]=n+1;
        put(base/"current/preferences.json","preferences-preserved");put(base/"current/trophies.json","trophies-preserved");
        put(base/"legacy/preferences.json","legacy-preserved");put(bundle/"assets/image.png","bundle-preserved");
        put(base/"outside/keep.bin","outside-preserved");
    }
    void populate(){
        put(current/"ready-v1/archives/pack.tar");put(current/"ready-v1/.complete.json");
        put(current/".stage-v2/assets/images/photo.png");put(current/"downloads/unfinished.tar.part");
        put(current/"media-cache/cache/photo.png");put(legacy/"old/archives/pack.tar");
        put(legacy/".stage-old/checkpoint.json");
    }
    bool launch(const fs::path&helper,std::string&error,const char*deny=nullptr,bool divergent_identity=false){
        auto binary=read_bytes(helper);assert(Writer::patch_for_test(binary,0,nonce,packs));
        const auto executable=base/"helper";{std::ofstream f(executable,std::ios::binary);f.write(reinterpret_cast<const char*>(binary.data()),binary.size());assert(f);}
        assert(chmod(executable.c_str(),divergent_identity?0755:0700)==0);int channel[2];assert(socketpair(AF_UNIX,SOCK_STREAM,0,channel)==0);
        child=fork();assert(child>=0);
        if(!child){
            // elfldr hands the SAME socket to all three standard descriptors.
            // A helper diagnostic on stderr is therefore protocol corruption.
            close(channel[0]);assert(dup2(channel[1],STDIN_FILENO)==STDIN_FILENO&&dup2(channel[1],STDOUT_FILENO)==STDOUT_FILENO&&dup2(channel[1],STDERR_FILENO)==STDERR_FILENO);close(channel[1]);
            if(divergent_identity){assert(setresgid(1,1,1)==0&&setresuid(1,2,2)==0);assert(getuid()==1&&geteuid()==2&&getgid()==1&&getegid()==1);}
            setenv("PMCW_TEST_ROOT",current.c_str(),1);setenv("PMCW_TEST_LEGACY_ROOT",legacy.c_str(),1);
            if(deny)setenv("PMCW_TEST_UNLINK_DENY_NAME",deny,1);else unsetenv("PMCW_TEST_UNLINK_DENY_NAME");
            execl(executable.c_str(),executable.c_str(),static_cast<char*>(nullptr));_exit(127);
        }
        close(channel[1]);raw=dup(channel[0]);assert(raw>=0);
        char hex[65]{};for(unsigned n=0;n<nonce.size();++n)std::snprintf(hex+n*2,3,"%02x",unsigned(nonce[n]));
        return writer.attach_fd_for_test(channel[0],nonce,(current/(std::string(".writer-session-")+hex)).string(),packs,error);
    }
    void protected_files()const{
        for(const auto&path:{base/"current/preferences.json",base/"current/trophies.json",base/"legacy/preferences.json",bundle/"assets/image.png",base/"outside/keep.bin"})assert(fs::exists(path));
    }
    void channel_ends_without_text()const{
        pollfd waiting{raw,POLLIN,0};assert(poll(&waiting,1,3000)>0);
        unsigned char byte=0;const auto count=recv(raw,&byte,1,MSG_DONTWAIT);
        assert(count==0); // REMOVE's binary ACK must be followed by clean EOF.
    }
    void finish(){writer.stop();if(raw>=0){close(raw);raw=-1;}if(child>0){int status=0;assert(waitpid(child,&status,0)==child);assert(WIFEXITED(status)||WIFSIGNALED(status));child=-1;}}
    ~Session(){finish();}
};
void exact_read(int fd,unsigned char*data,std::size_t size){while(size){pollfd waiting{fd,POLLIN,0};assert(poll(&waiting,1,3000)>0);const auto n=recv(fd,data,size,0);if(n<0&&(errno==EINTR||errno==EAGAIN))continue;assert(n>0);data+=n;size-=std::size_t(n);}}
}
int main(int argc,char**argv){
    assert(argc==2);const fs::path helper=argv[1];char temporary[]="/tmp/pmcw-removal-XXXXXX";assert(mkdtemp(temporary));const fs::path root=temporary;
    {
        Session s(root,"success");s.populate();fs::create_directory_symlink(s.base/"outside",s.current/"outside-directory-link");fs::create_symlink(s.base/"outside/keep.bin",s.current/"outside-file-link");
        std::string error;assert(s.launch(helper,error));assert(s.writer.remove_downloaded(error));
        assert(!fs::exists(s.current)&&!fs::exists(s.legacy));s.channel_ends_without_text();s.protected_files();s.finish();
    }
    {
        Session s(root,"unlink-error");s.populate();put(s.current/"deny-delete");std::string error;
        assert(s.launch(helper,error,"deny-delete"));assert(!s.writer.remove_downloaded(error));
        assert(errno==EACCES&&!error.empty()&&fs::exists(s.current/"deny-delete"));s.channel_ends_without_text();s.protected_files();s.finish();
        // A new authenticated helper can finish a previous partial removal.
        error.clear();assert(s.launch(helper,error));assert(s.writer.remove_downloaded(error));assert(!fs::exists(s.current)&&!fs::exists(s.legacy));s.channel_ends_without_text();s.protected_files();s.finish();
    }
    {
        Session s(root,"bootstrap-private-root");assert(chmod(root.c_str(),0755)==0);
        for(unsigned cycle=0;cycle<2;++cycle){
            for(const auto&tree:{s.current,s.legacy}){
                fs::create_directories(tree/"downloads");
                assert(chown(tree.parent_path().c_str(),1,1)==0&&chmod(tree.parent_path().c_str(),0770)==0);
                assert(chown(tree.c_str(),1,1)==0&&chmod(tree.c_str(),0700)==0);
                assert(chown((tree/"downloads").c_str(),1,1)==0&&chmod((tree/"downloads").c_str(),0700)==0);
            }
            std::string error;const bool connected=s.launch(helper,error,nullptr,true);
            if(!connected)std::fprintf(stderr,"Private-root bootstrap failed errno=%d error=%s\n",errno,error.c_str());
            assert(connected);
            for(const auto&path:{s.current,s.current/"downloads"}){struct stat info{};assert(stat(path.c_str(),&info)==0&&info.st_uid==1&&(info.st_mode&0777)==0770);}
            std::uint64_t offset=999;assert(s.writer.open(0,offset,error)&&offset==0);
            const std::vector<unsigned char>payload(10240,static_cast<unsigned char>(0x51+cycle));
            assert(s.writer.write(payload.data(),payload.size())==std::ptrdiff_t(payload.size()));assert(s.writer.finish(error));
            assert(read_bytes(s.current/"downloads"/(s.packs[0].sha+".tar.part"))==payload);
            assert(s.writer.remove_downloaded(error));assert(!fs::exists(s.current)&&!fs::exists(s.legacy));
            s.channel_ends_without_text();s.protected_files();s.finish();
        }
    }
    for(const bool restricted_ancestor:{false,true}){
        // Shared writer root remains accessible to the payload's group, while
        // actual app-created directories are private to uid1. Drop the Linux
        // helper's root privilege so this test cannot silently bypass DAC.
        // uid1/euid2 is a simulation; the native identity is probed separately.
        Session s(root,restricted_ancestor?"anchored-private-ownership":"app-private-ownership");
        if(restricted_ancestor)s.legacy=s.base/"helper-only/app-parent/collection";
        s.populate();put(s.legacy.parent_path()/"preferences.json","legacy-parent-preserved");
        put(s.current/"media-cache/cache/photos/private.png");put(s.legacy/"media-cache/private.bin");
        assert(chmod(root.c_str(),0755)==0);
        for(const auto&parent:{s.current.parent_path(),s.legacy.parent_path()}){assert(chown(parent.c_str(),1,1)==0&&chmod(parent.c_str(),0770)==0);}
        for(const auto&tree:{s.current,s.legacy}){
            for(const auto&entry:fs::recursive_directory_iterator(tree)){
                assert(chown(entry.path().c_str(),1,0)==0);
                assert(chmod(entry.path().c_str(),entry.is_directory()?0700:0600)==0);
            }
            assert(chown(tree.c_str(),1,1)==0&&chmod(tree.c_str(),0770)==0);
            fs::create_directories(tree/"downloads");assert(chown((tree/"downloads").c_str(),1,1)==0&&chmod((tree/"downloads").c_str(),0770)==0);
        }
        // Shared entrypoints now remain app-owned too: bootstrap must align to
        // the owner before its existing chmod, then restore the helper actor.
        if(restricted_ancestor){
            // Simulate /mnt/sandbox: only the original helper identity can
            // traverse this ancestor. The app-owned parent FD must be opened
            // before dropping euid and retained for all subsequent at-ops.
            assert(chown((s.base/"helper-only").c_str(),2,1)==0&&chmod((s.base/"helper-only").c_str(),0700)==0);
        }
        assert(chown((s.base/"outside").c_str(),3,0)==0&&chmod((s.base/"outside").c_str(),0700)==0);
        fs::create_directory_symlink(s.base/"outside",s.current/"external-link");
        std::string error;assert(s.launch(helper,error,nullptr,true));
        const bool removed=s.writer.remove_downloaded(error);
        if(!removed){std::fprintf(stderr,"Mixed ownership removal failed errno=%d error=%s\n",errno,error.c_str());}
        assert(removed);assert(!fs::exists(s.current)&&!fs::exists(s.legacy));
        assert(fs::exists(s.legacy.parent_path()/"preferences.json"));
        if(restricted_ancestor){struct stat info{};assert(stat((s.base/"helper-only").c_str(),&info)==0&&info.st_uid==2&&(info.st_mode&0777)==0700);}
        s.channel_ends_without_text();s.protected_files();s.finish();
    }
    {
        Session s(root,"root-symlink");fs::create_directory_symlink(s.base/"outside",s.current);std::string error;
        const bool attached=s.launch(helper,error);if(attached)assert(!s.writer.remove_downloaded(error));
        assert(!error.empty());s.protected_files();s.finish();
    }
    {
        Session s(root,"parent-symlink");fs::create_directory_symlink(s.base/"outside",s.base/"alias");s.current=s.base/"alias/collection";std::string error;
        const bool attached=s.launch(helper,error);if(attached)assert(!s.writer.remove_downloaded(error));
        assert(!error.empty()&&!fs::exists(s.base/"outside/collection"));s.protected_files();s.finish();
    }
    {
        Session s(root,"invalid-command-value");s.populate();std::string error;assert(s.launch(helper,error));
        unsigned char request[PMCW_REQUEST_BYTES]{};std::memcpy(request,PMCW_REQUEST_MAGIC,4);pmcw_put32(request+4,PMCW_REMOVE);pmcw_put64(request+8,1);
        assert(send(s.raw,request,sizeof(request),MSG_NOSIGNAL)==ssize_t(sizeof(request)));unsigned char ack[PMCW_ACK_BYTES]{};exact_read(s.raw,ack,sizeof(ack));
        assert(!std::memcmp(ack,PMCW_ACK_MAGIC,4)&&pmcw_get32(ack+4)==EINVAL);assert(fs::exists(s.current/"ready-v1/archives/pack.tar"));s.channel_ends_without_text();s.protected_files();s.finish();
    }
    {
        Session s(root,"disconnected-helper");s.populate();std::string error;assert(s.launch(helper,error));
        assert(kill(s.child,SIGKILL)==0);int status=0;assert(waitpid(s.child,&status,0)==s.child);s.child=-1;
        const auto start=std::chrono::steady_clock::now();assert(!s.writer.remove_downloaded(error));
        assert(!error.empty()&&std::chrono::steady_clock::now()-start<std::chrono::seconds(3));
        assert(fs::exists(s.current/"ready-v1/archives/pack.tar"));s.protected_files();s.finish();
    }
    fs::remove_all(root);
    std::puts("PASS: authenticated separate-helper bootstrap/write/finish/remove/redownload with app-owned0700 root/downloads and divergent identity; merged stdin/stdout/stderr binary ACK and clean EOF, app-private uid1 directories0700/files0600, anchored parent FDs below helper-only0700 ancestor, sibling/bundle preservation, nested symlinks, rejected root/parent links, EACCES/retry, invalid value rejection, disconnect without success or hang.");
}
