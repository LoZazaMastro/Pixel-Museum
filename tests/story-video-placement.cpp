#include "museum/catalog.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cassert>
#include <cstdio>
int main(){
    using J=nlohmann::json;
    J videos=J::array();
    for(const auto&placement:J::array({2,0,-1,3,999999999999LL,"2",true,nullptr}))
        videos.push_back(J{{"youtube_id","AAAAAAAAAAA"},{"title","Archive film"},{"story_paragraph",placement}});
    museum::Catalog catalog;
    assert(catalog.parse(J{{"entries",J::array({J{{"id","placement"},{"title","Museum"},{"year",1989},{"body",J::array({"First","Second","Third"})},{"videos",videos}}})}}.dump()));
    const auto&films=catalog.entries[0].videos;
    assert(films.size()==8&&films[0].story_paragraph==2&&films[1].story_paragraph==0);
    for(size_t n=2;n<films.size();++n)assert(films[n].story_paragraph==-1);
    std::puts("PASS: valid editorial video placement retained; invalid positions safely fall back.");
}
