/* Pixel Museum restricted collection writer; fixed-width network-order wire format. */
#ifndef PIXEL_MUSEUM_COLLECTION_WRITER_PROTOCOL_H
#define PIXEL_MUSEUM_COLLECTION_WRITER_PROTOCOL_H
#include <stdint.h>
#define PMCW_CONFIG_MARKER "PIXEL-MUSEUM-COLLECTION-WRITER-V1"
#define PMCW_MAGIC "PMCW001\0"
#define PMCW_CONFIG_CAPACITY 16384u
#define PMCW_CONFIG_HEADER 52u
#define PMCW_CONFIG_RECORD 72u
#define PMCW_MAX_PACKS 128u
#define PMCW_MAX_PACK_BYTES (900ull*1024ull*1024ull)
#define PMCW_MAX_DATA (2u*1024u*1024u)
#define PMCW_HELLO_BYTES 40u
#define PMCW_REQUEST_BYTES 16u
#define PMCW_ACK_BYTES 24u
#define PMCW_ACK_MAGIC "PMA1"
#define PMCW_REQUEST_MAGIC "PMC1"
enum { PMCW_OPEN=1, PMCW_DATA=2, PMCW_FINISH=3, PMCW_QUIT=4, PMCW_REMOVE=5 };
static inline uint32_t pmcw_get32(const unsigned char*p){return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
static inline uint64_t pmcw_get64(const unsigned char*p){return ((uint64_t)pmcw_get32(p)<<32)|pmcw_get32(p+4);}
static inline void pmcw_put32(unsigned char*p,uint32_t v){p[0]=(unsigned char)(v>>24);p[1]=(unsigned char)(v>>16);p[2]=(unsigned char)(v>>8);p[3]=(unsigned char)v;}
static inline void pmcw_put64(unsigned char*p,uint64_t v){pmcw_put32(p,(uint32_t)(v>>32));pmcw_put32(p+4,(uint32_t)v);}
#endif
