// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/search.hpp"
#include <cassert>
#include <cstdio>
int main(){
    museum::Catalog gaming,culture;
    const auto row=[](const char*id,const char*title,int year,int month,int day){museum::Entry e;e.id=id;e.title=title;e.year=year;e.month=month;e.day=day;e.precision="day";return e;};
    gaming.entries={row("zelda","The Legend of Zelda",1986,2,21),row("pokemon","Pok\xc3\xa9mon Legends",2025,10,16),row("mario","Super Mario Bros.",1985,9,13)};
    culture.entries={row("mario-film","Super Mario film",1993,5,28),row("mario-culture","Mario culture",1985,1,1)};
    auto matches=museum::search_collection(gaming,culture,"MARIO");assert(matches.size()==3);
    assert(matches[0].culture&&matches[0].index==1);assert(!matches[1].culture&&matches[1].index==2);assert(matches[2].culture);
    matches=museum::search_collection(gaming,culture,"pokemon 2025");assert(matches.size()==1&&matches[0].index==1);
    assert(museum::search_collection(gaming,culture,"Mario Zelda").empty());
    culture.entries[0].summary="This article also mentions 1989.";
    assert(museum::search_collection(gaming,culture,"1989").empty());
    assert(museum::search_collection(gaming,culture,"   !!! ").empty());
    auto duplicate=gaming.entries[2];duplicate.calendar_only=true;duplicate.linked_exhibit_id="mario";gaming.entries.push_back(duplicate);
    assert(museum::search_collection(gaming,culture,"Mario").size()==3);
    gaming.entries.push_back(gaming.entries[0]);assert(museum::search_collection(gaming,culture,"Zelda").size()==1);
    std::puts("Museum search PASS: both timelines, chronological dates, all query tokens, case/accent folding, empty searches, calendar aliases and repeated IDs.");
}
