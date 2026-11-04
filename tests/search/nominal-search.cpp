// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/search.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <set>

namespace {
museum::Entry row(const char*id,const char*title,int year){
    museum::Entry e;e.id=id;e.title=title;e.year=year;e.month=1;e.day=1;e.precision="day";return e;
}
std::set<std::string> ids(const museum::Catalog&a,const museum::Catalog&b,const std::vector<museum::SearchResult>&results){
    std::set<std::string> out;
    for(const auto&r:results){assert(r.index>=0);const auto&v=(r.culture?b:a).entries;assert(size_t(r.index)<v.size());out.insert(v[size_t(r.index)].id);}
    return out;
}
museum::Catalog load_titles(const char*path){
    // Exercise the actual catalogue titles without depending on unrelated
    // multimedia or platform services in this search-only regression binary.
    std::ifstream file(path);assert(file.good());nlohmann::json doc;file>>doc;
    museum::Catalog out;
    for(const auto&item:doc.at("entries")){
        museum::Entry e;e.id=item.at("id");e.title=item.at("title");e.subtitle=item.value("subtitle","");e.summary=item.value("summary","");
        e.year=item.value("year",0);e.month=item.value("month",0);e.day=item.value("day",0);e.precision=item.value("precision","");
        e.calendar_only=item.value("calendar_only",false);e.linked_exhibit_id=item.value("linked_exhibit_id","");out.entries.push_back(std::move(e));
    }
    return out;
}
}
int main(int argc,char**argv){
    museum::Catalog gaming,culture;
    gaming.entries={row("ridge","Ridge Racer",1994),row("ps2-game","PlayStation 2 launch collection",1999),
        row("ps2","PlayStation 2",2000),row("ps","PlayStation",1994),row("portable","PlayStation Portable",2004),
        row("ps20","PlayStation 20th Anniversary",2014),row("station","Stationfall",2023),
        row("pokemon","Pok\xc3\xa9mon Legends: Arceus",2022),row("zelda","The Legend of Zelda",1986),
        row("cafe","Caf\xc3\xa9 des Arts",2001),row("pop","Prince of Persia: The Sands of Time",2003)};
    gaming.entries[0].summary="One of the original PlayStation games; an important Sony release.";
    gaming.entries[0].subtitle="Arcade drifting comes to PlayStation";
    culture.entries={row("culture","History of cinema",1993),row("ps-culture","PlayStation in popular culture",2018),
        row("blade","Blade Runner 2049",2017),row("odyssey","2001: A Space Odyssey",1968)};
    culture.entries[0].summary="PlayStation 2 is mentioned, alongside The Legend of Zelda and the year 1994.";
    culture.entries[0].subtitle="Highlights from 1994";
    auto found=museum::search_collection(gaming,culture,"PlayStation");
    assert(found.size()==6);assert(!found[0].culture&&found[0].index==3);
    assert(!ids(gaming,culture,found).contains("ridge"));assert(!ids(gaming,culture,found).contains("culture"));
    found=museum::search_collection(gaming,culture,"PlayStation 2");
    assert(found.size()==2&&found[0].index==2&&found[1].index==1);
    assert(museum::search_collection(gaming,culture,"Station").size()==1);
    assert(ids(gaming,culture,museum::search_collection(gaming,culture,"play"))==ids(gaming,culture,museum::search_collection(gaming,culture,"PlayStation")));
    assert(museum::search_collection(gaming,culture,"play ").empty());
    assert(museum::search_collection(gaming,culture,"play sta").empty());
    assert(museum::search_collection(gaming,culture,"PlayStation 2 launch").size()==1);
    assert(museum::search_collection(gaming,culture,"PlayStation 2 launch Zelda").empty());
    assert(museum::search_collection(gaming,culture,"launch PlayStation 2").size()==1);
    assert(museum::search_collection(gaming,culture,"Poke Legends").empty());
    assert(museum::search_collection(gaming,culture,"Pokemon leg").size()==1);
    assert(museum::search_collection(gaming,culture,"POK\xc3\x89MON").size()==1);
    assert(museum::search_collection(gaming,culture,"Cafe\xcc\x81 des").size()==1);
    assert(museum::search_collection(gaming,culture,"cafe").size()==1);
    assert(museum::search_collection(gaming,culture,"1994").size()==2);
    found=museum::search_collection(gaming,culture,"PlayStation 1994");assert(found.size()==1&&found[0].index==3);
    found=museum::search_collection(gaming,culture,"Blade Runner 2049");assert(found.size()==1&&found[0].culture&&found[0].index==2);
    found=museum::search_collection(gaming,culture,"2049");assert(found.size()==1&&found[0].culture&&found[0].index==2);
    found=museum::search_collection(gaming,culture,"2001");assert(found.size()==2&&found[0].culture&&found[0].index==3);
    assert(museum::search_collection(gaming,culture,"2001 A Space Odyssey").size()==1);
    assert(museum::search_collection(gaming,culture,"Blade Runner 2017").size()==1);
    assert(museum::search_collection(gaming,culture,"204").empty());
    assert(museum::search_collection(gaming,culture,"1994 2000").empty());
    assert(museum::search_collection(gaming,culture,"199").empty());
    assert(museum::search_collection(gaming,culture,"Arcade drifting").size()==1); // Subtitle fallback only with zero nominal matches.
    assert(museum::search_collection(gaming,culture,"important Sony").empty()); // No summary matching, even as a fallback.
    assert(museum::search_collection(gaming,culture,"!!! ").empty());
    assert(museum::search_collection(gaming,culture," ").empty());
    auto alias=gaming.entries[3];alias.id="ps-birthday";alias.calendar_only=true;alias.linked_exhibit_id="ps";gaming.entries.push_back(alias);
    gaming.entries.push_back(gaming.entries[3]);assert(museum::search_collection(gaming,culture,"PlayStation").size()==6);
    // Localised official names are searched directly in the active catalogue.
    culture.entries.push_back(row("movie-it","Il ritorno dello Jedi",1983));
    assert(museum::search_collection(gaming,culture,"ritorno jed").size()==1);
    assert(museum::search_collection(gaming,culture,"dello 1983").size()==1);
    if(argc>1){
        auto actual=load_titles(argv[1]);museum::Catalog history;
        const auto matches=museum::search_collection(actual,history,"PlayStation");
        std::set<std::string> expected;
        for(const auto&e:actual.entries){const auto words=museum::search_detail::words(e.title);if(!e.calendar_only&&std::find(words.begin(),words.end(),"playstation")!=words.end())expected.insert(e.id);}
        // The current publication candidate has precisely these nine nominal entries.
        const std::set<std::string> known={"playstation","playstation-2","psp","playstation-3","playstation-move","wikipedia-35592396","playstation-4","playstation-5","hardware-playstation-vita"};
        assert(expected==known);assert(ids(actual,history,matches)==known);assert(matches[0].index>=0&&actual.entries[size_t(matches[0].index)].id=="playstation");
        found=museum::search_collection(actual,history,"PlayStation 1994");assert(found.size()==1&&actual.entries[size_t(found[0].index)].id=="playstation");
        std::printf("Real catalogue PASS: %zu entries, exactly nine nominal PlayStation results, no Ridge Racer / Final Fantasy subtitle leakage.\n",actual.entries.size());
    }
    std::puts("Nominal search PASS: exact-title ranking, whole-word AND, final-word prefix, numeric boundaries, exact years, accents, localised names, subtitle fallback, stable full indices and alias deduplication.");
}
