// Actual Screen owns focus and prevents every study from advancing offscreen.
#pragma once
#include <array>
namespace museum {
inline bool ScreenInspection::verify_experience_focus(Screen&s,unsigned framebuffer,int width,int height){
 const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"Experience focus check failed: %s\n",message);return pass;};
 const std::string data=s.data_;s.data_.clear();s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.select("pong");s.preview(0);
 const auto picture=[&](){hui::gfx::DrawList d;s.study_->draw(d,s.fonts_,{0,0,1920,960},hui::gfx::Color::rgb(0xb6a2cf));std::string value;for(const auto&instance:d.instances())value.append(reinterpret_cast<const char*>(&instance),sizeof(instance));return value;};
 const auto input=[](){hui::InputFrame i;i.connected=true;return i;};
 hui::ui::Feedback feedback;unsigned count=0;
 const auto&all=study_catalog();
 for(size_t n=0;n<all.size();++n){
  s.open_experience(int(n),{64,350,548,370});s.experience_open_.snap(1);s.experience_intro_.snap(0);s.experience_introduction_=false;
  if(!require(bool(s.study_),"every one of the21 reviewed studies has an actual instance"))return false;
  auto active=input();active.stick_x=.55f;active.stick_y=-.3f;active.pressed=active.held=hui::action_bit(hui::Action::confirm);s.handle(active,feedback);
  for(int k=0;k<12;++k)s.update(1.f/120);
  std::array<float,512>pcm{};std::array<float,256>speaker{};s.mix_experience(pcm.data(),256,speaker.data());
  auto lost=active;lost.focus_lost=true;lost.pressed|=hui::action_bit(hui::Action::back)|hui::action_bit(hui::Action::west);feedback.clear();s.handle(lost,feedback);
  const auto frozen=picture();const double audio_time=s.experience_audio_.time_s();
  if(!require(s.experience_active_&&s.experience_input_paused_&&feedback.tactile.empty()&&feedback.cues.empty()&&s.take_startup_note()==-1,"lost focus never executes Back/Restart or emits a tactile cue"))return false;
  for(int k=0;k<60;++k){s.update(1.f/120);pcm.fill(0);speaker.fill(1);s.mix_experience(pcm.data(),256,speaker.data());
   if(!require(std::all_of(pcm.begin(),pcm.end(),[](float v){return v==0;})&&std::all_of(speaker.begin(),speaker.end(),[](float v){return v==0;}),"HDMI experience audio and its pad speaker are silent outside focus"))return false;
  }
  if(!require(picture()==frozen&&s.experience_audio_.time_s()==audio_time,"actual Screen freezes study geometry/animations and audio sample clock for60updates"))return false;
  auto held=active;held.pressed=hui::action_bit(hui::Action::confirm)|hui::action_bit(hui::Action::page_next);held.trigger_r=1;held.touch.available=true;held.touch.count=1;held.touch.points[0]={.7f,.2f,1};feedback.clear();s.handle(held,feedback);s.update(.05f);
  if(!require(s.experience_input_paused_&&picture()==frozen&&feedback.tactile.empty()&&feedback.cues.empty(),"reconnect with held buttons/trigger/stick/touch does not restart physics or fire phantom feedback"))return false;
  auto neutral=input();feedback.clear();s.handle(neutral,feedback);
  if(!require(!s.experience_input_paused_&&!s.experience_rearm_&&feedback.tactile.empty()&&feedback.cues.empty()&&s.take_startup_note()==-1,"a genuinely neutral sample rearms the same experience without replaying queued notes or haptics"))return false;
  if(all[n].id=="rhythm"){
   pcm.fill(0);s.mix_experience(pcm.data(),256,speaker.data());
   if(!require(std::abs(s.experience_audio_.time_s()-audio_time-256./48000)<.000001,"DDR resumes at exactly its saved sample, without resetting or advancing the phrase"))return false;
  }
  for(int k=0;k<120;++k)s.update(1.f/120);
  if(picture()==frozen){auto edit=input();edit.nav=hui::Direction::right;edit.stick_x=.8f;edit.stick_y=-.7f;edit.pressed=hui::action_bit(hui::Action::confirm);s.handle(edit,feedback);for(int k=0;k<30;++k)s.update(1.f/120);}
  if(!require(picture()!=frozen,"the same study resumes simulation or editing after neutral input"))return false;
  feedback.clear();neutral.connected=false;neutral.pressed=hui::action_bit(hui::Action::back);s.handle(neutral,feedback);const auto disconnected=picture();s.update(.05f);
  if(!require(s.experience_active_&&s.experience_input_paused_&&picture()==disconnected,"connected=false is also a real pause even if focus_lost was not set"))return false;
  neutral=input();s.handle(neutral,feedback);neutral.pressed=hui::action_bit(hui::Action::back);s.handle(neutral,feedback);
  if(!require(!s.experience_active_,"a fresh Back press after neutral input closes normally"))return false;
  pcm.fill(0);for(int k=0;k<80;++k){pcm.fill(0);s.mix_experience(pcm.data(),256,speaker.data());}
  if(!require(std::all_of(pcm.begin(),pcm.end(),[](float v){return v==0;}),"closing after pause stops experience audio permanently"))return false;
  ++count;std::printf("Actual Screen focus: %s freeze/held-rearm/resume/disconnect/exit PASS\n",all[n].id.c_str());
 }
 // Media is a separate user-owned state. Focus handling must never issue an
 // automatic resume or change the listening room/stream selection. This
 // host check has no decoded native stream; native paused playback remains
 // a console check, not inferred from this idle engine fixture.
 s.study_.reset();s.experience_active_=false;s.experience_open_.snap(0);s.playlist_active_=true;s.screening_=true;s.fullscreen_=true;s.playlist_playing_=0;
 const bool paused=s.video_.paused();const auto media_state=s.video_.state();auto lost=input();lost.focus_lost=true;s.handle(lost,feedback);s.handle(input(),feedback);
 if(!require(s.playlist_active_&&s.screening_&&s.fullscreen_&&s.playlist_playing_==0&&s.video_.paused()==paused&&s.video_.state()==media_state,"focus return preserves the listening-room selection and the idle media engine state"))return false;
 s.playlist_active_=false;s.screening_=false;s.fullscreen_=false;s.playlist_playing_=-1;s.data_=data;s.preview(0);s.draw(width,height,framebuffer);
 if(!require(glGetError()==GL_NO_ERROR&&count==21,"all21 actual studies and restored UI render without GL errors"))return false;
 std::puts("PASS actual Screen: all21 studies freeze simulation/audio/clock on focus loss, rearm after neutral controls, retain session, no phantom feedback; idle media ownership preserved; GL0.");return true;
}
}
