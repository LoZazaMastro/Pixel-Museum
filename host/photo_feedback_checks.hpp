// Actual Screen input/update traces; no controller hardware is simulated here.
#pragma once
namespace museum {
inline bool ScreenInspection::verify_photo_feedback(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool ok,const char*message){if(!ok)std::fprintf(stderr,"Photo feedback check failed: %s\n",message);return ok;};
 const auto data=s.data_;s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.settings_=s.credits_=s.year_guide_=s.chapters_=false;s.select("wikipedia-3467400");s.preview(0);s.image_index_=0;s.open_photo({950,220,826,478});s.gallery_open_.snap(1);s.fade_=1;
 if(!require(s.gallery_&&!s.viewer_.images().empty(),"real catalog photograph opens in actual Screen"))return false;
 s.viewer_.set_bounds({0,0,1920,1080});
 hui::ui::Feedback feedback;const auto input=[](){hui::InputFrame i;i.connected=true;return i;};
 const auto step=[&](const hui::InputFrame&i,float dt){feedback.clear();s.handle(i,feedback);s.update(dt);return feedback.tactile.size();};
 const auto count=[&](int hz,int frames,const hui::InputFrame&i,hui::audio::Tactile expected){unsigned total=0;for(int n=0;n<frames;++n){step(i,1.f/hz);for(const auto&e:feedback.tactile){if(e.pattern!=expected)return -1;++total;}}return int(total);};
 for(int hz:{30,60,120}){
  s.viewer_.set_zoom(1,true);s.viewer_.take_motion_feedback();s.tactile_repeat_=0;
  auto zoom=input();zoom.trigger_r=.45f;const float before=s.viewer_.zoom();const int pulses=count(hz,hz,zoom,hui::audio::Tactile::zoom_in);
  if(!require(s.viewer_.zoom()>before&&pulses>=10&&pulses<=16,"trigger zoom produces spaced zoom-in textures at30/60/120Hz"))return false;
  step(input(),1.f/hz);s.tactile_repeat_=0;zoom.trigger_r=0;zoom.trigger_l=.3f;const float enlarged=s.viewer_.zoom();const int out=count(hz,hz,zoom,hui::audio::Tactile::zoom_out);
  if(!require(s.viewer_.zoom()<enlarged&&out>=10&&out<=16,"reverse trigger produces zoom-out rather than generic focus"))return false;
  std::printf("Actual photo analog %dHz: in=%d out=%d, bounded65ms cadence PASS\n",hz,pulses,out);
 }
 step(input(),1.f/60);s.viewer_.set_zoom(4,true);s.viewer_.take_motion_feedback();s.tactile_repeat_=0;
 auto pan=input();pan.stick_x=.25f;const float before_pan=s.viewer_.pan_x();const int pans=count(60,30,pan,hui::audio::Tactile::touch);
 if(!require(s.viewer_.pan_x()!=before_pan&&pans>0&&pans<=8,"left-stick pan reports actual movement with touch texture"))return false;
 step(input(),1.f/60);if(!require(count(60,20,input(),hui::audio::Tactile::touch)==0,"passive spring return emits no new texture"))return false;
 s.viewer_.set_zoom(100,true);s.viewer_.take_motion_feedback();s.tactile_repeat_=0;auto max=input();max.trigger_r=1;
 if(!require(count(60,20,max,hui::audio::Tactile::zoom_in)==0,"holding a clamped zoom trigger does not pulse"))return false;
 s.viewer_.set_zoom(1,true);s.viewer_.take_motion_feedback();s.tactile_repeat_=0;auto move=input();move.trigger_r=.4f;step(move,1.f/60);
 auto lost=input();lost.focus_lost=true;step(lost,1.f/60);if(!require(feedback.tactile.empty(),"focus loss consumes pending movement without feedback"))return false;
 step(input(),1.f/60);if(!require(feedback.tactile.empty(),"focus return does not replay a stale photograph gesture"))return false;
 step(move,1.f/60);lost=input();lost.connected=false;step(lost,1.f/60);if(!require(feedback.tactile.empty(),"disconnect suppresses pending movement"))return false;
 step(input(),1.f/60);if(!require(feedback.tactile.empty(),"reconnect does not replay a pending gesture"))return false;
 s.viewer_.set_zoom(1,true);s.viewer_.take_motion_feedback();s.tactile_repeat_=0;auto discrete=input();discrete.pressed=hui::action_bit(hui::Action::confirm);const auto events=step(discrete,1.f/60);
 if(!require(events<=1&&count(60,10,input(),hui::audio::Tactile::zoom_in)==0,"discrete zoom is not duplicated by deferred analog feedback"))return false;
 s.gallery_=false;s.gallery_open_.snap(0);s.object_inspect_=true;s.object_texture_=1;s.tactile_repeat_=0;auto orbit=input();orbit.stick2_x=.5f;feedback.clear();s.handle(orbit,feedback);
 if(!require(feedback.tactile.size()==1&&feedback.tactile.front().pattern==hui::audio::Tactile::rotate,"3D orbit retains one distinct rotation event"))return false;
 s.object_texture_=0;s.object_inspect_=false;s.data_=data;s.preview(0);s.draw(width,height,framebuffer);
 if(!require(glGetError()==GL_NO_ERROR,"restored actual Screen draws GL0"))return false;
 std::puts("PASS actual Screen photograph feedback: analog zoom/pan,30/60/120Hz cadence, clamps, passive return, focus/disconnect, discrete/3D dedup; GL0. Physical sensation remains unverified.");return true;
}
}
