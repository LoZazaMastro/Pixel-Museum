// Small CRT compatibility bridge for the shared POSIX-based file helpers.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#if defined(_WIN32)
#include <direct.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <cstdio>
#include <cerrno>
#include <mutex>
#include <algorithm>
inline int mkdir(const char* path, int) { return ::_mkdir(path); }
inline int fsync(int fd) { return ::_commit(fd); }
inline long long pread(int fd, void* bytes, std::size_t count, long long offset) {
    static std::mutex mutex;
    std::lock_guard lock(mutex);
    const auto previous=::_lseeki64(fd,0,SEEK_CUR);
    if(previous<0||::_lseeki64(fd,offset,SEEK_SET)<0)return -1;
    const int result=::_read(fd,bytes,static_cast<unsigned>(std::min<std::size_t>(count,0x7fffffff)));
    const int saved=errno;::_lseeki64(fd,previous,SEEK_SET);errno=saved;
    return result;
}
#ifndef O_NOFOLLOW
#define O_NOFOLLOW 0
#endif
#ifndef O_NONBLOCK
#define O_NONBLOCK 0
#endif
#ifndef O_DIRECTORY
#define O_DIRECTORY 0
#endif
#ifndef EDQUOT
#define EDQUOT ENOSPC
#endif
#endif
