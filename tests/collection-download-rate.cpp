// Deterministic throughput sampling; no network or filesystem required.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_download_rate.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
int main(){
    museum::CollectionDownloadRate rate;rate.reset();double speed=0;std::uint64_t bytes=0;
    for(int n=1;n<=20;++n){bytes+=2000000;speed=rate.observe(n*.1,bytes);assert(std::abs(speed-20000000)<1);}
    for(int n=21;n<=40;++n){bytes+=340000;speed=rate.observe(n*.1,bytes);if(n>=30)assert(std::abs(speed-3400000)<1);}
    // A callback after a multi-second write stall reflects the last second,
    // not the old 20 MB/s burst or an attempt-wide average.
    bytes+=16384;speed=rate.observe(8.,bytes);assert(std::abs(speed-16384)<1);
    rate.reset();assert(rate.observe(0.,0)==0);assert(rate.observe(.01,123)==0);
    rate.reset();bytes=0;for(int n=1;n<=10000;++n){bytes+=1000;speed=rate.observe(n*.001,bytes);}assert(std::abs(speed-1000000)<1);
    // Retry/rewind resets history; a resumed prefix is not counted as new data.
    rate.reset(0.,9000000);assert(std::abs(rate.observe(.1,9100000)-1000000)<1);
    assert(rate.observe(.2,0)==0);assert(rate.observe(.1,1)==0);
    std::cout<<"PASS one-second rate: burst-to-slow, long stall, startup, 1 kHz callbacks, resumed prefix and retry reset\n";
}
