// Hidden archival audio borrows the same exclusive transport as real players.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <array>
namespace museum {
void Screen::release_culture_ambience(){
 if(!culture_ambience_.owns_player())return;
 const bool local=culture_ambience_.using_local_audio();
 culture_ambience_.relinquish();if(!local){video_.close();video_.volume(media_volume_);}
}
void Screen::update_culture_ambience(){
 const auto*entry=current();
 CultureAmbience::Context context;
 if(history_focus_&&entry)context.entry_id=entry->id;
 const bool options_playback=settings_&&culture_ambience_.owns_player();
 context.eligible=history_focus_&&entry&&!onboarding_active()&&culture_input_active_&&
  (!settings_||options_playback)&&!credits_&&!year_guide_&&!search_page_&&!search_prompt_.visible()&&
  (panel_.value<.001f||options_playback)&&search_open_.value<.001f&&!screening_&&
  !playlist_active_&&!experience_active_&&!trophy_pin_open_;
 // The ambient-music preference controls only Music's background bed.
 // The cultural slider is independent of both the museum bed and film volume.
 // Keep an active recording audible behind Options so its slider can be heard.
 context.volume=culture_volume_;
 // gallery_ is the still-photo viewer: the same exhibit keeps its dwell and
 // one-shot latch while opening, zooming or closing that viewer.
 // Explicit players already released the borrowed transport before opening.
 // Never close or alter their gain in the automatic state machine.
 if(screening_||playlist_active_)return;
 CultureAmbience::Playback playback;
 playback.ready=video_.state()==media::State::ready;playback.failed=video_.state()==media::State::failed;
 playback.ended=video_.ended();playback.position=video_.time();
 const auto command=culture_ambience_.update(context,playback,dt_);
 if(command.kind==CultureAmbience::Command::open){
  if(!command.cue->local_audio){video_.volume(1.f);video_.open(command.cue->youtube_id,true,command.cue->start,command.cue->end);}
  hui::sys::log("[Museum] culture recollection %s / %s / one-shot %.2f..%.2f",context.entry_id.c_str(),command.cue->kind.c_str(),command.cue->start,command.cue->end);
 }else if(command.kind==CultureAmbience::Command::close&&(!command.cue||!command.cue->local_audio)){video_.close();video_.volume(media_volume_);}
}
void Screen::mix_video(float*out,unsigned frames,float*controller_speaker,bool culture_on_pad){
 if(!culture_ambience_.rendering()){culture_audio_route_.snap(culture_on_pad&&controller_speaker);video_.mix_audio(out,frames);return;}
 std::array<float,512>buffer{},recording{};
 for(unsigned at=0;at<frames;){
  const unsigned n=std::min(256u,frames-at);
  std::fill(buffer.begin(),buffer.end(),0.f);std::fill(recording.begin(),recording.end(),0.f);
  if(!culture_ambience_.rendering_local_audio())video_.mix_audio(buffer.data(),n);
  culture_ambience_.process(buffer.data(),recording.data(),n);
  culture_audio_route_.process(recording.data(),out+at*2,controller_speaker?controller_speaker+at:nullptr,n,culture_on_pad);
  at+=n;
 }
}
}
