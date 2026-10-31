// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/collection_install_view.hpp"
#include "museum/theme.hpp"
#include "ui/glyphs.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>

namespace museum {
namespace {
using namespace hui;
constexpr int mark[5][5]={{1,0,0,0,1},{1,1,0,1,1},{1,0,1,0,1},{1,0,0,0,1},{1,0,0,0,1}};
constexpr std::uint32_t accents[]={0xa5c8c0,0xd4b9d5,0xe2b994,0xa8bdce,0xd3cf9f,0xcba4ae,0xb8cfae,0xd8b5a1,0xa8bcca,0xc3b3d7,0xe2ccad,0xb8cfc6,0xd4c7bd};
void logo(gfx::DrawList& d,float x,float y,float cell,gfx::Color ink){
    for(int row=0;row<5;++row)for(int col=0;col<5;++col)
        if(mark[row][col])d.rounded_rect({x+col*cell,y+row*cell,cell,cell},0,ink);
}
std::string bytes(std::uint64_t n){
    char out[48];const double gib=double(n)/(1024.*1024.*1024.);
    if(gib>=1.)std::snprintf(out,sizeof(out),"%.2f GiB",gib);
    else std::snprintf(out,sizeof(out),"%.1f MiB",double(n)/(1024.*1024.));
    return out;
}
const char* title(CollectionInstallPhase phase){
    switch(phase){
    case CollectionInstallPhase::checking:return "Checking the collection";
    case CollectionInstallPhase::preparing:return "Preparing your museum";
    case CollectionInstallPhase::downloading:return "Downloading the collection";
    case CollectionInstallPhase::paused:return "Take your time";
    case CollectionInstallPhase::error:return "The download was interrupted";
    case CollectionInstallPhase::complete:return "Your museum is ready";
    }return "Preparing your museum";
}
const char* description(const CollectionInstallViewState& s){
    switch(s.phase){
    case CollectionInstallPhase::checking:return "Making sure everything is ready for your first visit.";
    case CollectionInstallPhase::preparing:return "Putting the collection in place. This may take a few moments.";
    case CollectionInstallPhase::downloading:return "The games, the people and the world around them. Your first visit begins when the collection is ready.";
    case CollectionInstallPhase::paused:return "The download is paused. Continue whenever you are ready.";
    case CollectionInstallPhase::complete:return "The collection is here. Make yourself at home.";
    case CollectionInstallPhase::error:
        if(s.error==CollectionInstallError::storage)return "There is not enough free space. Make room on your PS5, then try again.";
        if(s.error==CollectionInstallError::invalid_files)return "Some files could not be prepared. Please try again.";
        if(s.error==CollectionInstallError::network)return "Check your connection, then try again.";
        return "Please try again in a moment.";
    }return "";
}
}
void draw_collection_install_view(hui::gfx::DrawList& d,const hui::ui::Fonts& fonts,
    const CollectionInstallViewState& s,float dark_mix,float elapsed_seconds,bool reduced_motion){
    using namespace hui;using gfx::Align;using gfx::Color;
    const auto p=museum_palette(dark_mix);
    const float time=std::isfinite(elapsed_seconds)?std::max(0.f,elapsed_seconds):0.f;
    const bool active=s.phase==CollectionInstallPhase::downloading;
    const bool waiting=s.phase==CollectionInstallPhase::checking||s.phase==CollectionInstallPhase::preparing;
    const bool complete=s.phase==CollectionInstallPhase::complete;
    const bool known=s.progress>=0.f||s.total_bytes>0;
    const float fraction=complete?1.f:std::clamp(s.progress>=0.f?s.progress:(s.total_bytes?float(double(s.downloaded_bytes)/double(s.total_bytes)):0.f),0.f,1.f);
    d.rounded_rect({0,0,1920,1080},0,p.paper);
    const float arrival=reduced_motion?1.f:std::clamp(time/.32f,0.f,1.f);
    d.push_opacity(arrival*arrival*(3.f-2.f*arrival));
    logo(d,96,66,6.8f,p.ink);
    ui::text(d,fonts.semibold,"PIXEL MUSEUM",150,93,22,p.ink,Align::left,2);
    d.line(96,139,1824,139,1,p.rule);

    constexpr float x=260,right=1660;
    ui::paragraph(d,fonts.regular,title(s.phase),x,344,60,1110,74,p.ink,2);
    ui::paragraph(d,fonts.regular,description(s),x,488,27,1060,39,p.muted,3);

    // The collection's own thirteen-pixel M; a single quiet colour travels through it.
    constexpr float mx=1450,my=315,cell=33;
    logo(d,mx,my,cell,p.ink.with_alpha(.09f));
    const int ordinal=reduced_motion||(!active&&!waiting)?6:int(time/.7f)%13;
    int index=0;
    for(int row=0;row<5;++row)for(int col=0;col<5;++col)if(mark[row][col]){
        const float a=complete?.8f:index==ordinal?.85f:.17f;
        d.rounded_rect({mx+col*cell,my+row*cell,cell,cell},0,Color::rgb(accents[index],a));
        ++index;
    }

    const char* label=waiting?"Preparing files":s.phase==CollectionInstallPhase::paused?"Paused":complete?"Complete":s.phase==CollectionInstallPhase::error?"Download interrupted":"Collection download";
    ui::text(d,fonts.semibold,label,x,626,20,p.ink);
    if(known||complete){char percent[16];std::snprintf(percent,sizeof(percent),"%.0f%%",fraction*100.f);ui::text(d,fonts.mono,percent,right,626,40,p.ink,Align::right);}
    constexpr int count=78;constexpr float step=18,side=12;
    const int moving=reduced_motion?count/2:int(time*10.f)%count;
    for(int i=0;i<count;++i){
        auto c=p.ink.with_alpha(.10f);
        if(known&&float(i)<fraction*count)c=p.ink.with_alpha(.82f);
        if(complete)c=p.ink.with_alpha(.82f);
        else if(waiting||(active&&!known)){if(i>=moving&&i<moving+3)c=p.ink.with_alpha(.45f);}
        else if(active&&fraction<1.f&&i==std::min(count-1,int(fraction*count)))c=Color::rgb(0xc49b51,reduced_motion?.8f:.5f+.35f*std::sin(time*3));
        d.rounded_rect({x+i*step,659,side,side},0,c);
    }

    if(s.total_bytes>0){const auto amount=bytes(complete?s.total_bytes:s.downloaded_bytes)+" / "+bytes(s.total_bytes);ui::text(d,fonts.mono,amount,x,718,20,p.muted);}
    if(active&&std::isfinite(s.bytes_per_second)&&s.bytes_per_second>0){
        char speed[64];std::snprintf(speed,sizeof(speed),"%.1f MiB/s",s.bytes_per_second/(1024.*1024.));
        ui::text(d,fonts.mono,speed,right,718,20,p.muted,Align::right);
    }
    if(s.pack_count>0&&!complete){char file[96];ui::format(file,"File %d of %d",int(std::min(s.pack_index+1,s.pack_count)),int(s.pack_count));ui::text(d,fonts.regular,file,x,765,18,p.muted);}

    const char* action=active?"Pause":s.phase==CollectionInstallPhase::paused?"Resume":s.phase==CollectionInstallPhase::error?"Retry":nullptr;
    d.line(96,940,1824,940,1,p.rule);
    if(!complete){
        ui::Hint hints[2];int count=0;
        if(action)hints[count++]={ui::Button::cross,action};
        hints[count++]={ui::Button::circle,"Close Pixel Museum"};
        ui::HintLayout l;l.size=30;l.text_size=22;l.cy=995;
        auto style=ui::GlyphStyle::mono(p.ink,Color::rgb(0,0));style.label=p.ink;
        ui::draw_hints(d,fonts,style,hints,count,260,false,l);
    }
    d.pop_opacity();
}
}
