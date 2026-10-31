// Pixel Museum - area filtered photographic images, never source upscaling.
// Copyright (C) 2026 Andrea Sgarro. SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/image_quality.hpp"
#include "yt/image.hpp"
#include <algorithm>
#include <array>
#include <cmath>
namespace museum::media::detail {
bool reduce_photo(const std::vector<std::uint8_t>&source,int width,int height,int tw,int th,std::vector<std::uint8_t>*result){
 if(!result||width<1||height<1||tw<1||th<1||tw>width||th>height||static_cast<std::size_t>(width)*height>kPhotoSourcePixels||static_cast<std::size_t>(tw)*th>kPhotoPixels||source.size()!=static_cast<std::size_t>(width)*height*4)return false;
 result->resize(static_cast<std::size_t>(tw)*th*4);
 std::array<double,256> linear{};for(unsigned i=0;i<256;++i){const double v=double(i)/255;linear[i]=v<=.04045?v/12.92:std::pow((v+.055)/1.055,2.4);}
 const double sx=double(width)/tw,sy=double(height)/th;
 for(int y=0;y<th;++y)for(int x=0;x<tw;++x){
  const double left=x*sx,right=(x+1)*sx,top=y*sy,bottom=(y+1)*sy;std::array<double,3> color{};double alpha=0;
  for(int iy=int(top);iy<std::min(height,int(std::ceil(bottom)));++iy){const double wy=std::min(bottom,double(iy+1))-std::max(top,double(iy));
   for(int ix=int(left);ix<std::min(width,int(std::ceil(right)));++ix){const double area=wy*(std::min(right,double(ix+1))-std::max(left,double(ix)));const auto p=(static_cast<std::size_t>(iy)*width+ix)*4;const double weighted_alpha=area*source[p+3]/255.;alpha+=weighted_alpha;for(unsigned c=0;c<3;++c)color[c]+=linear[source[p+c]]*weighted_alpha;}}
  const auto to=(static_cast<std::size_t>(y)*tw+x)*4;for(unsigned c=0;c<3;++c){const double v=alpha>1e-12?color[c]/alpha:0;const double encoded=v<=.0031308?v*12.92:1.055*std::pow(v,1/2.4)-.055;(*result)[to+c]=static_cast<std::uint8_t>(std::clamp(std::lround(encoded*255),0L,255L));}(*result)[to+3]=static_cast<std::uint8_t>(std::clamp(std::lround(alpha/(sx*sy)*255),0L,255L));
 }
 return true;
}
bool prepare_photo(const std::string&encoded,int*w,int*h,int*sw,int*sh,std::vector<std::uint8_t>*rgba,std::string*error){
 if(!w||!h||!sw||!sh||!rgba||!error)return false;
 *w=*h=*sw=*sh=0;rgba->clear();error->clear();if(encoded.size()>=kPhotoLocalBytes){*error="Image exceeds the 32 MiB local source limit";return false;}
 if(!yt::decode_image(encoded,w,h,rgba,error,kPhotoSourcePixels,int(kPhotoSourceEdge)))return false;
 *sw=*w;*sh=*h;const int longest=std::max(*w,*h);if(longest<=int(kPhotoEdge))return true;
 const int tw=std::max(1,int(static_cast<std::int64_t>(*w)*kPhotoEdge/longest)),th=std::max(1,int(static_cast<std::int64_t>(*h)*kPhotoEdge/longest));std::vector<std::uint8_t> reduced;
 if(!reduce_photo(*rgba,*w,*h,tw,th,&reduced)){*error="Image cannot be reduced within the photographic memory limit";rgba->clear();return false;}
 *rgba=std::move(reduced);*w=tw;*h=th;return true;
}
}
