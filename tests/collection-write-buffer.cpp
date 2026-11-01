// Verify explicit syscall batching, partial writes, EINTR and retained tails.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_write_buffer.hpp"
#include <cassert>
#include <iostream>
int main(){
    constexpr std::size_t block=2u<<20;std::vector<char>source(5u*1024*1024+77);for(std::size_t n=0;n<source.size();++n)source[n]=char(n%251);
    museum::CollectionWriteBuffer buffer;std::vector<char>output;std::vector<std::size_t>requests;
    const auto sink=[&](const char*data,std::size_t count)->std::ptrdiff_t{requests.push_back(count);output.insert(output.end(),data,data+count);return count;};
    for(std::size_t n=0;n<source.size();n+=2048)assert(buffer.append(source.data()+n,std::min<std::size_t>(2048,source.size()-n),sink));
    assert(buffer.accepted()==source.size()&&buffer.flushed()==block*2);assert(requests==std::vector<std::size_t>({block,block}));assert(buffer.flush(sink));assert(requests.back()==source.size()-block*2&&output==source&&buffer.flushed()==buffer.accepted());
    museum::CollectionWriteBuffer partial;output.clear();unsigned calls=0;
    const auto failing=[&](const char*data,std::size_t count)->std::ptrdiff_t{++calls;if(calls==1){errno=EINTR;return -1;}if(calls==3){errno=ENOSPC;return -1;}const auto bytes=std::min<std::size_t>(count,12345);output.insert(output.end(),data,data+bytes);return bytes;};
    assert(!partial.append(source.data(),block+128,failing));assert(partial.accepted()==block&&partial.flushed()==12345);assert(partial.flush(sink));assert(output==std::vector<char>(source.begin(),source.begin()+block));assert(partial.accepted()==partial.flushed());
    museum::CollectionWriteBuffer tail;output.clear();assert(tail.append(source.data(),16384,sink));assert(!tail.flushed());const auto zero=[](const char*,std::size_t)->std::ptrdiff_t{errno=EIO;return 0;};assert(!tail.flush(zero)&&tail.accepted()==16384&&!tail.flushed());assert(tail.flush(sink));assert(output==std::vector<char>(source.begin(),source.begin()+16384));
    std::cout<<"PASS 2 MiB raw batching, small callbacks, final/pause/error tails, partial writes, EINTR, ENOSPC and zero writes\n";
}
