// UTF-8 caret and visible-window geometry shared by drawing and pointer input.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <string>
#include <string_view>
#include <vector>

namespace hui::ui::text_entry {
inline bool continuation(char c){return (static_cast<unsigned char>(c)&0xc0)==0x80;}
inline std::size_t count(std::string_view text){std::size_t n=0;for(char c:text)n+=!continuation(c);return n;}
inline std::size_t boundary(std::string_view text,std::size_t at){
    at=std::min(at,text.size());
    while(at&&at<text.size()&&continuation(text[at]))--at;
    return at;
}
inline std::size_t next(std::string_view text,std::size_t at){
    at=boundary(text,at);if(at==text.size())return at;
    ++at;while(at<text.size()&&continuation(text[at]))++at;return at;
}
inline std::size_t previous(std::string_view text,std::size_t at){
    at=boundary(text,at);if(!at)return 0;
    --at;while(at&&continuation(text[at]))--at;return at;
}
inline std::string printable(std::string_view typed){
    std::string result;
    for(std::size_t at=0;at<typed.size();){const auto after=next(typed,at);const auto lead=static_cast<unsigned char>(typed[at]);if(lead>=32&&lead!=127)result.append(typed.substr(at,after-at));at=after;}
    return result;
}
inline bool insert_bounded(std::string&text,std::size_t&caret,std::string_view typed,std::size_t limit){
    caret=boundary(text,caret);const auto length=count(text);const auto available=length<limit?limit-length:0;
    std::size_t end=0;for(std::size_t n=0;n<available&&end<typed.size();++n)end=next(typed,end);
    if(!end)return false;
    const std::string value(typed.substr(0,end));text.insert(caret,value);caret+=value.size();return true;
}
inline bool erase_previous(std::string&text,std::size_t&caret){
    caret=boundary(text,caret);if(!caret)return false;const auto before=previous(text,caret);text.erase(before,caret-before);caret=before;return true;
}
inline bool erase_next(std::string&text,std::size_t&caret){
    caret=boundary(text,caret);if(caret==text.size())return false;text.erase(caret,next(text,caret)-caret);return true;
}
struct Layout {std::string value;std::size_t begin=0,end=0;float caret_offset=0;};
inline std::string segment(std::string_view text,std::size_t begin,std::size_t end,std::string_view mask){
    if(mask.empty())return std::string(text.substr(begin,end-begin));
    std::string result;for(auto at=begin;at<end;at=next(text,at))result+=mask;return result;
}
template<class Measure>
Layout layout(std::string_view text,std::size_t caret,std::size_t prior_begin,float room,std::string_view mask,Measure measure){
    caret=boundary(text,caret);auto begin=boundary(text,prior_begin);room=std::max(0.f,room);
    if(caret<begin)begin=caret;
    while(begin<caret&&measure(segment(text,begin,caret,mask))>room)begin=next(text,begin);
    // After deletion, fill space at the left instead of leaving a short tail.
    while(begin>0){const auto before=previous(text,begin);if(measure(segment(text,before,text.size(),mask))>room)break;begin=before;}
    auto end=begin;
    while(end<text.size()){const auto after=next(text,end);if(measure(segment(text,begin,after,mask))>room)break;end=after;}
    return {segment(text,begin,end,mask),begin,end,measure(segment(text,begin,caret,mask))};
}
template<class Measure>
std::size_t pick(std::string_view text,const Layout&visible,float x,std::string_view mask,Measure measure){
    if(x<=0)return visible.begin;
    float before=0;
    for(auto at=visible.begin;at<visible.end;){
        const auto after=next(text,at);const float width=measure(segment(text,visible.begin,after,mask));
        if(x<(before+width)*.5f)return at;
        at=after;before=width;
    }
    return visible.end;
}
}
