// Host model for the actual allocation wrappers and lazy direct-memory path.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "runtime/large_heap.h"
#include <assert.h>
#include <errno.h>
#include <malloc.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
void *__wrap_malloc(size_t);void *__wrap_calloc(size_t,size_t);void *__wrap_realloc(void*,size_t);void __wrap_free(void*);int __wrap_posix_memalign(void**,size_t,size_t);size_t __wrap_malloc_usable_size(const void*);
static int map_failure,allocation_failure,allow_large_fallback,physical_live,maps,unmap_failure;
static int query_failure,query_invalid,high_failure,high_allocations,fallback_allocations;
static int64_t last_high_start;
void *__real_malloc(size_t n){return malloc(n);}void *__real_calloc(size_t a,size_t b){return calloc(a,b);}void *__real_realloc(void*p,size_t n){return realloc(p,n);}void __real_free(void*p){free(p);}int __real_posix_memalign(void**p,size_t a,size_t n){return posix_memalign(p,a,n);}size_t __real_malloc_usable_size(const void*p){return p?malloc_usable_size((void*)p):0;}
void*sceLibcMspaceCreate(const char*n,void*b,size_t s,unsigned f){(void)n;(void)b;(void)s;(void)f;return(void*)1;}
void*sceLibcMspaceMalloc(void*m,size_t n){(void)m;return n>=MUSEUM_LARGE_THRESHOLD&&!allow_large_fallback?NULL:malloc(n);}
void*sceLibcMspaceCalloc(void*m,size_t a,size_t b){(void)m;return a*b>=MUSEUM_LARGE_THRESHOLD&&!allow_large_fallback?NULL:calloc(a,b);}
void*sceLibcMspaceRealloc(void*m,void*p,size_t n){(void)m;return realloc(p,n);}void sceLibcMspaceFree(void*m,void*p){(void)m;free(p);}
int sceLibcMspacePosixMemalign(void*m,void**p,size_t a,size_t n){(void)m;return n>=MUSEUM_LARGE_THRESHOLD&&!allow_large_fallback?ENOMEM:posix_memalign(p,a,n);}
size_t sceLibcMspaceMallocUsableSize(const void*p){return p?malloc_usable_size((void*)p):0;}
int64_t sceKernelGetDirectMemorySize(void){return(int64_t)8<<30;}
int32_t sceKernelAllocateDirectMemory(int64_t a,int64_t b,size_t n,size_t align,int type,int64_t*p){
    const int64_t pool=(int64_t)8<<30;
    assert(a>=0&&b<=pool&&n%65536==0&&align>=65536&&type==12);
    if(a==0&&b==pool)++fallback_allocations;
    else{assert(a>=pool/2&&b-a==(int64_t)n&&(uint64_t)a%align==0);last_high_start=a;++high_allocations;if(high_failure)return-12;}
    if(allocation_failure)return-12;*p=++physical_live;return 0;
}
int32_t sceKernelReleaseDirectMemory(int64_t p,size_t n){(void)p;(void)n;assert(physical_live>0);--physical_live;return 0;}
int32_t sceKernelMapDirectMemory(void**p,size_t n,int prot,int flags,int64_t phys,size_t align){(void)phys;assert(prot==3&&flags==0);if(map_failure)return-13;int e=posix_memalign(p,align,n);if(!e)++maps;return e;}
int32_t sceKernelMunmap(void*p,size_t n){(void)n;if(unmap_failure)return-14;free(p);--maps;return 0;}
int32_t sceKernelAvailableDirectMemorySize(int64_t a,int64_t b,size_t align,int64_t*p,size_t*n){
    const int64_t pool=(int64_t)8<<30;assert(a>=0&&b==pool&&align>=65536&&(align&(align-1))==0);
    if(query_failure)return-15;
    *p=query_invalid?pool-65536:pool-((int64_t)128<<20);*n=(size_t)128<<20;return 0;
}
static void*thread(void*unused){(void)unused;for(unsigned n=0;n<10;++n){void*p=__wrap_malloc(8u<<20);if(p){memset(p,5,64);__wrap_free(p);}}return NULL;}
int main(void){
    size_t pool=0,available=0;assert(museum_direct_memory_info(&pool,&available)==0&&pool==((size_t)8<<30)&&available==((size_t)128<<20)&&physical_live==0);
    // Exact, aligned high-end placement leaves the GPU's lower ranges free.
    unsigned char*probe=__wrap_malloc(8u<<20);assert(probe&&high_allocations==1&&fallback_allocations==0&&last_high_start==((int64_t)8<<30)-(8u<<20));__wrap_free(probe);
    int fallbacks=fallback_allocations;query_failure=1;probe=__wrap_malloc(8u<<20);assert(probe&&fallback_allocations==fallbacks+1);__wrap_free(probe);query_failure=0;
    fallbacks=fallback_allocations;query_invalid=1;probe=__wrap_malloc(8u<<20);assert(probe&&fallback_allocations==fallbacks+1);__wrap_free(probe);query_invalid=0;
    fallbacks=fallback_allocations;high_failure=1;probe=__wrap_malloc(8u<<20);assert(probe&&fallback_allocations==fallbacks+1);__wrap_free(probe);high_failure=0;
    unsigned char*p=__wrap_malloc(8u<<20);assert(p&&((uintptr_t)p%65536)==0&&__wrap_malloc_usable_size(p)>=(8u<<20));memset(p,0x5a,1024);
    p=__wrap_realloc(p,12u<<20);assert(p&&p[0]==0x5a&&p[1023]==0x5a);
    p=__wrap_realloc(p,1024);assert(p&&p[1023]==0x5a&&museum_large_size(p)==0);__wrap_free(p);
    p=__wrap_calloc(2,4u<<20);assert(p&&p[0]==0&&p[(8u<<20)-1]==0);__wrap_free(p);
    void*aligned=NULL;assert(__wrap_posix_memalign(&aligned,1u<<20,8u<<20)==0&&((uintptr_t)aligned%(1u<<20))==0);__wrap_free(aligned);
    assert(__wrap_posix_memalign(&aligned,3,8u<<20)==EINVAL);
    assert(!__wrap_calloc(SIZE_MAX,2)&&errno==ENOMEM);
    p=__wrap_malloc(28u<<20);assert(p);p[0]=91;assert(!__wrap_realloc(p,12u<<20)&&p[0]==91);__wrap_free(p);
    map_failure=1;assert(!__wrap_malloc(8u<<20)&&physical_live==0&&maps==0);map_failure=0;
    allocation_failure=1;allow_large_fallback=1;p=__wrap_malloc(8u<<20);assert(p&&museum_large_size(p)==0);__wrap_free(p);allow_large_fallback=0;allocation_failure=0;
    p=__wrap_malloc(8u<<20);assert(p);unmap_failure=1;__wrap_free(p);assert(museum_large_size(p)>0);unmap_failure=0;__wrap_free(p);
    pthread_t workers[4];for(unsigned i=0;i<4;++i)assert(!pthread_create(&workers[i],NULL,thread,NULL));for(unsigned i=0;i<4;++i)pthread_join(workers[i],NULL);
    size_t live=0,peak=0,count=0,failed=0;int error=0;museum_large_stats(&live,&peak,&count,&failed,&error);
    assert(live==0&&count==0&&physical_live==0&&maps==0&&peak<=museum_large_capacity()&&failed>=3&&error!=0);
    printf("Lazy direct-memory wrappers pass: high-end packing, query/race fallback, realloc/calloc/alignment,32MiB cap model, syscall failures,4threads; peak %zu bytes, %zu refusals.\n",peak,failed);
    return 0;
}
