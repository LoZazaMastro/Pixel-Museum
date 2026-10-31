// Real native loader measurements, one fresh process per sample.
#include "museum/catalog.hpp"
#include <chrono>
#include <cstdio>
#include <sys/resource.h>
int main(int argc,char**argv){
 if(argc!=2)return 2;
 museum::Catalog catalogue;const auto begin=std::chrono::steady_clock::now();
 if(!catalogue.load(argv[1])){std::fprintf(stderr,"%s\n",catalogue.error.c_str());return 3;}
 const auto end=std::chrono::steady_clock::now();rusage usage{};getrusage(RUSAGE_SELF,&usage);
 std::size_t tracks=0,rooms=0,games=0;
 for(const auto&e:catalogue.entries){bool music=false;for(const auto&r:e.soundtrack_rooms)if(!r.tracks.empty()){++rooms;tracks+=r.tracks.size();music=true;}if(!e.soundtrack.tracks.empty()){++rooms;tracks+=e.soundtrack.tracks.size();music=true;}if(e.kind=="game"&&music)++games;}
 std::printf("Actual Catalog::load PASS entries=%zu rooms=%zu distinctgames=%zu tracks=%zu wall_ms=%.3f peak_RSS_bytes=%llu; hostonly, notPS5\n",catalogue.entries.size(),rooms,games,tracks,std::chrono::duration<double,std::milli>(end-begin).count(),static_cast<unsigned long long>(usage.ru_maxrss)*1024);
}
