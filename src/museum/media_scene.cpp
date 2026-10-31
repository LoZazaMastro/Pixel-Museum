// Pixel Museum - media expands from its place in the collection.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/caption_overlay.hpp"
#include "platform/playback_window.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
namespace museum {
using namespace hui;
using gfx::Color;using gfx::Rect;using gfx::Align;
namespace {
const Color paper=Color::rgb(0xf1efe7);
Rect between(Rect a,Rect b,float t){return {a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,a.w+(b.w-a.w)*t,a.h+(b.h-a.h)*t};}
Rect fitted(Rect r,float aspect){if(r.w/r.h>aspect){const float w=r.h*aspect;r.x+=(r.w-w)/2;r.w=w;}else{const float h=r.w/aspect;r.y+=(r.h-h)/2;r.h=h;}return r;}
std::string timer(double t){if(!std::isfinite(t)||t<0)return "--:--";char s[32];const int n=int(std::min(t,359999.));hui::ui::format(s,"%d:%02d",n/60,n%60);return s;}
}
void Screen::snapshot_current(){
    if(!composed_.texture())return;
    GLint read=0,draw=0,viewport[4];glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&read);glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING,&draw);glGetIntegerv(GL_VIEWPORT,viewport);
    const bool scissor=glIsEnabled(GL_SCISSOR_TEST);glDisable(GL_SCISSOR_TEST);
    // A quick second step snapshots the frame the visitor actually saw,
    // including the previous dissolve, rather than its unfinished new layer.
    if(entry_snapshot_&&previous_entry_.texture()&&fade_<1){
        gfx::DrawList blend;blend.image(previous_entry_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff,1-tween::smoothstep(fade_)));
        renderer_.begin();renderer_.draw(blend);renderer_.present(composed_.framebuffer(),composed_.width(),composed_.height());
    }
    if(previous_entry_.width()!=composed_.width()||previous_entry_.height()!=composed_.height()){
        if(!previous_entry_.create(composed_.width(),composed_.height(),1)){entry_snapshot_=false;glBindFramebuffer(GL_READ_FRAMEBUFFER,read);glBindFramebuffer(GL_DRAW_FRAMEBUFFER,draw);glViewport(viewport[0],viewport[1],viewport[2],viewport[3]);if(scissor)glEnable(GL_SCISSOR_TEST);return;}
    }
    // Keep the transition snapshot on the GPU too. A framebuffer blit enters
    // the same CPU fallback as the former per-frame display copy on PS5.
    gfx::DrawList copy;copy.image(composed_.texture(),{0,0,1920,1080},gfx::kCanvasUv,Color::rgb(0xffffff));
    renderer_.begin();renderer_.draw(copy);renderer_.present(previous_entry_.framebuffer(),previous_entry_.width(),previous_entry_.height());
    glBindFramebuffer(GL_READ_FRAMEBUFFER,read);glBindFramebuffer(GL_DRAW_FRAMEBUFFER,draw);glViewport(viewport[0],viewport[1],viewport[2],viewport[3]);if(scissor)glEnable(GL_SCISSOR_TEST);
    entry_snapshot_=true;
}
void Screen::draw_gallery(){
    const float raw=std::clamp(gallery_open_.value,0.f,1.f),amount=raw>.999f?1.f:raw;
    media_layer_.rounded_rect({0,0,1920,1080},0,Color::rgb(0x080b09,amount));
    const Rect bounds=between(gallery_origin_,{0,0,1920,1080},amount),old=viewer_.bounds();
    if(std::abs(old.x-bounds.x)+std::abs(old.y-bounds.y)+std::abs(old.w-bounds.w)+std::abs(old.h-bounds.h)>.001f)viewer_.set_bounds(bounds);
    media_layer_.push_opacity(amount>.001f?std::min(1.f,amount*5):0);
    ui::Canvas canvas{media_layer_,fonts_,0,time_};viewer_.draw(canvas);
    if(const auto*e=current();e&&image_index_>=0&&image_index_<int(e->images.size())){
        const auto&photo=e->images[size_t(image_index_)];
        if(!cache_.get(image_url(photo)).texture)image(media_layer_,photo,bounds,true);
    }
    media_layer_.pop_opacity();
    const float labels=amount*std::clamp(gallery_labels_.value,0.f,1.f);
    media_layer_.push_opacity(labels);
    media_layer_.gradient_rect({0,0,1920,180},0,Color::rgb(0,.7f),Color::rgb(0,0));
    media_layer_.gradient_rect({0,860,1920,220},0,Color::rgb(0,0),Color::rgb(0,.8f));
    if(const auto*e=current();e&&image_index_>=0&&image_index_<int(e->images.size())){
        ui::paragraph(media_layer_,fonts_.semibold,e->title,96,86,30,1600,38,paper);
    }
    ui::Hint h[]={{ui::Button::circle,"Back"},{ui::Button::l2,"Zoom",ui::Button::r2},{ui::Button::left_stick,"Pan"},{ui::Button::dpad,"Images"},{ui::Button::cross,"Fit / fill"}};
    ui::HintLayout l;l.cy=1014;l.size=30;l.text_size=22;l.item_gap=28;
    ui::draw_hints(media_layer_,fonts_,ui::GlyphStyle::mono(paper,Color::rgb(0,0)),h,5,96,false,l);
    media_layer_.pop_opacity();
}
void Screen::draw_screening(){
    const auto*e=current();if(!e)return;
    const bool listening=playlist_active_||playlist_closing_;
    const Soundtrack*list=listening?current_soundtrack():nullptr;
    if(playlist_closing_)list=playlist_display_music_room_>=0&&playlist_display_music_room_<int(e->soundtrack_rooms.size())?&e->soundtrack_rooms[size_t(playlist_display_music_room_)]:&e->soundtrack;
    const auto&records=listening&&list?list->tracks:e->videos;
    const int index=listening?(playlist_active_?playlist_playing_:playlist_display_index_):video_index_;
    if(index<0||index>=int(records.size()))return;
    const auto&v=records[size_t(index)];
    const float amount=std::clamp(screening_open_.value,0.f,1.f),full=std::clamp(video_full_.value,0.f,1.f);
    const Rect screen=between(screening_origin_,{0,0,1920,1080},full);
    media_layer_.rounded_rect({0,0,1920,1080},0,Color::rgb(0x080b09,amount*full));
    media_layer_.push_opacity(amount);
    if(listening||video_.texture()||video_.state()==media::State::failed)
        media_layer_.rounded_rect(screen,0,Color::rgb(0x141b17,listening||video_.state()==media::State::failed?1.f:video_frame_alpha_));
    if(listening){
        // Audio-only listening: the media backend never opens a video decoder.
        const auto palette=colours();
        media_layer_.rounded_rect(screen,0,palette.paper);
        const float scale=std::min(screen.w/1920.f,screen.h/1080.f);
        media_layer_.push_clip(screen);media_layer_.push_transform(scale,0,0,screen.x,screen.y);
        ui::text(media_layer_,fonts_.mono,"LISTENING ROOM",96,104,19,palette.muted,Align::left,2);
        const float energy=video_.audio_level();
        for(int n=0;n<16;++n)media_layer_.ring(1410,480,65+float(n)*18+energy*(18+float(n)*3),1+energy*.8f,palette.ink.with_alpha(.025f+float(n)*.003f+energy*.05f));
        media_layer_.circle(1410,480,40+energy*32,tone_);media_layer_.circle(1410,480,8+energy*4,palette.paper);
        const std::string artist=list?list->composer:std::string{};
        float title_size=54,artist_size=25;
        const auto heading_bottom=[&]{
            return 200.f+float(fonts_.display.font->wrap(e->title,title_size,1000).size())*title_size*1.18f
                +8.f+float(fonts_.regular.font->wrap(artist,artist_size,1020).size())*artist_size*1.4f;
        };
        // Long album identities use more lines rather than losing their names.
        // The recording list gives up a row only when that extra space is needed.
        while(heading_bottom()>480&&(title_size>34||artist_size>20)){
            if(title_size>34)title_size-=1;
            if(artist_size>20)artist_size-=.25f;
        }
        const float artist_y=ui::paragraph(media_layer_,fonts_.display,e->title,94,200,title_size,1000,title_size*1.18f,palette.ink)+8;
        const float artist_bottom=artist.empty()?artist_y:ui::paragraph(media_layer_,fonts_.regular,artist,100,artist_y,artist_size,1020,artist_size*1.4f,palette.muted);
        const float recordings_y=std::max(360.f,artist_bottom+44.f);
        const int visible=std::clamp(1+int(std::floor((780.f-recordings_y)/56.f)),1,7);
        const int first=std::clamp(playlist_selection_-visible/2,0,std::max(0,int(records.size())-visible));
        for(int row=0;row<visible&&first+row<int(records.size());++row){const int index=first+row;const auto&track=records[size_t(index)];const float y=recordings_y+row*56.f;
            const auto title=ui::paragraph_lines(fonts_.regular,track.title,23,970,1);
            if(index==playlist_selection_){
                std::vector<gfx::GlyphQuad> glyphs;
                fonts_.regular.font->layout(title.lines.front(),144,y,23,Align::left,glyphs);
                float center=y-(fonts_.regular.font->ascent(23)-fonts_.regular.font->descent(23))*.5f;
                if(!glyphs.empty()){
                    float low=glyphs.front().y0,high=glyphs.front().y1;
                    for(const auto&g:glyphs){low=std::min(low,g.y0);high=std::max(high,g.y1);}
                    center=(low+high)*.5f;
                }
                media_layer_.line(100,center,120,center,2,tone_);
            }
            ui::paragraph(media_layer_,fonts_.regular,title,144,y,23,31,index==playlist_playing_?tone_:palette.muted);
        }
        const bool ready=video_.state()==media::State::ready;
        if(!ready&&video_.state()!=media::State::failed){
            media_layer_.ring(118,814,12,1,palette.muted.with_alpha(.18f));
            media_layer_.arc(118,814,12,1.8f,time_*2.6f,2.4f,tone_);
        }else{
            const auto message=video_.state()==media::State::failed?video_.error():playlist_completed_?"Finished":video_.paused()?"Paused":"Now playing";
            ui::paragraph(media_layer_,fonts_.regular,message,100,826,23,1250,33,palette.muted,2);
        }
        media_layer_.line(100,898,1820,898,1,palette.rule);
        const media::PlaybackWindow window{v.start_seconds,v.end_seconds};
        const double cue_duration=window.duration(video_.duration()),cue_time=window.time(video_.time(),video_.duration());
        if(ready&&cue_duration>0)media_layer_.line(100,898,100+1720*std::clamp(float(cue_time/cue_duration),0.f,1.f),898,2,tone_);
        ui::text(media_layer_,fonts_.mono,timer(ready?cue_time:-1)+" / "+timer(ready?cue_duration:-1),100,943,22,palette.ink);
        char volume[48];hui::ui::format(volume,"Volume %d %%",int(std::round(media_volume_*100)));
        ui::text(media_layer_,fonts_.mono,volume,1820,943,21,palette.muted,Align::right);
        const ui::Hint hints[]={{ui::Button::cross,video_.paused()?"Play":"Pause"},{ui::Button::l2,"Volume",ui::Button::r2},{ui::Button::dpad,"Recordings / seek"},{ui::Button::circle,"Return to exhibit"}};
        ui::HintLayout l;l.cy=1014;l.size=28;l.text_size=21;l.item_gap=30;
        ui::draw_hints(media_layer_,fonts_,ui::GlyphStyle::mono(palette.ink,Color::rgb(0,0)),hints,4,96,false,l);
        media_layer_.pop_transform();media_layer_.pop_clip();media_layer_.pop_opacity();return;
    }
    media_layer_.push_clip(screen);
    if(video_.texture()){
        const float aspect=float(video_.width())/std::max(1,video_.height());
        media_layer_.image(video_.texture(),fitted(screen,aspect),gfx::kFullUv,Color::rgb(0xffffff,video_frame_alpha_));
    }else if(video_.state()==media::State::failed){
        const float size=std::min(34.f,screen.w/28);
        ui::text(media_layer_,fonts_.semibold,"This film could not be opened",screen.cx(),screen.cy()-20,size,paper,Align::center);
        ui::paragraph(media_layer_,fonts_.regular,video_.error(),screen.x+40,screen.cy()+24,std::min(24.f,size*.72f),screen.w-80,32,paper.with_alpha(.65f));
    }else{
        const float radius=std::clamp(screen.w*.022f,14.f,28.f);
        media_layer_.ring(screen.cx(),screen.cy(),radius,1.2f,paper.with_alpha(.14f));
        media_layer_.arc(screen.cx(),screen.cy(),radius,2.f,time_*2.6f,2.4f,paper.with_alpha(.88f));
    }
    media_layer_.pop_clip();
    // Embedded playback keeps its controls visible, including while loading.
    // Only a fullscreen film can use the existing idle fade.
    const float labels=full<.999f?1.f:std::clamp(media_hints_.value,0.f,1.f);
    if(film_captions_enabled_&&video_.texture())draw_film_captions(media_layer_,fonts_.regular,video_.caption_text(),
        fitted(screen,float(video_.width())/std::max(1,video_.height())),labels);
    media_layer_.push_opacity(labels);
    if(full>.001f){media_layer_.gradient_rect({0,0,1920,180},0,Color::rgb(0,.65f*full),Color::rgb(0,0));media_layer_.push_opacity(full);ui::paragraph(media_layer_,fonts_.semibold,v.title,96,90,32,1700,40,paper);media_layer_.pop_opacity();}
    const float x=screen.x+30,y=screen.y+screen.h-48,w=screen.w-60;
    media_layer_.rounded_rect({x-15,y-34,w+30,70},0,Color::rgb(0,.5f));
    media_layer_.rounded_rect({x,y,w,2},0,paper.with_alpha(.25f));
    const bool ready=video_.state()==media::State::ready;
    if(film_captions_enabled_&&video_.caption_status().rfind("fallback: en",0)==0)ui::text(media_layer_,fonts_.regular,"English subtitles",x+w*.5f,y-14,18,paper.with_alpha(.85f),Align::center);
    if(ready&&std::isfinite(video_.duration())&&video_.duration()>0)media_layer_.rounded_rect({x,y,w*std::clamp(float(video_.time()/video_.duration()),0.f,1.f),2},0,paper);
    ui::text(media_layer_,fonts_.mono,timer(ready?video_.time():-1)+" / "+timer(ready&&video_.duration()>0?video_.duration():-1),x,y+28,18,paper);
    char volume_status[128];ui::format(volume_status,video_.paused()?"Paused / Volume %d %%":"Volume %d %%",int(std::round(media_volume_*100)));
    ui::text(media_layer_,fonts_.regular,volume_status,x+w,y+28,18,paper,Align::right);
    media_layer_.pop_opacity();
    ui::Hint h[]={{ui::Button::cross,video_.paused()?"Play":"Pause"},{ui::Button::square,fullscreen_?"Return to frame":"Fullscreen"},{ui::Button::triangle,film_captions_enabled_?"Hide subtitles":"Show subtitles"},{ui::Button::dpad,"Seek 10 seconds"},{ui::Button::l2,"Volume",ui::Button::r2},{ui::Button::circle,"Back"}};
    ui::HintLayout l;l.cy=1014;l.size=28;l.text_size=20;l.item_gap=24;
    while(ui::measure_hints(fonts_,h,6,l)>1728.f&&l.text_size>14.f){l.size*=.97f;l.text_size*=.97f;l.item_gap*=.97f;}
    media_layer_.push_opacity(labels);
    media_layer_.push_opacity(1-full);ui::draw_hints(media_layer_,fonts_,ui::GlyphStyle::mono(colours().ink,Color::rgb(0,0)),h,6,96,false,l);media_layer_.pop_opacity();
    media_layer_.push_opacity(full);ui::draw_hints(media_layer_,fonts_,ui::GlyphStyle::mono(paper,Color::rgb(0,0)),h,6,96,false,l);media_layer_.pop_opacity();
    media_layer_.pop_opacity();media_layer_.pop_opacity();
}
void Screen::draw_object(){
    const float amount=std::clamp(object_open_.value,0.f,1.f);
    media_layer_.rounded_rect({0,0,1920,1080},0,Color::rgb(0x101916,amount));
    // Both rectangles are 3:2, as is the native object render target.
    if(object_texture_)media_layer_.image(object_texture_,between(object_origin_,{0,42,1920,960},amount),gfx::kCanvasUv,Color::rgb(0xffffff,object_alpha_));
    media_layer_.push_opacity(amount*std::clamp(media_hints_.value,0.f,1.f));
    logo(media_layer_,96,66,34,paper);ui::text(media_layer_,fonts_.semibold,"PIXEL MUSEUM",150,93,22,paper,Align::left,2.f);
    const auto*e=current();if(e&&!e->models.empty()){ui::text(media_layer_,fonts_.semibold,e->title,96,918,32,paper);}
    ui::Hint h[]={{ui::Button::right_stick,"Rotate"},{ui::Button::l2,"Zoom",ui::Button::r2},{ui::Button::cross,"Reset view"},{ui::Button::circle,detail_?"Return to exhibit":"Return to timeline"}};
    ui::HintLayout l;l.cy=1014;l.size=30;l.text_size=22;l.item_gap=28;ui::draw_hints(media_layer_,fonts_,ui::GlyphStyle::mono(paper,Color::rgb(0,0)),h,4,96,false,l);
    media_layer_.pop_opacity();
}
}
