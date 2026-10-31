// Reference overlay regression through the real runtime parser, without a device.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/catalog.hpp"
#include "core/save_file.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <cstdio>
#include <string>
#include <vector>

int main(int argc,char**argv){
    if(argc!=3){std::fprintf(stderr,"usage: locale-test catalog.json fixture-root\n");return 2;}
    museum::Catalog catalog;
    if(!catalog.load(argv[1])){std::fprintf(stderr,"%s\n",catalog.error.c_str());return 1;}
    const auto baseline=catalog.entries;
    const auto check=[&](bool valid,const char*message){if(!valid)std::fprintf(stderr,"%s\n",message);return valid;};
    unsigned translations=0;
    for(const auto*language:{"it","es","fr","de"}){
        std::string bytes;
        const auto path=std::string(argv[2])+"/content/locales/"+language+".json";
        if(!hui::save::read_file(path,&bytes,16u<<20))return 3;
        const auto doc=nlohmann::json::parse(bytes,nullptr,false);
        if(!check(!doc.is_discarded(),"invalid fixture locale"))return 4;
        if(!check(catalog.set_locale(argv[2],language)&&catalog.locale_error().empty(),"real parser rejected reviewed locale"))return 5;
        for(std::size_t index=0;index<catalog.entries.size();++index){
            const auto&e=catalog.entries[index];const auto&original=baseline[index];
            if(!check(e.id==original.id&&e.year==original.year&&e.precision==original.precision&&e.images.size()==original.images.size()&&e.sources.size()==original.sources.size(),"locale changed non-text fields"))return 6;
            if(!check(e.editorial_features.size()==original.editorial_features.size(),"locale lost original feature"))return 7;
            for(std::size_t i=0;i<e.editorial_features.size();++i){const auto&a=e.editorial_features[i];const auto&b=original.editorial_features[i];
                if(!check(a.id==b.id&&a.body==b.body&&a.story_headings==b.story_headings&&a.editorial_credit==b.editorial_credit,"reference locale changed attached original text"))return 8;
            }
            const auto found=doc["entries"].find(e.id);
            if(found==doc["entries"].end()){
                if(!check(e.title==original.title&&e.body==original.body&&e.story_headings==original.story_headings&&e.editorial_credit==original.editorial_credit,"missing locale did not retain English"))return 9;
                continue;
            }
            const auto&row=*found;
            for(const auto*field:{"title","subtitle","summary","body","story_headings"}){
                nlohmann::json actual=field==std::string("title")?nlohmann::json(e.title):field==std::string("subtitle")?nlohmann::json(e.subtitle):field==std::string("summary")?nlohmann::json(e.summary):field==std::string("body")?nlohmann::json(e.body):nlohmann::json(e.story_headings);
                if(!check(actual==row[field],"real parser text differs from source-bound locale"))return 10;
            }
            if(row.contains("editorial_credit")){
                if(!check(e.editorial_credit==row["editorial_credit"].get<std::string>()&&e.editorial_credit!=original.editorial_credit,"translation credit not applied"))return 11;
                ++translations;
            }
        }
        if(!check(catalog.set_locale(argv[2],"en"),"English restoration failed"))return 12;
        for(std::size_t index=0;index<catalog.entries.size();++index){
            const auto&e=catalog.entries[index];const auto&original=baseline[index];
            if(!check(e.title==original.title&&e.subtitle==original.subtitle&&e.summary==original.summary&&e.body==original.body&&e.story_headings==original.story_headings&&e.editorial_credit==original.editorial_credit,"English text/credit not restored exactly"))return 13;
        }
    }
    if(!check(translations==160,"expected precisely 160 active translation credits"))return 14;
    std::printf("PASS: 160 reference translations, real parser fields/credit, English restoration, original features and fallback\n");
}
