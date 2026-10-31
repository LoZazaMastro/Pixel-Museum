/* Porpoise - the notification relay: a tiny payload that posts one PS5 toast.
 *
 * Porpoise's own process can't load libSceNotification on recent firmware
 * (the system refuses the module), so the trophy-style popups go through the
 * jailbreak's ELF loader: Porpoise (src/porpoise_notify.cpp) writes the
 * toast's JSON over g_payload's marker in a copy of this program and sends it
 * to 127.0.0.1:9021, where the loader runs it as a process of its own.
 *
 * The approach and its findings (logged toasts only, the 3 s wait, _exit) are
 * PS5SX2's (Spyros, ps5/coreorbis/notify-relay/notify_relay.c, GPL-3.0-or-later).
 * Copyright (C) 2026 Ruben (Project Porpoise)
 * SPDX-License-Identifier: GPL-3.0-or-later */

#include <stdbool.h>
#include <unistd.h>
#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>

int sceNotificationSend(int userId, bool isLogged, const char *payload);

/* Initialized, so the whole array is in the file: the room Porpoise fills.
 * volatile: what Porpoise wrote is read, not the marker seen here. */
__attribute__((used)) volatile char g_payload[16384] = "PORPOISE-NOTIFY-RELAY-JSON-V1";

/* Bounded, append-only diagnostic; no saves or trophy state are changed. */
static void relay_record(const char *stage, int result)
{
    char line[256];
    const int saved_errno = errno;
    const int size = snprintf(line, sizeof line,
        "[MuseumRelay] time=%lld pid=%d stage=%s rc=0x%x errno=%d\n",
        (long long)time(NULL), (int)getpid(), stage, (unsigned)result, saved_errno);
    if (size > 0 && size < (int)sizeof line) {
        fputs(line, stdout); fflush(stdout);
        const int fd = open("/data/homebrew/PPSA70421/trophy-notify-relay.log",
                            O_WRONLY | O_CREAT | O_APPEND, 0644);
        if (fd >= 0) { (void)write(fd, line, (size_t)size); (void)fsync(fd); close(fd); }
        else { printf("[MuseumRelay] persistent-log-open errno=%d\n", errno); fflush(stdout); }
    }
    errno = saved_errno;
}

/* Stage only this application's known badge basename in the ShellUI-readable
 * namespace. A fresh install needs no external FTP copy of notification icons. */
#define ICON_DIRECTORY "/user/data/pixel-museum-notifications"
#define PRIMARY_ICON_SOURCE "/user/data/homebrew/PPSA70421/assets/trophies/notifications/"
#define FALLBACK_ICON_SOURCE "/data/homebrew/PPSA70421/assets/trophies/notifications/"
static int stage_icon_for_payload(const char *payload)
{
    const char *prefix = ICON_DIRECTORY "/";
    const char *at = strstr(payload, prefix);
    if (!at) { errno = EINVAL; return -1; }
    at += strlen(prefix);
    char badge[97]; size_t length = 0;
    while (at[length] && at[length] != '"' && length < sizeof(badge)-1) {
        badge[length] = at[length]; ++length;
    }
    badge[length] = 0;
    if (at[length] != '"' || length < 5 || strcmp(badge+length-4,".png") != 0) { errno=EINVAL; return -1; }
    for (size_t i=0; i<length-4; ++i)
        if (!((badge[i]>='a'&&badge[i]<='z')||(badge[i]>='0'&&badge[i]<='9')||badge[i]=='_')) { errno=EINVAL; return -1; }
    struct stat directory;
    if (mkdir(ICON_DIRECTORY,0755) != 0 && errno != EEXIST) return -1;
    if (lstat(ICON_DIRECTORY,&directory) != 0 || !S_ISDIR(directory.st_mode)) { errno=ENOTDIR; return -1; }
    int source=-1; char source_path[256];
    const char *sources[]={PRIMARY_ICON_SOURCE,FALLBACK_ICON_SOURCE};
    for (unsigned i=0;i<2;++i) {
        snprintf(source_path,sizeof(source_path),"%s%s",sources[i],badge);
        int flags=O_RDONLY;
#ifdef O_NOFOLLOW
        flags|=O_NOFOLLOW;
#endif
        source=open(source_path,flags);
        if(source>=0)break;
    }
    if(source<0)return -1;
    struct stat info;
    if(fstat(source,&info)!=0||!S_ISREG(info.st_mode)||info.st_size<=0||info.st_size>1024*1024){int e=errno?errno:EINVAL;close(source);errno=e;return -1;}
    char target[256],temporary[256];
    snprintf(target,sizeof(target),"%s/%s",ICON_DIRECTORY,badge);
    snprintf(temporary,sizeof(temporary),"%s/.%s.%d.tmp",ICON_DIRECTORY,badge,(int)getpid());
    int destination=open(temporary,O_WRONLY|O_CREAT|O_EXCL,0644);
    if(destination<0){int e=errno;close(source);errno=e;return -1;}
    int result=0,saved=0;size_t total=0;char buffer[8192];
    for(;;){
        ssize_t n=read(source,buffer,sizeof(buffer));
        if(n<0&&errno==EINTR)continue;
        if(n<0){result=-1;saved=errno;break;}
        if(n==0)break;
        total+=(size_t)n;if(total>1024*1024){result=-1;saved=EFBIG;break;}
        for(ssize_t offset=0;offset<n;){ssize_t done=write(destination,buffer+offset,(size_t)(n-offset));if(done<0&&errno==EINTR)continue;if(done<=0){result=-1;saved=done<0?errno:EIO;break;}offset+=done;}
        if(result)break;
    }
    if(!result&&total!=(size_t)info.st_size){result=-1;saved=EIO;}
    if(!result&&fsync(destination)!=0){result=-1;saved=errno;}
    if(close(destination)!=0&&!result){result=-1;saved=errno;}
    close(source);
    if(!result&&rename(temporary,target)!=0){result=-1;saved=errno;}
    if(result)unlink(temporary);
    if(result)errno=saved;
    return result;
}

int main(void)
{
    relay_record("entry", 0);
    if (g_payload[0] != '{') { relay_record("invalid-payload", 1); return 1; }
    if (stage_icon_for_payload((const char *)g_payload) != 0) { relay_record("icon-stage-failed", -1); _exit(4); }
    relay_record("icon-staged", 0);
    relay_record("native-begin", 0);
    /* 0xFE: the system user. Only a toast kept in the notification list shows. */
    const int rc = sceNotificationSend(0xFE, true, (const char *)g_payload);
    relay_record("native-result", rc);
    /* The library posts from a thread of its own: give it time, then end
     * without unloading anything under it. */
    sleep(3);
    relay_record("complete", rc);
    _exit(rc == 0 ? 0 : 2);
}
