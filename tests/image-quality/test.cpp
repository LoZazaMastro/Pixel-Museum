// Pixel Museum - photo source detail and area integration checks. SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/image_quality.hpp"
#include <cassert>
#include <cstdio>
#include <vector>
#include <string>
#include <cmath>
std::string read(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);std::string bytes(ftell(f),'\0');rewind(f);assert(fread(bytes.data(),1,bytes.size(),f)==bytes.size());fclose(f);return bytes;}
int main(int argc,char**argv){using namespace museum::media::detail;std::vector<unsigned char>out;
 assert(reduce_photo({0,0,0,255,255,255,255,255},2,1,1,1,&out));assert(std::abs(int(out[0])-188)<=1&&out[3]==255);
 assert(reduce_photo({255,0,0,255,0,0,255,0},2,1,1,1,&out));assert(out[0]==255&&out[1]==0&&out[2]==0&&out[3]==128);
 assert(reduce_photo({0,0,0,255,255,255,255,255,0,0,0,255},3,1,2,1,&out));assert(std::abs(int(out[0])-156)<=1&&std::abs(int(out[4])-156)<=1);
 assert(!reduce_photo({0,0,0,255},1,1,2,2,&out));
 int w,h,sw,sh;std::string error;
 assert(prepare_photo(read("build/photo-fixtures/native-4k.png"),&w,&h,&sw,&sh,&out,&error));assert(w==3840&&h==2160&&sw==3840&&sh==2160);assert(out[0]==255&&out[3840*4+1]==255);
 assert(prepare_photo(read("build/photo-fixtures/wide.png"),&w,&h,&sw,&sh,&out,&error));assert(w==4096&&h==1600&&sw==5120&&sh==2000);assert(out[2]==255);
 assert(prepare_photo(read("build/photo-fixtures/small.png"),&w,&h,&sw,&sh,&out,&error));assert(w==200&&h==100&&sw==200&&sh==100);
 assert(!prepare_photo(read("build/photo-fixtures/over-budget.png"),&w,&h,&sw,&sh,&out,&error));assert(error.find("memory limit")!=std::string::npos);
 assert(!prepare_photo(std::string(kPhotoLocalBytes,'x'),&w,&h,&sw,&sh,&out,&error));assert(error.find("32 MiB")!=std::string::npos);
 for(int i=1;i<argc;++i){
  const auto bytes=read(argv[i]);assert(prepare_photo(bytes,&w,&h,&sw,&sh,&out,&error));
  assert(std::size_t(sw)*sh>kPhotoPixels&&std::size_t(sw)*sh<=kPhotoSourcePixels);
  assert(w<=int(kPhotoEdge)&&h<=int(kPhotoEdge)&&std::size_t(w)*h<=kPhotoPixels&&out.size()==std::size_t(w)*h*4);
  if(sw==5560&&sh==3020){bool transparent=false,opaque=false;for(std::size_t n=3;n<out.size();n+=4){transparent|=out[n]==0;opaque|=out[n]==255;}assert(transparent&&opaque);}
  std::printf("PASS actual source %dx%d / %zu encoded bytes -> retained %dx%d / %zu bytes\n",sw,sh,bytes.size(),w,h,out.size());
 }
 puts("PASS: linear-light area average, premultiplied alpha, fractional area, no upscaling, exact4K detail,4096edge, source dimensions and encoded/decoded bounds");
}
