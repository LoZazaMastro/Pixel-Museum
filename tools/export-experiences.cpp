// Pixel Museum - Export and validate the production study metadata.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study_catalog.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <fstream>
#include <iostream>
#include <set>
#include <map>
int main(){
    std::ifstream file("content/catalog.json",std::ios::binary);
    const auto catalog=nlohmann::json::parse(file,nullptr,false);
    if(catalog.is_discarded()||!catalog.contains("entries"))return 2;
    std::set<std::string> entries,ids;
    for(const auto&e:catalog["entries"])entries.insert(e.value("id",std::string{}));
    std::map<std::string,unsigned> groups;
    nlohmann::json result={{"schema_version",1},{"scope","Original interpretive studies of game design, art direction and music. Experiences open directly in fullscreen from their explanatory exhibit cards; controller glyphs appear along the bottom during play."},{"entries",nlohmann::json::array()}};
    for(const auto&s:museum::study_catalog()){
        if(!ids.insert(s.id).second||!entries.count(s.entry_id)||s.explanation.empty()||s.discipline.empty()){
            std::cerr<<"Invalid or unlinked experience: "<<s.id<<" / "<<s.entry_id<<'\n';return 3;}
        ++groups[s.group];
        result["entries"].push_back({{"id",s.id},{"title",s.title},{"entry_id",s.entry_id},
            {"discipline",s.discipline},{"explanation",s.explanation},{"control_display","controller_glyphs"},{"group",s.group}});
    }
    // Only the reviewed selection is published; other factory implementations
    // remain research exercises and are not offered in the museum library.
    if(ids.size()!=21||groups["Arcade"]!=7||groups["Movement"]!=5||groups["Space"]!=3||groups["Workshops"]!=5||groups["Image"]!=1)return 4;
    std::ofstream output("content/experiences.json",std::ios::binary);
    output<<result.dump(2)<<'\n';if(!output)return 5;
    std::cout<<"Exported 21 reviewed experiences: 7 Arcade, 5 Movement, 3 Space, 5 Workshops, 1 pixel workshop; every linked exhibit exists.\n";
}
