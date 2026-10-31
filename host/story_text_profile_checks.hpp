// Actual composed narrative CPU profiling; no source or production data edits.
#pragma once
#include <chrono>
#include <set>
#include "third_party/nlohmann/json.hpp"
namespace museum {
inline bool ScreenInspection::profile_story_text(Screen&s){
 const char*override_catalog=std::getenv("MUSEUM_TEXT_PROFILE_CATALOG");
 const char*scoped_ids=std::getenv("MUSEUM_TEXT_PROFILE_PROBE_ENTRIES");const std::string scope=scoped_ids?std::string(",")+scoped_ids+",":"";
 const char*composition_path=std::getenv("MUSEUM_COMPOSITION_SNAPSHOT");
 const char*profile_output=std::getenv("MUSEUM_PROFILE_OUTPUT");
 const std::string frozen=override_catalog?override_catalog:"build/research/story-text-profile/catalog.json";
 if(!s.catalog_.load(frozen)){std::fprintf(stderr,"Cannot read frozen text profile catalogue: %s\n",s.catalog_.error.c_str());return false;}
 std::printf("Profiling loaded catalogue %s: %zu entries / explicit override %s\n",frozen.c_str(),s.catalog_.entries.size(),override_catalog?"yes":"no (historical benchmark)");
 s.onboarding_=false;s.data_.clear();s.boot_time_=5;s.boot_note_=13;s.detail_=true;s.story_open_.snap(1);
 struct Candidate{size_t entry;int card;size_t bytes;float weight;};std::vector<Candidate>candidates;
 nlohmann::json gaps=nlohmann::json::array(),media_probes=nlohmann::json::array(),scoped_probes=nlohmann::json::array(),compositions=nlohmann::json::array(),cover_probe,cover_alias_probe;bool media_probe_failed=false;
 for(size_t entry=0;entry<s.catalog_.entries.size();++entry){s.visible_={int(entry)};s.focus_=0;s.prepare_story();const auto&e=s.catalog_.entries[entry];
  if(composition_path){
   auto cards=nlohmann::json::array();
   for(const auto&c:s.story_cards_){
    const auto image=c.image>=0&&size_t(c.image)<e.images.size()?e.images[size_t(c.image)].url:std::string{};
    cards.push_back({{"kind",int(c.kind)},{"paragraph",c.paragraph},{"continuation",c.continuation},{"feature",c.feature},{"title",c.title},{"lead",c.lead},{"image_index",c.image},{"image_url",image},{"image_identity",image.empty()?std::string{}:s.cache_.image_identity(image)},{"video",c.video},{"study_index",c.study_index},{"music_room",c.music_room}});
   }
   compositions.push_back({{"entry_id",e.id},{"preferred_image",e.preferred_image},{"explicit_story_media_only",e.explicit_story_media_only},{"cards",std::move(cards)}});
  }
  if(override_catalog&&(e.id=="wikipedia-1120399"||e.id=="wikipedia-2364191"||e.id=="workbook-11-04-kinect-per-xbox-360")){
   const int expected=e.id=="wikipedia-1120399"?2:e.id=="wikipedia-2364191"?7:4;std::set<int>matched;std::set<std::string>identities;
   for(size_t n=0;n<s.story_cards_.size();++n){const auto&c=s.story_cards_[n];if(c.feature>=0||c.paragraph<0||(c.kind!=Screen::StoryCard::narrative&&c.kind!=Screen::StoryCard::film))continue;
    const bool valid=c.image>=0&&c.image!=e.preferred_image&&size_t(c.image)<e.images.size()&&e.images[size_t(c.image)].story_paragraph==c.paragraph&&c.continuation.empty();
    if(!valid){std::fprintf(stderr,"Current catalogue explicit photo association failed: %s p%d image%d\n",e.id.c_str(),c.paragraph,c.image);media_probe_failed=true;}
    matched.insert(c.paragraph);if(c.image>=0)identities.insert(s.cache_.image_identity(e.images[size_t(c.image)].url));media_probes.push_back({{"entry_id",e.id},{"paragraph",c.paragraph},{"card",n},{"image_index",c.image},{"continuation",c.continuation},{"exact_association_pass",valid},{"image_url",c.image<0?"":e.images[size_t(c.image)].url},{"image_title",c.image<0?"":e.images[size_t(c.image)].title}});
   }
   if(int(matched.size())!=expected||int(identities.size())!=expected){std::fprintf(stderr,"Missing or repeated composed current paragraph images: %s %zu paragraphs/%zu distinct images/%d\n",e.id.c_str(),matched.size(),identities.size(),expected);media_probe_failed=true;}
   if(!media_probe_failed)std::printf("PASS actual composed %s: all%d independent narrative paragraphs use their explicit non-cover image.\n",e.id.c_str(),expected);
   if(e.id=="wikipedia-2364191"){
    // Two genuine packaged URL variants with identical SHA256. This is a
    // host-only identity fixture, never a factual image change to the article.
    const std::string cover_url="https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b9/Roberta_Williams_Adventure_Game_Fan_Fair_Tacoma_Washington_July_2024.jpg/1920px-Roberta_Williams_Adventure_Game_Fan_Fair_Tacoma_Washington_July_2024.jpg";
    const std::string alias_url=cover_url+"?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail";
    if(s.cache_.image_identity(cover_url)!=s.cache_.image_identity(alias_url)){std::fprintf(stderr,"Cover alias fixture is not backed by equal packaged identities\n");return false;}
    auto original=e;auto fixture=original;fixture.images[0].url=cover_url;fixture.images[0].story_paragraph=0;auto duplicate=fixture.images[0];duplicate.url=alias_url;fixture.images.insert(fixture.images.begin()+1,std::move(duplicate));s.catalog_.entries[entry]=std::move(fixture);s.prepare_story();
    const auto card=std::find_if(s.story_cards_.begin(),s.story_cards_.end(),[](const auto&c){return c.feature<0&&c.paragraph==0;});
    const bool pass=card!=s.story_cards_.end()&&card->image==2&&card->continuation.empty();s.catalog_.entries[entry]=std::move(original);s.prepare_story();
    if(!pass){std::fprintf(stderr,"Equal-pixel cover URL alias consumed the explicit paragraph-zero photograph\n");return false;}
    cover_alias_probe={{"entry_id",e.id},{"same_pixel_aliases",2},{"distinct_explicit_p0_image_preserved",pass},{"fixture_only",true}};
    std::printf("PASS actual composed cover SHA alias: both equal-pixel cover URLs skipped before matching p0; distinct paragraph illustration retained.\n");
   }
  }
  if(override_catalog&&e.id=="wikipedia-3467400"&&e.images.size()==1&&e.videos.empty()&&e.models.empty()&&e.editorial_features.empty()){
   std::vector<int>paragraphs;bool clean=e.images.size()==1&&e.videos.empty()&&e.models.empty()&&e.editorial_features.empty();
   for(const auto&c:s.story_cards_){if(c.kind==Screen::StoryCard::photograph||c.image>=0)clean=false;if(c.kind==Screen::StoryCard::narrative&&c.paragraph>=0){paragraphs.push_back(c.paragraph);paragraphs.insert(paragraphs.end(),c.continuation.begin(),c.continuation.end());}}
   clean=clean&&paragraphs.size()==e.body.size();for(size_t p=0;p<paragraphs.size();++p)if(paragraphs[p]!=int(p))clean=false;
   if(!clean){std::fprintf(stderr,"Cover-only actual Star Trader dropped/reordered text or reused cover\n");media_probe_failed=true;}
   cover_probe={{"entry_id",e.id},{"paragraph_count",paragraphs.size()},{"all_source_paragraphs_in_order",clean},{"cover_reused",!clean}};
   if(clean)std::printf("PASS actual composed cover-only %s: all%zu paragraphs retained in order, no cover recycled as a story image.\n",e.id.c_str(),paragraphs.size());
  }
  if(!scope.empty()&&scope.find(","+e.id+",")!=std::string::npos){
   const auto squash=[](std::string value){value.erase(std::remove_if(value.begin(),value.end(),[](unsigned char c){return std::isspace(c);}),value.end());return value;};
   std::vector<std::vector<int>>retained(1+e.editorial_features.size());
   for(size_t n=0;n<s.story_cards_.size();++n){const auto&card=s.story_cards_[n];if(card.paragraph<0||(card.kind!=Screen::StoryCard::narrative&&card.kind!=Screen::StoryCard::film))continue;
    const auto&body=card.feature<0?e.body:e.editorial_features[size_t(card.feature)].body;
    std::vector<int>paragraphs{card.paragraph};paragraphs.insert(paragraphs.end(),card.continuation.begin(),card.continuation.end());std::string source;
    for(int p:paragraphs){source+=body[size_t(p)];retained[size_t(card.feature+1)].push_back(p);}
    s.story_focus_=int(n);s.story_position_.snap(float(n));s.scroll_.snap(0);s.page_.clear();s.draw_detail();const auto&layout=s.story_text_[n];std::string rendered;
    for(const auto&row:layout.rows())if(!row.heading)rendered+=row.text;
    if(!layout.ready||squash(rendered)!=squash(source)||!card.lead.empty()){std::fprintf(stderr,"Scoped source prose lost/reordered/truncated: %s card%zu\n",e.id.c_str(),n);return false;}
    s.scroll_.snap(s.scroll_max_);s.page_.clear();s.draw_detail();
    scoped_probes.push_back({{"entry_id",e.id},{"feature",card.feature},{"feature_id",card.feature<0?"":e.editorial_features[size_t(card.feature)].id},{"card",n},{"paragraphs",paragraphs},{"heading",card.title},{"complete_source_layout",true},{"layout_rows",layout.rows().size()},{"scroll_extent",s.scroll_max_},{"image_index",card.image},{"image_url",card.image<0?"":e.images[size_t(card.image)].url},{"image_paragraph",card.image<0?-1:e.images[size_t(card.image)].story_paragraph},{"image_title",card.image<0?"":e.images[size_t(card.image)].title}});
   }
   for(size_t f=0;f<retained.size();++f){const auto&body=f?e.editorial_features[f-1].body:e.body;if(retained[f].size()!=body.size()){std::fprintf(stderr,"Scoped composition lost source paragraphs: %s feature%zu\n",e.id.c_str(),f);return false;}for(size_t p=0;p<body.size();++p)if(retained[f][p]!=int(p)){std::fprintf(stderr,"Scoped paragraph source order changed\n");return false;}}
   std::printf("PASS scoped actual composed %s: complete source wording/order retained through layout and scroll endpoint; main+%zu features.\n",e.id.c_str(),e.editorial_features.size());
  }
  for(size_t n=0;n<s.story_cards_.size();++n){const auto&c=s.story_cards_[n];if(c.paragraph<0||(c.kind!=Screen::StoryCard::narrative&&c.kind!=Screen::StoryCard::film))continue;const auto&body=c.feature>=0?e.editorial_features[size_t(c.feature)].body:e.body;size_t bytes=body[size_t(c.paragraph)].size();for(int p:c.continuation)bytes+=body[size_t(p)].size();if(bytes>=1000)candidates.push_back({entry,int(n),bytes,float(bytes)/(c.image>=0||c.kind==Screen::StoryCard::film?560:1440)});
   if(c.image<0&&c.kind==Screen::StoryCard::narrative){std::vector<int>paragraphs={c.paragraph};paragraphs.insert(paragraphs.end(),c.continuation.begin(),c.continuation.end());gaps.push_back({{"entry_id",e.id},{"title",e.title},{"feature",c.feature},{"feature_title",c.feature<0?"":e.editorial_features[size_t(c.feature)].title},{"card",n},{"heading",c.title},{"paragraphs",paragraphs},{"paragraph_count",paragraphs.size()},{"source_bytes",bytes}});}
  }
 }
 std::sort(gaps.begin(),gaps.end(),[](const auto&a,const auto&b){return a.at("source_bytes").template get<size_t>()>b.at("source_bytes").template get<size_t>();});
 const std::string gap_output=profile_output?profile_output:override_catalog?"build/research/story-text-profile/unillustrated-scenes-current.json":"build/research/story-text-profile/unillustrated-scenes.json";
 if(gap_output.rfind("build/research/",0)!=0||gap_output.find("..")!=std::string::npos)return false;
 hui::save::write_atomic(gap_output,nlohmann::json{{"scope","Actual composed narrative cards only: not Credits, films, galleries, music or studies."},{"catalog",frozen},{"catalog_entries",s.catalog_.entries.size()},{"explicit_catalog_override",override_catalog!=nullptr},{"count",gaps.size()},{"entries",gaps},{"current_explicit_media_probes",media_probes},{"current_cover_only_probe",cover_probe},{"current_cover_sha_alias_probe",cover_alias_probe},{"scoped_composed_narrative_checks",scoped_probes}}.dump(2));
 if(media_probe_failed)return false;
 if(composition_path){
  const std::string path=composition_path;if(path.rfind("build/research/",0)!=0||path.find("..")!=std::string::npos){std::fprintf(stderr,"Composition snapshot must remain in build/research\n");return false;}
  const auto result=hui::save::write_atomic(path,nlohmann::json{{"scope","Complete actual native prepared StoryCard state, original order and image identities; no synthetic fixtures."},{"entries",std::move(compositions)}}.dump());
  if(!result.empty()){std::fprintf(stderr,"Composition snapshot write failed: %s\n",result.c_str());return false;}
  std::printf("PASS actual native complete composition snapshot: %zu entries saved to %s\n",s.catalog_.entries.size(),path.c_str());
 }
 if(std::getenv("MUSEUM_COMPOSITION_ONLY")){std::puts("PASS scoped composition and complete source layout checks; historical CPU benchmark intentionally excluded.");return true;}
 std::sort(candidates.begin(),candidates.end(),[](const auto&a,const auto&b){return a.weight>b.weight;});std::set<size_t>seen;unsigned tested=0;
 for(const auto&candidate:candidates){if(!seen.insert(candidate.entry).second)continue;s.visible_={int(candidate.entry)};s.focus_=0;s.prepare_story();s.story_focus_=candidate.card;s.story_position_.snap(float(candidate.card));s.scroll_.snap(0);s.page_.clear();s.draw_detail();const float extent=s.scroll_max_;
  const auto&card=s.story_cards_[size_t(candidate.card)];const auto&entry=*s.current();const auto&body=card.feature>=0?entry.editorial_features[size_t(card.feature)].body:entry.body;const auto&headings=card.feature>=0?entry.editorial_features[size_t(card.feature)].story_headings:entry.story_headings;
  const bool media=card.image>=0||card.kind==Screen::StoryCard::film;const float size=media?26.f:34.f,width=media?560.f:1440.f,line=media?38.f:50.f;
  std::vector<NarrativeLayout::Row>expected;float cursor=0;
  const auto append=[&](const std::string&value,bool heading){auto lines=hui::ui::paragraph_lines(heading?s.fonts_.semibold:s.fonts_.regular,value,heading?size*1.12f:size,width,std::numeric_limits<int>::max());for(auto&text:lines.lines){expected.push_back({std::move(text),cursor,heading?size*1.12f:size,heading});cursor+=heading?line*1.15f:line;}};
  append(body[size_t(card.paragraph)],false);std::string previous=card.title;
  for(int p:card.continuation){cursor+=32;if(p<int(headings.size())&&!headings[size_t(p)].empty()&&headings[size_t(p)]!=previous){previous=headings[size_t(p)];append(previous,true);cursor+=12;}append(body[size_t(p)],false);}
  const auto&cached=s.story_text_[size_t(candidate.card)];const auto&rows=cached.rows();
  if(rows.size()!=expected.size()||std::abs(cached.bottom-cursor)>.01f){std::fprintf(stderr,"Narrative cache lost source rows/height\n");return false;}
  for(size_t row=0;row<rows.size();++row)if(rows[row].text!=expected[row].text||rows[row].heading!=expected[row].heading||rows[row].size!=expected[row].size||std::abs(rows[row].baseline-expected[row].baseline)>.01f){std::fprintf(stderr,"Narrative cache changed source order, wording, font or baseline\n");return false;}
  for(const auto fraction:{0.f,.5f,1.f}){s.scroll_.snap(extent*fraction);double sum=0,worst=0;size_t instances=0;for(int run=0;run<15;++run){s.page_.clear();const auto start=std::chrono::steady_clock::now();s.draw_detail();const auto ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();if(run>=5){sum+=ms;worst=std::max(worst,ms);}instances=s.page_.instances().size();}std::printf("Story text %s/card%d %.0f%%: %zu sourcebytes / mean%.3fms max%.3fms / %zu instances / scroll%.1f\n",s.current()->id.c_str(),candidate.card,fraction*100,candidate.bytes,sum/10,worst,instances,extent);}
  if(s.page_.instances().size()>=2000){std::fprintf(stderr,"Hidden narrative glyphs still generated\n");return false;}
  if(++tested>=10)break;
 }
 std::printf("PASS actualScreen text profile: %u distinct long composed narratives; CPU generation only, no GL/PS5 rate claim. Frozen source order/content unchanged.\n",tested);return tested==10;
}
}
