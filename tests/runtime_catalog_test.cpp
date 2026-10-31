#include "museum/catalog.hpp"
#include "third_party/nlohmann/json.hpp"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
using J=nlohmann::json;
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x);std::abort();}}while(0)
static J image(const museum::Image&i){return J::array({i.url,i.source_page,i.title,i.creator,i.license,i.credit,i.story_paragraph,i.caption});}
static J video(const museum::VideoRecord&v){return J::array({v.youtube_id,v.url,v.title,v.caption,v.creator,v.source_page,v.poster_url,v.start_seconds,v.end_seconds,v.story_paragraph});}
static J source(const museum::Source&s){return J::array({s.title,s.url,s.publisher,s.license,s.attribution});}
static J snapshot(const museum::Catalog&c){
 J result={{"title",c.title},{"subtitle",c.subtitle},{"remote",c.remote_url},{"initial",c.initial_id},{"entries",J::array()},{"eras",J::array()}};
 for(const auto&r:c.eras)result["eras"].push_back(J::array({r.id,r.title,r.summary,r.start_year,r.end_year,r.colour}));
 for(const auto&e:c.entries){
  J row=J::array({e.id,e.kind,e.title,e.subtitle,e.summary,e.era_id,e.layout,e.year,e.month,e.day,e.precision,e.region,e.event_semantics,e.editorial_credit,e.factual_note,e.linked_exhibit_id,e.featured,e.calendar_only,e.calendar_month,e.calendar_day,e.body,e.tags,e.related_ids,e.story_headings});
  row.push_back(e.explicit_story_media_only);
  row.push_back(e.preserve_unillustrated_opening);
  row.push_back(e.preferred_image);
  row.push_back(e.story_entry_id);
  J photos=J::array(),films=J::array(),models=J::array(),sources=J::array(),features=J::array(),tracks=J::array();
  for(const auto&i:e.images)photos.push_back(image(i));
  for(const auto&v:e.videos)films.push_back(video(v));
  for(const auto&s:e.sources)sources.push_back(source(s));
  for(const auto&m:e.models)models.push_back(J::array({m.url,m.asset_file,m.source_page,m.title,m.creator,m.license,m.credit,m.include_groups,m.initial_tilt,m.initial_angle,m.initial_zoom,m.source_z_up,m.display_caption}));
  for(const auto&f:e.editorial_features){J refs=J::array();for(const auto&s:f.sources)refs.push_back(source(s));features.push_back(J::array({f.id,f.title,f.summary,f.editorial_credit,f.body,f.story_headings,f.image_indices,refs}));}
  for(const auto&t:e.soundtrack.tracks)tracks.push_back(video(t));
  row.push_back(photos);row.push_back(films);row.push_back(models);row.push_back(sources);row.push_back(features);
  row.push_back(J::array({e.soundtrack.title,e.soundtrack.composer,e.soundtrack.curator_note,tracks}));
  J rooms=J::array();for(const auto&r:e.soundtrack_rooms){J items=J::array();for(const auto&t:r.tracks)items.push_back(video(t));rooms.push_back(J::array({r.title,r.composer,r.curator_note,items}));}row.push_back(rooms);result["entries"].push_back(std::move(row));
 }
 return result;
}
int main(int argc,char**argv){
 museum::Catalog fixture;
 CHECK(fixture.parse(R"({"entries":[{"id":"cover-test","title":"Cover test","year":1994,"body":["A","B"],"images":[{"url":"https://example.org/thumb","width":320,"height":240,"story_paragraph":1},{"url":"https://example.org/cover","width":2400,"height":1600,"story_paragraph":0},{"url":"https://example.org/larger","width":6000,"height":4000}],"editorial_features":[{"id":"f","title":"Feature","body":["Text"],"story_headings":["Title"],"images":[{"url":"https://example.org/portrait","width":8000,"height":6000}]}]},{"id":"unknown","title":"Unknown dimensions","year":1995,"images":[{"url":"https://example.org/unknown"}]}]})"));
 CHECK(fixture.entries[0].preferred_image==1);
 CHECK(fixture.entries[0].images.size()==4&&fixture.entries[0].images[0].story_paragraph==1);
 CHECK(fixture.entries[0].images[1].url=="https://example.org/cover");
 CHECK(fixture.entries[0].editorial_features[0].image_indices[0]==3);
 CHECK(fixture.entries[1].preferred_image==0);
 museum::Catalog captioned;CHECK(captioned.parse(R"({"entries":[{"id":"accessory","title":"Wii U","year":2012,"models":[{"asset_file":"models/wii-u-gamepad.glb","title":"Original creator title","display_caption":"Wii U GamePad","creator":"Credited creator"},{"asset_file":"models/legacy.glb","title":"Legacy title"}]}]})"));CHECK(captioned.entries[0].models.size()==2&&captioned.entries[0].models[0].display_caption=="Wii U GamePad"&&captioned.entries[0].models[0].title=="Original creator title"&&captioned.entries[0].models[0].creator=="Credited creator"&&captioned.entries[0].models[1].display_caption.empty());
 // Explicit image-to-paragraph selections survive the native boundary. Old
 // entries without a flag retain positional fallback; canonical enrichments
 // keep their already-established explicit-only policy.
 museum::Catalog media_policy;CHECK(media_policy.parse(R"({"entries":[{"id":"mapped","title":"Mapped","year":1996,"explicit_story_media_only":true},{"id":"legacy","title":"Legacy","year":1996},{"id":"false","title":"False","year":1996,"explicit_story_media_only":false},{"id":"malformed","title":"Malformed","year":1996,"explicit_story_media_only":"true"},{"id":"canonical","title":"Canonical","year":1996,"canonical_narrative_enrichment":{}},{"id":"canonical-false","title":"Canonical false","year":1996,"explicit_story_media_only":false,"canonical_narrative_enrichment":{}}]})"));CHECK(media_policy.entries.size()==6&&media_policy.entries[0].explicit_story_media_only&&!media_policy.entries[1].explicit_story_media_only&&!media_policy.entries[2].explicit_story_media_only&&!media_policy.entries[3].explicit_story_media_only&&media_policy.entries[4].explicit_story_media_only&&media_policy.entries[5].explicit_story_media_only);
 museum::Catalog opening_policy;CHECK(opening_policy.parse(R"({"entries":[{"id":"partial","title":"Partial","year":1991,"preserve_unillustrated_opening":true},{"id":"default","title":"Default","year":1991},{"id":"bad","title":"Bad","year":1991,"preserve_unillustrated_opening":"true"}]})"));
 CHECK(opening_policy.entries[0].preserve_unillustrated_opening&&!opening_policy.entries[1].preserve_unillustrated_opening&&!opening_policy.entries[2].preserve_unillustrated_opening);
 museum::Catalog shared_story;CHECK(shared_story.parse(R"({"entries":[{"id":"birth","title":"Designer","year":1952},{"id":"recognition","title":"Cultural recognition","year":2026,"story_entry_id":"birth"}]})"));
 CHECK(shared_story.find_entry("recognition")->story_entry_id=="birth"&&shared_story.find_entry("recognition")->year==2026);
 // Complete albums must survive the native reader, including their final cue.
 J album=J::object(),album_entry=J::object(),recordings=J::array();
 album_entry["id"]="album-72";album_entry["title"]="Complete album";album_entry["year"]=2016;
 for(int n=0;n<72;++n){char id[12];std::snprintf(id,sizeof(id),"AAAAAAAAA%02d",n);recordings.push_back({{"youtube_id",id},{"title","Recording "+std::to_string(n+1)},{"source_page","https://example.org/official-album"}});}
 album_entry["soundtrack"]={{"tracks",recordings}};album["entries"]=J::array({album_entry});museum::Catalog complete_album;
 CHECK(complete_album.parse(album.dump()));CHECK(complete_album.entries.size()==1&&complete_album.entries[0].soundtrack.tracks.size()==72);
 CHECK(complete_album.entries[0].soundtrack.tracks.back().title=="Recording 72");
 CHECK(argc==3);museum::Catalog authoring,runtime;
 using Clock=std::chrono::steady_clock;
 const auto a=Clock::now();
 // Authoring receipts grow beyond the intentionally bounded native format.
 // Compare their parsed selections in bounded chunks, while requiring the
 // complete projected runtime to load as one ordinary native catalogue.
 std::ifstream input(argv[1]);CHECK(input.good());const std::string bytes((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());J document=J::parse(bytes);
 for(size_t begin=0;begin<document["entries"].size();begin+=128){J batch=document;batch["entries"]=J::array();const auto end=std::min(begin+128,document["entries"].size());for(size_t n=begin;n<end;++n)batch["entries"].push_back(document["entries"][n]);museum::Catalog part;CHECK(part.parse(batch.dump()));if(begin==0)authoring=std::move(part);else for(auto&e:part.entries)authoring.entries.push_back(std::move(e));}
 const auto b=Clock::now();CHECK(runtime.load(argv[2]));const auto d=Clock::now();
 CHECK(snapshot(authoring)==snapshot(runtime));
 // Top-level alias records must survive projection semantically, including
 // retired IDs absent from the timeline. Do not synthesize duplicate entries.
 size_t alias_count=0;
 if(document.contains("entry_aliases")&&document["entry_aliases"].is_object())for(auto alias=document["entry_aliases"].begin();alias!=document["entry_aliases"].end();++alias){
  CHECK(authoring.resolve_entry_id(alias.key())==runtime.resolve_entry_id(alias.key()));++alias_count;
 }
 const double original=std::chrono::duration<double,std::milli>(b-a).count(),projected=std::chrono::duration<double,std::milli>(d-b).count();
 std::printf("Native parser equivalence PASS: %zu entries, all parsed text/media/rights/source/date/model/feature/era fields and %zu alias resolutions. Host timings: authoring %.2f ms, projected %.2f ms (not PS5 timings).\n",runtime.entries.size(),alias_count,original,projected);
}
