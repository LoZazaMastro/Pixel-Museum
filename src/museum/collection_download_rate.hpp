// Bounded one-second receive/write throughput, sampled at 100 ms.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
namespace museum {
class CollectionDownloadRate {
    struct Sample {double time=0;std::uint64_t bytes=0;};
    std::array<Sample,16> samples_{};
    std::size_t count_=0;
    double last_time_=0;
    std::uint64_t last_bytes_=0;
public:
    void reset(double time=0,std::uint64_t bytes=0){samples_[0]={time,bytes};count_=1;last_time_=time;last_bytes_=bytes;}
    double observe(double now,std::uint64_t bytes){
        if(!count_||now<last_time_||bytes<last_bytes_){reset(now,bytes);return 0;}
        // No callback means no accepted payload. A long stall must not turn
        // the next rate into an average over the entire download attempt.
        if(now-last_time_>1.)reset(now-1.,last_bytes_);
        const double cutoff=now-1.;
        while(count_>1&&samples_[1].time<=cutoff){for(std::size_t n=1;n<count_;++n)samples_[n-1]=samples_[n];--count_;}
        if(now-samples_[count_-1].time>=.1-1e-9){
            if(count_==samples_.size()){for(std::size_t n=1;n<count_;++n)samples_[n-1]=samples_[n];--count_;}
            samples_[count_++]={now,bytes};
        }
        double base_time=samples_[0].time,base_bytes=double(samples_[0].bytes);
        if(base_time<cutoff&&count_>1&&samples_[1].time>base_time){
            const double fraction=(cutoff-base_time)/(samples_[1].time-base_time);
            base_bytes+=fraction*double(samples_[1].bytes-samples_[0].bytes);base_time=cutoff;
        }
        last_time_=now;last_bytes_=bytes;const auto seconds=now-base_time;
        return seconds>.05?(double(bytes)-base_bytes)/seconds:0.;
    }
};
}
