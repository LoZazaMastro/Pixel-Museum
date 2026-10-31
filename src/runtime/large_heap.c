// Pixel Museum - lazily allocated direct memory for large decoded media.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
// Kernel signatures/alignment follow the public PS5_PayloadSDK platform layer.
// No allocation or mapping is attempted until a large block is actually needed.
#include "large_heap.h"
#include <errno.h>
#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

int32_t sceKernelAllocateDirectMemory(int64_t,int64_t,size_t,size_t,int,int64_t*);
int32_t sceKernelReleaseDirectMemory(int64_t,size_t);
int32_t sceKernelMapDirectMemory(void**,size_t,int,int,int64_t,size_t);
int32_t sceKernelMunmap(void*,size_t);
int64_t sceKernelGetDirectMemorySize(void);
int32_t sceKernelAvailableDirectMemorySize(int64_t,int64_t,size_t,int64_t*,size_t*);

#ifndef MUSEUM_LARGE_HEAP_MIB
#define MUSEUM_LARGE_HEAP_MIB 2048u
#endif
#define LARGE_CAP ((size_t)MUSEUM_LARGE_HEAP_MIB * 1024u * 1024u)
#define DIRECT_UNIT ((size_t)0x10000)
#define LARGE_SLOTS 256
struct block { void *pointer; size_t bytes; int64_t physical; int used; };
static struct block blocks[LARGE_SLOTS];
static atomic_flag lock=ATOMIC_FLAG_INIT;
static size_t live_bytes,peak_bytes,live_blocks,failures;
static int last_error;
static void acquire(void){while(atomic_flag_test_and_set_explicit(&lock,memory_order_acquire)){} }
static void release(void){atomic_flag_clear_explicit(&lock,memory_order_release);}
static int fail(int error){
    ++failures;last_error=error;errno=ENOMEM;
    // A failure can precede the next frame's telemetry. Write an allocation-
    // free breadcrumb: printf/logging here could recursively call this heap.
    char message[]="[Museum] direct allocation refused 0x00000000\n";
    const char digits[]="0123456789abcdef";unsigned value=(unsigned)error;
    for(unsigned n=0;n<8;++n){message[sizeof(message)-3-n]=digits[value&15u];value>>=4;}
    (void)write(1,message,sizeof(message)-1);return 0;
}
size_t museum_large_capacity(void){return LARGE_CAP;}

void *museum_large_alloc(size_t bytes,size_t alignment,int clear){
    if(!bytes)return NULL;
    if(!alignment)alignment=DIRECT_UNIT;
    if(alignment<sizeof(void*)||(alignment&(alignment-1))) {errno=EINVAL;return NULL;}
    if(alignment<DIRECT_UNIT)alignment=DIRECT_UNIT;
    if(bytes>SIZE_MAX-(DIRECT_UNIT-1)){errno=ENOMEM;return NULL;}
    bytes=(bytes+DIRECT_UNIT-1)&~(DIRECT_UNIT-1);
    acquire();
    if(bytes>LARGE_CAP||live_bytes>LARGE_CAP-bytes){fail(ENOMEM);release();return NULL;}
    unsigned slot=0;while(slot<LARGE_SLOTS&&blocks[slot].used)++slot;
    if(slot==LARGE_SLOTS){fail(ENOMEM);release();return NULL;}
    const int64_t pool=sceKernelGetDirectMemorySize();
    if(pool<=0){fail(ENOMEM);release();return NULL;}
    // CPU staging and GPU resources share the same physical pool. The GPU
    // allocator searches upward from zero; putting temporary decoded atlases
    // there interleaves them with long-lived GPU textures and leaves holes too
    // small for the next original-resolution atlas. Prefer the high end of a
    // free range in the upper half, without reserving any idle memory.
    int64_t physical=0,free_start=0;
    size_t free_bytes=0;
    const int64_t upper=(pool/2)&~(int64_t)(DIRECT_UNIT-1);
    int error=sceKernelAvailableDirectMemorySize(upper,pool,alignment,&free_start,&free_bytes);
    int allocated=0;
    // Treat the query as advisory: validate all arithmetic and still use the
    // original whole-pool allocation if the API is unavailable, the range is
    // too small, or another allocator claims it before our exact reservation.
    if(!error&&free_start>=upper&&free_start<pool&&free_bytes>=bytes&&
       free_bytes<=(uint64_t)(pool-free_start)){
        const uint64_t end=(uint64_t)free_start+free_bytes;
        const uint64_t start=(end-bytes)&~((uint64_t)alignment-1);
        if(start>=(uint64_t)free_start&&start<=(uint64_t)pool-bytes){
            error=sceKernelAllocateDirectMemory((int64_t)start,(int64_t)(start+bytes),bytes,alignment,12,&physical);
            allocated=!error;
        }
    }
    if(!allocated)error=sceKernelAllocateDirectMemory(0,pool,bytes,alignment,12,&physical);
    if(error){fail(error);release();return NULL;}
    void*pointer=NULL;
    error=sceKernelMapDirectMemory(&pointer,bytes,0x01|0x02,0,physical,alignment);
    if(error||!pointer){
        const int cleanup=sceKernelReleaseDirectMemory(physical,bytes);
        if(cleanup){blocks[slot]=(struct block){NULL,bytes,physical,1};live_bytes+=bytes;++live_blocks;if(live_bytes>peak_bytes)peak_bytes=live_bytes;}
        fail(error?error:ENOMEM);release();return NULL;
    }
    blocks[slot]=(struct block){pointer,bytes,physical,1};
    live_bytes+=bytes;++live_blocks;if(live_bytes>peak_bytes)peak_bytes=live_bytes;
    release();
    if(clear)memset(pointer,0,bytes);
    return pointer;
}
size_t museum_large_size(const void*pointer){
    if(!pointer)return 0;
    acquire();size_t bytes=0;
    for(unsigned i=0;i<LARGE_SLOTS;++i)if(blocks[i].used&&blocks[i].pointer==pointer){bytes=blocks[i].bytes;break;}
    release();return bytes;
}
int museum_large_free(void*pointer){
    if(!pointer)return 0;
    acquire();unsigned i=0;
    while(i<LARGE_SLOTS&&(!blocks[i].used||blocks[i].pointer!=pointer))++i;
    if(i==LARGE_SLOTS){release();return 0;}
    const struct block old=blocks[i];
    int error=sceKernelMunmap(pointer,old.bytes);
    if(error){fail(error);release();return 1;}
    // If physical release is refused, retain a retired slot and its budget;
    // never reuse a still-owned physical range or count it as free memory.
    blocks[i].pointer=NULL;
    error=sceKernelReleaseDirectMemory(old.physical,old.bytes);
    if(error){fail(error);release();return 1;}
    blocks[i]=(struct block){0};live_bytes-=old.bytes;--live_blocks;
    release();return 1;
}
void museum_large_stats(size_t*live,size_t*peak,size_t*count,size_t*failed,int*error){
    acquire();if(live)*live=live_bytes;if(peak)*peak=peak_bytes;if(count)*count=live_blocks;if(failed)*failed=failures;if(error)*error=last_error;release();
}
int museum_direct_memory_info(size_t*pool_out,size_t*largest){
    const int64_t pool=sceKernelGetDirectMemorySize();if(pool_out)*pool_out=pool>0?(size_t)pool:0;
    if(largest)*largest=0;if(pool<=0)return ENOMEM;
    int64_t physical=0;size_t available=0;
    const int error=sceKernelAvailableDirectMemorySize(0,pool,DIRECT_UNIT,&physical,&available);
    if(!error&&largest)*largest=available;return error;
}
