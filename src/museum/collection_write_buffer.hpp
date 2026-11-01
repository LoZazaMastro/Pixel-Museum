// Explicit bounded disk coalescing; callbacks never choose raw write sizes.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <vector>
namespace museum {
class CollectionWriteBuffer {
    std::vector<char>bytes_=std::vector<char>(2u<<20);
    std::size_t used_=0;
    std::uint64_t accepted_=0,flushed_=0;
public:
    std::uint64_t accepted()const{return accepted_;}
    std::uint64_t flushed()const{return flushed_;}
    template<class Sink>bool flush(Sink&&sink){
        std::size_t offset=0;
        while(offset<used_){const auto count=sink(bytes_.data()+offset,used_-offset);if(count<0&&errno==EINTR)continue;if(count<=0){if(offset){std::memmove(bytes_.data(),bytes_.data()+offset,used_-offset);used_-=offset;}return false;}if(std::size_t(count)>used_-offset){errno=EIO;return false;}offset+=std::size_t(count);flushed_+=std::size_t(count);}
        used_=0;return true;
    }
    template<class Sink>bool append(const char*source,std::size_t size,Sink&&sink){
        while(size){if(used_==bytes_.size()&&!flush(sink))return false;const auto count=std::min(size,bytes_.size()-used_);std::memcpy(bytes_.data()+used_,source,count);source+=count;size-=count;used_+=count;accepted_+=count;if(used_==bytes_.size()&&!flush(sink))return false;}return true;
    }
};
}
