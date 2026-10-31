// ps5-homebrew-ui - Process-lifetime heap for the OpenGL runtime.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Adapted from ps5-opengl native-app/app_heap.c. tools/build.sh links with
// --wrap for the malloc family whenever this file exists, routing allocations
// into a bounded, configurable sceLibcMspace that is never unmapped.

#include <errno.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "large_heap.h"

void *__real_malloc(size_t size);
void *__real_calloc(size_t count, size_t size);
void *__real_realloc(void *address, size_t size);
void __real_free(void *address);
int __real_posix_memalign(void **address, size_t alignment, size_t size);
size_t __real_malloc_usable_size(const void *address);

void *sceLibcMspaceCreate(const char *name, void *base, size_t size, unsigned flags);
void *sceLibcMspaceMalloc(void *mspace, size_t size);
void *sceLibcMspaceCalloc(void *mspace, size_t count, size_t size);
void *sceLibcMspaceRealloc(void *mspace, void *address, size_t size);
void sceLibcMspaceFree(void *mspace, void *address);
int sceLibcMspacePosixMemalign(void *mspace, void **address, size_t alignment, size_t size);
size_t sceLibcMspaceMallocUsableSize(const void *address);

/* Fixed, process-lifetime heap: do not unmap underneath late C++ destructors. */
#ifndef MUSEUM_HEAP_MIB
#define MUSEUM_HEAP_MIB 512u
#endif
#define HUI_HEAP_SIZE ((size_t)MUSEUM_HEAP_MIB * 1024u * 1024u)

size_t hui_heap_capacity(void)
{
    return HUI_HEAP_SIZE;
}

static atomic_int hui_heap_state;
static void *hui_heap_base;
static void *hui_heap_mspace;
/* Owned-heap usable bytes only; relaxed counters are observations, not fences. */
static atomic_size_t hui_heap_live_bytes, hui_heap_peak_bytes, hui_heap_blocks;
static atomic_size_t hui_heap_failures;

static void hui_heap_resize_stats(size_t before, size_t after)
{
    size_t live = after >= before ? atomic_fetch_add_explicit(&hui_heap_live_bytes, after - before,
                                                              memory_order_relaxed) +
                                        after - before
                                  : atomic_fetch_sub_explicit(&hui_heap_live_bytes, before - after,
                                                              memory_order_relaxed) -
                                        (before - after);
    size_t peak = atomic_load_explicit(&hui_heap_peak_bytes, memory_order_relaxed);
    while (live > peak &&
           !atomic_compare_exchange_weak_explicit(&hui_heap_peak_bytes, &peak, live,
                                                  memory_order_relaxed, memory_order_relaxed))
    {
    }
}

static void *hui_heap_record_allocation(void *address, int nonzero)
{
    if (address)
    {
        hui_heap_resize_stats(0, sceLibcMspaceMallocUsableSize(address));
        atomic_fetch_add_explicit(&hui_heap_blocks, 1, memory_order_relaxed);
    }
    else if (nonzero)
    {
        atomic_fetch_add_explicit(&hui_heap_failures, 1, memory_order_relaxed);
    }
    return address;
}

static int hui_heap_ready(void)
{
    int state = atomic_load_explicit(&hui_heap_state, memory_order_acquire);
    if (state == 2)
        return 1;
    if (state != 0)
        return 0;

    int expected = 0;
    if (!atomic_compare_exchange_strong_explicit(&hui_heap_state, &expected, 1,
                                                 memory_order_acq_rel, memory_order_acquire))
        return expected == 2;

    /* Keep the ordinary/system pool available to driver and pthread internals.
     * The arena has process lifetime; its capacity and small-allocation API are
     * unchanged, using the existing bounded cached CPU direct-memory allocator. */
    void *base = museum_large_alloc(HUI_HEAP_SIZE, 0, 0);
    if (base == NULL)
    {
        atomic_store_explicit(&hui_heap_state, -1, memory_order_release);
        return 0;
    }

    hui_heap_base = base;
    hui_heap_mspace = sceLibcMspaceCreate("ps5-homebrew-ui", base, HUI_HEAP_SIZE, 0);
    if (hui_heap_mspace == NULL)
    {
        hui_heap_base = NULL;
        museum_large_free(base);
        atomic_store_explicit(&hui_heap_state, -1, memory_order_release);
        return 0;
    }

    atomic_store_explicit(&hui_heap_state, 2, memory_order_release);
    return 1;
}

static int hui_heap_owns(const void *address)
{
    /* Acquire publication before reading non-atomic heap metadata. */
    if (atomic_load_explicit(&hui_heap_state, memory_order_acquire) != 2)
        return 0;
    uintptr_t value = (uintptr_t)address;
    uintptr_t base = (uintptr_t)hui_heap_base;
    return value >= base && value - base < HUI_HEAP_SIZE;
}

void *__wrap_malloc(size_t size)
{
    if(size>=MUSEUM_LARGE_THRESHOLD){void*large=museum_large_alloc(size,0,0);if(large)return large;}
    return hui_heap_ready()
               ? hui_heap_record_allocation(sceLibcMspaceMalloc(hui_heap_mspace, size), size != 0)
               : __real_malloc(size);
}

void *__wrap_calloc(size_t count, size_t size)
{
    if(size&&count>SIZE_MAX/size){errno=ENOMEM;return NULL;}
    if(count*size>=MUSEUM_LARGE_THRESHOLD){void*large=museum_large_alloc(count*size,0,1);if(large)return large;}
    return hui_heap_ready()
               ? hui_heap_record_allocation(sceLibcMspaceCalloc(hui_heap_mspace, count, size),
                                            count != 0 && size != 0)
               : __real_calloc(count, size);
}

void *__wrap_realloc(void *address, size_t size)
{
    if (address == NULL)
        return __wrap_malloc(size);
    const size_t large_size=museum_large_size(address);
    if(large_size){if(!size){museum_large_free(address);return NULL;}void*next=__wrap_malloc(size);if(next){memcpy(next,address,large_size<size?large_size:size);museum_large_free(address);}return next;}
    if (!hui_heap_owns(address))
        return __real_realloc(address, size);
    if(size>=MUSEUM_LARGE_THRESHOLD){void*next=__wrap_malloc(size);if(next){size_t before=sceLibcMspaceMallocUsableSize(address);memcpy(next,address,before<size?before:size);hui_heap_resize_stats(before,0);atomic_fetch_sub_explicit(&hui_heap_blocks,1,memory_order_relaxed);sceLibcMspaceFree(hui_heap_mspace,address);}return next;}
    size_t before = sceLibcMspaceMallocUsableSize(address);
    void *result = sceLibcMspaceRealloc(hui_heap_mspace, address, size);
    if (result)
        hui_heap_resize_stats(before, sceLibcMspaceMallocUsableSize(result));
    else if (size)
        atomic_fetch_add_explicit(&hui_heap_failures, 1, memory_order_relaxed);
    return result;
}

void __wrap_free(void *address)
{
    if(museum_large_free(address))return;
    if (hui_heap_owns(address))
    {
        hui_heap_resize_stats(sceLibcMspaceMallocUsableSize(address), 0);
        atomic_fetch_sub_explicit(&hui_heap_blocks, 1, memory_order_relaxed);
        sceLibcMspaceFree(hui_heap_mspace, address);
    }
    else
    {
        __real_free(address);
    }
}

int __wrap_posix_memalign(void **address, size_t alignment, size_t size)
{
    if(size>=MUSEUM_LARGE_THRESHOLD){if(alignment<sizeof(void*)||(alignment&(alignment-1)))return EINVAL;void*large=museum_large_alloc(size,alignment,0);if(large){*address=large;return 0;}}
    if (!hui_heap_ready())
        return __real_posix_memalign(address, alignment, size);
    int result = sceLibcMspacePosixMemalign(hui_heap_mspace, address, alignment, size);
    if (result == 0)
        hui_heap_record_allocation(*address, size != 0);
    else if (result == ENOMEM)
        atomic_fetch_add_explicit(&hui_heap_failures, 1, memory_order_relaxed);
    return result;
}

size_t __wrap_malloc_usable_size(const void *address)
{
    const size_t large=museum_large_size(address);if(large)return large;
    return hui_heap_owns(address) ? sceLibcMspaceMallocUsableSize(address)
                                  : __real_malloc_usable_size(address);
}

/* Diagnostics: current heap counters for logs and the diagnostics screen. */
void hui_heap_stats(size_t *live_bytes, size_t *peak_bytes, size_t *blocks, size_t *failures)
{
    if (live_bytes)
        *live_bytes = atomic_load_explicit(&hui_heap_live_bytes, memory_order_relaxed);
    if (peak_bytes)
        *peak_bytes = atomic_load_explicit(&hui_heap_peak_bytes, memory_order_relaxed);
    if (blocks)
        *blocks = atomic_load_explicit(&hui_heap_blocks, memory_order_relaxed);
    if (failures)
        *failures = atomic_load_explicit(&hui_heap_failures, memory_order_relaxed);
}
