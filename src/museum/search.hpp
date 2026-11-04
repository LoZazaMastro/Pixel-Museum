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
            else if(d==0x86||d==0xa6)out+="ae";else if(d==0x98||d==0xb8)out+='o';
            else if(d==0x9d||d==0xbd||d==0xbf)out+='y';
            else if(d==0x9f)out+="ss";else {out+=char(c);out+=char(d);}
        }else if((c==0xcc||c==0xcd)&&n+1<text.size()&&
                 static_cast<unsigned char>(text[n+1])>=0x80&&
                 static_cast<unsigned char>(text[n+1])<=(c==0xcc?0xbf:0xaf)){
            ++n; // Combining accents in decomposed UTF-8 names.
        }else if(c==0xe2&&n+2<text.size()&&static_cast<unsigned char>(text[n+1])==0x80&&
                 static_cast<unsigned char>(text[n+2])>=0x80&&static_cast<unsigned char>(text[n+2])<=0xbf){
            out+=' ';n+=2; // Typographic apostrophes and dashes separate title words.
        }else if(c<128)out+=std::isalnum(c)?char(std::tolower(c)):' ';
        else out+=char(c);
    }
    return out;
}
namespace search_detail {
inline std::vector<std::string> words(const std::string&text){
    const auto normalized=search_key(text);std::vector<std::string> tokens;
    for(size_t begin=0;begin<normalized.size();){
        begin=normalized.find_first_not_of(" \t\r\n",begin);if(begin==std::string::npos)break;
        const auto end=normalized.find_first_of(" \t\r\n",begin);tokens.push_back(normalized.substr(begin,end==std::string::npos?end:end-begin));
        if(end==std::string::npos)break;begin=end+1;
    }
    return tokens;
}
inline bool numeric(const std::string&text){
    return !text.empty()&&std::all_of(text.begin(),text.end(),[](unsigned char c){return c>='0'&&c<='9';});
}
// Whole title words are required. Only the last non-numeric query word may
// still be in the process of being typed; "station" never matches "PlayStation".
inline int relevance(const std::vector<std::string>&title,const std::vector<std::string>&terms,bool partial){
    bool prefix_used=false;
    for(size_t n=0;n<terms.size();++n){
        const auto&term=terms[n];
        if(std::find(title.begin(),title.end(),term)!=title.end())continue;
        const bool prefix=partial&&n+1==terms.size()&&!numeric(term)&&
            std::any_of(title.begin(),title.end(),[&](const std::string&word){return word.compare(0,term.size(),term)==0;});
        if(!prefix)return -1;
        prefix_used=true;
    }
    if(title==terms)return 0;
    bool starts=title.size()>=terms.size();
    for(size_t n=0;starts&&n<terms.size();++n)
        starts=terms[n]==title[n]||(partial&&n+1==terms.size()&&!numeric(terms[n])&&title[n].compare(0,terms[n].size(),terms[n])==0);
    return starts?1:(prefix_used?3:2);
}
}
inline std::vector<SearchResult> search_collection(const Catalog&gaming,const Catalog&culture,const std::string&query){
    const auto tokens=search_detail::words(query);std::vector<SearchResult> results;if(tokens.empty())return results;
    const bool partial=!query.empty()&&!std::isspace(static_cast<unsigned char>(query.back()))&&
        !search_detail::numeric(tokens.back());
    struct RankedResult { SearchResult result;int rank=0; };
    std::vector<RankedResult> primary,fallback;
    std::set<std::string> seen;
    const auto collect=[&](const Catalog&catalog,bool history){
        for(size_t n=0;n<catalog.entries.size();++n){
            const auto&e=catalog.entries[n];
            if(e.calendar_only&&!e.linked_exhibit_id.empty())continue;
            if(!seen.insert((history?"culture:":"gaming:")+e.id).second)continue;
            const auto title=search_detail::words(e.title);
            const auto year=std::to_string(e.year);
            // A number can be part of the official name (Blade Runner 2049,
            // 2001: A Space Odyssey), or an exact chronological constraint.
            // A number mentioned only in a subtitle/description cannot qualify.
            if(std::any_of(tokens.begin(),tokens.end(),[&](const std::string&t){
                return t.size()==4&&search_detail::numeric(t)&&t!=year&&std::find(title.begin(),title.end(),t)==title.end();
            }))continue;
            auto terms=tokens;
            terms.erase(std::remove_if(terms.begin(),terms.end(),[&](const std::string&t){return t.size()==4&&search_detail::numeric(t)&&t==year;}),terms.end());
            int rank=search_detail::relevance(title,tokens,partial);
            if(rank<0){rank=search_detail::relevance(title,terms,partial);if(rank>=0)rank+=4;}
            if(rank>=0){primary.push_back({{int(n),history},rank});continue;}
            if(!e.subtitle.empty()){
                const int secondary=search_detail::relevance(search_detail::words(e.title+" "+e.subtitle),terms,partial);
                if(secondary>=0)fallback.push_back({{int(n),history},secondary});
            }
        }
    };
    collect(gaming,false);collect(culture,true);
    // Editorial subtitles remain useful as a fallback, but cannot fill a
    // nominal search with unrelated games that merely mention a platform.
    auto&ranked=primary.empty()?fallback:primary;
    const auto entry=[&](const SearchResult&r)->const Entry&{return (r.culture?culture:gaming).entries[size_t(r.index)];};
    std::stable_sort(ranked.begin(),ranked.end(),[&](const RankedResult&a,const RankedResult&b){const auto&x=entry(a.result);const auto&y=entry(b.result);return std::make_tuple(a.rank,x.year,chronology_day(x),search_key(x.title),a.result.culture)<std::make_tuple(b.rank,y.year,chronology_day(y),search_key(y.title),b.result.culture);});
    for(const auto&item:ranked)results.push_back(item.result);
    return results;
}
}
