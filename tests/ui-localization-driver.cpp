// Exercises the production dictionary loader and dynamic UI formatter.
#include "museum/localization.hpp"
#include "ui/fonts.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cstdio>
#include <string>
int main(int argc,char**argv){
    if(argc<3)return 2;
    const std::string mode=argv[1],root=argv[2];nlohmann::json report=nlohmann::json::array();
    if(mode=="all"){
        for(const char*language:{"en","it","es","fr","de"}){
            const bool loaded=museum::i18n::load(root,language);
            const std::string error(museum::i18n::error());
            if(!loaded||museum::i18n::locale()!=language){std::fprintf(stderr,"FAIL %s: %s\n",language,error.c_str());return 1;}
            const std::string folder(museum::i18n::tr("Cannot prepare the database update folder."));
            if(std::string(language)!="en"&&folder=="Cannot prepare the database update folder.")return 1;
            report.push_back({{"locale",language},{"loaded",loaded},{"options",museum::i18n::tr("Options")},{"folder_error",folder}});
        }
    }else if(mode=="bad-entry"){
        if(!museum::i18n::load(root,"fr")||museum::i18n::tr("Options")!="Options françaises"||museum::i18n::tr("Press {cross}")!="Press {cross}"||museum::i18n::tr("Lives %d")!="Lives %d")return 1;
        hui::ui::text_resolver=&museum::i18n::tr;char formatted[64];hui::ui::format(formatted,"Lives %d",3);
        if(std::string(formatted)!="Lives 3")return 1;
        report.push_back({{"bad_entry_falls_back_only_for_that_key",true},{"good_french_entry_retained",true},{"dynamic_format_safe",true}});
    }else if(mode=="malformed"){
        if(museum::i18n::load(root,"fr"))return 1;
        report.push_back({{"malformed_dictionary_rejected",true}});
    }else return 2;
    std::puts(report.dump(-1,' ',true).c_str());return 0;
}
