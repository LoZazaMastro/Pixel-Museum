// Read-only, offline-baked lossless RGBA/mip sidecars. Included inside the
// object renderer's private namespace after ImageUpload is declared.
// Original masters remain the authority; any mismatch returns to PNG decoding.
extern "C" std::size_t ZSTD_decompress(void*,std::size_t,const void*,std::size_t);
extern "C" unsigned ZSTD_isError(std::size_t);
constexpr unsigned kArtworkCacheVersion=1;
#include "museum/object_artwork_cache_v2.hpp"
bool read_artwork_cache(ImageUpload&job,const std::atomic<std::uint64_t>&revision){
    if(!job.encoded||job.encoded->artwork_path.empty()||!job.encoded->unchanged())return false;
    const auto started=SceneClock::now();
    const auto current=[&]{return revision.load(std::memory_order_relaxed)==job.serial;};
    FILE*f=std::fopen(job.encoded->artwork_path.c_str(),"rb");if(!f)return false;
    struct Close{FILE*f;~Close(){std::fclose(f);}}close{f};
    struct stat info{};if(fstat(fileno(f),&info)!=0||info.st_size<20||info.st_size>(768LL<<20))return false;
    std::array<unsigned char,20> prefix{};
    if(std::fread(prefix.data(),1,prefix.size(),f)!=prefix.size())return false;
    const bool v2=std::memcmp(prefix.data(),"PMAC0002",8)==0;if(!v2&&std::memcmp(prefix.data(),"PMAC0001",8)!=0)return false;
    const auto header_bytes=u32(prefix.data()+8);if(!header_bytes||header_bytes>(128u<<10)||20u+header_bytes>static_cast<std::uint64_t>(info.st_size))return false;
    std::string text(header_bytes,'\0');if(std::fread(text.data(),1,text.size(),f)!=text.size()||!json_depth_ok(text.data(),text.data()+text.size()))return false;
    const auto header_fingerprint=std::uint64_t(u32(prefix.data()+12))|(std::uint64_t(u32(prefix.data()+16))<<32);if(encoded_fingerprint(reinterpret_cast<const unsigned char*>(text.data()),text.size())!=header_fingerprint)return false;
    const auto metadata=Json::parse(text,nullptr,false);if(!metadata.is_object()||integer(member(metadata,"version"))!=(v2?2:int(kArtworkCacheVersion))||member(metadata,"frame_checksum")!="xxh64-low32")return false;
    const auto&source_bytes=member(metadata,"source_bytes");if(!source_bytes.is_number_unsigned()||source_bytes.get<std::uint64_t>()!=job.encoded->bytes)return false;
    if(v2){if(!read_artwork_cache_v2(job,metadata,f,info,20u+header_bytes,revision))return false;job.cache_hit=true;job.cache_decode_ms=elapsed_ms(started);hui::sys::log("[Museum] lossless prepacked artwork cache atlas %zu / %dx%d original pixels+mips / %.2fms",job.index+1,job.source.width,job.source.height,job.cache_decode_ms);return true;}
    const auto&atlases=member(metadata,"atlases");if(!atlases.is_array()||atlases.size()>64)return false;
    const Json*atlas=nullptr;for(const auto&a:atlases)if(integer(member(a,"index"))==int(job.index)){atlas=&a;break;}
    if(!atlas||integer(member(*atlas,"width"))!=job.source.width||integer(member(*atlas,"height"))!=job.source.height||integer(member(*atlas,"roles"))!=int(job.source.roles)||integer(member(*atlas,"data_channels"))!=int(job.source.data_channels))return false;
    const auto&fingerprint=member(*atlas,"source_fingerprint");if(!fingerprint.is_number_unsigned()||fingerprint.get<std::uint64_t>()!=job.source.encoded_fingerprint)return false;
    const auto&views=member(*atlas,"views");if(!views.is_array()||views.size()!=std::size_t(job.source.roles==3?2:1))return false;
    std::vector<std::uint8_t> base;std::array<std::vector<MipPixels>,2> chains;unsigned seen=0;
    const std::uint64_t payload=20u+header_bytes,file_bytes=static_cast<std::uint64_t>(info.st_size);
    for(const auto&view:views){
        const auto role=integer(member(view,"role"));if(role<0||role>1||!(job.source.roles&(1u<<role))||(seen&(1u<<role)))return false;seen|=1u<<role;
        const auto&levels=member(view,"levels");unsigned expected_levels=1;for(int w=job.source.width,h=job.source.height;w>1||h>1;++expected_levels){w=std::max(1,w/2);h=std::max(1,h/2);}
        if(!levels.is_array()||levels.size()!=expected_levels)return false;
        int w=job.source.width,h=job.source.height;
        for(std::size_t n=0;n<levels.size();++n){
            if(!current())return false;const auto&level=levels[n];
            const auto&offset_value=member(level,"offset"),&length_value=member(level,"compressed_bytes");
            if(!offset_value.is_number_unsigned()||!length_value.is_number_unsigned())return false;
            const auto offset=offset_value.get<std::uint64_t>(),length=length_value.get<std::uint64_t>();
            const auto raw_bytes=static_cast<std::size_t>(w)*h*4;
            if(!length||length>std::min(std::size_t(48u<<20),raw_bytes+(1u<<20))||offset>file_bytes-payload||length>file_bytes-payload-offset||integer(member(level,"width"))!=w||integer(member(level,"height"))!=h)return false;
            std::vector<unsigned char> compressed(static_cast<std::size_t>(length));std::size_t received=0;
            while(received<compressed.size()){
                if(!current())return false;const auto count=std::min(std::size_t(256u<<10),compressed.size()-received);
                const auto got=pread(fileno(f),compressed.data()+received,count,static_cast<off_t>(payload+offset+received));
                if(got<0&&errno==EINTR)continue;if(got<=0)return false;received+=std::size_t(got);
            }
            // Frame descriptor bit2 requires Zstandard's content checksum. Its
            // reference decoder verifies all decoded bytes without a second
            // scalar pass over nearly a gigabyte of artwork per model.
            if(compressed.size()<5||u32(compressed.data())!=0xFD2FB528u||!(compressed[4]&4u))return false;
            std::vector<unsigned char> decoded(raw_bytes);const auto result=ZSTD_decompress(decoded.data(),decoded.size(),compressed.data(),compressed.size());
            if(ZSTD_isError(result)||result!=raw_bytes)return false;
            if(n==0){if(base.empty())base=std::move(decoded);else if(base!=decoded)return false;}
            else chains[unsigned(role)].push_back(MipPixels{w,h,std::move(decoded)});
            w=std::max(1,w/2);h=std::max(1,h/2);
        }
    }
    if(seen!=job.source.roles||!current()||!job.encoded->unchanged())return false;
    struct stat after{};if(fstat(fileno(f),&after)!=0||after.st_size!=info.st_size||after.st_mtime!=info.st_mtime||after.st_ctime!=info.st_ctime)return false;
    job.source.rgba=std::move(base);job.levels=std::move(chains);job.source.alpha_known=true;job.source.opaque=true;
    for(std::size_t n=3;n<job.source.rgba.size();n+=4)if(job.source.rgba[n]!=255){job.source.opaque=false;break;}
    job.cache_hit=true;job.cache_decode_ms=elapsed_ms(started);
    hui::sys::log("[Museum] lossless artwork cache atlas %zu / %dx%d original pixels+mips / %.2fms",job.index+1,job.source.width,job.source.height,job.cache_decode_ms);
    return true;
}
