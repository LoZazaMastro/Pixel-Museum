// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/localization.hpp"
#include "core/save_file.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <map>
#include <vector>
namespace museum::i18n {
namespace {
std::map<std::string,std::string,std::less<>> values,music_values;std::string language="en",failure;
std::vector<std::string> format_fields(std::string_view text){
    std::vector<std::string> fields;
    for(std::size_t n=0;n<text.size();++n){
        if(text[n]!='%')continue;
        std::size_t end=n+1;
        if(end<text.size()&&text[end]=='%'){fields.emplace_back("%%");n=end;continue;}
        while(end<text.size()&&std::string_view("-+ #0.123456789").find(text[end])!=std::string_view::npos)++end;
        std::string field;
        if(end<text.size()&&text[end]=='*'){field+='*';++end;}
        while(end<text.size()&&std::string_view("hljztL").find(text[end])!=std::string_view::npos)field+=text[end++];
        if(end<text.size()&&std::string_view("diuoxXfFeEgGaAcspn").find(text[end])!=std::string_view::npos){field+=text[end];fields.push_back(field);n=end;}
    }
    return fields;
}
std::vector<std::string_view> controls(std::string_view text){
    constexpr std::string_view tokens[]={"{left_stick}","{right_stick}","{dpad}","{touchpad}","{cross}","{circle}","{square}","{triangle}","{l1}","{r1}","{l2}","{r2}","{options}"};
    std::vector<std::string_view> result;
    for(std::size_t n=0;n<text.size();++n)if(text[n]=='{')for(const auto&t:tokens)if(text.substr(n,t.size())==t){result.push_back(t);n+=t.size()-1;break;}
    return result;
}
}
bool supported(std::string_view s){return s=="en"||s=="it"||s=="es"||s=="fr"||s=="de";}
bool load(const std::string&root,std::string_view requested){
    values.clear();music_values.clear();language="en";failure.clear();
    if(!supported(requested)){failure="Unsupported interface language; English is retained.";return false;}
    std::string bytes;if(!hui::save::read_file(root+"/content/ui-locales/"+std::string(requested)+".json",&bytes,512u<<10)){
        failure="Interface translation is unavailable; English is retained.";return false;}
    const auto j=nlohmann::json::parse(bytes,nullptr,false);
    if(j.is_discarded()||!j.is_object()||!j.contains("strings")||!j["strings"].is_object()||j["strings"].size()>2000){
        failure="Interface translation is invalid; English is retained.";return false;}
    const auto own=j.find("locale");if(own!=j.end()&&(!own->is_string()||own->get<std::string>()!=requested)){
        failure="Interface translation language mismatch; English is retained.";return false;}
    for(auto i=j["strings"].begin();i!=j["strings"].end();++i){
        if(i.key().size()>2048||!i.value().is_string()){failure="Invalid interface string; English is retained.";return false;}
        auto v=i.value().get<std::string>();if(v.size()>8192||v.find('\0')!=std::string::npos){failure="Invalid interface string; English is retained.";return false;}
        const auto fields=format_fields(i.key());
        if(!fields.empty()&&format_fields(v)!=fields){failure="Interface translation has incompatible format fields; English is retained.";return false;}
        if(controls(i.key())!=controls(v)){failure="Interface translation has incompatible controller symbols; English is retained.";return false;}
    }
    const auto musical=j.find("music_strings");
    if(musical!=j.end()){
        if(!musical->is_object()||musical->size()>2000){failure="Music presentation translation is invalid; English is retained.";return false;}
        for(auto i=musical->begin();i!=musical->end();++i){
            if(i.key().size()>2048||i.key().find('\0')!=std::string::npos||!i.value().is_string()){failure="Invalid music presentation string; English is retained.";return false;}
            const auto v=i.value().get<std::string>();
            if(v.size()>8192||v.find('\0')!=std::string::npos){failure="Invalid music presentation string; English is retained.";return false;}
            if(format_fields(i.key())!=format_fields(v)){failure="Music presentation has incompatible format fields; English is retained.";return false;}
            if(controls(i.key())!=controls(v)){failure="Music presentation has incompatible controller symbols; English is retained.";return false;}
        }
    }
    // English interface strings retain literal semantics, including legacy nonidentity entries.
    if(requested!="en")for(auto i=j["strings"].begin();i!=j["strings"].end();++i)values.emplace(i.key(),i.value().get<std::string>());
    if(musical!=j.end())for(auto i=musical->begin();i!=musical->end();++i)music_values.emplace(i.key(),i.value().get<std::string>());
    language=requested;return true;
}
std::string_view tr(std::string_view s){const auto i=values.find(s);return i==values.end()?s:std::string_view(i->second);}
std::string_view music(std::string_view s){const auto i=music_values.find(s);return i==music_values.end()?s:std::string_view(i->second);}
std::string music_room_title(std::string_view s){
    const auto specific=music_values.find(s);
    if(specific!=music_values.end())return specific->second;
    const auto translated=tr(s);
    constexpr std::string_view prefix="Listen to ";
    if(translated!=s||s.size()<=prefix.size()||s.substr(0,prefix.size())!=prefix)return std::string(translated);
    std::string result(tr("Music from %s"));
    const auto slot=result.find("%s");
    if(slot==std::string::npos)return std::string(translated);
    result.replace(slot,2,s.substr(prefix.size()));
    return result;
}
std::string_view locale(){return language;}
std::string_view error(){return failure;}
}
