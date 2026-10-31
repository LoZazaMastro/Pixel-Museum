// Pixel Museum - a listening room driven by the single native media player.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/music_waveform.hpp"
#include "museum/soundtrack_card.hpp"
#include "platform/playback_window.hpp"
#include "platform/ps5/system.hpp"
#include <algorithm>
#include <cmath>
namespace museum {
using namespace hui;
bool Screen::story_soundtrack()const{return detail_&&story_focus_>=0&&story_focus_<int(story_cards_.size())&&story_cards_[size_t(story_focus_)].kind==StoryCard::soundtrack;}
gfx::Rect Screen::playlist_frame()const{
    // Same reference geometry as draw_soundtrack_card within its story slot.
    constexpr gfx::Rect slot{132,310,1656,575};const float scale=std::min(slot.w/1040.f,slot.h/552.f);
    const float x=slot.x+(slot.w-1040*scale)/2,y=slot.y+(slot.h-552*scale)/2;
    return{x+36*scale,y+145*scale,480*scale,270*scale};
}
void Screen::stop_playlist(){
    if(playlist_active_)video_.close();
    playlist_active_=false;playlist_completed_=false;playlist_selection_=0;playlist_playing_=-1;playlist_music_room_=-1;
}
void Screen::play_playlist(int index){
    const auto*e=current();const auto*list=current_soundtrack();if(!e||!list||index<0||index>=int(list->tracks.size()))return;
    release_culture_ambience();
    const auto&track=list->tracks[size_t(index)];
    const bool reuse=playlist_active_&&playlist_playing_>=0&&playlist_playing_<int(list->tracks.size())&&list->tracks[size_t(playlist_playing_)].youtube_id==track.youtube_id&&video_.state()==media::State::ready;
    if(!playlist_active_)playlist_music_room_=story_focus_>=0&&story_focus_<int(story_cards_.size())?story_cards_[size_t(story_focus_)].music_room:-1;
    playlist_active_=true;playlist_closing_=false;playlist_completed_=false;playlist_selection_=playlist_playing_=index;
    screening_=true;fullscreen_=true;screening_origin_=playlist_frame();
    video_frame_alpha_=0;idle_=0;
    if(reuse)video_.play_range(track.start_seconds,track.end_seconds);
    else video_.open(track.youtube_id,true,track.start_seconds,track.end_seconds);
    sys::log("[Museum] soundtrack %s / recording %d / YouTube %s",e->id.c_str(),index+1,track.youtube_id.c_str());
}
void Screen::update_playlist(){
    if(!playlist_active_)return;
    if(playlist_completed_&&video_.state()==media::State::ready&&!video_.ended())playlist_completed_=false;
    if(playlist_completed_)return;
    const auto*e=current();const auto*list=current_soundtrack();if(!e||!list||playlist_playing_<0||playlist_playing_>=int(list->tracks.size())){stop_playlist();return;}
    if(video_.state()==media::State::ready&&video_.ended()){
        if(playlist_playing_+1<int(list->tracks.size()))play_playlist(playlist_playing_+1);
        else playlist_completed_=true;
    }
}
bool Screen::handle_playlist(const InputFrame&i,ui::Feedback&f){
    const auto*e=current();const auto*list=current_soundtrack();if(!e||!list||list->tracks.empty())return false;
    const bool expanded=playlist_active_&&screening_;
    if(!expanded&&(!story_soundtrack()||std::abs(story_position_.value-float(story_focus_))>.08f))return false;
    if(i.focus_lost)return expanded;
    const auto play_selected=[&]{
        if(playlist_active_&&playlist_playing_==playlist_selection_&&video_.state()==media::State::ready&&!video_.ended())video_.pause(!video_.paused());
        else if(!playlist_active_||playlist_playing_!=playlist_selection_||video_.state()!=media::State::loading)play_playlist(playlist_selection_);
        f.play(audio::Cue::select,1,0,.5f);
    };
    if(expanded&&(i.is_pressed(Action::back)||i.is_pressed(Action::west))){playlist_display_index_=std::max(0,playlist_playing_);playlist_display_music_room_=playlist_music_room_;playlist_closing_=true;stop_playlist();screening_=false;fullscreen_=false;f.play(audio::Cue::back);return true;}
    if(expanded&&(i.nav==Direction::down||i.nav==Direction::up)){
        const int next=std::clamp(playlist_selection_+(i.nav==Direction::down?1:-1),0,int(list->tracks.size())-1);
        if(next!=playlist_selection_){playlist_selection_=next;if(expanded)play_playlist(next);f.play(audio::Cue::focus,1,0,.4f);}return true;
    }
    if(i.is_pressed(Action::confirm)){play_selected();return true;}
    if(!expanded&&i.is_pressed(Action::west)){
        if(!playlist_active_||playlist_playing_!=playlist_selection_)play_playlist(playlist_selection_);
        screening_origin_=playlist_frame();screening_=true;fullscreen_=true;idle_=0;f.play(audio::Cue::select);return true;
    }
    if(playlist_active_&&video_.state()==media::State::ready){
        const auto&t=list->tracks[size_t(playlist_playing_)];const media::PlaybackWindow window{t.start_seconds,t.end_seconds};
        if((expanded&&i.nav==Direction::left)){video_.seek(window.seek(window.time(video_.time(),video_.duration())-10,video_.duration()));playlist_completed_=false;f.play(audio::Cue::focus,1,-1,.65f);return true;}
        if((expanded&&i.nav==Direction::right)){video_.seek(window.seek(window.time(video_.time(),video_.duration())+10,video_.duration()));playlist_completed_=false;f.play(audio::Cue::focus,1,1,.65f);return true;}
    }
    return expanded;
}
void Screen::adjust_media_volume(const InputFrame&i){
    const float direction=(i.trigger_r>.08f?i.trigger_r:0)-(i.trigger_l>.08f?i.trigger_l:0);
    if(std::abs(direction)<.001f)return;
    const float next=std::clamp(media_volume_+direction*dt_*.35f,0.f,1.f);
    if(next==media_volume_)return;
    media_volume_=next;video_.volume(media_volume_);dirty_=true;save_delay_=1.f;idle_=0;
}
void Screen::draw_playlist(gfx::Rect bounds,bool active,int room_index){
    const auto*e=current();if(!e)return;const auto palette=colours();
    const auto&list=room_index>=0&&room_index<int(e->soundtrack_rooms.size())?e->soundtrack_rooms[size_t(room_index)]:e->soundtrack;
    const float phase=reduced_?0.f:time_*1.4f;
    const float cx=bounds.x+350,cy=bounds.cy();
    // A decorative sound wave invites listening; it is not a recording meter.
    page_.push_clip(bounds);
    draw_music_waveform(page_,{cx-275,cy-155,550,310},palette.ink.with_alpha(.85f),phase);
    const float left=bounds.x+755,width=bounds.w-815;
    float author_size=44,title_size=76;
    const auto height=[&]{return float(fonts_.semibold.font->wrap(list.composer,author_size,width).size())*author_size*1.22f+float(fonts_.display.font->wrap(e->title,title_size,width).size())*title_size*1.18f;};
    while(height()>330&&(title_size>34||author_size>28)){if(title_size>34)title_size-=1;if(author_size>28)author_size-=.35f;}
    const float top=bounds.cy()-height()*.5f;
    ui::text(page_,fonts_.mono,"LISTEN TO THE MUSIC OF",left,top-42,18,palette.muted,gfx::Align::left,1.3f);
    const float after=ui::paragraph(page_,fonts_.semibold,list.composer,left,top+author_size,author_size,width,author_size*1.22f,palette.muted);
    ui::paragraph(page_,fonts_.display,e->title,left,after+title_size*.7f,title_size,width,title_size*1.18f,palette.ink);
    page_.pop_clip();
    if(active)scroll_max_=0;
}
} // namespace museum
