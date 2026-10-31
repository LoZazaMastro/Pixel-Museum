#pragma once
#include <thread>
namespace museum {
inline bool ScreenInspection::verify_model_stage_1080(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*note){if(!ok)std::fprintf(stderr,"Native4K stage FAILED: %s\n",note);return ok;};
 if(!require(width==3840&&height==2160,"actual output is4K"))return false;
 s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.year_guide_=false;s.panel_.snap(0);s.year_panel_.snap(0);s.dark_theme_=true;s.theme_mix_.snap(1);s.reduced_=true;s.preview(0);
 const char*selected=std::getenv("MUSEUM_MODEL_STAGE_ENTRY");
 const std::vector<std::string>ids=selected?std::vector<std::string>{selected}:std::vector<std::string>{"game-boy","playstation"};
 for(const auto&entry_id:ids){const char*id=entry_id.c_str();
  s.select(id);freeze_object(s);const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(120);
  while(!s.object_texture_&&std::chrono::steady_clock::now()<deadline){s.update(1.f/120);std::this_thread::sleep_for(std::chrono::milliseconds(2));if(!s.object_.error().empty()){std::fprintf(stderr,"%s error: %s\n",id,s.object_.error().c_str());return false;}}
  if(!require(s.object_texture_&&s.object_.ready(),"actual production Screen loads3D texture"))return false;
  for(int n=0;n<40;++n){s.update(1.f/120);s.draw(width,height,framebuffer);}
  const auto t=s.object_.timings();
  if(!require(t.render_width==3840&&t.render_height==1920&&t.render_samples==1&&t.coverage_post_aa,"transparent2:1stage3840x1920withGPUcoverageAA"))return false;
  if(!require(s.composed_.width()==3840&&s.composed_.height()==2160&&s.output_width_==3840&&s.output_height_==2160,"UIcomposedatfull4Knot1080upscale"))return false;
  glBindTexture(GL_TEXTURE_2D,s.object_texture_);GLint tw=0,th=0;glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&tw);glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_HEIGHT,&th);
  if(!require(tw==3840&&th==1920,"actualGLobjecttexturematchesstage"))return false;
  std::vector<unsigned char>stage(size_t(tw)*th*4);glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,stage.data());size_t empty=0,solid=0,coverage=0;int left=tw,right=-1,bottom=th,top=-1;for(size_t n=3;n<stage.size();n+=4){if(stage[n]==0)++empty;else {if(stage[n]==255)++solid;else ++coverage;const int pixel=int(n/4),x=pixel%tw,y=pixel/tw;left=std::min(left,x);right=std::max(right,x);bottom=std::min(bottom,y);top=std::max(top,y);}}
  if(selected){if(!require(left>0&&right<tw-1&&bottom>0&&top<th-1,"entire selected model fits stage without edge clipping"))return false;std::printf("Modelbounds %s %d,%d .. %d,%d / initialzoom%.3f actualrenderzoom%.3f\n",id,left,bottom,right,top,s.object_zoom_,s.object_render_zoom_);}
  if(!require(empty>1000&&solid>1000&&coverage>0&&glGetError()==GL_NO_ERROR,"actualtransparenttexturecontainsmodelandfractionalAAcoverageGL0"))return false;
  std::vector<unsigned char>pixels(size_t(width)*height*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);const auto path=std::string("build/previews/model-stage4k-")+id+"-4k.png";
  if(!require(stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4)&&glGetError()==GL_NO_ERROR,"actual4KcompositePNGGL0"))return false;
  if(selected){const float upper=-9.f+(th-1-top)*.5f,lower=-9.f+(th-bottom)*.5f;std::printf("Actualtimelinehero modelbounds %.2f..%.2f / clip142..766\n",upper,lower);if(!require(upper>=142&&lower<=766,"entire selected model also fits actual timeline hero clip"))return false;}
  std::printf("PASSnative4Kstage %s / stage%dx%d /4KUI%d x%d / empty%zu solid%zu coverage%zu / planned%zu actual%zuMiB / ready%.2fms / GL0\n",id,tw,th,width,height,empty,solid,coverage,t.planned_gpu_bytes>>20,t.estimated_gpu_bytes>>20,t.load_ready_ms);
 }
 return true;
}
}
