// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
namespace museum {
using namespace hui;
namespace {
constexpr const char*culture_categories[]={"", "history", "science", "technology", "cinema-tv", "music", "literature", "arts", "sport"};
constexpr const char*culture_filter_labels[]={"All", "History", "Science", "Technology", "Cinema & TV", "Music", "Literature", "Arts", "Sport"};
constexpr const char*game_filter_labels[]={"All", "Consoles & hardware", "Games", "People", "Culture & industry"};
}
const char* Screen::active_filter_label()const{
    return history_focus_?culture_filter_labels[std::clamp(culture_filter_,0,8)]:game_filter_labels[std::clamp(filter_,0,4)];
}
void Screen::rebuild_history_filter(){
    const auto*selected=history_focus_?current():nullptr;
    const std::string id=selected?selected->id:std::string{};
    const int day=selected?chronology_day(*selected):0;
    history_catalog_.entries.clear();
    const auto category=culture_categories[std::clamp(culture_filter_,0,8)];
    for(const auto&entry:history_catalog_all_.entries)
        if(!culture_filter_||entry.culture_category==category)history_catalog_.entries.push_back(entry);
    int nearest=0;
    for(size_t n=0;n<history_catalog_.entries.size();++n){
        const auto&entry=history_catalog_.entries[n];
        if(entry.id==id){nearest=int(n);break;}
        if(n==0||std::abs(chronology_day(entry)-day)<std::abs(chronology_day(history_catalog_.entries[size_t(nearest)])-day))nearest=int(n);
    }
    history_focus_index_=nearest;history_position_.snap(float(nearest));
}
void Screen::warm_history(){
    std::vector<std::string> nearby;
    for(int distance=0;distance<=4;++distance)for(int direction:{1,-1}){
        if(!distance&&direction<0)continue;
        const int n=history_focus_index_+distance*direction;
        if(n<0||n>=int(history_catalog_.entries.size()))continue;
        const auto&e=history_catalog_.entries[size_t(n)];
        if(!e.images.empty())nearby.push_back(e.images[e.preferred_image].url);
    }
    cache_.prefetch_images(nearby);
    if(history_focus_)nearby_covers_=std::move(nearby);
}
void Screen::focus_history(bool active){
    if(active==history_focus_||history_catalog_.entries.empty())return;
    const auto*selected=current();if(!selected||(!active&&visible_.empty()))return;
    const Entry source_copy=*selected;const auto*source=&source_copy;
    const int day=chronology_day(*source);
    auto&source_memory=active?gaming_year_selection_:culture_year_selection_;
    auto&target_memory=active?culture_year_selection_:gaming_year_selection_;
    source_memory[source->year]=source->id;
    snapshot_current();
    filter_=culture_filter_=0;rebuild(false);rebuild_history_filter();
    filter_notice_time_=0;year_notice_time_=0;
    if(active){
        int nearest=0;
        for(size_t n=1;n<history_catalog_.entries.size();++n)
            if(std::abs(chronology_day(history_catalog_.entries[n])-day)<std::abs(chronology_day(history_catalog_.entries[size_t(nearest)])-day))nearest=int(n);
        // A new year enters at its first stop. A visited year restores that
        // route's exact last exhibit, independently in both directions.
        for(size_t n=0;n<history_catalog_.entries.size();++n)if(history_catalog_.entries[n].year==source->year){nearest=int(n);break;}
        if(const auto saved=target_memory.find(source->year);saved!=target_memory.end())
            for(size_t n=0;n<history_catalog_.entries.size();++n)if(history_catalog_.entries[n].year==source->year&&history_catalog_.entries[n].id==saved->second){nearest=int(n);break;}
        history_focus_index_=nearest;history_position_.snap(float(nearest));history_focus_=true;
        culture_year_selection_[current()->year]=current()->id;
    }else{
        int nearest=0;
        for(size_t n=1;n<visible_.size();++n)
            if(std::abs(chronology_day(catalog_.entries[size_t(visible_[n])])-day)<std::abs(chronology_day(catalog_.entries[size_t(visible_[size_t(nearest)])])-day))nearest=int(n);
        for(size_t n=0;n<visible_.size();++n)if(catalog_.entries[size_t(visible_[n])].year==source->year){nearest=int(n);break;}
        if(const auto saved=target_memory.find(source->year);saved!=target_memory.end())
            for(size_t n=0;n<visible_.size();++n){const auto&entry=catalog_.entries[size_t(visible_[n])];if(entry.year==source->year&&entry.id==saved->second){nearest=int(n);break;}}
        history_focus_=false;focus_=nearest;timeline_.snap(float(nearest));changed();
    }
    history_transition_=true;history_direction_=active?-1.f:1.f;fade_=0;scroll_.snap(0);scroll_max_=0;
    image_index_=current()?current()->preferred_image:0;
    if(active)warm_history();
    else{
        nearby_covers_.clear();
        if(const auto*e=current())for(const auto&i:e->images)cache_.request(image_url(i));
    }
}
void Screen::move_history(int delta,ui::Feedback&feedback){
    const int next=std::clamp(history_focus_index_+delta,0,std::max(0,int(history_catalog_.entries.size())-1));
    if(next==history_focus_index_)return;
    if(current())culture_year_selection_[current()->year]=current()->id;
    history_transition_=false;history_focus_index_=next;fade_=1;entry_snapshot_=false;scroll_.snap(0);image_index_=current()->preferred_image;
    warm_history();feedback.timeline_step(delta);
    if(current())culture_year_selection_[current()->year]=current()->id;
}
void Screen::open_photo(gfx::Rect origin){
    const auto*e=current();if(!e||e->images.empty())return;
    const auto asset=cache_.get(image_url(e->images[size_t(std::clamp(image_index_,0,int(e->images.size())-1))]));
    if(asset.width>0&&asset.height>0){
        const float aspect=float(asset.width)/asset.height;
        if(origin.w/origin.h>aspect){const float width=origin.h*aspect;origin.x+=(origin.w-width)/2;origin.w=width;}
        else{const float height=origin.w/aspect;origin.y+=(origin.h-height)/2;origin.h=height;}
    }
    gallery_origin_=origin;prepare_gallery();viewer_.set_mode(ui::ZoomMode::fit,true);gallery_=true;idle_=0;
}
void Screen::draw_history_rail(float opened){
    if(history_catalog_.entries.empty())return;
    const auto palette=colours();const float emphasis=std::clamp(history_emphasis_.value,0.f,1.f);
    page_.push_opacity(1-opened);
    const float rail_y=260;
    page_.line(0,rail_y,1920,rail_y,1,palette.ink.with_alpha(.11f+.12f*emphasis));
    page_.line(920,rail_y,1000,rail_y,2+emphasis*2,gfx::mix(palette.muted,tone_,.6f).with_alpha(.5f+.5f*emphasis));
    page_.push_clip({0,142,1920,130});
    const int rail_focus=timeline_motion_.rail_focus(history_focus_index_);
    for(int n=std::max(0,rail_focus-4);n<std::min(int(history_catalog_.entries.size()),rail_focus+5);++n){
        if(!timeline_motion_.stop_visible(n))continue;
        const auto&e=history_catalog_.entries[size_t(timeline_motion_.content_index(n,history_focus_index_))];const float distance=float(n)-timeline_motion_.rail_position(history_position_.value);
        const float hover=std::clamp(1-std::abs(distance),0.f,1.f);
        const float extra=170*tween::smoothstep(std::min(1.f,std::abs(distance)));
        const float x=960+distance*340+(distance<0?-extra:extra);
        const auto colour=gfx::mix(palette.muted.with_alpha(.65f),palette.ink.with_alpha(.65f+.35f*emphasis),hover);
        // Wrap at the focused dimensions once; focus only scales the same lines.
        float reference_size=26;
        while(fonts_.regular.font->wrap(e.title,reference_size,450).size()>2&&reference_size>15)reference_size-=1;
        const auto lines=ui::paragraph_lines(fonts_.regular,e.title,reference_size,450);
        const float size=reference_size*(.72f+.28f*hover);
        ui::paragraph(page_,fonts_.regular,lines,x,195-float(lines.lines.size()-1)*size*1.15f,size,size*1.15f,colour,gfx::Align::center);
        ui::text(page_,fonts_.mono,date_label(e),x,238,16+hover*(3+2*emphasis),colour,gfx::Align::center);
        page_.line(x,rail_y-4,x,rail_y+4,1,colour.with_alpha(.4f));
    }
    page_.pop_clip();page_.pop_opacity();
}
hui::gfx::Rect Screen::history_image_bounds()const{
    constexpr float band_top=282.f,band_height=688.f,image_height=480.f;
    return {1000,band_top+(band_height-image_height)*.5f,780,image_height};
}
void Screen::draw_history_page(){
    const auto*e=current();if(!e)return;
    const auto palette=colours();const auto ink=palette.ink,quiet=palette.muted;
    background_.rounded_rect({0,282,1920,688},0,gfx::mix(palette.paper,tone_,.14f));
    draw_history_rail(0);
    page_.push_opacity(history_transition_?1.f:fade_);
    page_.push_transform(1,0,0,0,history_transition_?0.f:(1-fade_)*14);
    ui::text(page_,fonts_.mono,"CULTURE & DISCOVERY",100,329,17,quiet,gfx::Align::left,1.2f);
    const auto date=date_label(*e,false);
    if(!date.empty())ui::text(page_,fonts_.mono,ui::upper(date),100,365,18,quiet,gfx::Align::left,1.f);
    const float year_baseline=date.empty()?414.f:459.f;
    ui::text(page_,fonts_.display,std::to_string(e->year),96,year_baseline,74,ink);
    float size=46;
    while(fonts_.semibold.font->wrap(e->title,size,770).size()>2&&size>28)size-=1;
    const float after_title=ui::paragraph(page_,fonts_.semibold,e->title,96,year_baseline+62,size,770,size*1.15f,ink);
    std::string description;
    for(const auto&paragraph:e->body){if(!description.empty())description+="\n\n";description+=paragraph;}
    if(description.empty())description=e->summary;
    const float top=after_title+20,body_size=24,line_height=34;
    const float bottom=930-2*line_height;
    const auto lines=ui::paragraph_lines(fonts_.regular,description,body_size,760);
    const float viewport=std::max(1.f,bottom-top);
    const float content_height=lines.lines.empty()?0.f:float(lines.lines.size()-1)*line_height+fonts_.regular.font->descent(body_size);
    scroll_max_=content_height>viewport+1.f?content_height-viewport:0.f;
    page_.push_clip({98,top-25,774,viewport+25});
    ui::paragraph(page_,fonts_.regular,lines,100,top-scroll_.value,body_size,line_height,quiet);
    page_.pop_clip();
    if(scroll_max_>0){
        const float height=std::max(18.f,viewport*viewport/(viewport+scroll_max_));
        page_.line(880,top,880,bottom,1,quiet.with_alpha(.12f));
        const float y=top+(viewport-height)*std::clamp(scroll_.value/scroll_max_,0.f,1.f);
        page_.line(880,y,880,y+height,2,tone_);
    }
    if(!e->images.empty()){
        const auto&photo=e->images[e->preferred_image];
        image(page_,photo,history_image_bounds(),true);
    }
    page_.pop_transform();page_.pop_opacity();
    if(!gallery_&&gallery_open_.value<.001f){
        std::vector<ui::Hint> controls={{ui::Button::square,"View image"},{ui::Button::l1,"Decade",ui::Button::r1},{ui::Button::triangle,active_filter()?"All":"Today"},{ui::Button::l2,"Filter",ui::Button::r2},{ui::Button::touchpad,"Guide"}};
        if(scroll_max_>0)controls.push_back({ui::Button::right_stick,"Read"});
        controls.push_back({ui::Button::options,"Options"});hints(controls);
    }
}
}
