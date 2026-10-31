// Research-only equivalent opacity scans; no production renderer changes.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>

bool scalar(const std::vector<std::uint8_t>& bytes) {
    for(std::size_t n=3;n<bytes.size();n+=4)if(bytes[n]!=255)return false;
    return true;
}
bool blocks(const std::vector<std::uint8_t>& bytes) {
    static constexpr std::array<std::uint8_t,8> mask_bytes{0,0,0,255,0,0,0,255};
    std::uint64_t mask;std::memcpy(&mask,mask_bytes.data(),sizeof(mask));
    std::size_t n=0;
    for(;n+64<=bytes.size();n+=64) {
        std::uint64_t alpha=~std::uint64_t(0);
        for(std::size_t q=0;q<8;++q){std::uint64_t word;std::memcpy(&word,bytes.data()+n+q*8,8);alpha&=word;}
        if((alpha&mask)!=mask)return false;
    }
    for(n+=3;n<bytes.size();n+=4)if(bytes[n]!=255)return false;
    return true;
}
volatile unsigned sink=0;
int main(int argc,char**argv) {
    for(std::size_t pixels=0;pixels<140;++pixels) {
        std::vector<std::uint8_t> bytes(pixels*4,37);
        for(std::size_t p=0;p<pixels;++p)bytes[p*4+3]=255;
        if(!scalar(bytes)||!blocks(bytes))return 1;
        for(std::size_t p=0;p<pixels;++p)for(unsigned alpha:{0u,1u,127u,254u}) {
            bytes[p*4+3]=alpha;if(scalar(bytes)!=blocks(bytes)||blocks(bytes))return 2;bytes[p*4+3]=255;
        }
    }
    std::puts("Exact opacity parity: empty, short tails, every pixel and four alpha values PASS");
    for(int arg=1;arg<argc;++arg) {
        std::ifstream file(argv[arg],std::ios::binary);
        std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
        if(bytes.empty()||bytes.size()%4||scalar(bytes)!=blocks(bytes))return 3;
        for(int variant=0;variant<2;++variant) {
            double sum=0,minimum=1e9;
            for(int sample=0;sample<9;++sample) {
                const auto start=std::chrono::steady_clock::now();
                for(int i=0;i<10;++i){auto fn=variant?blocks:scalar;sink=sink+unsigned(fn(bytes));}
                const double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/10;
                sum+=ms;minimum=std::min(minimum,ms);
            }
            std::printf("path=%s bytes=%zu opaque=%d variant=%s mean_ms=%.6f minimum_ms=%.6f samples=9x10\n",argv[arg],bytes.size(),int(scalar(bytes)),variant?"blocks":"scalar",sum/9,minimum);
        }
    }
    return sink==12345;
}
