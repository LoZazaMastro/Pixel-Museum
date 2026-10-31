// Pixel Museum - The mkostemp variant needed by FFmpeg's temporary I/O.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>
int mkostemp(char *pattern, int flags)
{
    int descriptor=mkstemp(pattern);
    if (descriptor<0) return descriptor;
    if ((flags&O_CLOEXEC)!=0) (void)fcntl(descriptor,F_SETFD,FD_CLOEXEC);
    if ((flags&O_APPEND)!=0) (void)fcntl(descriptor,F_SETFL,O_APPEND);
    return descriptor;
}
