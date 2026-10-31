// Pixel Museum - static GLB geometry rendered with the existing OpenGL kit.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/object_scene.hpp"
#include "gfx/gl_program.hpp"
#include "platform/ps5/system.hpp"
#include "third_party/nlohmann/json.hpp"
#include "yt/image.hpp"
#include "third_party/stb/stb_image.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <functional>
#include <limits>
#include <mutex>
#include <chrono>
#include <thread>
#include <utility>
#include <vector>
#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>

namespace museum {
namespace {
using Json = nlohmann::json;
using Matrix = std::array<float, 16>;
constexpr std::size_t kMaxFile = 160u << 20;
constexpr std::size_t kMaxVertices = 4000000;
constexpr std::size_t kMaxIndices = 16000000;
// Full-resolution museum masters can contain several 4K material atlases.
// Keep this finite and release decoded pixels one image at a time on upload.
constexpr std::size_t kMaxTexturePixels = 384u << 20;
constexpr std::size_t kMaxNodes = 16384;
constexpr std::size_t kMaxSourceParts = 8192;
const Json kNull;
struct Vec3 { float x=0, y=0, z=0; };
struct Vertex { Vec3 position, normal; std::array<std::array<float,2>,4> uv{}; std::array<float,4> tangent{}; };
struct Sampler { int min=GL_LINEAR_MIPMAP_LINEAR,mag=GL_LINEAR,s=GL_REPEAT,t=GL_REPEAT;bool operator==(const Sampler&) const=default; };
struct Pixels { int width=0, height=0; unsigned roles=0,data_channels=0;std::size_t encoded_offset=0,encoded_length=0;std::uint64_t encoded_fingerprint=0;bool alpha_known=false,opaque=false;std::vector<std::uint8_t> rgba; };
// Optional, authored UV-only restoration; source bitmaps remain unchanged.
struct SurfaceRestore {
    std::array<std::array<float,4>,4> regions{},details{},ink{};
    std::array<float,4> colour_roughness{};
    int region_count=0,detail_count=0,ink_count=0;
    bool operator==(const SurfaceRestore&) const=default;
};
struct Part {
    std::vector<Vertex> vertices;
    std::vector<std::uint32_t> indices;
    std::array<float,4> color{1,1,1,1};
    int image=-1;
    int emissive_image=-1,normal_image=-1,orm_image=-1,ao_image=-1;
    std::array<float,3> emission{};
    std::array<int,5> uv_sets{};std::array<Sampler,5> samplers{};
    float normal_scale=1,ao_strength=1;
    float cutoff=-1;
    float roughness=.7f,metallic=0,specular=1;
    std::array<float,3> specular_color{1,1,1};
    SurfaceRestore restore;
    bool unlit=false, blend=false, double_sided=false, mirrored=false;
    Vec3 center{};std::size_t tangent_vertices=0;
};
struct Model { int texture_limit=0;std::vector<Part> parts; std::vector<Pixels> images;std::string notes;std::size_t deduplicated_images=0; };
// Cache admission counts conservative physical backing, not merely uploaded
// texels. The PS5 trace allocates149.375MiB for a4K RGBA mip chain whose
// logical size is85.333MiB; a2x allowance also covers row/tile alignment.
std::size_t texture_residency(std::size_t logical) { return (logical*2+65535u)&~std::size_t(65535u); }
std::size_t model_residency(const Model&model) {
    std::size_t bytes=0;
    for(const auto&image:model.images)if(image.width>0&&image.roles){
        std::size_t logical=0;int w=image.width,h=image.height;
        while(model.texture_limit>0&&(w>model.texture_limit||h>model.texture_limit)){w=std::max(1,w/2);h=std::max(1,h/2);}
        for(;;){logical+=static_cast<std::size_t>(w)*h*4;if(w==1&&h==1)break;w=std::max(1,w/2);h=std::max(1,h/2);}
        bytes+=texture_residency(logical)*(image.roles==3?2:1);
    }
    for(const auto&part:model.parts)bytes+=part.vertices.size()*sizeof(Vertex)+part.indices.size()*sizeof(std::uint32_t);
    return bytes;
}

const Json &member(const Json &value, const char *key) {
    if (!value.is_object()) return kNull;
    const auto it=value.find(key);
    return it==value.end() ? kNull : *it;
}
const Json &element(const Json &value, int index) {
    return value.is_array() && index>=0 && static_cast<std::size_t>(index)<value.size()
        ? value[static_cast<std::size_t>(index)] : kNull;
}
int integer(const Json &value, int fallback=-1) {
    if (!value.is_number_integer()) return fallback;
    if (value.is_number_unsigned()) {
        const auto n=value.get<std::uint64_t>();
        return n<=static_cast<std::uint64_t>(std::numeric_limits<int>::max()) ? static_cast<int>(n) : fallback;
    }
    const auto n=value.get<std::int64_t>();
    return n>=std::numeric_limits<int>::min() && n<=std::numeric_limits<int>::max() ? static_cast<int>(n) : fallback;
}
float number(const Json &value, float fallback=0) {
    if (!value.is_number()) return fallback;
    const double d=value.get<double>();
    return std::isfinite(d) && std::abs(d)<=1e12 ? static_cast<float>(d) : fallback;
}
bool text(const Json &v, const char *s) { return v.is_string() && v.get<std::string>()==s; }
std::uint32_t u32(const unsigned char *p) {
    return std::uint32_t(p[0]) | (std::uint32_t(p[1])<<8) |
        (std::uint32_t(p[2])<<16) | (std::uint32_t(p[3])<<24);
}
Matrix identity() { return {1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1}; }
Matrix multiply(const Matrix &a, const Matrix &b) {
    Matrix c{};
    for (int x=0;x<4;++x) for(int y=0;y<4;++y) for(int k=0;k<4;++k)
        c[static_cast<std::size_t>(x*4+y)]+=a[static_cast<std::size_t>(k*4+y)]*b[static_cast<std::size_t>(x*4+k)];
    return c;
}
Vec3 transform(const Matrix &m, Vec3 v) {
    return {m[0]*v.x+m[4]*v.y+m[8]*v.z+m[12],m[1]*v.x+m[5]*v.y+m[9]*v.z+m[13],m[2]*v.x+m[6]*v.y+m[10]*v.z+m[14]};
}
Vec3 sub(Vec3 a, Vec3 b) { return {a.x-b.x,a.y-b.y,a.z-b.z}; }
Vec3 cross(Vec3 a, Vec3 b) { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
Vec3 normal(Vec3 v) {
    const float length=std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z);
    return length>1e-12f ? Vec3{v.x/length,v.y/length,v.z/length} : Vec3{0,1,0};
}
bool finite(Vec3 v) { return std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z); }
bool json_depth_ok(const char *begin, const char *end) {
    bool quoted=false, escape=false;
    int depth=0;
    for (const char *p=begin;p!=end;++p) {
        if (quoted) { if(escape)escape=false; else if(*p=='\\')escape=true; else if(*p=='"')quoted=false; }
        else if(*p=='"')quoted=true;
        else if(*p=='['||*p=='{') { if(++depth>64)return false; }
        else if(*p==']'||*p=='}') { if(--depth<0)return false; }
    }
    return !quoted&&depth==0;
}

std::uint64_t encoded_fingerprint(const unsigned char*data,std::size_t bytes){std::uint64_t h=1469598103934665603ull;for(std::size_t n=0;n<bytes;++n){h^=data[n];h*=1099511628211ull;}return h;}
#include "museum/object_cache_sha256.hpp"
struct EncodedFile {
    FILE*stream=nullptr;std::size_t bytes=0;struct stat identity{};std::string artwork_path,source_sha256;
    ~EncodedFile(){if(stream)std::fclose(stream);}
    bool unchanged()const{struct stat now{};return stream&&fstat(fileno(stream),&now)==0&&now.st_size==identity.st_size&&now.st_mtime==identity.st_mtime&&now.st_ctime==identity.st_ctime;}
};

class Reader {
public:
    double read_decode_ms=0,source_read_ms=0,source_hash_ms=0;
    bool defer_images=false;
    std::shared_ptr<EncodedFile> encoded_file;
    std::function<bool()> cancelled;
    bool superseded() const {return cancelled&&cancelled();}
    Json doc;
    std::vector<unsigned char> bytes;
    std::size_t bin_offset=0, bin_length=0, vertex_count=0,index_count=0, texture_pixels=0;
    std::vector<std::string> include_groups;
    std::string error;
    Model model;
    bool specular_required=false;
    std::array<int,64> image_alias=[] {std::array<int,64> aliases{};aliases.fill(-1);return aliases;}();
    struct Access {
        const unsigned char *data=nullptr;
        std::size_t count=0,stride=0;
        int component=0, components=0;
        bool normalized=false;
        float read(std::size_t index,int part) const {
            const auto *p=data+index*stride;
            if (component==5126) { float f;std::memcpy(&f,p+part*4,4);return f; }
            if (component==5123) { const auto n=std::uint16_t(p[part*2])|(std::uint16_t(p[part*2+1])<<8);return normalized ? float(n)/65535.0f : float(n); }
            if (component==5121) return normalized ? float(p[part])/255.0f : float(p[part]);
            return 0;
        }
        std::uint32_t index(std::size_t i) const {
            const auto *p=data+i*stride;
            if(component==5125)return u32(p);
            if(component==5123)return std::uint32_t(p[0])|(std::uint32_t(p[1])<<8);
            return p[0];
        }
    };
    bool fail(const std::string &why) { error=why;return false; }
    bool view(int index,const unsigned char **data,std::size_t *length,std::size_t *stride) {
        const auto &v=element(member(doc,"bufferViews"),index);
        if(!v.is_object()||integer(member(v,"buffer"))!=0||!member(v,"extensions").is_null())
            return fail("Unsupported or missing GLB buffer view");
        const int start=integer(member(v,"byteOffset"),0), size=integer(member(v,"byteLength"));
        const int step=integer(member(v,"byteStride"),0);
        if(start<0||size<0||step<0||static_cast<std::size_t>(start)>bin_length||
           static_cast<std::size_t>(size)>bin_length-static_cast<std::size_t>(start))
            return fail("GLB buffer view is outside its binary chunk");
        *data=bytes.data()+bin_offset+static_cast<std::size_t>(start);
        *length=static_cast<std::size_t>(size);*stride=static_cast<std::size_t>(step);
        return true;
    }
    bool accessor(int index,int parts,bool indices,Access *out) {
        const auto &a=element(member(doc,"accessors"),index);
        if(!a.is_object()||!member(a,"sparse").is_null())return fail("Sparse or missing GLB accessor");
        if(!text(member(a,"type"),parts==4?"VEC4":parts==3?"VEC3":parts==2?"VEC2":"SCALAR"))return fail("GLB accessor has an unexpected shape");
        const int component=integer(member(a,"componentType"));
        const int count=integer(member(a,"count")),offset=integer(member(a,"byteOffset"),0);
        const bool norm=member(a,"normalized").is_boolean()&&member(a,"normalized").get<bool>();
        if(count<=0||static_cast<std::size_t>(count)>(indices?kMaxIndices:kMaxVertices)||offset<0)
            return fail("GLB accessor exceeds the exhibit size limit");
        const bool supported=indices ? (component==5121||component==5123||component==5125)&&!norm :
            component==5126||(parts==2&&norm&&(component==5121||component==5123));
        if(!supported)return fail("Unsupported GLB accessor component format");
        const unsigned char *data=nullptr;std::size_t length=0,stride=0;
        if(!view(integer(member(a,"bufferView")),&data,&length,&stride))return false;
        const std::size_t element_size=static_cast<std::size_t>(parts)*(component==5121?1u:component==5123?2u:4u);
        if(!stride)stride=element_size;
        if(stride<element_size||stride>252||static_cast<std::size_t>(offset)>length||
           element_size>length-static_cast<std::size_t>(offset)||
           static_cast<std::size_t>(count-1)>(length-static_cast<std::size_t>(offset)-element_size)/stride)
            return fail("GLB accessor straddles its buffer view");
        *out={data+offset,static_cast<std::size_t>(count),stride,component,parts,norm};
        return true;
    }
    bool node_matrix(const Json &node,Matrix *result) {
        const auto &m=member(node,"matrix");
        if(!m.is_null()) {
            if(!m.is_array()||m.size()!=16)return fail("Invalid GLB node matrix");
            for(std::size_t i=0;i<16;++i) {
                if(!m[i].is_number())return fail("Invalid GLB matrix number");
                (*result)[i]=number(m[i],std::numeric_limits<float>::quiet_NaN());
                if(!std::isfinite((*result)[i]))return fail("Nonfinite GLB matrix");
            }
            if(std::abs((*result)[3])>1e-6f||std::abs((*result)[7])>1e-6f||
               std::abs((*result)[11])>1e-6f||std::abs((*result)[15]-1)>1e-6f)return fail("GLB node matrix is not affine");
            return true;
        }
        std::array<float,3> t{0,0,0},s{1,1,1};std::array<float,4> q{0,0,0,1};
        const auto values=[&](const char *key,float *target,std::size_t count) {
            const auto &v=member(node,key);if(v.is_null())return true;
            if(!v.is_array()||v.size()!=count)return false;
            for(std::size_t i=0;i<count;++i) {
                target[i]=number(v[i],std::numeric_limits<float>::quiet_NaN());
                if(!std::isfinite(target[i]))return false;
            }
            return true;
        };
        if(!values("translation",t.data(),3)||!values("scale",s.data(),3)||!values("rotation",q.data(),4))return fail("Invalid GLB node transform");
        const float length=std::sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);
        if(length<1e-8f)return fail("Invalid GLB rotation quaternion");
        for(float &v:q)v/=length;
        const float x=q[0],y=q[1],z=q[2],w=q[3];
        *result={(1-2*y*y-2*z*z)*s[0],(2*x*y+2*w*z)*s[0],(2*x*z-2*w*y)*s[0],0,
                 (2*x*y-2*w*z)*s[1],(1-2*x*x-2*z*z)*s[1],(2*y*z+2*w*x)*s[1],0,
                 (2*x*z+2*w*y)*s[2],(2*y*z-2*w*x)*s[2],(1-2*x*x-2*y*y)*s[2],0,t[0],t[1],t[2],1};
        return true;
    }
    bool image(int texture_index,int *result) {
        const auto &texture=element(member(doc,"textures"),texture_index);
        const int source=integer(member(texture,"source"));
        const auto &images=member(doc,"images");
        const auto &image=element(images,source);
        if(!images.is_array()||images.size()>64)return fail("Too many GLB images");
        if(!texture.is_object()||!image.is_object()||!member(image,"uri").is_null())
            return fail("GLB texture must use an embedded image");
        if(source>=64)return fail("Too many GLB images");
        if(source>=0&&image_alias[static_cast<std::size_t>(source)]>=0){*result=image_alias[static_cast<std::size_t>(source)];return true;}
        if(model.images.size()<images.size())model.images.resize(images.size());
        auto &pixels=model.images[static_cast<std::size_t>(source)];
        if(pixels.width==0) {
            const unsigned char *data=nullptr;std::size_t length=0,stride=0;
            if(!view(integer(member(image,"bufferView")),&data,&length,&stride))return false;
            // Some official exports embed the exact same PNG more than once
            // for separate material slots. Reuse its decoded/GPU image while
            // preserving the original material assignment and resolution.
            for(std::size_t i=0;i<model.images.size();++i) {
                if(i==static_cast<std::size_t>(source)||model.images[i].width==0)continue;
                const auto &other=element(images,static_cast<int>(i));
                const unsigned char *other_data=nullptr;std::size_t other_length=0,other_stride=0;
                if(!view(integer(member(other,"bufferView")),&other_data,&other_length,&other_stride))return false;
                if(length==other_length&&std::memcmp(data,other_data,length)==0){*result=static_cast<int>(i);image_alias[static_cast<std::size_t>(source)]=*result;++model.deduplicated_images;return true;}
            }
            // Check the aggregate staging budget before stb allocates either
            // its temporary output or the retained RGBA copy. A failed model
            // must not exceed the arena merely to discover that it is large.
            int image_width=0,image_height=0,channels=0;
            if(length>static_cast<std::size_t>(std::numeric_limits<int>::max())||
               !stbi_info_from_memory(data,static_cast<int>(length),&image_width,&image_height,&channels)||
               image_width<=0||image_height<=0||image_width>8192||image_height>8192)
                return fail("GLB image dimensions are invalid");
            const std::size_t expected_pixels=static_cast<std::size_t>(image_width)*static_cast<std::size_t>(image_height);
            if(expected_pixels>(16u<<20)||expected_pixels>kMaxTexturePixels-texture_pixels)
                return fail("GLB textures exceed the exhibit memory limit");
            if(superseded())return fail("3D request superseded");
            pixels.width=image_width;pixels.height=image_height;pixels.alpha_known=channels<4;pixels.opaque=channels<4;
            if(defer_images){
                pixels.encoded_offset=static_cast<std::size_t>(data-bytes.data());pixels.encoded_length=length;pixels.encoded_fingerprint=encoded_fingerprint(data,length);
            }else{
                std::string decode_error;
                if(!yt::decode_image(std::string(reinterpret_cast<const char*>(data),length),&pixels.width,&pixels.height,&pixels.rgba,&decode_error))return fail("GLB image: "+decode_error);
                pixels.alpha_known=true;pixels.opaque=true;for(std::size_t n=3;n<pixels.rgba.size();n+=4)if(pixels.rgba[n]!=255){pixels.opaque=false;break;}
            }
            const std::size_t count=static_cast<std::size_t>(pixels.width)*static_cast<std::size_t>(pixels.height);
            if(count>kMaxTexturePixels-texture_pixels)return fail("GLB textures exceed the exhibit memory limit");
            texture_pixels+=count;
        }
        image_alias[static_cast<std::size_t>(source)]=source;*result=source;return true;
    }
    bool primitive(const Json &p,const Matrix &world) {
        if(!p.is_object())return fail("Invalid GLB primitive");
        const int mode=integer(member(p,"mode"),4);
        // CAD/SketchUp exports may include drafting edges beside their solid
        // triangles. The object pass renders surfaces, not those helper lines.
        // A file containing only lines still fails the no-visible-mesh check.
        if(mode>=0&&mode<=3)return true;
        if(mode!=4||!member(p,"targets").is_null()||!member(p,"extensions").is_null())
            return fail("Only uncompressed static GLB triangle primitives are supported");
        Access position,normals,tangents,indices;std::array<Access,4> uv;std::array<bool,4> has_uv{};
        const auto &attributes=member(p,"attributes");
        if(!accessor(integer(member(attributes,"POSITION")),3,false,&position))return false;
        const bool has_normals=!member(attributes,"NORMAL").is_null();
        const bool has_tangents=has_normals&&!member(attributes,"TANGENT").is_null();
        const bool indexed=!member(p,"indices").is_null();
        if(has_tangents&&(!accessor(integer(member(attributes,"TANGENT")),4,false,&tangents)||tangents.count!=position.count))return fail("Invalid GLB tangent count");
        if(has_normals&&(!accessor(integer(member(attributes,"NORMAL")),3,false,&normals)||normals.count!=position.count))return fail("Invalid GLB normal count");
        for(std::size_t set=0;set<4;++set) {
            const char *keys[]{"TEXCOORD_0","TEXCOORD_1","TEXCOORD_2","TEXCOORD_3"};
            has_uv[set]=!member(attributes,keys[set]).is_null();
            if(has_uv[set]&&(!accessor(integer(member(attributes,keys[set])),2,false,&uv[set])||uv[set].count!=position.count))return fail("Invalid GLB UV count");
        }
        if(indexed&&!accessor(integer(member(p,"indices")),1,true,&indices))return false;
        const std::size_t count=indexed?indices.count:position.count;
        if(count%3||count>kMaxIndices-index_count||position.count>kMaxVertices-vertex_count)return fail("GLB triangles exceed the exhibit size limit");
        if(model.parts.size()>=kMaxSourceParts)return fail("Too many GLB material primitives");
        Part part;
        const auto &material=element(member(doc,"materials"),integer(member(p,"material")));
        if(!member(p,"material").is_null()&&!material.is_object())return fail("GLB references a missing material");
        const auto&restore=member(member(material,"extras"),"museum_surface_restore");
        if(!restore.is_null()){
            if(!restore.is_object())return fail("Invalid material surface restoration");
            const auto read_rectangles=[&](const char*key,auto&out,int&count){
                const auto&rows=member(restore,key);if(rows.is_null())return true;
                if(!rows.is_array()||rows.size()>out.size())return false;
                count=static_cast<int>(rows.size());
                for(std::size_t n=0;n<rows.size();++n){if(!rows[n].is_array()||rows[n].size()!=4)return false;
                    for(std::size_t k=0;k<4;++k){if(!rows[n][k].is_number())return false;const double v=rows[n][k].template get<double>();if(!std::isfinite(v)||v<0||v>1)return false;out[n][k]=static_cast<float>(v);}
                    if(out[n][2]<=out[n][0]||out[n][3]<=out[n][1])return false;
                }return true;
            };
            if(!read_rectangles("regions",part.restore.regions,part.restore.region_count)||!read_rectangles("preserve",part.restore.details,part.restore.detail_count)||!read_rectangles("preserve_ink",part.restore.ink,part.restore.ink_count))return fail("Invalid restoration UV rectangle");
            const auto&values=member(restore,"linear_colour_roughness");
            if(!values.is_array()||values.size()!=4)return fail("Invalid restoration surface colour");
            for(std::size_t k=0;k<4;++k){if(!values[k].is_number())return fail("Invalid restoration surface value");const double v=values[k].get<double>();if(!std::isfinite(v)||v<0||v>1)return fail("Invalid restoration surface range");part.restore.colour_roughness[k]=static_cast<float>(v);}
        }
        part.double_sided=member(material,"doubleSided").is_boolean()&&member(material,"doubleSided").get<bool>();
        const auto &pbr=member(material,"pbrMetallicRoughness");
        part.roughness=std::clamp(number(member(pbr,"roughnessFactor"),1),.04f,1.0f);
        part.metallic=std::clamp(number(member(pbr,"metallicFactor"),1),0.0f,1.0f);
        const auto &factor=member(pbr,"baseColorFactor");
        if(!factor.is_null()) {
            if(!factor.is_array()||factor.size()!=4)return fail("Invalid GLB base color");
            for(std::size_t c=0;c<4;++c)part.color[c]=std::clamp(number(factor[c],1),0.0f,1.0f);
        }
        const auto &base_texture=member(pbr,"baseColorTexture");
        const auto map=[&](const Json &info,int *target,std::size_t slot) {
            if(info.is_null())return true;
            const int set=integer(member(info,"texCoord"),0);
            if(set<0||set>=4||!has_uv[static_cast<std::size_t>(set)]||!member(info,"extensions").is_null())return fail("GLB material map references unsupported or missing UV coordinates");
            part.uv_sets[slot]=set;
            const int texture_index=integer(member(info,"index"));
            const auto &texture=element(member(doc,"textures"),texture_index);
            if(!member(texture,"sampler").is_null()) {
                const auto &sampler=element(member(doc,"samplers"),integer(member(texture,"sampler")));
                if(!sampler.is_object())return fail("GLB texture references a missing sampler");
                auto &out=part.samplers[slot];
                out.min=integer(member(sampler,"minFilter"),GL_LINEAR_MIPMAP_LINEAR);out.mag=integer(member(sampler,"magFilter"),GL_LINEAR);
                out.s=integer(member(sampler,"wrapS"),GL_REPEAT);out.t=integer(member(sampler,"wrapT"),GL_REPEAT);
                if((out.mag!=GL_LINEAR&&out.mag!=GL_NEAREST)||(out.min!=GL_LINEAR&&out.min!=GL_NEAREST&&out.min!=GL_NEAREST_MIPMAP_NEAREST&&out.min!=GL_LINEAR_MIPMAP_NEAREST&&out.min!=GL_NEAREST_MIPMAP_LINEAR&&out.min!=GL_LINEAR_MIPMAP_LINEAR)||
                   (out.s!=GL_REPEAT&&out.s!=GL_CLAMP_TO_EDGE&&out.s!=GL_MIRRORED_REPEAT)||(out.t!=GL_REPEAT&&out.t!=GL_CLAMP_TO_EDGE&&out.t!=GL_MIRRORED_REPEAT))return fail("Invalid GLB texture sampler");
            }
            if(!image(texture_index,target))return false;
            model.images[static_cast<std::size_t>(*target)].roles|=slot<2?1u:2u;
            if(slot>=2)model.images[static_cast<std::size_t>(*target)].data_channels|=slot==2?7u:slot==3?6u:1u;
            return true;
        };
        if(!map(base_texture,&part.image,0)||!map(member(material,"emissiveTexture"),&part.emissive_image,1)||
           !map(member(material,"normalTexture"),&part.normal_image,2)||
           !map(member(pbr,"metallicRoughnessTexture"),&part.orm_image,3)||!map(member(material,"occlusionTexture"),&part.ao_image,4))return false;
        part.ao_strength=std::clamp(number(member(member(material,"occlusionTexture"),"strength"),1),0.0f,1.0f);
        const auto &emission=member(material,"emissiveFactor");
        if(!emission.is_null()) {
            if(!emission.is_array()||emission.size()!=3)return fail("Invalid GLB emission factor");
            for(std::size_t i=0;i<3;++i)part.emission[i]=std::clamp(number(emission[i]),0.0f,1.0f);
        }
        const float emission_strength=std::clamp(number(member(member(member(material,"extensions"),"KHR_materials_emissive_strength"),"emissiveStrength"),1),0.0f,32.0f);
        for(auto &value:part.emission)value*=emission_strength;
        part.normal_scale=std::clamp(number(member(member(material,"normalTexture"),"scale"),1),-64.0f,64.0f);
        const auto &extensions=member(material,"extensions");
        const auto &specular=member(extensions,"KHR_materials_specular");
        if(!specular.is_null()) {
            if(!specular.is_object())return fail("Invalid GLB specular extension");
            if(extensions.contains("KHR_materials_unlit")||extensions.contains("KHR_materials_pbrSpecularGlossiness"))return fail("Incompatible GLB specular material extensions");
            const auto &factor=member(specular,"specularFactor");
            if(!factor.is_null()) {
                const double value=factor.is_number()?factor.get<double>():-1;
                if(!std::isfinite(value)||value<0||value>1)return fail("Invalid GLB specular factor");
                part.specular=static_cast<float>(value);
            }
            const auto &color=member(specular,"specularColorFactor");
            if(!color.is_null()) {
                if(!color.is_array()||color.size()!=3)return fail("Invalid GLB specular colour factor");
                for(unsigned i=0;i<3;++i) {
                    const double value=color[i].is_number()?color[i].get<double>():-1;
                    if(!std::isfinite(value)||value<0)return fail("Invalid GLB specular colour factor");
                    // The dielectric F0 clamp saturates at25; bounding before the
                    // float conversion retains that exact response even for huge JSON numbers.
                    part.specular_color[i]=static_cast<float>(std::min(value,25.0));
                }
            }
            for(const char *map_name:{"specularTexture","specularColorTexture"})if(!member(specular,map_name).is_null()) {
                if(specular_required)return fail("Required KHR_materials_specular texture maps are not supported");
                const std::string note=std::string("Material map not rendered: KHR_materials_specular.")+map_name;
                if(model.notes.find(note)==std::string::npos) { if(!model.notes.empty())model.notes+="; ";model.notes+=note; }
            }
        }
        if(extensions.is_object())for(auto it=extensions.begin();it!=extensions.end();++it) {
            if(it.key()=="KHR_materials_unlit"||it.key()=="KHR_materials_emissive_strength"||it.key()=="KHR_materials_specular")continue;
            const std::string note="Material extension not rendered: "+it.key();
            if(model.notes.find(note)==std::string::npos) { if(!model.notes.empty())model.notes+="; ";model.notes+=note; }
        }
        part.blend=text(member(material,"alphaMode"),"BLEND");
        // Exporters often mark a completely opaque texture as BLEND. Keeping
        // those in the depth-writing pass avoids needless sorting artifacts.
        if(part.blend&&part.color[3]>=.999f) {
            bool opaque=true;
            if(part.image>=0) {
                const auto &pixels=model.images[static_cast<std::size_t>(part.image)];
                opaque=pixels.alpha_known&&pixels.opaque;
            }
            if(opaque)part.blend=false;
        }
        if(text(member(material,"alphaMode"),"MASK"))part.cutoff=std::clamp(number(member(material,"alphaCutoff"),.5f),0.0f,1.0f);
        part.unlit=member(material,"extensions").is_object()&&member(material,"extensions").contains("KHR_materials_unlit");
        // Cofactor columns implement inverse-transpose normals. Dividing by the
        // determinant retains the correct orientation for mirrored nodes.
        const Vec3 a{world[0],world[1],world[2]},b{world[4],world[5],world[6]},c{world[8],world[9],world[10]};
        const Vec3 ca=cross(b,c),cb=cross(c,a),cc=cross(a,b);
        const float determinant=a.x*ca.x+a.y*ca.y+a.z*ca.z;
        if(!std::isfinite(determinant)||std::abs(determinant)<1e-12f)return fail("Singular GLB node transform");
        part.mirrored=determinant<0;
        part.vertices.reserve(position.count);
        for(std::size_t index=0;index<position.count;++index) {
            if((index&4095u)==0&&superseded())return fail("3D request superseded");
            Vertex vertex;
            vertex.position=transform(world,{position.read(index,0),position.read(index,1),position.read(index,2)});
            if(has_normals) {
                const Vec3 n{normals.read(index,0),normals.read(index,1),normals.read(index,2)};
                if(!finite(n))return fail("Nonfinite GLB normal data");
                vertex.normal=normal({(ca.x*n.x+cb.x*n.y+cc.x*n.z)/determinant,(ca.y*n.x+cb.y*n.y+cc.y*n.z)/determinant,(ca.z*n.x+cb.z*n.y+cc.z*n.z)/determinant});
            }
            if(has_tangents) {
                const Vec3 authored{tangents.read(index,0),tangents.read(index,1),tangents.read(index,2)};
                const float sign=tangents.read(index,3);
                if(!finite(authored)||!std::isfinite(sign)||std::abs(std::abs(sign)-1)>1e-4f)return fail("Invalid GLB tangent handedness");
                Vec3 tangent{world[0]*authored.x+world[4]*authored.y+world[8]*authored.z,world[1]*authored.x+world[5]*authored.y+world[9]*authored.z,world[2]*authored.x+world[6]*authored.y+world[10]*authored.z};
                const float projection=tangent.x*vertex.normal.x+tangent.y*vertex.normal.y+tangent.z*vertex.normal.z;
                tangent=normal({tangent.x-projection*vertex.normal.x,tangent.y-projection*vertex.normal.y,tangent.z-projection*vertex.normal.z});
                vertex.tangent={tangent.x,tangent.y,tangent.z,sign*(determinant<0?-1.f:1.f)};
            }
            for(std::size_t set=0;set<4;++set)if(has_uv[set]) {
                vertex.uv[set]={uv[set].read(index,0),uv[set].read(index,1)};
                if(!std::isfinite(vertex.uv[set][0])||!std::isfinite(vertex.uv[set][1]))return fail("Nonfinite GLB UV data");
            }
            if(!finite(vertex.position)||!finite(vertex.normal))return fail("Nonfinite GLB vertex data");
            part.vertices.push_back(vertex);
        }
        part.indices.reserve(count);
        for(std::size_t i=0;i<count;++i) {
            const std::size_t index=indexed?indices.index(i):i;
            if(index>=position.count)return fail("GLB index is outside its vertex accessor");
            part.indices.push_back(static_cast<std::uint32_t>(index));
        }
        if(!has_normals) {
            if(count>kMaxVertices-vertex_count)return fail("Flat-normal vertex splits exceed the exhibit vertex limit");
            std::vector<Vertex> flat;flat.reserve(count);
            for(std::size_t i=0;i<count;i+=3) {
                const auto a=part.indices[i],b=part.indices[i+1],c=part.indices[i+2];
                const Vec3 face=normal(cross(sub(part.vertices[b].position,part.vertices[a].position),sub(part.vertices[c].position,part.vertices[a].position)));
                for(std::size_t corner=0;corner<3;++corner){auto vertex=part.vertices[part.indices[i+corner]];vertex.normal=face;vertex.tangent={};flat.push_back(vertex);part.indices[i+corner]=static_cast<std::uint32_t>(i+corner);}
            }
            part.vertices=std::move(flat);
        }
        vertex_count+=part.vertices.size();index_count+=count;model.parts.push_back(std::move(part));return true;
    }
    bool read(const std::string &path) {
        const auto source_started=std::chrono::steady_clock::now();
        FILE *stream=std::fopen(path.c_str(),"rb");
        if(!stream)return fail("The downloaded 3D model cannot be opened");
        if(std::fseek(stream,0,SEEK_END)!=0){std::fclose(stream);return fail("The GLB download cannot be sized");}
        const long length=std::ftell(stream);
        if(length<20||static_cast<unsigned long>(length)>kMaxFile||std::fseek(stream,0,SEEK_SET)!=0){std::fclose(stream);return fail("GLB file exceeds the 160 MiB exhibit limit");}
        bytes.resize(static_cast<std::size_t>(length));
        const std::size_t received=std::fread(bytes.data(),1,bytes.size(),stream);
        source_read_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-source_started).count();
        if(defer_images){encoded_file=std::make_shared<EncodedFile>();encoded_file->stream=stream;encoded_file->bytes=bytes.size();encoded_file->artwork_path=path.size()>4?path.substr(0,path.size()-4)+".artwork.pmc":std::string{};if(fstat(fileno(stream),&encoded_file->identity)!=0)return fail("The GLB file identity cannot be read");}
        else std::fclose(stream);
        if(received!=bytes.size())return fail("The GLB download is incomplete");
        if(encoded_file){FILE*cache=std::fopen(encoded_file->artwork_path.c_str(),"rb");if(cache){std::array<char,8>magic{};const auto count=std::fread(magic.data(),1,magic.size(),cache);std::fclose(cache);if(count==8&&std::memcmp(magic.data(),"PMAC0002",8)==0){if(superseded())return fail("3D request superseded");const auto hash_started=std::chrono::steady_clock::now();encoded_file->source_sha256=object_source_sha256_hex(bytes.data(),bytes.size());source_hash_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-hash_started).count();hui::sys::log("[Museum] source SHA256 binding %.2fms / %zu bytes / worker",source_hash_ms,bytes.size());}}}
        if(u32(bytes.data())!=0x46546c67||u32(bytes.data()+4)!=2||u32(bytes.data()+8)!=bytes.size())return fail("The exhibit is not a complete GLB 2.0 file");
        std::size_t cursor=12;bool json_seen=false;
        while(cursor<bytes.size()) {
            if(bytes.size()-cursor<8)return fail("Truncated GLB chunk header");
            const std::size_t size=u32(bytes.data()+cursor);const auto type=u32(bytes.data()+cursor+4);cursor+=8;
            if(size%4||size>bytes.size()-cursor)return fail("Invalid GLB chunk size");
            if(type==0x4e4f534a) {
                if(json_seen||cursor!=20||size>(4u<<20))return fail("Invalid GLB JSON chunk");
                const auto *start=reinterpret_cast<const char*>(bytes.data()+cursor);
                if(!json_depth_ok(start,start+size))return fail("GLB JSON nesting exceeds the exhibit limit");
                doc=Json::parse(start,start+size,nullptr,false);json_seen=true;
            } else if(type==0x004e4942) {
                if(!json_seen||bin_length)return fail("Invalid GLB binary chunk order");
                bin_offset=cursor;bin_length=size;
            }
            cursor+=size;
        }
        if(!json_seen||!bin_length||!doc.is_object()||!text(member(member(doc,"asset"),"version"),"2.0"))return fail("Missing GLB 2.0 asset or binary chunk");
        const auto &required=member(doc,"extensionsRequired");
        if(!required.is_null()) {
            if(!required.is_array())return fail("Invalid GLB extension list");
            for(const auto &e:required) {
                if(text(e,"KHR_materials_specular")){specular_required=true;continue;}
                if(!text(e,"KHR_materials_unlit")&&!text(e,"KHR_materials_emissive_strength"))return fail("This GLB requires an unsupported extension");
            }
        }
        const auto &buffers=member(doc,"buffers");
        const auto &buffer=element(buffers,0);
        const int declared=integer(member(buffer,"byteLength"));
        if(!buffers.is_array()||buffers.size()!=1||!member(buffer,"uri").is_null()||declared<0||static_cast<std::size_t>(declared)>bin_length)return fail("GLB must contain one embedded binary buffer");
        bin_length=static_cast<std::size_t>(declared);
        if(member(doc,"skins").is_array()&&!member(doc,"skins").empty())return fail("Skinned GLB objects are not supported");
        const auto &animations=member(doc,"animations");
        if(!animations.is_null()) {
            if(!animations.is_array()||animations.size()>16)return fail("Invalid GLB animation list");
            // Render the author's rest pose. Simple lid/turntable TRS tracks
            // may accompany an otherwise static product model; no animation
            // accessors are decoded or evaluated in this exhibit viewer.
            for(const auto &animation:animations) {
                const auto &channels=member(animation,"channels");
                if(!channels.is_array()||channels.size()>1024)return fail("Invalid GLB animation channels");
                for(const auto &channel:channels) {
                    const auto &target=member(channel,"target"),&path=member(target,"path");
                    if(element(member(doc,"nodes"),integer(member(target,"node"))).is_null()||
                       !(text(path,"translation")||text(path,"rotation")||text(path,"scale")))return fail("Only static rest poses with TRS animation tracks are supported");
                }
            }
        }
        const auto &nodes=member(doc,"nodes"),&scenes=member(doc,"scenes"),&images=member(doc,"images");
        if(!nodes.is_array()||nodes.size()>kMaxNodes||(images.is_array()&&images.size()>64))return fail("GLB scene exceeds the exhibit limit");
        const auto &scene=element(scenes,integer(member(doc,"scene"),0));
        const auto &roots=member(scene,"nodes");
        if(!roots.is_array())return fail("GLB has no default scene");
        std::vector<bool> active(nodes.size(),false);std::size_t visited=0;
        std::function<bool(int,const Matrix&,int,const std::string&,bool)> walk;
        walk=[&](int index,const Matrix &parent,int depth,const std::string &inherited_group,bool inherited_node_selection) {
            const auto &node=element(nodes,index);
            if(!node.is_object()||depth>64||++visited>kMaxNodes*2)return fail("Invalid or overly deep GLB node tree");
            if(active[static_cast<std::size_t>(index)])return fail("GLB node tree contains a cycle");
            active[static_cast<std::size_t>(index)]=true;
            if(!member(node,"skin").is_null())return fail("Skinned GLB node is unsupported");
            Matrix local{};if(!node_matrix(node,&local))return false;
            const Matrix world=multiply(parent,local);
            const auto &assembly=member(member(node,"extras"),"assembly");
            const std::string group=assembly.is_string()?assembly.get<std::string>():inherited_group;
            // Explicit node: selectors retain an authored glTF subtree. Plain
            // selectors keep the original CAD extras.assembly semantics.
            const auto &node_name=member(node,"name");
            const std::string node_selector=node_name.is_string()?"node:"+node_name.get<std::string>():std::string{};
            const bool selected_node=inherited_node_selection||(!node_selector.empty()&&std::find(include_groups.begin(),include_groups.end(),node_selector)!=include_groups.end());
            const bool included=include_groups.empty()||selected_node||std::find(include_groups.begin(),include_groups.end(),group)!=include_groups.end();
            if(included&&!member(node,"mesh").is_null()) {
                const auto &mesh=element(member(doc,"meshes"),integer(member(node,"mesh")));
                const auto &primitives=member(mesh,"primitives");
                if(!primitives.is_array()||primitives.size()>512)return fail("Invalid GLB mesh");
                for(const auto &p:primitives)if(!primitive(p,world))return false;
            }
            const auto &children=member(node,"children");
            if(!children.is_null()) {
                if(!children.is_array()||children.size()>kMaxNodes)return fail("Invalid GLB child list");
                for(const auto &child:children)if(!walk(integer(child),world,depth+1,group,selected_node))return false;
            }
            active[static_cast<std::size_t>(index)]=false;return true;
        };
        if(superseded())return fail("3D request superseded");
        for(const auto &root:roots)if(!walk(integer(root),identity(),0,{},false))return false;
        if(model.parts.empty())return fail("GLB contains no visible triangle meshes");
        Vec3 low{1e30f,1e30f,1e30f},high{-1e30f,-1e30f,-1e30f};
        for(const auto &part:model.parts)for(const auto &v:part.vertices) {
            low.x=std::min(low.x,v.position.x);low.y=std::min(low.y,v.position.y);low.z=std::min(low.z,v.position.z);
            high.x=std::max(high.x,v.position.x);high.y=std::max(high.y,v.position.y);high.z=std::max(high.z,v.position.z);
        }
        const Vec3 center{(low.x+high.x)*.5f,(low.y+high.y)*.5f,(low.z+high.z)*.5f};
        float radius_squared=0;
        for(const auto &part:model.parts)for(const auto &v:part.vertices) {
            const auto p=sub(v.position,center);radius_squared=std::max(radius_squared,p.x*p.x+p.y*p.y+p.z*p.z);
        }
        const float radius=std::sqrt(radius_squared);
        if(!std::isfinite(radius)||radius<1e-10f)return fail("GLB has no measurable geometry");
        for(auto &part:model.parts)for(auto &v:part.vertices) {
            const auto p=sub(v.position,center);v.position={p.x/radius,p.y/radius,p.z/radius};
        }
        std::size_t dual_role_bytes=0;
        for(const auto &image:model.images)if(image.roles==3)dual_role_bytes+=static_cast<std::size_t>(image.width)*image.height*4;
        if(dual_role_bytes>(64u<<20))return fail("Dual colour/data texture views exceed the 64 MiB duplicate-storage budget");
        if(!model.notes.empty())std::fprintf(stderr,"[HUI] 3D fidelity limitation: %s\n",model.notes.c_str());
        // The JSON and downloaded bytes are no longer needed after traversal.
        // Release them before merging so they never overlap merge reallocation.
        if(!defer_images)std::vector<unsigned char>().swap(bytes);doc=Json{};
        // Merge already-transformed indexed meshes by appearance, preserving
        // every original triangle while keeping detailed CAD to a few draws.
        const auto compatible=[](const Part&part,const Part&other){return part.restore==other.restore&&part.color==other.color&&part.image==other.image&&part.emissive_image==other.emissive_image&&part.normal_image==other.normal_image&&part.orm_image==other.orm_image&&part.ao_image==other.ao_image&&part.ao_strength==other.ao_strength&&part.samplers==other.samplers&&part.emission==other.emission&&part.uv_sets==other.uv_sets&&part.normal_scale==other.normal_scale&&part.cutoff==other.cutoff&&part.roughness==other.roughness&&part.metallic==other.metallic&&part.specular==other.specular&&part.specular_color==other.specular_color&&part.unlit==other.unlit&&part.blend==other.blend&&part.double_sided==other.double_sided&&part.mirrored==other.mirrored;};
        std::vector<std::size_t> representatives,assignment(model.parts.size()),vertices,indices;
        for(std::size_t n=0;n<model.parts.size();++n){
            std::size_t group=0;for(;group<representatives.size();++group)if(compatible(model.parts[n],model.parts[representatives[group]]))break;
            if(group==representatives.size()){representatives.push_back(n);vertices.push_back(0);indices.push_back(0);}
            assignment[n]=group;vertices[group]+=model.parts[n].vertices.size();indices[group]+=model.parts[n].indices.size();
        }
        std::vector<Part> merged;merged.reserve(representatives.size());
        for(std::size_t group=0;group<representatives.size();++group){
            merged.push_back(std::move(model.parts[representatives[group]]));auto&dest=merged.back();dest.vertices.reserve(vertices[group]);dest.indices.reserve(indices[group]);
            for(std::size_t n=representatives[group]+1;n<model.parts.size();++n){
                if(assignment[n]!=group)continue;auto&part=model.parts[n];const auto base=static_cast<std::uint32_t>(dest.vertices.size());
                dest.vertices.insert(dest.vertices.end(),part.vertices.begin(),part.vertices.end());for(auto index:part.indices)dest.indices.push_back(base+index);
                std::vector<Vertex>().swap(part.vertices);std::vector<std::uint32_t>().swap(part.indices);
            }
        }
        model.parts=std::move(merged);
        for(auto&part:model.parts){for(const auto&v:part.vertices){part.center.x+=v.position.x;part.center.y+=v.position.y;part.center.z+=v.position.z;if(std::abs(v.tangent[3])>.5f)++part.tangent_vertices;}const float count=float(part.vertices.size());part.center.x/=count;part.center.y/=count;part.center.z/=count;}

        if(model.parts.size()>128)return fail("GLB exceeds the 128 material-group draw budget");
        if(defer_images&&!encoded_file->unchanged())return fail("The GLB file changed while being prepared");
        // Only prepared geometry/decoded pixels cross the worker handoff.
        // The potentially 128 MiB source and JSON are freed before GPU upload.
        std::vector<unsigned char>().swap(bytes);doc=Json{};
        return true;
    }
};

// Preserve state touched by the offscreen pass; UI batching must be flushed
// before calling render. No second renderer or platform window is involved.
struct State {
    GLint draw=0,read=0,program=0,vao=0,array=0,active=0,textures[5]{},samplers[5]{},renderbuffer=0;
    GLint viewport[4]{},depth_func=0,blend_src_rgb=0,blend_dst_rgb=0,blend_src_a=0,blend_dst_a=0,front_face=0,cull_mode=0;
    GLint equation_rgb=0,equation_a=0,unpack=0,row_length=0,skip_pixels=0,skip_rows=0,alignment=0;
    GLboolean depth=0,blend=0,cull=0,scissor=0,srgb=0,multisample=0,alpha_coverage=0,sample_coverage=0,depth_mask=0,color_mask[4]{};
    GLfloat clear[4]{},depth_clear=1;
    State() {
        glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING,&draw);glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&read);
        glGetIntegerv(GL_CURRENT_PROGRAM,&program);glGetIntegerv(GL_VERTEX_ARRAY_BINDING,&vao);
        glGetIntegerv(GL_ARRAY_BUFFER_BINDING,&array);glGetIntegerv(GL_RENDERBUFFER_BINDING,&renderbuffer);
        glGetIntegerv(GL_ACTIVE_TEXTURE,&active);
        for(unsigned i=0;i<5;++i){glActiveTexture(GL_TEXTURE0+i);glGetIntegerv(GL_TEXTURE_BINDING_2D,&textures[i]);glGetIntegerv(GL_SAMPLER_BINDING,&samplers[i]);}
        glActiveTexture(GL_TEXTURE0);
        glGetIntegerv(GL_VIEWPORT,viewport);glGetIntegerv(GL_DEPTH_FUNC,&depth_func);
        glGetIntegerv(GL_FRONT_FACE,&front_face);glGetIntegerv(GL_CULL_FACE_MODE,&cull_mode);
        glGetIntegerv(GL_BLEND_SRC_RGB,&blend_src_rgb);glGetIntegerv(GL_BLEND_DST_RGB,&blend_dst_rgb);
        glGetIntegerv(GL_BLEND_SRC_ALPHA,&blend_src_a);glGetIntegerv(GL_BLEND_DST_ALPHA,&blend_dst_a);
        glGetIntegerv(GL_BLEND_EQUATION_RGB,&equation_rgb);glGetIntegerv(GL_BLEND_EQUATION_ALPHA,&equation_a);
        glGetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING,&unpack);glGetIntegerv(GL_UNPACK_ROW_LENGTH,&row_length);
        glGetIntegerv(GL_UNPACK_SKIP_PIXELS,&skip_pixels);glGetIntegerv(GL_UNPACK_SKIP_ROWS,&skip_rows);glGetIntegerv(GL_UNPACK_ALIGNMENT,&alignment);
        depth=glIsEnabled(GL_DEPTH_TEST);blend=glIsEnabled(GL_BLEND);cull=glIsEnabled(GL_CULL_FACE);scissor=glIsEnabled(GL_SCISSOR_TEST);
        srgb=glIsEnabled(GL_FRAMEBUFFER_SRGB);glGetFloatv(GL_DEPTH_CLEAR_VALUE,&depth_clear);
        multisample=glIsEnabled(GL_MULTISAMPLE);alpha_coverage=glIsEnabled(GL_SAMPLE_ALPHA_TO_COVERAGE);sample_coverage=glIsEnabled(GL_SAMPLE_COVERAGE);
        glGetBooleanv(GL_DEPTH_WRITEMASK,&depth_mask);glGetBooleanv(GL_COLOR_WRITEMASK,color_mask);glGetFloatv(GL_COLOR_CLEAR_VALUE,clear);
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER,0);glPixelStorei(GL_UNPACK_ROW_LENGTH,0);glPixelStorei(GL_UNPACK_SKIP_PIXELS,0);glPixelStorei(GL_UNPACK_SKIP_ROWS,0);glPixelStorei(GL_UNPACK_ALIGNMENT,4);
    }
    ~State() {
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER,static_cast<GLuint>(draw));glBindFramebuffer(GL_READ_FRAMEBUFFER,static_cast<GLuint>(read));
        glUseProgram(static_cast<GLuint>(program));glBindVertexArray(static_cast<GLuint>(vao));glBindBuffer(GL_ARRAY_BUFFER,static_cast<GLuint>(array));
        glBindRenderbuffer(GL_RENDERBUFFER,static_cast<GLuint>(renderbuffer));
        for(unsigned i=0;i<5;++i){glActiveTexture(GL_TEXTURE0+i);glBindTexture(GL_TEXTURE_2D,static_cast<GLuint>(textures[i]));glBindSampler(i,static_cast<GLuint>(samplers[i]));}
        glActiveTexture(static_cast<GLenum>(active));
        glViewport(viewport[0],viewport[1],viewport[2],viewport[3]);glDepthFunc(static_cast<GLenum>(depth_func));
        glFrontFace(static_cast<GLenum>(front_face));glCullFace(static_cast<GLenum>(cull_mode));
        const auto enable=[](GLenum cap,GLboolean on){if(on)glEnable(cap);else glDisable(cap);};
        enable(GL_DEPTH_TEST,depth);enable(GL_BLEND,blend);enable(GL_CULL_FACE,cull);enable(GL_SCISSOR_TEST,scissor);
        enable(GL_FRAMEBUFFER_SRGB,srgb);glClearDepth(depth_clear);
        enable(GL_MULTISAMPLE,multisample);enable(GL_SAMPLE_ALPHA_TO_COVERAGE,alpha_coverage);enable(GL_SAMPLE_COVERAGE,sample_coverage);
        glDepthMask(depth_mask);glColorMask(color_mask[0],color_mask[1],color_mask[2],color_mask[3]);
        glBlendEquationSeparate(static_cast<GLenum>(equation_rgb),static_cast<GLenum>(equation_a));
        glBlendFuncSeparate(static_cast<GLenum>(blend_src_rgb),static_cast<GLenum>(blend_dst_rgb),static_cast<GLenum>(blend_src_a),static_cast<GLenum>(blend_dst_a));
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER,static_cast<GLuint>(unpack));glPixelStorei(GL_UNPACK_ROW_LENGTH,row_length);glPixelStorei(GL_UNPACK_SKIP_PIXELS,skip_pixels);glPixelStorei(GL_UNPACK_SKIP_ROWS,skip_rows);glPixelStorei(GL_UNPACK_ALIGNMENT,alignment);
        glClearColor(clear[0],clear[1],clear[2],clear[3]);
    }
};

// Generic metallic/roughness equations follow the glTF material model:
// https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials
constexpr const char *kVertex=R"(
layout(location=0)in vec3 position;layout(location=1)in vec3 normal;
layout(location=2)in vec2 uv;layout(location=3)in vec2 uv1;layout(location=4)in vec2 uv2;layout(location=5)in vec2 uv3;layout(location=6)in vec4 tangent;
uniform mat4 mvp;uniform mat3 rotation;
out vec3 vNormal;out vec3 vPosition;out vec2 vUv;out vec2 vUv1;out vec2 vUv2;out vec2 vUv3;out vec4 vTangent;
void main(){vNormal=rotation*normal;vTangent=vec4(rotation*tangent.xyz,tangent.w);vPosition=rotation*position;vUv=uv;vUv1=uv1;vUv2=uv2;vUv3=uv3;gl_Position=mvp*vec4(position,1.0);}
)";
constexpr const char *kFragment=R"(
in vec3 vNormal;in vec3 vPosition;in vec2 vUv;in vec2 vUv1;in vec2 vUv2;in vec2 vUv3;in vec4 vTangent;
uniform vec4 baseColor;uniform sampler2D artwork;uniform int textured,unlit,blended,alphaPass;
uniform float cutoff,roughness,metallic,specular;uniform vec3 specularColor;out vec4 fragColor;
uniform int pinStudio;
uniform sampler2D emissionMap,normalMap,ormMap,aoMap;uniform int hasEmission,hasNormal,hasOrm,hasAo,aoUv;uniform vec3 emission;uniform float normalScale,aoStrength;
uniform ivec4 uvSets;
uniform vec4 restoreRegions[4],restoreDetails[4],restoreInk[4],restoreColourRoughness;uniform ivec3 restoreCounts;
vec2 texcoord(int index){return index==3?vUv3:index==2?vUv2:index==1?vUv1:vUv;}
float rectangleCoverage(vec2 uv,vec4 r){vec2 edge=min(uv-r.xy,r.zw-uv);return smoothstep(0.0,.001,min(edge.x,edge.y));}
float restoredSurface(vec2 uv,vec3 colour){
 float mask=0.0;for(int i=0;i<4;++i)if(i<restoreCounts.x)mask=max(mask,rectangleCoverage(uv,restoreRegions[i]));
 for(int i=0;i<4;++i)if(i<restoreCounts.y)mask*=1.0-rectangleCoverage(uv,restoreDetails[i]);
 // Keep only the original printed pigment or embossed lettering inside
 // these authored regions, so a dirty rectangle cannot survive around a logo.
 float pigment=smoothstep(.008,.035,max(colour.r,max(colour.g,colour.b)));
 float embossed=hasNormal!=0?smoothstep(.08,.18,length(texture(normalMap,texcoord(uvSets.z)).xy*2.0-1.0)):0.0;
 for(int i=0;i<4;++i)if(i<restoreCounts.z)mask*=1.0-rectangleCoverage(uv,restoreInk[i])*max(pigment,embossed);
 // Apertures have explicit protected UV regions.
 // No luminance threshold: dark scuffs must not become new black blotches.
 return mask;
}
const float PI=3.141592653589793;
vec3 fresnel(vec3 f0,float f90,float cosine){float x=1.0-clamp(cosine,0.0,1.0);float x2=x*x;return f0+(f90-f0)*(x2*x2*x);}
vec3 dielectricFresnel(float cosine){return fresnel(min(vec3(.04)*specularColor,vec3(1.0))*specular,specular,cosine);}
float maxComponent(vec3 value){return max(value.r,max(value.g,value.b));}
vec3 directLight(vec3 n,vec3 v,vec3 l,vec3 radiance,vec3 albedo,float metal,float perceptualRoughness){
 float nv=max(dot(n,v),.0001),nl=max(dot(n,l),0.0);if(nl<=0.0)return vec3(0.0);
 vec3 h=normalize(v+l);float nh=max(dot(n,h),0.0),vh=max(dot(v,h),0.0);
 float alpha=perceptualRoughness*perceptualRoughness,a2=alpha*alpha;
 float denominator=nh*nh*(a2-1.0)+1.0;
 float distribution=a2/max(PI*denominator*denominator,1e-8);
 float visibility=.5/max(nl*sqrt(nv*nv*(1.0-a2)+a2)+nv*sqrt(nl*nl*(1.0-a2)+a2),1e-6);
 vec3 dielectric=dielectricFresnel(vh);vec3 f=mix(dielectric,fresnel(albedo,1.0,vh),metal);
 vec3 diffuse=(1.0-maxComponent(dielectric))*(1.0-metal)*albedo/PI;
 return (diffuse+f*distribution*visibility)*radiance*nl;
}
void main(){
 // Colour samplers use SRGB8_ALPHA8; the driver decodes before filtering.
 // All factors and normal/MR/AO samplers remain linear.
 vec4 c=baseColor;if(textured!=0)c*=texture(artwork,texcoord(uvSets.x));
 float restore=restoreCounts.x>0?restoredSurface(texcoord(uvSets.x),c.rgb):0.0;
 c.rgb=mix(c.rgb,restoreColourRoughness.rgb,restore);
 if(cutoff>=0.0&&c.a<cutoff)discard;
 if(alphaPass==1&&c.a<.999)discard;if(alphaPass==2&&c.a>=.999)discard;
 if(unlit!=0){fragColor=vec4(c.rgb,blended!=0?c.a:1.0);return;}
 vec3 ng=normalize(vNormal),n=ng;bool back=!gl_FrontFacing;if(back)n=-n;
 if(hasNormal!=0){
  vec3 detail=texture(normalMap,texcoord(uvSets.z)).xyz*2.0-1.0;detail.xy=mix(detail.xy,clamp(detail.xy,vec2(-.025),vec2(.025)),restore);detail.xy*=normalScale;
  if(abs(vTangent.w)>.5){
   vec3 t=normalize(vTangent.xyz-ng*dot(ng,vTangent.xyz));vec3 b=cross(ng,t)*vTangent.w;
   if(back){t=-t;b=-b;}n=normalize(mat3(t,b,n)*detail);
  }else{
   vec2 normalUv=texcoord(uvSets.z);vec3 p1=dFdx(vPosition),p2=dFdy(vPosition);vec2 u1=dFdx(normalUv),u2=dFdy(normalUv);
   if(pinStudio!=0){
    // Derivative magnitudes shrink with screen resolution and zoom. The
    // cotangent frame is scale-invariant, but its squared magnitude is not:
    // an absolute epsilon otherwise drops the stamped reverse normal map at
    // close range. Normalize each derivative pair before testing degeneracy.
    float ps=max(length(p1),length(p2)),us=max(length(u1),length(u2));
    if(ps>0.0&&us>0.0){p1/=ps;p2/=ps;u1/=us;u2/=us;}
   }
   vec3 a=cross(p2,n),b=cross(n,p1),t=a*u1.x+b*u2.x,bt=a*u1.y+b*u2.y;
   float magnitude=max(dot(t,t),dot(bt,bt));if(magnitude>1e-12){float inv=inversesqrt(magnitude);n=normalize(mat3(t*inv,bt*inv,n)*detail);}
  }
 }
 float r=clamp(roughness,.04,1.0),m=metallic;if(hasOrm!=0){vec3 orm=texture(ormMap,texcoord(uvSets.w)).rgb;r=clamp(r*orm.g,.04,1.0);m=clamp(m*orm.b,0.0,1.0);}
 r=mix(r,restoreColourRoughness.a,restore);
 vec3 v=normalize(vec3(0.0,0.0,4.1)-vPosition);
 vec3 direct=directLight(n,v,normalize(vec3(-.65,.85,1.2)),vec3(3.1),c.rgb,m,r)
            +directLight(n,v,normalize(vec3(.8,.15,.6)),vec3(.70),c.rgb,m,r)
            +directLight(n,v,normalize(vec3(-.4,.25,-1.0)),vec3(.30),c.rgb,m,r);
 float nv=max(dot(n,v),0.0);vec3 dielectric=dielectricFresnel(nv);vec3 f=mix(dielectric,fresnel(c.rgb,1.0,nv),m);
 // Bounded neutral hemispheric studio approximation; no artist HDR map is
 // claimed. AO affects this indirect contribution, never the direct lights.
 vec3 environment=mix(vec3(.38),vec3(.64),n.y*.5+.5);
 vec3 diffuseAmbient=(1.0-maxComponent(dielectric))*(1.0-m)*c.rgb*environment;
 vec3 specularAmbient=f*environment*(1.0-.5*r);
 if(pinStudio!=0){
  // View-dependent reflections of broad studio light cards. These are an
  // analytic environment, not painted highlights glued to the pin artwork.
  vec3 reflected=reflect(-v,n);
  float blur=.055+r*.34;
  float key=1.0-smoothstep(.15,.15+blur,abs(reflected.x+.36));
  float fillCard=1.0-smoothstep(.10,.10+blur,abs(reflected.x-.68));
  float ceiling=smoothstep(.12,.12+blur,reflected.y);
  vec3 studio=vec3(.055)+vec3(1.35)*key+vec3(.48,.54,.66)*fillCard+vec3(.26)*ceiling;
  specularAmbient=f*studio*(1.0-.45*r);
 }
 float ao=hasAo!=0?mix(1.0,texture(aoMap,texcoord(aoUv)).r,aoStrength):1.0;
 vec3 emitted=emission;if(hasEmission!=0)emitted*=texture(emissionMap,texcoord(uvSets.y)).rgb;
 fragColor=vec4(max(direct+(diffuseAmbient+specularAmbient)*ao+emitted,vec3(0.0)),blended!=0?c.a:1.0);
}
)";
constexpr const char *kResolveVertex=R"(
out vec2 uv;
void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.0-1.0,0.0,1.0);}
)";
constexpr const char *kResolveFragment=R"(
in vec2 uv;uniform sampler2D scene;uniform vec2 inverseSize;out vec4 fragColor;
vec3 encodeSRGB(vec3 linearColor){vec3 c=max(linearColor,vec3(0.0));return mix(1.055*pow(c,vec3(1.0/2.4))-.055,c*12.92,lessThanEqual(c,vec3(.0031308)));}
void main(){
 vec4 c=texture(scene,uv);
 // Coverage-only post AA: source texture lookup decodes sRGB before filtering.
 // All five opaque neighbours return the exact centre sample, preserving the
 // original lettering, decals and material detail within the model. Only a
 // changing silhouette alpha is filtered, in linear premultiplied colour.
 float n=texture(scene,uv+vec2(0.0,inverseSize.y)).a;
 float s=texture(scene,uv-vec2(0.0,inverseSize.y)).a;
 float e=texture(scene,uv+vec2(inverseSize.x,0.0)).a;
 float w=texture(scene,uv-vec2(inverseSize.x,0.0)).a;
 float low=min(c.a,min(min(n,s),min(e,w))),high=max(c.a,max(max(n,s),max(e,w)));
 vec2 gradient=vec2(e-w,n-s);float magnitude=dot(gradient,gradient);
 if(high-low>.05&&magnitude>.0001){
  vec2 step=gradient*inversesqrt(magnitude)*inverseSize*.5;
  c=(texture(scene,uv+step)+texture(scene,uv-step))*.5;
 }
 fragColor=vec4(encodeSRGB(c.a>.00001?c.rgb/c.a:vec3(0.0)),c.a);
}
)";
} // namespace

namespace {
using SceneClock=std::chrono::steady_clock;
double elapsed_ms(SceneClock::time_point start){return std::chrono::duration<double,std::milli>(SceneClock::now()-start).count();}
struct CpuSample {double&last;double&peak;double*total=nullptr;SceneClock::time_point start=SceneClock::now();~CpuSample(){last=elapsed_ms(start);peak=std::max(peak,last);if(total)*total+=last;}};
}
struct MipPixels {int width=0,height=0;std::vector<std::uint8_t> bytes;};
struct ImageUpload {
    Pixels source;int texture_limit=0;std::shared_ptr<EncodedFile> encoded;std::string error;std::array<std::vector<MipPixels>,2> levels;std::size_t index=0,role=0,level=0,row=0;std::uint64_t serial=0;bool allocated=false;
    std::vector<std::uint8_t> packed_base;std::vector<MipPixels> packed_levels;std::array<unsigned,2> packed_channels{};unsigned packed_components=0;bool compact_active=false;
    double prepare_ms=0,decode_ms=0,cache_decode_ms=0;bool use_cache=true,cache_hit=false;
    std::array<bool,2> uniform_roles{};
    bool direct_payload=false,compact_reprepare=false,disable_compact=false;
    std::array<std::size_t,2> original_view_bytes{};
};
#include "museum/object_artwork_cache.hpp"
// Check exact RGBA equality, including unused channels and every existing mip.
// No tolerance, inferred material colour or lossy normal reconstruction.
bool constant_texels(const std::vector<std::uint8_t>&bytes,const std::array<std::uint8_t,4>&value,
                     const std::atomic<std::uint64_t>&revision,std::uint64_t serial){
    if(bytes.empty()||bytes.size()%4)return false;
    const auto first=std::min(std::size_t(65536),bytes.size());
    for(std::size_t n=0;n<first;++n)if(bytes[n]!=value[n%4])return false;
    for(std::size_t n=first;n<bytes.size();n+=first){
        if(revision.load(std::memory_order_relaxed)!=serial)return false;
        if(std::memcmp(bytes.data()+n,bytes.data(),std::min(first,bytes.size()-n)))return false;
    }
    return revision.load(std::memory_order_relaxed)==serial;
}
bool prepare_mips(ImageUpload&job,const std::atomic<std::uint64_t>&revision) {
    if(job.use_cache&&job.source.rgba.empty())read_artwork_cache(job,revision);
    if(job.direct_payload)return revision.load(std::memory_order_relaxed)==job.serial;
    if(job.source.rgba.empty()){
        if(!job.encoded||job.source.encoded_offset>job.encoded->bytes||job.source.encoded_length>job.encoded->bytes-job.source.encoded_offset){job.error="The encoded 3D image range is invalid";return false;}
        if(revision.load(std::memory_order_relaxed)!=job.serial)return false;
        if(!job.encoded->unchanged()){job.error="The original model changed during artwork loading";return false;}
        const auto decode_start=SceneClock::now();const int expected_width=job.source.width,expected_height=job.source.height;
        std::string encoded(job.source.encoded_length,'\0');std::size_t received=0;
        while(received<encoded.size()){
            if(revision.load(std::memory_order_relaxed)!=job.serial)return false;
            const auto count=std::min(std::size_t(256u<<10),encoded.size()-received);
            const auto got=pread(fileno(job.encoded->stream),encoded.data()+received,count,static_cast<off_t>(job.source.encoded_offset+received));
            if(got<0&&errno==EINTR)continue;
            if(got<=0){job.error="The original model artwork could not be read completely";return false;}received+=std::size_t(got);
        }
        if(!job.encoded->unchanged()||encoded_fingerprint(reinterpret_cast<const unsigned char*>(encoded.data()),encoded.size())!=job.source.encoded_fingerprint){job.error="The original model artwork changed during loading";return false;}
        if(!yt::decode_image(encoded,&job.source.width,&job.source.height,&job.source.rgba,&job.error))return false;
        if(job.source.width!=expected_width||job.source.height!=expected_height){job.error="The decoded 3D image dimensions changed";return false;}
        job.decode_ms=elapsed_ms(decode_start);job.source.alpha_known=true;job.source.opaque=true;
        for(std::size_t n=3;n<job.source.rgba.size();n+=4)if(job.source.rgba[n]!=255){job.source.opaque=false;break;}
    }
    if(revision.load(std::memory_order_relaxed)!=job.serial)return false;
    const auto started=SceneClock::now();
    // Reuse transfer tables across atlases and exhibits. The old mip path called
    // pow for every output colour channel (millions of calls for a single4K
    // atlas). Table quantization stays below one8-bit code value, while the
    // source level and material/data channels retain their original bytes.
    static const auto linear=[] {std::array<float,256> table{};for(unsigned i=0;i<table.size();++i){const float c=float(i)/255;table[i]=c<=.04045f?c/12.92f:std::pow((c+.055f)/1.055f,2.4f);}return table;}();
    static const auto encoded=[] {std::array<std::uint8_t,65536> table{};for(unsigned i=0;i<table.size();++i){const double v=double(i)/65535;const double s=v<=.0031308?v*12.92:1.055*std::pow(v,1/2.4)-.055;table[i]=static_cast<std::uint8_t>(std::clamp(std::lround(s*255),0L,255L));}return table;}();
    const auto encode=[&](double value){return encoded[static_cast<std::size_t>(std::clamp(std::lround(value*65535),0L,65535L))];};
    for(unsigned role=0;role<2&&!job.cache_hit;++role) {
        if(!(job.source.roles&(1u<<role)))continue;
        const std::vector<std::uint8_t>*previous=&job.source.rgba;int w=job.source.width,h=job.source.height;
        while(w>1||h>1) {
            if(revision.load(std::memory_order_relaxed)!=job.serial)return false;
            MipPixels mip;mip.width=std::max(1,w/2);mip.height=std::max(1,h/2);mip.bytes.resize(static_cast<std::size_t>(mip.width)*mip.height*4);
            const double sx=double(w)/mip.width,sy=double(h)/mip.height;
            if(w==mip.width*2&&h==mip.height*2){
                // Common power-of-two atlases have exact2x2 footprints. Avoid
                // floor/ceil, coverage tests and floating point normalization
                // for each texel while preserving linear-light colour filtering.
                for(int y=0;y<mip.height;++y){
                    if((y&63)==0&&revision.load(std::memory_order_relaxed)!=job.serial)return false;
                    for(int x=0;x<mip.width;++x){
                        const auto a=(static_cast<std::size_t>(y*2)*w+x*2)*4,b=a+4,c=a+static_cast<std::size_t>(w)*4,d=c+4;
                        const auto out=(static_cast<std::size_t>(y)*mip.width+x)*4;
                        for(unsigned channel=0;channel<4;++channel){
                            if(role==0&&channel<3)mip.bytes[out+channel]=encode((linear[(*previous)[a+channel]]+linear[(*previous)[b+channel]]+linear[(*previous)[c+channel]]+linear[(*previous)[d+channel]])*.25);
                            else mip.bytes[out+channel]=static_cast<std::uint8_t>((unsigned((*previous)[a+channel])+unsigned((*previous)[b+channel])+unsigned((*previous)[c+channel])+unsigned((*previous)[d+channel])+2)/4);
                        }
                    }
                }
            }else for(int y=0;y<mip.height;++y){if((y&63)==0&&revision.load(std::memory_order_relaxed)!=job.serial)return false;
                for(int x=0;x<mip.width;++x){std::array<double,4> sum{};const double left=x*sx,right=(x+1)*sx,top=y*sy,bottom=(y+1)*sy;
                    for(int yy=int(top);yy<std::min(h,int(std::ceil(bottom)));++yy)for(int xx=int(left);xx<std::min(w,int(std::ceil(right)));++xx){const double area=(std::min(bottom,double(yy+1))-std::max(top,double(yy)))*(std::min(right,double(xx+1))-std::max(left,double(xx)));const auto offset=(static_cast<std::size_t>(yy)*w+xx)*4;for(unsigned c=0;c<4;++c)sum[c]+=area*(role==0&&c<3?linear[(*previous)[offset+c]]:double((*previous)[offset+c])/255);}
                    const auto offset=(static_cast<std::size_t>(y)*mip.width+x)*4;for(unsigned c=0;c<4;++c){const double value=sum[c]/(sx*sy);mip.bytes[offset+c]=role==0&&c<3?encode(value):static_cast<std::uint8_t>(std::clamp(std::lround(value*255),0L,255L));}
                }
            }
            job.levels[role].push_back(std::move(mip));previous=&job.levels[role].back().bytes;w=job.levels[role].back().width;h=job.levels[role].back().height;
        }
    }
    if(job.source.rgba.size()>=4){
        const std::array<std::uint8_t,4>value{job.source.rgba[0],job.source.rgba[1],job.source.rgba[2],job.source.rgba[3]};
        if(constant_texels(job.source.rgba,value,revision,job.serial))for(unsigned role=0;role<2;++role)if(job.source.roles&(1u<<role)){
            job.uniform_roles[role]=std::all_of(job.levels[role].begin(),job.levels[role].end(),[&](const auto&level){return constant_texels(level.bytes,value,revision,job.serial);});
        }
    }
    // Preserve every sampled8-bit data channel. ORM-only requires G/B,
    // AO-only requires R; normal maps and union masks with3channels stayRGBA.
    const auto mask=job.source.data_channels;unsigned used=0;for(unsigned c=0;c<3;++c)if(mask&(1u<<c))++used;
    if(!job.disable_compact&&(job.source.roles&2u)&&used>0&&used<=2){
        job.packed_components=used;used=0;for(unsigned c=0;c<3;++c)if(mask&(1u<<c))job.packed_channels[used++]=c;
        const auto pack=[&](const std::vector<std::uint8_t>&rgba,std::vector<std::uint8_t>&out){out.resize(rgba.size()/4*job.packed_components);for(std::size_t n=0;n<rgba.size()/4;++n)for(unsigned c=0;c<job.packed_components;++c)out[n*job.packed_components+c]=rgba[n*4+job.packed_channels[c]];};
        if(job.uniform_roles[1]){
            // All original RGBA texels and every mip are already verified
            // identical. Pack only the sampled texel; retain the original
            // RGBA/mips for the exact unsupported-format fallback.
            job.packed_base.resize(job.packed_components);
            for(unsigned c=0;c<job.packed_components;++c)job.packed_base[c]=job.source.rgba[job.packed_channels[c]];
        }else{
            pack(job.source.rgba,job.packed_base);for(const auto&level:job.levels[1]){MipPixels packed;packed.width=level.width;packed.height=level.height;pack(level.bytes,packed.bytes);job.packed_levels.push_back(std::move(packed));}
        }
    }
    job.prepare_ms=elapsed_ms(started);return true;
}
struct ObjectScene::Impl {
    struct Draw { GLuint vao=0,vbo=0,ebo=0;std::size_t vertex_bytes=0,index_bytes=0;GLsizei count=0;std::array<float,4> color{};int image=-1,emissive_image=-1,normal_image=-1,orm_image=-1,ao_image=-1;std::array<float,3> emission{};std::array<int,5> uv_sets{};std::array<GLuint,5> samplers{};float ao_strength=1;float cutoff=-1,roughness=.7f,metallic=0,normal_scale=1,specular=1;std::array<float,3> specular_color{1,1,1};SurfaceRestore restore;bool unlit=false,blend=false,double_sided=false,mirrored=false;Vec3 center; };
    std::vector<Draw> parts;std::vector<GLuint> images,linear_images;std::vector<GLuint> samplers;
    std::vector<Sampler> sampler_configs;
    std::vector<std::size_t> image_storage,linear_storage;
    std::size_t gpu_bytes=0,retired_bytes=0,transfer_chunk=512u<<10,upload_byte_cap=2u<<20;
    double upload_budget_ms=2.0,transfer_bytes_per_ms=0;std::size_t transfer_samples=0;
    std::vector<std::size_t> blended_parts;
    struct RetiredGpu {unsigned kind;GLuint name;std::size_t bytes=0;};std::vector<RetiredGpu> retired_gpu;
    GLuint sampler_for(const Sampler&config) {
        const auto found=std::find(sampler_configs.begin(),sampler_configs.end(),config);
        if(found!=sampler_configs.end())return samplers[static_cast<std::size_t>(found-sampler_configs.begin())];
        GLuint sampler=0;glGenSamplers(1,&sampler);
        glSamplerParameteri(sampler,GL_TEXTURE_MIN_FILTER,config.min);glSamplerParameteri(sampler,GL_TEXTURE_MAG_FILTER,config.mag);
        glSamplerParameteri(sampler,GL_TEXTURE_WRAP_S,config.s);glSamplerParameteri(sampler,GL_TEXTURE_WRAP_T,config.t);
        sampler_configs.push_back(config);samplers.push_back(sampler);stats.sampler_objects=samplers.size();return sampler;
    }
    void transfer_sample(SceneClock::time_point started,std::size_t bytes) {
        const double ms=elapsed_ms(started);timings.max_transfer_ms=std::max(timings.max_transfer_ms,ms);timings.total_transfer_ms+=ms;
        const double speed=double(bytes)/std::max(.01,ms);transfer_bytes_per_ms=transfer_samples?transfer_bytes_per_ms*.875+speed*.125:speed;++transfer_samples;
        timings.transfer_bytes_per_ms=transfer_bytes_per_ms;
        if(ms>1)transfer_chunk=std::max(std::size_t(64u<<10),transfer_chunk/2);
        else if(ms<.25)transfer_chunk=std::min(std::size_t(512u<<10),transfer_chunk+(64u<<10));
        timings.transfer_chunk_bytes=transfer_chunk;
    }
    void defer_gpu() {
        retired_gpu.reserve(retired_gpu.size()+parts.size()*3+images.size()+linear_images.size()+samplers.size());
        // LIFO retirement releases the large atlases first, rather than spending
        // many frames deleting hundreds of equivalent sampler objects first.
        for(auto name:samplers)if(name)retired_gpu.push_back({3,name});
        for(const auto&part:parts){if(part.vao)retired_gpu.push_back({0,part.vao});if(part.vbo)retired_gpu.push_back({1,part.vbo,part.vertex_bytes});if(part.ebo)retired_gpu.push_back({1,part.ebo,part.index_bytes});}
        for(std::size_t i=0;i<images.size();++i)if(images[i])retired_gpu.push_back({2,images[i],i<image_storage.size()?image_storage[i]:0});
        for(std::size_t i=0;i<linear_images.size();++i)if(linear_images[i])retired_gpu.push_back({2,linear_images[i],i<linear_storage.size()?linear_storage[i]:0});
        retired_bytes+=gpu_bytes;gpu_bytes=0;
        parts.clear();images.clear();linear_images.clear();image_storage.clear();linear_storage.clear();samplers.clear();sampler_configs.clear();blended_parts.clear();material_notes.clear();stats={};
        {std::lock_guard<std::mutex> lock(mutex);retirement_pending=!retired_gpu.empty();}
    }
    bool drain_gpu(bool all=false) {
        const auto started=SceneClock::now();unsigned count=0;
        while(!retired_gpu.empty()) {const auto item=retired_gpu.back();retired_gpu.pop_back();const auto operation=SceneClock::now();switch(item.kind){case 0:glDeleteVertexArrays(1,&item.name);break;case 1:glDeleteBuffers(1,&item.name);break;case 2:glDeleteTextures(1,&item.name);break;case 4:glDeleteRenderbuffers(1,&item.name);break;case 5:glDeleteFramebuffers(1,&item.name);break;default:glDeleteSamplers(1,&item.name);break;}const double ms=elapsed_ms(operation);timings.max_delete_ms=std::max(timings.max_delete_ms,ms);if(ms>4)hui::sys::log("[Museum] 3D slow retirement %.2fms / kind %u / estimated %zu KiB",ms,item.kind,item.bytes>>10);retired_bytes=item.bytes>retired_bytes?0:retired_bytes-item.bytes;if(!all&&(++count>=4||elapsed_ms(started)>=upload_budget_ms))break;}
        if(retired_gpu.empty()){
            retired_bytes=0;
            // A new source buffer shares the PS5 physical allocation pool with
            // GL textures. Admit it only after the previous atlases have gone.
            {std::lock_guard<std::mutex> lock(mutex);retirement_pending=false;}
            wake.notify_one();
        }
        return retired_gpu.empty();
    }
    GLuint program=0,fbo=0,texture=0,depth=0,resolve_program=0,resolve_fbo=0,scene_texture=0,resolve_vao=0;
    GLint inverse_size=-1;
    GLint mvp=-1,rotation=-1,base=-1,textured=-1,unlit=-1,cutoff=-1,blended=-1,alpha_pass=-1,roughness=-1,metallic=-1,specular=-1,specular_color=-1,pin_studio=-1;
    GLint restore_regions=-1,restore_details=-1,restore_ink=-1,restore_colour=-1,restore_counts=-1;
    GLint has_emission=-1,has_normal=-1,has_orm=-1,has_ao=-1,ao_strength=-1,ao_uv=-1,emission=-1,normal_scale=-1,uv_sets=-1;
    int width=0,height=0;
    std::string error,material_notes,progress;
    std::mutex mutex;bool retirement_pending=false;
    std::condition_variable wake;
    std::thread worker;
    std::string queued;
    std::vector<std::string> queued_groups;
    std::uint64_t serial=0;std::atomic<std::uint64_t> revision{0};
    std::unique_ptr<Reader> pending;
    std::unique_ptr<Reader> uploading;
    std::size_t next_image=0,geometry_part=0,vertex_offset=0,index_offset=0;
    std::unique_ptr<ImageUpload> queued_image,pending_image,active_image;
    std::vector<std::unique_ptr<Reader>> retired;
    std::vector<std::unique_ptr<ImageUpload>> retired_images;
    bool upload_image_step(std::size_t&budget,SceneClock::time_point started);
    bool upload_geometry_step(Model&model,std::size_t&budget,SceneClock::time_point started);
    // Caller holds mutex: invalidating a request and removing its mailboxes
    // must be one transition, otherwise the worker can publish between them.
    void retire_cpu_locked() {
        if(uploading)retired.push_back(std::move(uploading));if(pending)retired.push_back(std::move(pending));
        if(active_image)retired_images.push_back(std::move(active_image));if(queued_image)retired_images.push_back(std::move(queued_image));if(pending_image)retired_images.push_back(std::move(pending_image));wake.notify_one();
    }
    void retire_cpu() {std::lock_guard<std::mutex> lock(mutex);retire_cpu_locked();}
    std::atomic<bool> loading{false};
    std::atomic<std::size_t> planned_gpu_bytes{0};SceneClock::time_point request_started=SceneClock::now();
    bool stopping=false,image_waiting=false;
    ObjectScene::Stats stats;
    ObjectScene::Timings timings;
    std::array<GLuint,4> gpu_queries{};std::array<bool,4> gpu_pending{};std::array<std::uint64_t,4> gpu_serial{};std::array<SceneClock::time_point,4> gpu_started{};bool gpu_supported=false;
    void poll_gpu() {
        if(!gpu_supported)return;
        for(unsigned i=0;i<4;++i)if(gpu_pending[i]){GLuint available=0;glGetQueryObjectuiv(gpu_queries[i],GL_QUERY_RESULT_AVAILABLE,&available);if(!available)continue;GLuint64 nanoseconds=0;glGetQueryObjectui64v(gpu_queries[i],GL_QUERY_RESULT,&nanoseconds);gpu_pending[i]=false;if(gpu_serial[i]==serial){const double ms=double(nanoseconds)/1000000.;if(ms>elapsed_ms(gpu_started[i])*1.05+1){++timings.gpu_rejected;continue;}++timings.gpu_samples;timings.last_gpu_ms=ms;timings.max_gpu_ms=std::max(timings.max_gpu_ms,ms);}}
    }
    int begin_gpu() {
        poll_gpu();if(!gpu_supported)return -1;GLint current=0;glGetQueryiv(GL_TIME_ELAPSED,GL_CURRENT_QUERY,&current);if(current)return -1;
        for(unsigned i=0;i<4;++i)if(!gpu_pending[i]){glBeginQuery(GL_TIME_ELAPSED,gpu_queries[i]);gpu_serial[i]=serial;gpu_started[i]=SceneClock::now();return int(i);}return -1;
    }
    void end_gpu(int query){if(query>=0){glEndQuery(GL_TIME_ELAPSED);gpu_pending[static_cast<unsigned>(query)]=true;}}

    void stop_worker() {
        { std::lock_guard<std::mutex> lock(mutex);stopping=true;queued.clear();revision.fetch_add(1,std::memory_order_relaxed);retire_cpu_locked(); }
        wake.notify_one();
        if(worker.joinable())worker.join();
        loading.store(false,std::memory_order_relaxed);
    }
    bool upload(Model &model);
    bool upload_image(Model &model,std::size_t index);
    bool upload_geometry(Model &model);
    void clear_model() {
        for(auto &p:parts){if(p.vbo)glDeleteBuffers(1,&p.vbo);if(p.ebo)glDeleteBuffers(1,&p.ebo);if(p.vao)glDeleteVertexArrays(1,&p.vao);}parts.clear();
        for(GLuint t:images)if(t)glDeleteTextures(1,&t);
        for(GLuint t:linear_images)if(t)glDeleteTextures(1,&t);
        for(GLuint sampler:samplers)if(sampler)glDeleteSamplers(1,&sampler);
        images.clear();linear_images.clear();image_storage.clear();linear_storage.clear();samplers.clear();sampler_configs.clear();gpu_bytes=0;material_notes.clear();blended_parts.clear();stats={};
    }
    void clear_target() {
        if(depth)glDeleteRenderbuffers(1,&depth);
        if(fbo)glDeleteFramebuffers(1,&fbo);
        if(texture)glDeleteTextures(1,&texture);
        if(resolve_fbo)glDeleteFramebuffers(1,&resolve_fbo);
        if(scene_texture)glDeleteTextures(1,&scene_texture);
        depth=fbo=texture=resolve_fbo=scene_texture=0;width=height=0;
    }
};

ObjectScene::ObjectScene():impl_(std::make_unique<Impl>()){}
ObjectScene::~ObjectScene(){release();}
void ObjectScene::swap(ObjectScene&other)noexcept{impl_.swap(other.impl_); }
bool ObjectScene::init() {
    if(impl_->program)return true;
    State state;
    impl_->program=hui::gfx::build_program("museum-object",kVertex,kFragment);
    if(!impl_->program){impl_->error="The 3D exhibit shader could not be initialized";return false;}
    auto &p=*impl_;p.mvp=glGetUniformLocation(p.program,"mvp");p.rotation=glGetUniformLocation(p.program,"rotation");
    p.base=glGetUniformLocation(p.program,"baseColor");p.textured=glGetUniformLocation(p.program,"textured");
    p.unlit=glGetUniformLocation(p.program,"unlit");p.cutoff=glGetUniformLocation(p.program,"cutoff");
    p.blended=glGetUniformLocation(p.program,"blended");
    p.alpha_pass=glGetUniformLocation(p.program,"alphaPass");
    p.restore_regions=glGetUniformLocation(p.program,"restoreRegions");p.restore_details=glGetUniformLocation(p.program,"restoreDetails");p.restore_ink=glGetUniformLocation(p.program,"restoreInk");p.restore_colour=glGetUniformLocation(p.program,"restoreColourRoughness");p.restore_counts=glGetUniformLocation(p.program,"restoreCounts");
    p.roughness=glGetUniformLocation(p.program,"roughness");p.metallic=glGetUniformLocation(p.program,"metallic");p.specular=glGetUniformLocation(p.program,"specular");p.specular_color=glGetUniformLocation(p.program,"specularColor");
    p.pin_studio=glGetUniformLocation(p.program,"pinStudio");
    p.has_emission=glGetUniformLocation(p.program,"hasEmission");p.has_normal=glGetUniformLocation(p.program,"hasNormal");p.has_orm=glGetUniformLocation(p.program,"hasOrm");p.emission=glGetUniformLocation(p.program,"emission");p.normal_scale=glGetUniformLocation(p.program,"normalScale");
    p.uv_sets=glGetUniformLocation(p.program,"uvSets");p.has_ao=glGetUniformLocation(p.program,"hasAo");p.ao_strength=glGetUniformLocation(p.program,"aoStrength");p.ao_uv=glGetUniformLocation(p.program,"aoUv");
    glUseProgram(p.program);glUniform1i(glGetUniformLocation(p.program,"artwork"),0);
    glUniform1i(glGetUniformLocation(p.program,"emissionMap"),1);glUniform1i(glGetUniformLocation(p.program,"normalMap"),2);glUniform1i(glGetUniformLocation(p.program,"ormMap"),3);glUniform1i(glGetUniformLocation(p.program,"aoMap"),4);
    p.resolve_program=hui::gfx::build_program("museum-object-alpha",kResolveVertex,kResolveFragment);
    if(!p.resolve_program){glDeleteProgram(p.program);p.program=0;p.error="The 3D exhibit alpha shader could not be initialized";return false;}
    glUseProgram(p.resolve_program);glUniform1i(glGetUniformLocation(p.resolve_program,"scene"),0);p.inverse_size=glGetUniformLocation(p.resolve_program,"inverseSize");glGenVertexArrays(1,&p.resolve_vao);
    GLint counter_bits=0;glGetQueryiv(GL_TIME_ELAPSED,GL_QUERY_COUNTER_BITS,&counter_bits);const auto query_error=glGetError();p.gpu_supported=counter_bits>0&&query_error==GL_NO_ERROR;if(p.gpu_supported){glGenQueries(4,p.gpu_queries.data());if(glGetError()!=GL_NO_ERROR||!p.gpu_queries[0]||!p.gpu_queries[1]||!p.gpu_queries[2]||!p.gpu_queries[3]){glDeleteQueries(4,p.gpu_queries.data());p.gpu_queries={};p.gpu_supported=false;}}p.timings.gpu_timing_supported=p.gpu_supported;
    p.error.clear();return true;
}
bool ObjectScene::validate(const std::string &path,std::string *error,const std::vector<std::string> &include_groups) {
    Reader reader;reader.include_groups=include_groups;const bool ok=reader.read(path);if(error)*error=reader.error;return ok;
}
bool ObjectScene::load(const std::string &path,const std::vector<std::string> &include_groups) {
    Reader reader;reader.include_groups=include_groups;
    if(!reader.read(path)){impl_->error=reader.error;return false;}
    if(!init())return false;
    return impl_->upload(reader.model);
}
void ObjectScene::request(const std::string &path,const std::vector<std::string> &include_groups) {
    auto &p=*impl_;
    const auto retire_start=SceneClock::now();
    {
        std::lock_guard<std::mutex> lock(p.mutex);
        p.retirement_pending=true;p.queued=path;p.queued_groups=include_groups;++p.serial;p.revision.store(p.serial,std::memory_order_relaxed);p.stopping=false;
        p.retire_cpu_locked();
        p.loading.store(!path.empty(),std::memory_order_relaxed);p.progress=path.empty()?"":"Reading the original model";
    }
    p.defer_gpu();p.planned_gpu_bytes.store(0,std::memory_order_relaxed);p.error.clear();p.timings={};p.request_started=SceneClock::now();p.timings.last_retire_ms=elapsed_ms(retire_start);
    if(!p.worker.joinable()) {
        p.worker=std::thread([state=&p] {
            for(;;) {
                std::string path;std::vector<std::string> groups;std::uint64_t serial=0;std::unique_ptr<ImageUpload> image;
                std::vector<std::unique_ptr<Reader>> retired;std::vector<std::unique_ptr<ImageUpload>> retired_images;bool stop=false;
                {
                    std::unique_lock<std::mutex> lock(state->mutex);
                    state->wake.wait(lock,[&]{return state->stopping||(!state->queued.empty()&&!state->retirement_pending)||state->queued_image||!state->retired.empty()||!state->retired_images.empty();});
                    retired.swap(state->retired);retired_images.swap(state->retired_images);stop=state->stopping;
                    if(!stop&&!state->queued.empty()&&!state->retirement_pending){path=std::move(state->queued);groups=state->queued_groups;state->queued.clear();serial=state->serial;}
                    else if(!stop&&state->queued_image)image=std::move(state->queued_image);
                }
                // Potentially gigabytes of cancelled pixels are freed here, never
                // while handling controller input or holding the handoff lock.
                retired.clear();retired_images.clear();if(stop)return;
                if(image){const bool prepared=prepare_mips(*image,state->revision);std::lock_guard<std::mutex> lock(state->mutex);if(image->serial==state->serial&&!state->stopping&&(prepared||!image->error.empty()))state->pending_image=std::move(image);continue;}
                if(path.empty())continue;
                const auto decode_start=SceneClock::now();auto result=std::make_unique<Reader>();result->defer_images=true;result->include_groups=std::move(groups);result->cancelled=[state,serial]{return state->revision.load(std::memory_order_relaxed)!=serial;};
#if defined(__cpp_exceptions)
                try {result->read(path);}
                catch(...) {result->model=Model{};std::vector<unsigned char>().swap(result->bytes);result->doc=Json{};result->error="Insufficient memory while preparing the 3D exhibit";}
#else
                // The console build disables C++ exceptions. Image decode
                // failures still return a readable error through Reader.
                result->read(path);
#endif
                // Bound GPU texture residency for unusually large exhibits.
                // Source images and cached mip chains remain untouched; upload
                // promotes their existing role-specific2048-level to GPUlevel0.
                if(result->error.empty()&&model_residency(result->model)>(768u<<20))result->model.texture_limit=2048;
                result->read_decode_ms=elapsed_ms(decode_start);
                {
                    std::lock_guard<std::mutex> lock(state->mutex);
                    if(state->stopping)return;
                    if(serial==state->serial){state->planned_gpu_bytes.store(result->error.empty()?model_residency(result->model):0,std::memory_order_relaxed);state->progress=result->error.empty()?"Preparing original-resolution artwork":result->error;state->pending=std::move(result);}
                }
            }
        });
    }
    p.wake.notify_one();
}
void ObjectScene::cancel() {
    auto&p=*impl_;const auto started=SceneClock::now();
    {std::lock_guard<std::mutex> lock(p.mutex);p.queued.clear();p.queued_groups.clear();++p.serial;p.revision.store(p.serial,std::memory_order_relaxed);p.retire_cpu_locked();p.loading.store(false,std::memory_order_relaxed);p.progress.clear();}
    p.defer_gpu();p.planned_gpu_bytes.store(0,std::memory_order_relaxed);p.error.clear();
    p.timings.last_retire_ms=elapsed_ms(started);p.wake.notify_one();
}
void ObjectScene::release_render_target() {
    auto&p=*impl_;
    const auto plane=static_cast<std::size_t>(p.width)*static_cast<std::size_t>(p.height)*4;
    // Release framebuffer references first when LIFO maintenance runs. The
    // original geometry, material atlases, shaders and worker remain warm.
    if(p.texture)p.retired_gpu.push_back({2,p.texture,plane});
    if(p.scene_texture)p.retired_gpu.push_back({2,p.scene_texture,plane});
    if(p.depth)p.retired_gpu.push_back({4,p.depth,plane});
    if(p.fbo)p.retired_gpu.push_back({5,p.fbo});
    if(p.resolve_fbo)p.retired_gpu.push_back({5,p.resolve_fbo});
    p.retired_bytes+=plane*3;
    p.depth=p.fbo=p.texture=p.resolve_fbo=p.scene_texture=0;p.width=p.height=0;
    p.timings.render_width=p.timings.render_height=0;
}
bool ObjectScene::upload_pending(double budget_ms,bool adaptive) {
    auto &p=*impl_;const auto started=SceneClock::now();CpuSample sample{p.timings.last_upload_ms,p.timings.max_upload_ms,&p.timings.total_upload_cpu_ms};p.upload_budget_ms=std::isfinite(budget_ms)?std::clamp(budget_ms,.25,3.0):2.0;
    if(adaptive&&p.transfer_samples>=8){
        const auto predicted=static_cast<std::size_t>(std::clamp(p.transfer_bytes_per_ms*p.upload_budget_ms*.65,double(2u<<20),double(16u<<20)));
        const auto wanted=p.timings.last_upload_ms>p.upload_budget_ms*1.25?std::max(std::size_t(2u<<20),p.upload_byte_cap/2):predicted;
        p.upload_byte_cap=wanted<p.upload_byte_cap?wanted:std::min(wanted,p.upload_byte_cap+(2u<<20));
    }else p.upload_byte_cap=2u<<20;
    std::size_t budget=p.upload_byte_cap;p.timings.last_upload_bytes=0;p.timings.upload_budget_bytes=budget;p.timings.upload_budget_ms=p.upload_budget_ms;p.timings.adaptive_upload=adaptive;
    if(!p.drain_gpu())return false;
    if(elapsed_ms(started)>=p.upload_budget_ms)return false;
    if(!p.uploading) {
        std::unique_ptr<Reader> reader;
        {std::lock_guard<std::mutex> lock(p.mutex);reader=std::move(p.pending);}
        if(!reader)return false;
        p.timings.encoded_model_bytes=reader->encoded_file?reader->encoded_file->bytes:0;
        p.timings.source_read_ms=reader->source_read_ms;p.timings.source_hash_ms=reader->source_hash_ms;p.timings.parse_ms=std::max(0.0,reader->read_decode_ms-reader->source_read_ms-reader->source_hash_ms);p.timings.read_decode_ms=reader->read_decode_ms;std::printf("[Museum] 3D read/decode %.2fms\n",p.timings.read_decode_ms);
        if(!reader->error.empty()){p.loading.store(false,std::memory_order_relaxed);p.error=reader->error;hui::sys::log("[Museum] 3D failed: %s",p.error.c_str());std::lock_guard<std::mutex> lock(p.mutex);p.retired.push_back(std::move(reader));p.wake.notify_one();return false;}
        if(!init()){p.loading.store(false,std::memory_order_relaxed);std::lock_guard<std::mutex> lock(p.mutex);p.retired.push_back(std::move(reader));p.wake.notify_one();return false;}
        p.clear_model();p.stats.deduplicated_images=reader->model.deduplicated_images;p.images.resize(reader->model.images.size());p.linear_images.resize(reader->model.images.size());p.image_storage.resize(reader->model.images.size());p.linear_storage.resize(reader->model.images.size());p.next_image=0;p.image_waiting=false;p.geometry_part=0;p.vertex_offset=p.index_offset=0;p.uploading=std::move(reader);
    }
    auto&model=p.uploading->model;p.timings.pending_images=model.images.size()-p.next_image;
    if(!p.active_image){std::lock_guard<std::mutex> lock(p.mutex);p.active_image=std::move(p.pending_image);if(p.active_image){char text[120];std::snprintf(text,sizeof(text),"Uploading original artwork / atlas %zu of %zu",p.next_image+1,model.images.size());p.progress=text;}}
    if(p.active_image) {
        if(!p.active_image->error.empty()){p.loading.store(false,std::memory_order_relaxed);p.error="GLB image decode: "+p.active_image->error;hui::sys::log("[Museum] 3D failed: %s",p.error.c_str());p.retire_cpu();p.defer_gpu();return false;}
        p.timings.mip_prepare_ms=p.active_image->prepare_ms;p.timings.image_decode_ms=p.active_image->decode_ms;
        std::size_t staged=p.active_image->source.rgba.size();for(const auto&role:p.active_image->levels)for(const auto&level:role)staged+=level.bytes.size();
        staged+=p.active_image->packed_base.size();for(const auto&level:p.active_image->packed_levels)staged+=level.bytes.size();
        p.timings.peak_staged_image_bytes=std::max(p.timings.peak_staged_image_bytes,staged);
        if(!p.upload_image_step(budget,started)){
            if(p.active_image&&p.active_image->compact_reprepare){
                if(p.active_image->cache_hit){++p.timings.artwork_cache_hits;p.timings.total_cache_decode_ms+=p.active_image->cache_decode_ms;}++p.timings.compact_cache_fallbacks;
                auto fallback=std::make_unique<ImageUpload>();fallback->source=p.active_image->source;fallback->texture_limit=p.active_image->texture_limit;fallback->source.rgba.clear();fallback->encoded=p.active_image->encoded;fallback->index=p.active_image->index;fallback->serial=p.active_image->serial;fallback->use_cache=false;fallback->disable_compact=true;
                {std::lock_guard<std::mutex> lock(p.mutex);p.retired_images.push_back(std::move(p.active_image));p.queued_image=std::move(fallback);p.image_waiting=true;p.progress="Preparing original artwork fallback";p.wake.notify_one();}
                return false;
            }
            if(!p.error.empty()){p.loading.store(false,std::memory_order_relaxed);p.retire_cpu();p.defer_gpu();std::lock_guard<std::mutex> lock(p.mutex);p.progress=p.error;}return false;
        }
        if(p.active_image->cache_hit){++p.timings.artwork_cache_hits;p.timings.total_cache_decode_ms+=p.active_image->cache_decode_ms;}
        p.timings.total_image_decode_ms+=p.active_image->decode_ms;p.timings.total_mip_prepare_ms+=p.active_image->prepare_ms;
        if(p.active_image->source.alpha_known&&p.active_image->source.opaque)for(auto&part:model.parts)if(part.image==int(p.active_image->index)&&part.color[3]>=.999f)part.blend=false;
        {std::lock_guard<std::mutex> lock(p.mutex);p.retired_images.push_back(std::move(p.active_image));p.wake.notify_one();}
        ++p.next_image;p.image_waiting=false;
    }
    if(p.image_waiting)return false;
    while(p.next_image<model.images.size()&&model.images[p.next_image].rgba.empty()&&!model.images[p.next_image].encoded_length)++p.next_image;
    if(p.next_image<model.images.size()) {
        std::lock_guard<std::mutex> lock(p.mutex);
        if(!p.queued_image&&!p.pending_image){auto job=std::make_unique<ImageUpload>();job->source=std::move(model.images[p.next_image]);job->texture_limit=model.texture_limit;job->encoded=p.uploading->encoded_file;job->index=p.next_image;job->serial=p.serial;const auto bytes=static_cast<std::size_t>(job->source.width)*job->source.height*4;p.stats.texture_bytes+=bytes;if(job->source.roles==3)p.stats.dual_role_texture_bytes+=bytes;char text[120];std::snprintf(text,sizeof(text),"Decoding original artwork / atlas %zu of %zu",p.next_image+1,model.images.size());p.progress=text;p.queued_image=std::move(job);p.image_waiting=true;p.wake.notify_one();}
        return false;
    }
    const bool done=p.upload_geometry_step(model,budget,started);
    if(done){p.timings.load_ready_ms=elapsed_ms(p.request_started);hui::sys::log("[Museum] 3D ready breakdown: file %.2fms / parse+identity %.2fms / artwork decode %.2fms / mip+packing %.2fms / cache %zu hits %.2fms / GL allocation %.2fms / row transfer %.2fms / request-to-ready %.2fms / estimated residency %zu MiB",p.timings.source_read_ms,p.timings.parse_ms,p.timings.total_image_decode_ms,p.timings.total_mip_prepare_ms,p.timings.artwork_cache_hits,p.timings.total_cache_decode_ms,p.timings.total_storage_ms,p.timings.total_transfer_ms,p.timings.load_ready_ms,p.gpu_bytes>>20);}
    if(done||!p.error.empty()){p.loading.store(false,std::memory_order_relaxed);p.retire_cpu();if(!done)p.defer_gpu();std::lock_guard<std::mutex> lock(p.mutex);p.progress=done?"Ready to inspect":p.error;}return done;
}

bool ObjectScene::loading() const{return impl_->loading.load(std::memory_order_relaxed)||bool(impl_->uploading);}
bool ObjectScene::Impl::upload(Model &model) {
    State state;auto &p=*this;p.clear_model();p.stats.deduplicated_images=model.deduplicated_images;p.error.clear();
    p.images.resize(model.images.size());p.linear_images.resize(model.images.size());p.image_storage.resize(model.images.size());p.linear_storage.resize(model.images.size());
    for(std::size_t i=0;i<model.images.size();++i)if(!p.upload_image(model,i)){p.clear_model();return false;}
    return p.upload_geometry(model);
}
bool ObjectScene::Impl::upload_image_step(std::size_t&budget,SceneClock::time_point started) {
    State state;auto&job=*active_image;
    while(job.role<2) {
        if(!(job.source.roles&(1u<<job.role))){++job.role;continue;}
        const bool uniform=job.uniform_roles[job.role];
        const bool compact_payload=job.role==1&&job.packed_components>0;
        const auto&role_levels=compact_payload?job.packed_levels:job.levels[job.role];
        std::size_t base_level=0;int base_width=job.source.width,base_height=job.source.height;
        while(!uniform&&job.texture_limit>0&&(base_width>job.texture_limit||base_height>job.texture_limit)){
            base_width=std::max(1,base_width/2);base_height=std::max(1,base_height/2);++base_level;
        }
        if(base_level>role_levels.size()){error="The budgeted 3D mip chain is incomplete";return false;}
        const auto last_level=uniform?std::size_t(0):role_levels.size()-base_level;
        auto&name=job.role==0?images[job.index]:linear_images[job.index];
        if(!name){
            glGenTextures(1,&name);glBindTexture(GL_TEXTURE_2D,name);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,static_cast<GLint>(last_level));
            // Allocate the complete mip chain once. Repeated glTexImage2D for
            // successive levels can grow/copy the entire resource on PS5.
            const auto storage_start=SceneClock::now();
            job.compact_active=job.role==1&&job.packed_components>0;
            GLenum storage_error=GL_NO_ERROR;
            const auto allocate=[&](bool compact){
                glTexStorage2D(GL_TEXTURE_2D,static_cast<GLsizei>(last_level+1),compact?(job.packed_components==1?GL_R8:GL_RG8):(job.role==0?GL_SRGB8_ALPHA8:GL_RGBA8),uniform?1:base_width,uniform?1:base_height);
                storage_error=glGetError();if(storage_error!=GL_NO_ERROR)return false;
                if(compact){std::array<GLint,4> swizzle{GL_ZERO,GL_ZERO,GL_ZERO,GL_ONE};for(unsigned c=0;c<job.packed_components;++c)swizzle[job.packed_channels[c]]=c?GL_GREEN:GL_RED;glTexParameteriv(GL_TEXTURE_2D,GL_TEXTURE_SWIZZLE_RGBA,swizzle.data());storage_error=glGetError();if(storage_error!=GL_NO_ERROR)return false;}
                return true;
            };
            bool allocated=allocate(job.compact_active);
            if(!allocated&&job.compact_active){
                if(job.direct_payload){
                    timings.last_storage_ms=elapsed_ms(storage_start);timings.max_storage_ms=std::max(timings.max_storage_ms,timings.last_storage_ms);timings.total_storage_ms+=timings.last_storage_ms;++timings.storage_calls;
                    glDeleteTextures(1,&name);name=0;job.compact_active=false;job.compact_reprepare=true;
                    hui::sys::log("[Museum] compact prepacked format unavailable; original RGBA preparation queued on worker");return false;
                }
                hui::sys::log("[Museum] compact material format unavailable; retrying original RGBA8");glDeleteTextures(1,&name);glGenTextures(1,&name);glBindTexture(GL_TEXTURE_2D,name);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,static_cast<GLint>(last_level));job.compact_active=false;allocated=allocate(false);
            }
            timings.last_storage_ms=elapsed_ms(storage_start);timings.max_storage_ms=std::max(timings.max_storage_ms,timings.last_storage_ms);timings.total_storage_ms+=timings.last_storage_ms;++timings.storage_calls;
            const auto failure=allocated?GL_NO_ERROR:storage_error;if(failure!=GL_NO_ERROR){char message[180];std::snprintf(message,sizeof(message),"Graphics memory unavailable for 3D atlas %zu (%dx%d, %s, GL 0x%x)",job.index+1,job.source.width,job.source.height,job.role==0?"colour":"material",unsigned(failure));error=message;hui::sys::log("[Museum] 3D failed: %s",error.c_str());return false;}
            const auto&allocated_levels=job.compact_active?job.packed_levels:job.levels[job.role];
            std::size_t allocation_bytes=base_level?allocated_levels[base_level-1].bytes.size():(job.compact_active?job.packed_base.size():job.source.rgba.size());
            for(std::size_t n=base_level;n<allocated_levels.size();++n)allocation_bytes+=allocated_levels[n].bytes.size();
            if(uniform){
                // Account for the full equivalent packed chain even when its
                // redundant CPU copy was never allocated.
                std::size_t original_bytes=allocation_bytes;
                if(job.original_view_bytes[job.role])original_bytes=job.original_view_bytes[job.role]/4*(job.compact_active?job.packed_components:4);
                else if(job.compact_active){original_bytes=job.source.rgba.size()/4*job.packed_components;for(const auto&level:job.levels[1])original_bytes+=level.bytes.size()/4*job.packed_components;}
                allocation_bytes=job.compact_active?job.packed_components:4;++timings.uniform_texture_views;timings.uniform_saved_logical_bytes+=original_bytes-allocation_bytes;hui::sys::log("[Museum] lossless constant atlas%zu / %dx%d and all mips verified byte-identical / 1x1 equivalent / %zu KiB logical storage avoided",job.index+1,job.source.width,job.source.height,(original_bytes-allocation_bytes)>>10);}
            allocation_bytes=texture_residency(allocation_bytes);
            (job.role==0?image_storage:linear_storage)[job.index]=allocation_bytes;gpu_bytes+=allocation_bytes;
            if(job.role==0)++stats.srgb_textures;else ++stats.linear_textures;
            if(job.compact_active)hui::sys::log("[Museum] lossless material channel packing atlas%zu / %u channels / uploaded %dx%d / %zu MiB backing estimate",job.index+1,job.packed_components,uniform?1:base_width,uniform?1:base_height,allocation_bytes>>20);
            if(base_level)hui::sys::log("[Museum] budgeted 3D atlas %zu / source %dx%d / GPU %dx%d / original mip %zu promoted",job.index+1,job.source.width,job.source.height,base_width,base_height,base_level);
            hui::sys::log("[Museum] 3D atlas %zu / %dx%d source / %s / immutable %zu levels / %.2fms allocation / %zu MiB current model / one decoded atlas",job.index+1,job.source.width,job.source.height,job.role==0?"colour":"material",last_level+1,timings.last_storage_ms,gpu_bytes>>20);
            if(elapsed_ms(started)>=upload_budget_ms)return false;
        }else glBindTexture(GL_TEXTURE_2D,name);
        const auto&upload_levels=job.compact_active?job.packed_levels:job.levels[job.role];
        const auto source_level=job.level+base_level;
        const int w=uniform?1:source_level?upload_levels[source_level-1].width:job.source.width,h=uniform?1:source_level?upload_levels[source_level-1].height:job.source.height;
        const auto&pixels=job.compact_active?(source_level?job.packed_levels[source_level-1].bytes:job.packed_base):(source_level?job.levels[job.role][source_level-1].bytes:job.source.rgba);

        const auto row_bytes=static_cast<std::size_t>(w)*(job.compact_active?job.packed_components:4);if(budget<row_bytes||elapsed_ms(started)>=upload_budget_ms)return false;
        const auto rows=std::min({static_cast<std::size_t>(h)-job.row,budget/row_bytes,std::max(std::size_t(1),transfer_chunk/row_bytes)});const auto count=rows*row_bytes;
        const auto transfer_start=SceneClock::now();
        glPixelStorei(GL_UNPACK_ALIGNMENT,1);
        glTexSubImage2D(GL_TEXTURE_2D,static_cast<GLint>(job.level),0,static_cast<GLint>(job.row),w,static_cast<GLsizei>(rows),job.compact_active?(job.packed_components==1?GL_RED:GL_RG):GL_RGBA,GL_UNSIGNED_BYTE,pixels.data()+job.row*row_bytes);
        transfer_sample(transfer_start,count);
        budget-=count;timings.uploaded_bytes+=count;timings.last_upload_bytes+=count;timings.max_upload_bytes=std::max(timings.max_upload_bytes,timings.last_upload_bytes);++timings.upload_calls;job.row+=rows;
        if(glGetError()!=GL_NO_ERROR){error="The graphics driver could not upload a staged 3D texture";return false;}
        if(job.row==static_cast<std::size_t>(h)){job.row=0;job.allocated=false;++job.level;if(job.level>last_level){++job.role;job.level=0;}}
    }
    return true;
}
bool ObjectScene::Impl::upload_image(Model &model,std::size_t i) {
    State state;auto &p=*this;auto &pixels=model.images[i];if(pixels.rgba.empty())return true;
    p.stats.texture_bytes+=pixels.rgba.size();
    p.timings.uploaded_bytes+=pixels.rgba.size()*(pixels.roles==3?2:1);++p.timings.upload_calls;
    const auto upload=[&](GLuint &name,GLint format) {
        glGenTextures(1,&name);glBindTexture(GL_TEXTURE_2D,name);
        glTexImage2D(GL_TEXTURE_2D,0,format,pixels.width,pixels.height,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels.rgba.data());
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);glGenerateMipmap(GL_TEXTURE_2D);
        std::size_t allocation=0;int w=pixels.width,h=pixels.height;
        for(;;){allocation+=static_cast<std::size_t>(w)*h*4;if(w==1&&h==1)break;w=std::max(1,w/2);h=std::max(1,h/2);}
        allocation=texture_residency(allocation);
        (format==GL_SRGB8_ALPHA8?p.image_storage:p.linear_storage)[i]=allocation;p.gpu_bytes+=allocation;
    };
    if(pixels.roles&1u){upload(p.images[i],GL_SRGB8_ALPHA8);++p.stats.srgb_textures;}
    if(pixels.roles&2u){upload(p.linear_images[i],GL_RGBA8);++p.stats.linear_textures;}
    if(pixels.roles==3)p.stats.dual_role_texture_bytes+=pixels.rgba.size();
    std::vector<std::uint8_t>().swap(pixels.rgba);
    if(glGetError()!=GL_NO_ERROR){p.error="The graphics driver could not allocate the 3D exhibit textures";return false;}
    return true;
}
bool ObjectScene::Impl::upload_geometry(Model &model) {
    State state;auto &p=*this;p.material_notes=model.notes;
    p.timings.pending_images=0;
    for(const auto &part:model.parts) {
        Impl::Draw draw;draw.count=static_cast<GLsizei>(part.indices.size());draw.color=part.color;
        draw.image=part.image;draw.cutoff=part.cutoff;draw.unlit=part.unlit;draw.blend=part.blend;
        draw.double_sided=part.double_sided;draw.mirrored=part.mirrored;
        draw.restore=part.restore;draw.roughness=part.roughness;draw.metallic=part.metallic;draw.specular=part.specular;draw.specular_color=part.specular_color;
        draw.emissive_image=part.emissive_image;draw.normal_image=part.normal_image;draw.orm_image=part.orm_image;draw.emission=part.emission;draw.normal_scale=part.normal_scale;draw.uv_sets=part.uv_sets;draw.ao_image=part.ao_image;draw.ao_strength=part.ao_strength;
        for(unsigned slot=0;slot<5;++slot) {
            draw.samplers[slot]=p.sampler_for(part.samplers[slot]);
        }
        for(const auto &vertex:part.vertices){draw.center.x+=vertex.position.x;draw.center.y+=vertex.position.y;draw.center.z+=vertex.position.z;}
        const float denominator=static_cast<float>(part.vertices.size());draw.center.x/=denominator;draw.center.y/=denominator;draw.center.z/=denominator;
        draw.vertex_bytes=part.vertices.size()*sizeof(Vertex);draw.index_bytes=part.indices.size()*sizeof(std::uint32_t);p.gpu_bytes+=draw.vertex_bytes+draw.index_bytes;
        glGenVertexArrays(1,&draw.vao);glGenBuffers(1,&draw.vbo);glGenBuffers(1,&draw.ebo);glBindVertexArray(draw.vao);glBindBuffer(GL_ARRAY_BUFFER,draw.vbo);
        glBufferData(GL_ARRAY_BUFFER,static_cast<GLsizeiptr>(part.vertices.size()*sizeof(Vertex)),part.vertices.data(),GL_STATIC_DRAW);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,draw.ebo);glBufferData(GL_ELEMENT_ARRAY_BUFFER,static_cast<GLsizeiptr>(part.indices.size()*sizeof(std::uint32_t)),part.indices.data(),GL_STATIC_DRAW);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,position)));
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,normal)));
        for(unsigned set=0;set<4;++set){glEnableVertexAttribArray(2+set);glVertexAttribPointer(2+set,2,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,uv)+set*2*sizeof(float)));}
        glEnableVertexAttribArray(6);glVertexAttribPointer(6,4,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,tangent)));
        if(draw.blend)p.blended_parts.push_back(p.parts.size());
        p.parts.push_back(draw);
        p.stats.vertices+=part.vertices.size();p.stats.triangles+=part.indices.size()/3;
        for(const auto &vertex:part.vertices)if(std::abs(vertex.tangent[3])>.5f)++p.stats.tangent_vertices;
        p.stats.geometry_bytes+=part.vertices.size()*sizeof(Vertex)+part.indices.size()*sizeof(std::uint32_t);
        p.stats.draw_calls+=part.blend?2:1;
    }
    if(glGetError()!=GL_NO_ERROR){p.clear_model();p.error="The graphics driver could not allocate the 3D exhibit geometry";return false;}
    return true;
}
bool ObjectScene::Impl::upload_geometry_step(Model&model,std::size_t&budget,SceneClock::time_point started) {
    State state;auto&p=*this;p.material_notes=model.notes;p.timings.pending_images=0;
    while(p.geometry_part<model.parts.size()) {
        const auto&part=model.parts[p.geometry_part];
        if(p.parts.size()==p.geometry_part) {
        if(elapsed_ms(started)>=upload_budget_ms)return false;
        const auto storage_start=SceneClock::now();
        Impl::Draw draw;draw.count=static_cast<GLsizei>(part.indices.size());draw.color=part.color;
        draw.image=part.image;draw.cutoff=part.cutoff;draw.unlit=part.unlit;draw.blend=part.blend;
        draw.double_sided=part.double_sided;draw.mirrored=part.mirrored;
        draw.restore=part.restore;draw.roughness=part.roughness;draw.metallic=part.metallic;draw.specular=part.specular;draw.specular_color=part.specular_color;
        draw.emissive_image=part.emissive_image;draw.normal_image=part.normal_image;draw.orm_image=part.orm_image;draw.emission=part.emission;draw.normal_scale=part.normal_scale;draw.uv_sets=part.uv_sets;draw.ao_image=part.ao_image;draw.ao_strength=part.ao_strength;
        for(unsigned slot=0;slot<5;++slot) {
            draw.samplers[slot]=p.sampler_for(part.samplers[slot]);
        }
        draw.center=part.center;
        draw.vertex_bytes=part.vertices.size()*sizeof(Vertex);draw.index_bytes=part.indices.size()*sizeof(std::uint32_t);p.gpu_bytes+=draw.vertex_bytes+draw.index_bytes;
        glGenVertexArrays(1,&draw.vao);glGenBuffers(1,&draw.vbo);glGenBuffers(1,&draw.ebo);glBindVertexArray(draw.vao);glBindBuffer(GL_ARRAY_BUFFER,draw.vbo);
        glBufferData(GL_ARRAY_BUFFER,static_cast<GLsizeiptr>(part.vertices.size()*sizeof(Vertex)),nullptr,GL_STATIC_DRAW);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,draw.ebo);glBufferData(GL_ELEMENT_ARRAY_BUFFER,static_cast<GLsizeiptr>(part.indices.size()*sizeof(std::uint32_t)),nullptr,GL_STATIC_DRAW);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,position)));
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,normal)));
        for(unsigned set=0;set<4;++set){glEnableVertexAttribArray(2+set);glVertexAttribPointer(2+set,2,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,uv)+set*2*sizeof(float)));}
        glEnableVertexAttribArray(6);glVertexAttribPointer(6,4,GL_FLOAT,GL_FALSE,sizeof(Vertex),reinterpret_cast<void*>(offsetof(Vertex,tangent)));
        if(draw.blend)p.blended_parts.push_back(p.parts.size());
        p.parts.push_back(draw);
            p.stats.vertices+=part.vertices.size();p.stats.triangles+=part.indices.size()/3;p.stats.tangent_vertices+=part.tangent_vertices;p.stats.geometry_bytes+=part.vertices.size()*sizeof(Vertex)+part.indices.size()*sizeof(std::uint32_t);p.stats.draw_calls+=part.blend?2:1;
            p.timings.last_storage_ms=elapsed_ms(storage_start);p.timings.max_storage_ms=std::max(p.timings.max_storage_ms,p.timings.last_storage_ms);p.timings.total_storage_ms+=p.timings.last_storage_ms;p.timings.storage_calls+=2;
            if(p.timings.last_storage_ms>4)hui::sys::log("[Museum] 3D geometry allocation %.2fms / %zu KiB / %zu unique samplers",p.timings.last_storage_ms,(draw.vertex_bytes+draw.index_bytes)>>10,p.samplers.size());
            if(glGetError()!=GL_NO_ERROR){p.error="The graphics driver could not allocate staged 3D geometry";return false;}
        }
        auto&draw=p.parts[p.geometry_part];
        const std::size_t vertex_bytes=part.vertices.size()*sizeof(Vertex),index_bytes=part.indices.size()*sizeof(std::uint32_t);
        while(p.vertex_offset<vertex_bytes||p.index_offset<index_bytes) {
            if(!budget||elapsed_ms(started)>=upload_budget_ms)return false;
            const bool vertex=p.vertex_offset<vertex_bytes;auto&offset=vertex?p.vertex_offset:p.index_offset;const auto total=vertex?vertex_bytes:index_bytes;
            const auto count=std::min({total-offset,budget,transfer_chunk});const auto target=vertex?GL_ARRAY_BUFFER:GL_ELEMENT_ARRAY_BUFFER;glBindVertexArray(draw.vao);glBindBuffer(target,vertex?draw.vbo:draw.ebo);
            const auto*data=vertex?reinterpret_cast<const std::uint8_t*>(part.vertices.data()):reinterpret_cast<const std::uint8_t*>(part.indices.data());
            const auto transfer_start=SceneClock::now();glBufferSubData(target,static_cast<GLintptr>(offset),static_cast<GLsizeiptr>(count),data+offset);transfer_sample(transfer_start,count);offset+=count;budget-=count;timings.uploaded_bytes+=count;timings.last_upload_bytes+=count;timings.max_upload_bytes=std::max(timings.max_upload_bytes,timings.last_upload_bytes);++timings.upload_calls;
            if(glGetError()!=GL_NO_ERROR){p.error="The graphics driver could not upload staged 3D geometry";return false;}
        }
        ++p.geometry_part;p.vertex_offset=p.index_offset=0;
        if(elapsed_ms(started)>=upload_budget_ms&&p.geometry_part<model.parts.size())return false;
    }
    return true;
}

GLuint ObjectScene::render(float angle,int width,int height,float tilt,bool source_z_up,float zoom,float center_x,float center_y,bool pin_studio) {
    auto &p=*impl_;if(!ready())return 0;
    CpuSample render_sample{p.timings.last_render_ms,p.timings.max_render_ms};p.timings.render_width=width;p.timings.render_height=height;p.timings.render_samples=1;p.timings.coverage_post_aa=true;
    if(width<1||height<1||width>4096||height>4096||static_cast<std::uint64_t>(width)*static_cast<std::uint64_t>(height)>3840u*2160u||!std::isfinite(angle)){p.error="Invalid 3D exhibit viewport";return 0;}
    State state;
    if(width!=p.width||height!=p.height) {
        const auto allocation_start=SceneClock::now();
        p.clear_target();p.width=width;p.height=height;
        glGenTextures(1,&p.texture);glBindTexture(GL_TEXTURE_2D,p.texture);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,nullptr);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
        glGenFramebuffers(1,&p.resolve_fbo);glBindFramebuffer(GL_FRAMEBUFFER,p.resolve_fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,p.texture,0);
        if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE){p.error="3D exhibit alpha framebuffer is incomplete";p.clear_target();return 0;}
        glGenTextures(1,&p.scene_texture);glBindTexture(GL_TEXTURE_2D,p.scene_texture);glTexImage2D(GL_TEXTURE_2D,0,GL_SRGB8_ALPHA8,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,nullptr);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
        // PS5 AGC currently resolves multisample framebuffer blits on the CPU.
        // Keep every requested pixel, using a directly renderable single-sample
        // texture and the GPU coverage-only post pass instead of that fallback.
        glGenRenderbuffers(1,&p.depth);glBindRenderbuffer(GL_RENDERBUFFER,p.depth);
        glRenderbufferStorage(GL_RENDERBUFFER,GL_DEPTH_COMPONENT24,width,height);
        glGenFramebuffers(1,&p.fbo);glBindFramebuffer(GL_FRAMEBUFFER,p.fbo);
        glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,p.scene_texture,0);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_RENDERBUFFER,p.depth);
        if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE){p.error="3D exhibit framebuffer is incomplete";p.clear_target();return 0;}
        p.timings.render_samples=1;p.timings.coverage_post_aa=true;
        hui::sys::log("[Museum] 3D target %dx%d / single-sample + GPU silhouette AA / no framebuffer blit",width,height);
        p.timings.target_allocation_ms=elapsed_ms(allocation_start);
    }
    const int gpu_query=p.begin_gpu();
    glBindFramebuffer(GL_FRAMEBUFFER,p.fbo);glViewport(0,0,width,height);glDisable(GL_SCISSOR_TEST);glDisable(GL_CULL_FACE);glDisable(GL_BLEND);glEnable(GL_FRAMEBUFFER_SRGB);
    glDisable(GL_MULTISAMPLE);glDisable(GL_SAMPLE_ALPHA_TO_COVERAGE);glDisable(GL_SAMPLE_COVERAGE);
    glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);
    glClearDepth(1);glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    tilt=std::clamp(std::isfinite(tilt)?tilt:.13f,-1.5f,1.5f);
    const float cosine=std::cos(angle),sine=std::sin(angle),ct=std::cos(tilt),st=std::sin(tilt);
    const Matrix turn{cosine,0,-sine,0,0,1,0,0,sine,0,cosine,0,0,0,0,1};
    const Matrix pitch{1,0,0,0,0,ct,st,0,0,-st,ct,0,0,0,0,1};
    // CAD sources can be authored with Z as their physical up axis. Normalize
    // that baseline before rotating, so a tabletop console turns horizontally
    // rather than tumbling around its front-to-back axis.
    const Matrix source=source_z_up?Matrix{1,0,0,0,0,0,-1,0,0,1,0,0,0,0,0,1}:identity();
    const Matrix rotation=multiply(pitch,multiply(turn,source));
    const std::array<float,9> normal_rotation{rotation[0],rotation[1],rotation[2],rotation[4],rotation[5],rotation[6],rotation[8],rotation[9],rotation[10]};
    Matrix view=identity();view[14]=-4.1f;
    zoom=std::clamp(std::isfinite(zoom)?zoom:1.0f,.25f,4.0f);
    const float aspect=static_cast<float>(width)/static_cast<float>(height),near=.1f,far=20;
    // Geometry is normalized to a unit sphere. Its perspective tangent gives
    // an orientation-independent horizontal bound, including when tilted.
    const float distance_tangent=std::sqrt(4.1f*4.1f-1.f);
    const float focal=std::min(2.85f*std::min(1.0f,aspect)*zoom,.98f*aspect*distance_tangent);
    const float horizontal_extent=focal/(aspect*distance_tangent);
    const float position=std::clamp(std::isfinite(center_x)?center_x:0.f,-.98f+horizontal_extent,.98f-horizontal_extent);
    Matrix projection{};projection[0]=focal/aspect;projection[5]=focal;projection[8]=-position;projection[9]=-std::clamp(std::isfinite(center_y)?center_y:0.f,-1.f,1.f);projection[10]=(far+near)/(near-far);projection[11]=-1;projection[14]=2*far*near/(near-far);
    const Matrix mvp=multiply(projection,multiply(view,rotation));
    glUseProgram(p.program);glUniformMatrix4fv(p.mvp,1,GL_FALSE,mvp.data());glUniformMatrix3fv(p.rotation,1,GL_FALSE,normal_rotation.data());
    glUniform1i(p.pin_studio,pin_studio?1:0);
    const auto draw=[&](const Impl::Draw &part,int pass) {
        glFrontFace(part.mirrored?GL_CW:GL_CCW);glCullFace(GL_BACK);
        if(part.double_sided)glDisable(GL_CULL_FACE);else glEnable(GL_CULL_FACE);
        glUniform4fv(p.base,1,part.color.data());glUniform1f(p.cutoff,part.cutoff);glUniform1i(p.unlit,part.unlit?1:0);glUniform1i(p.textured,part.image>=0?1:0);glUniform1i(p.blended,part.blend?1:0);glUniform1i(p.alpha_pass,pass);
        glUniform3i(p.restore_counts,part.restore.region_count,part.restore.detail_count,part.restore.ink_count);
        // Ordinary authored materials never read restoration-region arrays.
        // Always reset the counts, including after a restored material, while
        // avoiding repeated inactive uniform uploads on unmodified consoles.
        if(part.restore.region_count>0){
            glUniform4fv(p.restore_regions,part.restore.region_count,part.restore.regions[0].data());
            if(part.restore.detail_count>0)glUniform4fv(p.restore_details,part.restore.detail_count,part.restore.details[0].data());
            if(part.restore.ink_count>0)glUniform4fv(p.restore_ink,part.restore.ink_count,part.restore.ink[0].data());
            glUniform4fv(p.restore_colour,1,part.restore.colour_roughness.data());
        }
        glUniform1f(p.roughness,part.roughness);glUniform1f(p.metallic,part.metallic);glUniform1f(p.specular,part.specular);glUniform3fv(p.specular_color,1,part.specular_color.data());
        glUniform1i(p.has_emission,part.emissive_image>=0?1:0);glUniform1i(p.has_normal,part.normal_image>=0?1:0);glUniform1i(p.has_orm,part.orm_image>=0?1:0);glUniform3fv(p.emission,1,part.emission.data());glUniform1f(p.normal_scale,part.normal_scale);
        glUniform4iv(p.uv_sets,1,part.uv_sets.data());
        glUniform1i(p.has_ao,part.ao_image>=0?1:0);glUniform1f(p.ao_strength,part.ao_strength);glUniform1i(p.ao_uv,part.uv_sets[4]);
        const int maps[]{part.image,part.emissive_image,part.normal_image,part.orm_image,part.ao_image};
        for(unsigned i=0;i<5;++i){glActiveTexture(GL_TEXTURE0+i);glBindSampler(i,part.samplers[i]);glBindTexture(GL_TEXTURE_2D,maps[i]>=0?(i<2?p.images:p.linear_images)[static_cast<std::size_t>(maps[i])]:0);}
        glActiveTexture(GL_TEXTURE0);glBindVertexArray(part.vao);glDrawElements(GL_TRIANGLES,part.count,GL_UNSIGNED_INT,nullptr);
    };
    // Depth-write opaque texels even when an exporter combines the entire
    // console shell and its translucent screen in one BLEND primitive.
    for(const auto &part:p.parts)draw(part,part.blend?1:0);
    std::sort(p.blended_parts.begin(),p.blended_parts.end(),[&](std::size_t a,std::size_t b){return transform(rotation,p.parts[a].center).z<transform(rotation,p.parts[b].center).z;});
    glEnable(GL_BLEND);glBlendEquationSeparate(GL_FUNC_ADD,GL_FUNC_ADD);glBlendFuncSeparate(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA,GL_ONE,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);
    for(std::size_t index:p.blended_parts)draw(p.parts[index],2);
    // One GPU sampling pass does silhouette AA and straight-alpha conversion.
    // No framebuffer readback, multisample resolve or framebuffer blit occurs.
    glBindFramebuffer(GL_FRAMEBUFFER,p.resolve_fbo);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);
    glUseProgram(p.resolve_program);glUniform2f(p.inverse_size,1.f/float(width),1.f/float(height));
    glBindVertexArray(p.resolve_vao);glBindTexture(GL_TEXTURE_2D,p.scene_texture);glBindSampler(0,0);glDrawArrays(GL_TRIANGLES,0,3);
    p.end_gpu(gpu_query);return p.texture;
}
void ObjectScene::release() {
    if(!impl_)return;
    impl_->stop_worker();impl_->clear_model();impl_->drain_gpu(true);impl_->clear_target();
    impl_->uploading.reset();
    if(impl_->gpu_queries[0])glDeleteQueries(4,impl_->gpu_queries.data());impl_->gpu_queries={};impl_->gpu_pending={};impl_->gpu_supported=false;
    if(impl_->program)glDeleteProgram(impl_->program);
    if(impl_->resolve_program)glDeleteProgram(impl_->resolve_program);
    if(impl_->resolve_vao)glDeleteVertexArrays(1,&impl_->resolve_vao);
    impl_->program=0;
    impl_->resolve_program=impl_->resolve_vao=0;
}
const std::string &ObjectScene::error() const{return impl_->error;}
std::string ObjectScene::stage()const{std::lock_guard<std::mutex> lock(impl_->mutex);return impl_->progress;}
const std::string &ObjectScene::material_notes() const{return impl_->material_notes;}
bool ObjectScene::ready() const{return impl_->program&&!impl_->parts.empty()&&!impl_->uploading;}
ObjectScene::Stats ObjectScene::stats() const{return impl_->stats;}
ObjectScene::Timings ObjectScene::timings() const{impl_->poll_gpu();impl_->timings.render_width=impl_->width;impl_->timings.render_height=impl_->height;impl_->timings.gpu_timing_supported=impl_->gpu_supported;impl_->timings.pending_gpu_deletes=impl_->retired_gpu.size();impl_->timings.planned_gpu_bytes=impl_->planned_gpu_bytes.load(std::memory_order_relaxed);impl_->timings.estimated_gpu_bytes=impl_->gpu_bytes+impl_->retired_bytes+static_cast<std::size_t>(impl_->width)*static_cast<std::size_t>(impl_->height)*12;impl_->timings.peak_estimated_gpu_bytes=std::max(impl_->timings.peak_estimated_gpu_bytes,impl_->timings.estimated_gpu_bytes);return impl_->timings;}
} // namespace museum
