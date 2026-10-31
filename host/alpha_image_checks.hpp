// Real PNG decode/upload/Screen image/composition checks, no media downloaded.
#pragma once
#include "yt/image.hpp"
#include "third_party/stb/stb_image_write.h"
#include <fstream>
#include <iterator>
namespace museum {
inline bool ScreenInspection::verify_alpha_images(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*what){if(!ok)std::fprintf(stderr,"Alpha image check failed: %s\n",what);return ok;};
 const auto read=[](const char*path){std::ifstream in(path,std::ios::binary);return std::string(std::istreambuf_iterator<char>(in),{});};
 s.onboarding_=false;s.data_.clear();s.cache_.stop();
 if(!require(s.cache_.images_from_package("build/photo-alpha-package")&&s.cache_.start("build/photo-alpha-package/cache"),"local synthetic alpha package opens without network"))return false;
 s.select("nintendo-64");s.object_.cancel();s.object_texture_=0;
 const auto*entry=s.current();if(!require(entry&&entry->id=="nintendo-64"&&entry->images.size()>5,"actual Nintendo64 DD source exists"))return false;
 const Image photo=entry->images[5];
 const auto wait=[&](const std::string&url,int wanted_width){s.cache_.set_visible({url});s.cache_.request(url);for(unsigned tick=0;tick<10000;++tick){s.cache_.upload_pending(s.renderer_);const auto a=s.cache_.get(url);if(a.texture&&a.width==wanted_width&&a.width==a.source_width&&a.height==a.source_height){GLint resident_width=0;glBindTexture(GL_TEXTURE_2D,a.texture);glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&resident_width);if(resident_width==wanted_width)return true;}std::this_thread::sleep_for(std::chrono::milliseconds(1));}return false;};
 if(!require(wait(photo.url,2960),"real packaged PNG master becomes resident"))return false;
 const auto asset=s.cache_.get(photo.url);int sw=0,sh=0;std::vector<std::uint8_t>source;std::string error;
 if(!require(yt::decode_image(read("build/research/n64-source-recovery-editorial/64DD-Attached.png"),&sw,&sh,&source,&error),"native STB decodes original RGBA PNG"))return false;
 if(!require(asset.width==sw&&asset.height==sh,"real transparent master retains native dimensions"))return false;
 std::vector<std::uint8_t>uploaded(source.size());glBindTexture(GL_TEXTURE_2D,asset.texture);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,uploaded.data());
 if(!require(uploaded==source,"all uploaded native RGBA bytes match original, including hidden RGB and alpha"))return false;
 Image synthetic;synthetic.url="https://local.test/alpha-composition";if(!require(wait(synthetic.url,500),"numerical alpha fixture loads through the same cache worker"))return false;
 const auto pixel=[&](const std::vector<std::uint8_t>&pixels,int x,int y,unsigned c){return pixels[(size_t(height-1-y)*width+size_t(x))*4+c];};
 auto paint=[&](const Image&i,hui::gfx::Color background,float opacity,std::vector<std::uint8_t>&pixels,hui::gfx::Rect&bounds){
  hui::gfx::DrawList layer;layer.rounded_rect({0,0,1920,1080},0,background);s.image_fades_[i.url]=1;s.image(layer,i,{160,150,1600,780},true,opacity);
  if(layer.instances().size()!=2||layer.instances().back().params[0]!=0)return false;
  const auto&rect=layer.instances().back().rect;bounds={rect[0],rect[1],rect[2],rect[3]};
  s.renderer_.begin();s.renderer_.draw(layer);s.renderer_.present(framebuffer,width,height);glBindFramebuffer(GL_FRAMEBUFFER,framebuffer);pixels.resize(size_t(width)*height*4);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());return glGetError()==GL_NO_ERROR;
 };
 for(bool dark:{false,true}){
  s.dark_theme_=dark;s.theme_mix_.snap(dark?1.f:0.f);const auto background=s.colours().paper;std::vector<std::uint8_t>pixels;hui::gfx::Rect bounds;
  if(!require(paint(photo,background,1,pixels,bounds),"real Screen image emits only image geometry, with no added frame"))return false;
  unsigned invisible=0,hidden_nonzero=0;
  for(int y=0;y<height;y+=13)for(int x=0;x<width;x+=13){const float u=((float(x)+.5f)*1920/width-bounds.x)/bounds.w,v=((float(y)+.5f)*1080/height-bounds.y)/bounds.h;if(u<=0||u>=1||v<=0||v>=1)continue;const int sx=std::clamp(int(std::floor(u*sw-.5f)),0,sw-2),sy=std::clamp(int(std::floor(v*sh-.5f)),0,sh-2);bool transparent=true;for(int dy=0;dy<2;++dy)for(int dx=0;dx<2;++dx)transparent&=source[(size_t(sy+dy)*sw+size_t(sx+dx))*4+3]==0;if(!transparent)continue;++invisible;const auto at=(size_t(sy)*sw+size_t(sx))*4;hidden_nonzero+=source[at]||source[at+1]||source[at+2];const float bg[]={background.r,background.g,background.b};for(unsigned c=0;c<3;++c)if(std::abs(int(pixel(pixels,x,y,c))-int(std::lround(bg[c]*255)))>1)return require(false,"zero-alpha hidden RGB never creates a white rectangle on either theme");}
  if(!require(invisible>1000&&hidden_nonzero>0,"real source exercises thousands of transparent pixels containing hidden RGB"))return false;
  const auto path=std::string("build/previews/png-alpha-")+(dark?"dark":"light")+"-4k.png";stbi_flip_vertically_on_write(1);if(!require(stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4)!=0,"native-resolution inspection PNG written"))return false;
  std::printf("PASS real PNG %s: %dx%d RGBA retained, %u fully-transparent samples preserve theme (%u with hidden RGB), no border geometry, GL0.\n",dark?"dark":"light",sw,sh,invisible,hidden_nonzero);
  for(float opacity:{1.f,.5f}){
   if(!require(paint(synthetic,background,opacity,pixels,bounds),"synthetic source uses actual Screen/image/shader path"))return false;
   for(unsigned stripe=0;stripe<5;++stripe){const auto x=int((bounds.x+bounds.w*(float(stripe)+.5f)/5)*width/1920),y=int((bounds.y+bounds.h*.5f)*height/1080);const float alpha=float(std::array<int,5>{0,64,128,192,255}[stripe])/255*opacity;const float bg[]={background.r,background.g,background.b};const int rgb[]={40,170,230};for(unsigned c=0;c<3;++c){const int expected=int(std::lround(rgb[c]*alpha+bg[c]*255*(1-alpha)));if(std::abs(int(pixel(pixels,x,y,c))-expected)>2)return require(false,"straight RGBA alpha and image fade blend exactly once, without double multiplication");}}
  }
 }
 std::puts("PASS native PNG alpha: original byte parity, transparent-background pixel invariance, straight RGBA/opacity compositing on both themes; host4K renderer, not physical PS5.");return true;
}
}
