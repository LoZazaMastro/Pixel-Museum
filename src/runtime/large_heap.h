// Pixel Museum - bounded, lazy CPU direct-memory allocations.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
#define MUSEUM_LARGE_THRESHOLD ((size_t)8u << 20)
void *museum_large_alloc(size_t bytes, size_t alignment, int clear);
size_t museum_large_size(const void *pointer);
int museum_large_free(void *pointer);
void museum_large_stats(size_t *live, size_t *peak, size_t *blocks, size_t *failures, int *last_error);
size_t museum_large_capacity(void);
int museum_direct_memory_info(size_t *pool, size_t *largest_available);
#ifdef __cplusplus
}
#endif
