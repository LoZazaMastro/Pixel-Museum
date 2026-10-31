// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/catalog.hpp"
#include <algorithm>
#include <cctype>
#include <set>
#include <tuple>
namespace museum {
struct SearchResult { int index=0;bool culture=false; };
inline std::string search_key(const std::string&text){
    std::string out;
    for(size_t n=0;n<text.size();++n){
        unsigned char c=text[n];
        if(c==0xc3&&n+1<text.size()){
            const unsigned char d=text[++n];
            if((d>=0x80&&d<=0x85)||(d>=0xa0&&d<=0xa5))out+='a';
            else if((d>=0x88&&d<=0x8b)||(d>=0xa8&&d<=0xab))out+='e';
            else if((d>=0x8c&&d<=0x8f)||(d>=0xac&&d<=0xaf))out+='i';
            else if((d>=0x92&&d<=0x96)||(d>=0xb2&&d<=0xb6))out+='o';
            else if((d>=0x99&&d<=0x9c)||(d>=0xb9&&d<=0xbc))out+='u';
            else if(d==0x87||d==0xa7)out+='c';else if(d==0x91||d==0xb1)out+='n';
            else if(d==0x9f)out+="ss";else {out+=char(c);out+=char(d);}
        }else if(c<128)out+=std::isalnum(c)?char(std::tolower(c)):' ';
        else out+=char(c);
    }
    return out;
}
inline std::vector<SearchResult> search_collection(const Catalog&gaming,const Catalog&culture,const std::string&query){
    const auto normalized=search_key(query);std::vector<std::string> tokens;
    for(size_t begin=0;begin<normalized.size();){
        begin=normalized.find_first_not_of(" \t\r\n",begin);if(begin==std::string::npos)break;
        const auto end=normalized.find_first_of(" \t\r\n",begin);tokens.push_back(normalized.substr(begin,end==std::string::npos?end:end-begin));
        if(end==std::string::npos)break;begin=end+1;
    }
    std::vector<SearchResult> results;if(tokens.empty())return results;
    std::set<std::string> seen;
    const auto collect=[&](const Catalog&catalog,bool history){
        for(size_t n=0;n<catalog.entries.size();++n){
            const auto&e=catalog.entries[n];
            if(e.calendar_only&&!e.linked_exhibit_id.empty())continue;
            if(!seen.insert((history?"culture:":"gaming:")+e.id).second)continue;
            const auto text=search_key(e.title+" "+e.subtitle+" "+e.summary+" "+std::to_string(e.year));
            if(std::all_of(tokens.begin(),tokens.end(),[&](const std::string&t){
                const bool year=t.size()==4&&std::all_of(t.begin(),t.end(),[](unsigned char c){return std::isdigit(c);});
                return year?t==std::to_string(e.year):text.find(t)!=std::string::npos;
            }))results.push_back({int(n),history});
        }
    };
    collect(gaming,false);collect(culture,true);
    const auto entry=[&](const SearchResult&r)->const Entry&{return (r.culture?culture:gaming).entries[size_t(r.index)];};
    std::stable_sort(results.begin(),results.end(),[&](const SearchResult&a,const SearchResult&b){const auto&x=entry(a);const auto&y=entry(b);return std::make_tuple(x.year,chronology_day(x),search_key(x.title),a.culture)<std::make_tuple(y.year,chronology_day(y),search_key(y.title),b.culture);});
    return results;
}
}
