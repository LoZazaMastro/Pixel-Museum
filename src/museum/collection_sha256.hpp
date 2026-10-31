// Streaming adaptation of the bundled SponsorBlock/ObjectScene SHA256.
// SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <string>
#include <algorithm>
namespace museum {
class CollectionSha256 {
public:
    void update(const void*data,std::size_t size){
        const auto*p=static_cast<const unsigned char*>(data);bytes_+=size;
        while(size){const auto n=std::min(size,buffer_.size()-used_);std::memcpy(buffer_.data()+used_,p,n);used_+=n;p+=n;size-=n;if(used_==64){block(buffer_.data());used_=0;}}
    }
    std::string finish(){
        const auto bits=bytes_*8;buffer_[used_++]=128;
        if(used_>56){std::fill(buffer_.begin()+used_,buffer_.end(),0);block(buffer_.data());used_=0;}
        std::fill(buffer_.begin()+used_,buffer_.begin()+56,0);for(unsigned n=0;n<8;++n)buffer_[63-n]=static_cast<unsigned char>(bits>>(n*8));block(buffer_.data());
        constexpr char hex[]="0123456789abcdef";std::string out(64,'0');for(unsigned n=0;n<32;++n){const auto value=static_cast<unsigned char>(h_[n/4]>>(24-(n%4)*8));out[n*2]=hex[value>>4];out[n*2+1]=hex[value&15];}return out;
    }
private:
    std::array<std::uint32_t,8>h_{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    std::array<unsigned char,64>buffer_{};std::size_t used_=0;std::uint64_t bytes_=0;
    static std::uint32_t ror(std::uint32_t x,unsigned n){return(x>>n)|(x<<(32-n));}
    void block(const unsigned char*p){
        static constexpr std::uint32_t k[]{
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
        std::array<std::uint32_t,64>w{};for(unsigned n=0;n<16;++n)w[n]=std::uint32_t(p[n*4])<<24|std::uint32_t(p[n*4+1])<<16|std::uint32_t(p[n*4+2])<<8|p[n*4+3];
        for(unsigned n=16;n<64;++n)w[n]=w[n-16]+(ror(w[n-15],7)^ror(w[n-15],18)^(w[n-15]>>3))+w[n-7]+(ror(w[n-2],17)^ror(w[n-2],19)^(w[n-2]>>10));
        auto a=h_[0],b=h_[1],c=h_[2],d=h_[3],e=h_[4],f=h_[5],g=h_[6],j=h_[7];
        for(unsigned n=0;n<64;++n){const auto t1=j+(ror(e,6)^ror(e,11)^ror(e,25))+((e&f)^(~e&g))+k[n]+w[n];const auto t2=(ror(a,2)^ror(a,13)^ror(a,22))+((a&b)^(a&c)^(b&c));j=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
        h_[0]+=a;h_[1]+=b;h_[2]+=c;h_[3]+=d;h_[4]+=e;h_[5]+=f;h_[6]+=g;h_[7]+=j;
    }
};
}
