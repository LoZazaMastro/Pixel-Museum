#include "museum/catalog.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cstdio>
#include <cstdlib>
using J=nlohmann::json;
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL %d %s\n",__LINE__,#x);std::abort();}}while(0)
static J track(){return {{"youtube_id","AAAAAAAAAAA"},{"title","A cue"},{"source_page","https://example.org/actual-chapters"}};}
int main(){
 J entry={{"id","score"},{"title","Original score"},{"year",2000}};
 J cues=J::array();cues.push_back(track());auto bounded=track();bounded["start_seconds"]=10.25;bounded["end_seconds"]=31.5;cues.push_back(bounded);
 for(const auto&pair:J::array({J::array({0,0}),J::array({12,11}),J::array({-1,5}),J::array({1,true}),J::array({1,"20"}),J::array({nullptr,20}),J::array({0,1e100})})){auto bad=track();bad["start_seconds"]=pair[0];bad["end_seconds"]=pair[1];cues.push_back(bad);}
 auto bad=track();bad["start_seconds"]=5;cues.push_back(bad);bad=track();bad["end_seconds"]=10;cues.push_back(bad);
 entry["soundtrack"]={{"composer","Legacy"},{"tracks",cues}};
 entry["soundtrack_rooms"]=J::array({{{"title","Woodkid"},{"composer","Woodkid"},{"tracks",J::array({bounded})}},{{"title","Forssell"},{"composer","Ludvig Forssell"},{"tracks",J::array({track(),track()})}},{{"title","Empty"},{"tracks",J::array()}}});
 museum::Catalog c;CHECK(c.parse(J{{"entries",J::array({entry})}}.dump()));const auto&e=c.entries[0];CHECK(e.soundtrack.tracks.size()==2);CHECK(e.soundtrack.tracks[0].start_seconds==0&&e.soundtrack.tracks[0].end_seconds==0);CHECK(e.soundtrack.tracks[1].start_seconds==10.25&&e.soundtrack.tracks[1].end_seconds==31.5);
 CHECK(e.soundtrack_rooms.size()==2);CHECK(e.soundtrack_rooms[0].composer=="Woodkid"&&e.soundtrack_rooms[0].tracks.size()==1&&e.soundtrack_rooms[0].tracks[0].start_seconds==10.25);CHECK(e.soundtrack_rooms[1].composer=="Ludvig Forssell"&&e.soundtrack_rooms[1].tracks.size()==2&&e.soundtrack_rooms[1].tracks[0].end_seconds==0);CHECK(e.soundtrack.composer=="Legacy");
 // Retain a 1000+ cue album and cap malicious/unbounded inventories at2048.
 J large=J::array();for(int n=0;n<2050;++n){auto t=track();t["title"]="Cue "+std::to_string(n+1);t["start_seconds"]=n*30;t["end_seconds"]=(n+1)*30;large.push_back(t);}entry["soundtrack"]["tracks"]=large;entry.erase("soundtrack_rooms");CHECK(c.parse(J{{"entries",J::array({entry})}}.dump()));CHECK(c.entries[0].soundtrack_rooms.empty());CHECK(c.entries[0].soundtrack.tracks.size()==2048);CHECK(c.entries[0].soundtrack.tracks.back().title=="Cue 2048"&&c.entries[0].soundtrack.tracks.back().end_seconds==61440);
 std::puts("Soundtrack catalog PASS: legacy, two independent rooms, fractional cue bounds, malformed-row rejection, 2048-cue inventory preserved.");
}
