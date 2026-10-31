// Offline presentation/control ownership checks; no streaming success is inferred.
#pragma once
#include "third_party/stb/stb_image_write.h"
namespace museum {
inline bool ScreenInspection::verify_playlist(Screen&s,unsigned framebuffer,int width,int height){
    const auto require=[](bool value,const char*message){if(!value)std::fprintf(stderr,"Playlist check failed: %s\n",message);return value;};
    const std::string data=s.data_,id=s.current()?s.current()->id:"pong";s.data_.clear();
    s.onboarding_=false;s.boot_time_=5;s.boot_note_=13;s.year_guide_=false;s.year_panel_.snap(0);s.settings_=s.credits_=false;s.panel_.snap(0);s.experience_active_=false;s.experience_open_.snap(0);
    hui::ui::Feedback feedback;auto press=[&](hui::Action a){hui::InputFrame i;i.connected=true;i.pressed=hui::action_bit(a);s.handle(i,feedback);};
    auto nav=[&](hui::Direction d){hui::InputFrame i;i.connected=true;i.nav=d;s.handle(i,feedback);};auto advance=[&](int n){for(int k=0;k<n;++k)s.update(1.f/60);};
    auto finish=[&](bool result){s.stop_playlist();s.screening_=false;s.screening_open_.snap(0);s.select(id);s.preview(0);s.data_=data;return result;};
    for(const char*entry:{"journey","celeste"}){
        s.select(entry);s.preview(1);const auto*e=s.current();if(!require(e&&e->soundtrack.tracks.size()>=3,"real exhibit retains its attributed recordings"))return finish(false);
        const auto found=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[](const auto&c){return c.kind==Screen::StoryCard::soundtrack;});
        if(!require(found!=s.story_cards_.end(),"playlist is an actual exhibit card"))return finish(false);
        s.story_focus_=int(found-s.story_cards_.begin());s.story_position_.snap(float(s.story_focus_));
        // Exercise presentation ownership with an idle engine: no network stream.
        s.playlist_active_=true;s.playlist_playing_=0;s.screening_=true;s.fullscreen_=true;
        advance(90);s.draw(width,height,framebuffer);
        if(!require(glGetError()==GL_NO_ERROR,"listening room renders without decoded video"))return finish(false);
        press(hui::Action::back);advance(90);
        if(!require(!s.screening_&&!s.playlist_active_&&s.playlist_playing_==-1,"Back closes listening room and releases soundtrack playback"))return finish(false);
        const int card=s.story_focus_;nav(hui::Direction::left);advance(90);
        if(!require(s.story_focus_==card-1&&!s.playlist_active_,"browsing the exhibit does not restart music"))return finish(false);
        s.select("pong");if(!require(!s.playlist_active_&&s.playlist_playing_==-1,"changing exhibit releases the native player"))return finish(false);
    }
    // Exercise production story construction: alternate rooms replace legacy,
    // each receives its own card and playback keeps the selected room stable.
    s.select("journey");s.preview(1);auto&fixture=s.catalog_.entries[size_t(s.visible_[size_t(s.focus_)])];
    const auto saved_rooms=fixture.soundtrack_rooms;
    Soundtrack first=fixture.soundtrack,second=fixture.soundtrack;first.title="Room one";first.composer="Woodkid";second.title="Room two";second.composer="Ludvig Forssell";
    fixture.soundtrack_rooms={first,second};s.prepare_story();
    std::vector<int> rooms;for(size_t n=0;n<s.story_cards_.size();++n)if(s.story_cards_[n].kind==Screen::StoryCard::soundtrack)rooms.push_back(int(n));
    bool pass=require(rooms.size()==2,"two alternative soundtrack rooms produce exactly two cards, never an extra legacy duplicate");
    if(pass){
        pass=require(s.story_cards_[size_t(rooms[0])].music_room==0&&s.story_cards_[size_t(rooms[1])].music_room==1,"soundtrack cards retain distinct room indices");
        s.story_focus_=rooms[0];s.story_position_.snap(float(rooms[0]));pass=require(s.current_soundtrack()&&s.current_soundtrack()->composer=="Woodkid","focused first card resolves first soundtrack")&&pass;
        s.playlist_active_=true;s.playlist_music_room_=0;s.playlist_playing_=0;s.story_focus_=rooms[1];
        pass=require(s.current_soundtrack()->composer=="Woodkid"&&s.video_active(),"active listening room owns its soundtrack and suspends ambience despite adjacent card focus")&&pass;
        s.stop_playlist();pass=require(s.playlist_music_room_==-1&&s.current_soundtrack()->composer=="Ludvig Forssell","exit resets room ownership and restores card selection")&&pass;
        s.story_position_.snap(float(rooms[1]));s.playlist_active_=true;s.playlist_music_room_=1;s.playlist_playing_=0;s.screening_=s.fullscreen_=true;
        press(hui::Action::back);pass=require(!s.playlist_active_&&s.playlist_display_music_room_==1&&s.playlist_music_room_==-1,"closing animation retains second room while playback is stopped")&&pass;
    }
    fixture.soundtrack_rooms=saved_rooms;s.prepare_story();
    if(!pass)return finish(false);
    if(const char* probes=std::getenv("MUSEUM_PLAYLIST_PROBE_ENTRIES")){
        std::string pending=probes;
        while(!pending.empty()){
            const auto comma=pending.find(',');const auto target=pending.substr(0,comma);
            pending=comma==std::string::npos?std::string{}:pending.substr(comma+1);
            s.stop_playlist();s.select(target);s.preview(1);
            // select() starts the real exhibit dissolve. These static captures
            // must show the selected room, not the previous exhibit snapshot.
            s.fade_=1;s.entry_snapshot_=false;s.history_transition_=false;
            const auto*entry=s.current();if(!require(entry&&entry->id==target,"scoped music target resolves the actual loaded entry"))return finish(false);
            const auto card=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[](const auto&c){return c.kind==Screen::StoryCard::soundtrack;});
            if(!require(card!=s.story_cards_.end(),"new real music collection receives a story card"))return finish(false);
            s.story_focus_=int(card-s.story_cards_.begin());s.story_position_.snap(float(s.story_focus_));
            const auto*room=s.current_soundtrack();if(!require(room&&!room->tracks.empty(),"new music card resolves its own loaded room"))return finish(false);
            const int count=int(room->tracks.size());
            if(target=="workbook-03-12-yakuza-0"&&!require(count==92,"Yakuza collection contains exactly92 reviewed distinct passages"))return finish(false);
            if(target=="wikipedia-52874820"&&!require(count==48,"Splatoon collection contains exactly48 reviewed public recordings"))return finish(false);
            for(const auto&track:room->tracks){
                if(!require(s.fonts_.regular.font->has_text(track.title)&&s.fonts_.regular.font->has_text(track.creator),"all new track titles and actual recording credits have genuine font coverage"))return finish(false);
            }
            for(const int selected:{0,count/2,count-1}){
                s.playlist_active_=true;s.playlist_music_room_=card->music_room;s.playlist_selection_=s.playlist_playing_=selected;
                s.screening_=s.fullscreen_=true;s.screening_open_.snap(1);s.video_full_.snap(1);
                s.draw(width,height,framebuffer);if(!require(glGetError()==GL_NO_ERROR,"first middle and final listening selections render at actual4K without GL errors"))return finish(false);
                const int first=std::clamp(s.playlist_selection_-1,0,std::max(0,count-3));
                if(!require(selected>=first&&selected<std::min(count,first+3),"selected final recording remains in the visible list window"))return finish(false);
                const auto path=std::string("build/previews/playlist-scoped-")+target+"-"+std::to_string(selected)+"-4k.png";
                std::vector<unsigned char> pixels(size_t(width)*size_t(height)*4);glBindFramebuffer(GL_READ_FRAMEBUFFER,framebuffer);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
                stbi_flip_vertically_on_write(1);if(!stbi_write_png(path.c_str(),width,height,4,pixels.data(),width*4))return finish(false);
                std::printf("PASS scoped playlist %s %d/%d: %s / selected row visible, current font credits complete, GL0; idle media engine, no playback claim.\n",target.c_str(),selected+1,count,room->tracks[size_t(selected)].title.c_str());
            }
            press(hui::Action::back);if(!require(!s.playlist_active_&&!s.screening_&&s.playlist_playing_==-1,"new long room exits and releases ownership without starting ambience early"))return finish(false);
        }
    }
    std::puts("Playlist: cards/credits/fullscreen, exit cleanup, two independent soundtrack rooms and legacy fallback passed; streaming/decoder success not tested");return finish(true);
}
}
