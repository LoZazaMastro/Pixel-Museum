// Exact prepacked upload payloads, decoded one view on the existing worker.
// SPDX-License-Identifier: GPL-3.0-or-later
bool read_artwork_cache_v2(ImageUpload&job,const Json&metadata,FILE*f,const struct stat&identity,
                          std::uint64_t payload,const std::atomic<std::uint64_t>&revision){
    if(job.encoded->source_sha256.empty()||member(metadata,"source_sha256")!=job.encoded->source_sha256||
       member(metadata,"mip_algorithm")!="exact-existing-RGBA8-mips-and-current-packed-views-v2")return false;
    const auto&atlases=member(metadata,"atlases");if(!atlases.is_array()||atlases.size()>64)return false;
    const Json*atlas=nullptr;for(const auto&a:atlases)if(integer(member(a,"index"))==int(job.index)){if(atlas)return false;atlas=&a;}
    if(!atlas||integer(member(*atlas,"width"))!=job.source.width||integer(member(*atlas,"height"))!=job.source.height||
       integer(member(*atlas,"roles"))!=int(job.source.roles)||integer(member(*atlas,"data_channels"))!=int(job.source.data_channels))return false;
    const auto&fingerprint=member(*atlas,"source_fingerprint");if(!fingerprint.is_number_unsigned()||fingerprint.get<std::uint64_t>()!=job.source.encoded_fingerprint||!member(*atlas,"source_opaque").is_boolean())return false;
    const auto&views=member(*atlas,"views");if(!views.is_array()||views.size()!=std::size_t(job.source.roles==3?2:1))return false;
    std::vector<std::uint8_t>base,packed_base;std::array<std::vector<MipPixels>,2>chains;std::vector<MipPixels>packed_levels;
    std::array<bool,2>uniform{};std::array<std::size_t,2>original_bytes{};std::array<unsigned,2>channels{};unsigned packed_components=0,seen=0;
    for(const auto&view:views){
        const auto role=integer(member(view,"role"));if(role<0||role>1||!(job.source.roles&(1u<<role))||(seen&(1u<<role)))return false;seen|=1u<<role;
        const auto&format=member(view,"format");unsigned components=4;
        if(format=="rg8")components=2;else if(format=="r8")components=1;else if(format!="rgba8")return false;
        if(components<4){
            if(role!=1||job.source.roles!=2)return false;
            unsigned used=0;for(unsigned c=0;c<3;++c)if(job.source.data_channels&(1u<<c)){if(used>=components)return false;channels[used++]=c;}
            if(used!=components)return false;packed_components=components;
        }
        else if(role==1&&job.source.roles==2){unsigned used=0;for(unsigned c=0;c<3;++c)if(job.source.data_channels&(1u<<c))++used;if(used==1||used==2)return false;}
        if(!member(view,"constant").is_boolean())return false;const bool constant=member(view,"constant").get<bool>();uniform[unsigned(role)]=constant;
        const auto&levels=member(view,"levels");unsigned count=1;std::size_t full_bytes=std::size_t(job.source.width)*job.source.height*4;
        for(int w=job.source.width,h=job.source.height;w>1||h>1;++count){w=std::max(1,w/2);h=std::max(1,h/2);full_bytes+=std::size_t(w)*h*4;}
        original_bytes[unsigned(role)]=full_bytes;
        if(!levels.is_array()||levels.size()!=(constant?1:count))return false;
        int w=constant?1:job.source.width,h=constant?1:job.source.height;
        for(std::size_t n=0;n<levels.size();++n){
            if(revision.load(std::memory_order_relaxed)!=job.serial)return false;
            const auto&level=levels[n];const auto&offset_value=member(level,"offset"),&length_value=member(level,"compressed_bytes");
            if(!offset_value.is_number_unsigned()||!length_value.is_number_unsigned())return false;
            const auto offset=offset_value.get<std::uint64_t>(),length=length_value.get<std::uint64_t>();const auto raw=std::size_t(w)*h*components,file_bytes=std::uint64_t(identity.st_size);
            if(!length||length>std::min(std::size_t(48u<<20),raw+(1u<<20))||payload>file_bytes||offset>file_bytes-payload||length>file_bytes-payload-offset||
               integer(member(level,"width"))!=w||integer(member(level,"height"))!=h)return false;
            std::vector<unsigned char>compressed(static_cast<std::size_t>(length));std::size_t received=0;
            while(received<compressed.size()){
                if(revision.load(std::memory_order_relaxed)!=job.serial)return false;const auto chunk=std::min(std::size_t(256u<<10),compressed.size()-received);
                const auto got=pread(fileno(f),compressed.data()+received,chunk,static_cast<off_t>(payload+offset+received));if(got<0&&errno==EINTR)continue;if(got<=0)return false;received+=std::size_t(got);
            }
            if(compressed.size()<5||u32(compressed.data())!=0xFD2FB528u||!(compressed[4]&4u))return false;
            std::vector<unsigned char>decoded(raw);const auto result=ZSTD_decompress(decoded.data(),decoded.size(),compressed.data(),compressed.size());if(ZSTD_isError(result)||result!=raw)return false;
            if(components<4){if(!n)packed_base=std::move(decoded);else packed_levels.push_back({w,h,std::move(decoded)});}
            else if(!n){if(base.empty())base=std::move(decoded);else if(base!=decoded)return false;}
            else chains[unsigned(role)].push_back({w,h,std::move(decoded)});
            w=std::max(1,w/2);h=std::max(1,h/2);
        }
    }
    if(seen!=job.source.roles||revision.load(std::memory_order_relaxed)!=job.serial||!job.encoded->unchanged())return false;
    struct stat after{};if(fstat(fileno(f),&after)!=0||after.st_size!=identity.st_size||after.st_mtime!=identity.st_mtime||after.st_ctime!=identity.st_ctime)return false;
    job.source.rgba=std::move(base);job.levels=std::move(chains);job.packed_base=std::move(packed_base);job.packed_levels=std::move(packed_levels);
    job.packed_components=packed_components;job.packed_channels=channels;job.uniform_roles=uniform;job.original_view_bytes=original_bytes;
    job.source.alpha_known=true;job.source.opaque=member(*atlas,"source_opaque").get<bool>();job.direct_payload=job.source.roles!=3;return true;
}
