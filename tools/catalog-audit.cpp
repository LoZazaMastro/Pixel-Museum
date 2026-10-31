// Pixel Museum - Read-only audit of catalogue schema retention in the real parser.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/catalog.hpp"
#define JSON_NOEXCEPTION 1
#include "third_party/nlohmann/json.hpp"
#include <cstdio>
#include <cmath>
#include <string>
#include <unordered_map>
#include <array>
#include <unordered_set>
namespace {
nlohmann::json read_json(const char*path){
    FILE*f=std::fopen(path,"rb");if(!f)return {};
    std::fseek(f,0,SEEK_END);const long size=std::ftell(f);std::rewind(f);
    if(size<=0||size>32*1024*1024){std::fclose(f);return {};}
    std::string bytes(static_cast<std::size_t>(size),'\0');const auto count=std::fread(bytes.data(),1,bytes.size(),f);std::fclose(f);
    return count==bytes.size()?nlohmann::json::parse(bytes,nullptr,false):nlohmann::json{};
}
bool calendar_checks(const museum::Catalog&catalog,const nlohmann::json&json,const char*original_path){
    const auto fail=[](const std::string&message){std::fprintf(stderr,"Calendar audit failed: %s\n",message.c_str());return false;};
    const auto imported=read_json("content/expansion/calendar-features.json");
    if(!imported.is_object()||!imported.contains("entries")||!imported.contains("schedule"))return fail("published calendar import is missing");
    std::unordered_map<std::string,const nlohmann::json*> source_rows;
    for(const auto&row:imported["entries"])if(!source_rows.emplace(row.value("id",std::string{}),&row).second)return fail("duplicate imported feature id");
    if(source_rows.size()!=365||imported["schedule"].size()!=365)return fail("published calendar needs exactly365 unique features and schedule slots");
    std::unordered_map<std::string,nlohmann::json> revisions;
    for(const auto*agent:{"soundtrack","curation","native"}){
        const auto path=std::string("content/expansion/calendar-template-revisions-")+agent+".json";
        const auto document=read_json(path.c_str());
        if(!document.is_object()||!document.contains("entries"))return fail("missing researched revision document "+path);
        for(const auto&row:document["entries"])if(!revisions.emplace(row.value("id",std::string{}),row).second)return fail("duplicate researched revision");
    }
    if(revisions.size()!=53)return fail("all53 reviewed generic templates must have researched replacements");
    const auto identity_review=read_json("content/expansion/calendar-identity-corrections-02.json");
    std::unordered_map<std::string,const nlohmann::json*> identity_cases;
    if(identity_review.is_object()&&identity_review.contains("cases"))for(const auto&row:identity_review["cases"]){
        const auto id=row.value("edition_id",std::string{});
        if((id!="daily-05-21"&&id!="daily-08-30")||!identity_cases.emplace(id,&row).second)return fail("unreviewed or duplicate identity migration");
    }
    const auto identity03_review=read_json("content/expansion/calendar-identity-corrections-03.json");
    std::unordered_map<std::string,const nlohmann::json*> identity03_cases;
    const std::unordered_set<std::string> allowed03={"daily-02-02","daily-03-14","daily-03-17","daily-03-18",
        "daily-04-15","daily-04-17","daily-04-18","daily-04-22","daily-04-23","daily-05-02","daily-05-05",
        "daily-05-16","daily-05-20","daily-06-05","daily-07-02","daily-08-22","daily-08-25","daily-08-26",
        "daily-09-01","daily-09-04","daily-09-05","daily-09-06"};
    if(!identity03_review.is_object()||!identity03_review.contains("cases"))return fail("identity03 reviewed declaration missing");
    for(const auto&row:identity03_review["cases"]){
        if(row.value("correction_kind",std::string{})!="whole_subject_mapping")continue;
        const auto id=row.value("edition_id",std::string{});
        if(!allowed03.count(id)||!identity03_cases.emplace(id,&row).second)return fail("unreviewed identity03 migration");
    }
    if(identity03_cases.size()!=allowed03.size())return fail("incomplete identity03 reviewed case set");
    const auto identity03_media=read_json("content/expansion/daily-identity-media-03.json");
    const auto identity04_media=read_json("content/expansion/daily-identity-media-04.json");
    std::unordered_map<std::string,const nlohmann::json*> actual_rows;
    for(const auto&row:json["entries"])actual_rows.emplace(row.value("id",std::string{}),&row);
    std::unordered_set<std::string> narrative_targets;
    for(const std::string batch:{"06","07"}){
    const auto declaration="content/expansion/calendar-canonical-narratives-"+batch+".json";
    const auto narratives=read_json(declaration.c_str());
    const auto expected_count=batch=="06"?45u:12u;
    const auto expected_sha=batch=="06"?"f0a477b0cacda3ed917d7ace328db6e5eb58f80e6c6aaf241473c48257d21dab":"37d5df6064baba0a5a88be69741f05e7491ec1584a35d88d1eb9286437b5e289";
    if(!narratives.is_object()||!narratives.contains("cases")||narratives["cases"].size()!=expected_count)return fail("reviewed narratives declaration missing: "+batch);
    for(const auto&case_row:narratives["cases"]){
        const auto target=case_row.value("target_canonical_id",std::string{});
        const auto edition=case_row.value("edition_id",std::string{});
        if(!narrative_targets.insert(target).second||!actual_rows.count(target)||!actual_rows.count(edition))return fail("narratives duplicate or absent target");
        const auto&canonical=*actual_rows.at(target);const auto&daily=*actual_rows.at(edition);
        const auto&proposal=case_row["proposed_canonical"];
        if(canonical.value("calendar_only",false)||!canonical.contains("canonical_narrative_enrichment")||
           canonical["body"]!=proposal["body"]||canonical["story_headings"]!=proposal["story_headings"]||
           canonical.value("summary",std::string{})!=proposal.value("summary",std::string{})||
           daily["body"]!=case_row["expected_daily"]["body"]||daily["story_headings"]!=case_row["expected_daily"]["story_headings"])return fail(target+" loses reviewed canonical or archival narrative prose");
        const auto&marker=canonical["canonical_narrative_enrichment"];
        if(marker.value("source_daily_id",std::string{})!=edition||
           marker.value("review_file",std::string{})!=declaration||
           marker.value("reviewed_declaration_sha256",std::string{})!=expected_sha||
           !marker.value("original_daily_prose_preserved",false))return fail(target+" has an unexplained canonical prose exception");
        for(const auto&source:proposal["sources"]){
            bool found=false;for(const auto&actual:canonical["sources"])if(actual.value("url",std::string{})==source.value("url",std::string{}))found=true;
            if(!found)return fail(target+" loses a reviewed narrative source");
        }
        for(const char*field:{"images","videos","models"})if(canonical.contains(field))for(const auto&media:canonical[field])
            if(media.contains("story_paragraph"))return fail(target+" inherits an obsolete parent paragraph media binding");
    }
    }
    const std::array<int,12> months={31,28,31,30,31,30,31,31,30,31,30,31};
    std::unordered_set<std::string> ids;unsigned scheduled=0,normal=0,paragraphs=0;
    for(const auto&e:catalog.entries){
        ids.insert(e.id);
        if(!e.calendar_only){++normal;continue;}
        ++scheduled;
        if(e.calendar_month<1||e.calendar_month>12||e.calendar_day<1||e.calendar_day>months[static_cast<std::size_t>(e.calendar_month-1)])return fail(e.id+" has an invalid nonleap publication slot");
        const auto row=source_rows.find(e.id);if(row==source_rows.end())return fail(e.id+" is not a published imported edition");
        const auto&r=*row->second;
        const auto&actual=*actual_rows.at(e.id);
        const auto revised=revisions.find(e.id);
        const auto identity=identity_cases.find(e.id);
        const bool corrected=actual.contains("source_identity_correction");
        if(corrected&&actual["source_identity_correction"].value("review_file",std::string{})=="content/expansion/calendar-identity-corrections-03.json"){
            const auto found=identity03_cases.find(e.id);
            if(found==identity03_cases.end())return fail(e.id+" has no reviewed identity03 case");
            const auto&case_row=*found->second;const auto&receipt=actual["source_identity_correction"];
            const auto&part=case_row["proposed_partitions"][0];
            if(receipt.value("reviewed_declaration_sha256",std::string{})!="7eedf0930c06601d5fe7fd9fbdc3f4d819539313f2c99befded1dd223de0ba76"||
               receipt.value("edition_id",std::string{})!=e.id||
               receipt.value("old_canonical_id",std::string{})!=case_row.value("wrong_canonical_id",std::string{})||
               receipt.value("published_body_sha256",std::string{})!=case_row.value("source_body_sha256",std::string{})||
               receipt.value("published_headings_sha256",std::string{})!=case_row.value("source_headings_sha256",std::string{})||
               actual["body"]!=case_row["archived_published_edition"]["body"]||
               actual["story_headings"]!=case_row["archived_published_edition"]["story_headings"]||
               e.title!=part.value("title",std::string{})||e.year!=case_row.value("proposed_calendar_historical_year",0)||
               !e.linked_exhibit_id.empty()||!e.videos.empty()||!e.models.empty())return fail(e.id+" differs from the reviewed identity03 migration");
            if(!e.images.empty()){
                if(!identity03_media.is_object()||!identity03_media.contains("entries")||!actual.contains("identity_media_admission"))return fail(e.id+" has no explicit corrected-subject media admission");
                const auto&admission=actual["identity_media_admission"];
                const auto file=admission.value("review_file",std::string{});
                const bool fourth=file=="content/expansion/daily-identity-media-04.json";
                const auto expected_hash=fourth?"bac85c15d6207614ab08b87ec0198a07e6886f838cc82ec0f7eeafb0f8ace056":"8ad5bbead570444e40b70194a72ad38fdc6260ec40378ef85c0b5b369ceeb3fd";
                if((!fourth&&file!="content/expansion/daily-identity-media-03.json")||
                   admission.value("reviewed_batch_sha256",std::string{})!=expected_hash)return fail(e.id+" has unreviewed corrected-subject images");
                const nlohmann::json*approved=nullptr;
                const auto&media_batch=fourth?identity04_media:identity03_media;
                if(!media_batch.is_object()||!media_batch.contains("entries"))return fail("missing reviewed corrected-subject media batch");
                for(const auto&media:media_batch["entries"])if(media.value("entry_id",std::string{})==e.id)approved=&media;
                if(!approved||(*approved)["images"].size()!=e.images.size())return fail(e.id+" corrected-subject image count differs");
                for(std::size_t i=0;i<e.images.size();++i){const auto&image=(*approved)["images"][i];
                    if(e.images[i].url!=image.value("url",std::string{})||e.images[i].credit!=image.value("credit",std::string{})||e.images[i].license!=image.value("license",std::string{})||e.images[i].story_paragraph!=-1)return fail(e.id+" transfers an unrelated or remapped image");
                }
            }
        }else if(corrected){
            if(identity==identity_cases.end())return fail(e.id+" has no explicit reviewed identity case");
            const auto&case_row=*identity->second;const auto&receipt=actual["source_identity_correction"];
            if(receipt.value("review_file",std::string{})!="content/expansion/calendar-identity-corrections-02.json"||
               receipt.value("source_edition_id",std::string{})!=e.id||
               receipt.value("original_title",std::string{})!=r.value("title",std::string{})||
               receipt.value("original_year",0)!=r.value("year",0)||
               receipt.value("published_body_sha256",std::string{})!=case_row.value("expected_source_body_sha256",std::string{})||
               receipt.value("published_heading_sha256",std::string{})!=case_row.value("expected_source_heading_sha256",std::string{})||
               actual["body"]!=case_row["archived_published_edition"]["body"]||
               actual["story_headings"]!=case_row["archived_published_edition"]["story_headings"]||
               e.title!=case_row.value("corrected_title",std::string{})||e.year!=case_row.value("corrected_year",0)||
               e.linked_exhibit_id!=case_row.value("corrected_canonical_id",std::string{}))return fail(e.id+" differs from the reviewed identity migration");
        }
        const bool original_source=actual.contains("source_edition_restoration");
        const auto&expected=(original_source||revised==revisions.end())?r:revised->second;
        if(e.body.size()!=e.story_headings.size()||e.body.size()!=expected["body"].size())return fail(e.id+" loses a researched paragraph or chapter heading");
        const auto expected_title=revised==revisions.end()?expected.value("title",r.value("title",std::string{})):revised->second.value("title",r.value("title",std::string{}));
        if(e.subtitle!=r.value("subtitle",std::string{})||(!corrected&&e.year!=r.value("year",0)))return fail(e.id+" changes the historical anchor or source feature subtitle");
        if(!corrected&&e.title!=expected_title&&!actual.contains("calendar_link_provenance"))return fail(e.id+" has an unexplained subject rename");
        bool reviewed_biography_link=false;
        if(actual.contains("canonical_reference_restoration")){
            const auto&receipt=actual["canonical_reference_restoration"];
            const std::unordered_map<std::string,std::string> biographies={{"daily-02-22","workbook-02-22-ed-boon"},{"daily-02-24","workbook-02-24-sid-meier"},{"daily-03-08","wikipedia-292874"}};
            const auto expected_link=biographies.find(e.id);
            if(expected_link==biographies.end()||e.linked_exhibit_id!=expected_link->second||
               receipt.value("review_file",std::string{})!="content/expansion/calendar-prose-restorations-05.json"||
               receipt.value("reviewed_declaration_sha256",std::string{})!="7ff63f12f41a159a5e465a94bc8af497d5b20eb503f96e1443869f86a56d020b"||
               receipt.value("source_daily_id",std::string{})!=e.id||!receipt.value("daily_source_prose_preserved",false))return fail(e.id+" has an unreviewed biography destination");
            reviewed_biography_link=true;
        }
        if(!corrected&&!reviewed_biography_link&&e.linked_exhibit_id!=r.value("linked_exhibit_id",std::string{})&&!actual.contains("calendar_link_provenance"))return fail(e.id+" loses its historical identity without provenance");
        if(e.calendar_month!=r["calendar"].value("month",0)||e.calendar_day!=r["calendar"].value("day",0))return fail(e.id+" changes the original schedule");
        if(e.precision=="day"&&(!actual.contains("date_provenance")||!actual["date_provenance"].contains("source")||actual["date_provenance"]["source"].value("url",std::string{}).empty()))return fail(e.id+" asserts a release day without primary date evidence");
        for(std::size_t n=0;n<e.body.size();++n){if(e.body[n]!=expected["body"][n].get<std::string>()||e.story_headings[n]!=expected["story_headings"][n].get<std::string>())return fail(e.id+" loses reviewed original or revised English writing");++paragraphs;}
        if(!r.contains("provenance")||r["provenance"].value("source_origin",std::string{})!="editions.entries"||r["provenance"].value("source_record_id",std::string{}).empty())return fail(e.id+" lacks published-workbook provenance");
        if(e.editorial_credit.find("Playhub")==std::string::npos||e.editorial_credit.find("LoZazaMastro")==std::string::npos)return fail(e.id+" loses the original collection credit");
        bool original_credit=false;
        for(const auto&s:e.sources)if(s.url==r["provenance"].value("source_url",std::string{})&&!s.attribution.empty())original_credit=true;
        if(!original_credit)return fail(e.id+" lacks its attributed original source link");
    }
    if(scheduled!=365||normal+scheduled!=catalog.entries.size()||normal!=json["entries"].size()-365)return fail("normal chronology and scheduled features are not a complete disjoint partition");
    for(int month=1;month<=12;++month)for(int day=1;day<=months[static_cast<std::size_t>(month-1)];++day){
        char slot[8];std::snprintf(slot,sizeof(slot),"%02d-%02d",month,day);
        const auto expected=imported["schedule"].find(slot);if(expected==imported["schedule"].end()||!expected->is_string())return fail(std::string("missing schedule slot ")+slot);
        if(!ids.count(expected->get<std::string>()))return fail(std::string(slot)+" loses its published discovery record");
        const auto today=catalog.on_this_day(month,day);std::unordered_set<std::string> returned;
        for(int index:today){
            if(index<0||static_cast<std::size_t>(index)>=catalog.entries.size())return fail("Today returns an invalid index");
            const auto&e=catalog.entries[static_cast<std::size_t>(index)];
            if(!returned.insert(e.id).second)return fail("Today returns the same record twice");
            if(e.precision=="day"){
                if(e.month!=month||e.day!=day)return fail(e.id+" lets its editorial slot override a different verified historical date");
            }else if(!e.calendar_only||e.calendar_month!=month||e.calendar_day!=day)return fail(e.id+" invents an anniversary from year-only evidence");
            if(!e.linked_exhibit_id.empty()&&!ids.count(e.linked_exhibit_id))return fail(e.id+" links an exhibit absent from the collection");
            for(int other:today){const auto&historical=catalog.entries[static_cast<std::size_t>(other)];if(e.calendar_only&&!historical.calendar_only&&e.linked_exhibit_id==historical.id&&e.year==historical.year)return fail(e.id+" duplicates its linked historical record in Today");}
        }
    }
    const auto oct=catalog.on_this_day(10,20);
    if(oct.empty()||catalog.entries[static_cast<std::size_t>(oct.front())].id!="daily-10-20")return fail("October20 lacks the published Wonder feature");
    const auto&wonder=catalog.entries[static_cast<std::size_t>(oct.front())];
    if(wonder.title!="Super Mario Bros. Wonder"||wonder.linked_exhibit_id!="workbook-10-20-super-mario-bros-wonder"||wonder.body.size()!=7)return fail("October20 incorrectly uses the legacy Inscryption card or loses the full Wonder story");
    if(original_path){
        const auto original=read_json(original_path);if(!original.is_object()||!original.contains("editions"))return fail("original Playhub source is unreadable");
        unsigned originals=0;
        for(const auto&edition:original["editions"]["entries"]){
            if(!edition.value("published",false))continue;
            const auto&theme=edition["theme"];const auto slot=edition["anniversary"].value("date",std::string{});const auto match=source_rows.find("daily-"+slot);
            if(match==source_rows.end())return fail(slot+" was omitted from the original publication schedule");
            const auto&r=*match->second;std::vector<std::string> body={theme["intro"].value("en",std::string{})},headings={theme["title"].value("en",std::string{})};
            for(const auto&chapter:theme["chapters"]){const auto text=chapter["body"].value("en",std::string{});if(!text.empty()){body.push_back(text);headings.push_back(chapter["title"].value("en",std::string{}));}}
            if(r["body"]!=body||r["story_headings"]!=headings||r.value("title",std::string{})!=theme.value("subject",std::string{}))return fail(slot+" differs from the original published English edition");
            for(const auto&url:theme["sources"]){bool retained=false;for(const auto&reference:r["sources"])if(reference["url"]==url)retained=true;if(!retained)return fail(slot+" drops an original historical source");}
            ++originals;
        }
        if(originals!=365)return fail("original source does not contain365 published editions");
        std::puts("Original Playhub source:365 editions, full English text/headings and all source URLs match byte-for-byte.");
    }
    std::printf("Calendar:365 original schedule slots retained;53 researched alternatives preserved separately; %u current source paragraphs/headings, %u normal chronology records; known historical dates override editorial slots and linked Today duplicates are suppressed.\n",paragraphs,normal);
    return true;
}
}
int main(int argc,char**argv){
    if(argc<2||argc>3)return 2;
    FILE* file=std::fopen(argv[1],"rb");if(!file)return 3;
    std::fseek(file,0,SEEK_END);long size=std::ftell(file);std::rewind(file);
    if(size<=0||size>32*1024*1024){std::fclose(file);return 4;}
    std::string bytes(static_cast<std::size_t>(size),'\0');
    auto got=std::fread(bytes.data(),1,bytes.size(),file);std::fclose(file);if(got!=bytes.size())return 5;
    auto json=nlohmann::json::parse(bytes,nullptr,false);if(json.is_discarded())return 6;
    museum::Catalog catalog;if(!catalog.parse(bytes)){std::fprintf(stderr,"%s\n",catalog.error.c_str());return 7;}
    std::unordered_map<std::string,const museum::Entry*> loaded;
    for(const auto& e:catalog.entries)if(!loaded.emplace(e.id,&e).second){std::fprintf(stderr,"duplicate id %s\n",e.id.c_str());return 8;}
    unsigned sources=0,days=0,playlists=0,soundtrack_records=0;std::size_t words=0;
    std::unordered_set<std::string> soundtrack_ids;
    for(const auto& row:json["entries"]){
        const auto id=row.value("id",std::string{});auto it=loaded.find(id);
        if(it==loaded.end()){std::fprintf(stderr,"missing record %s\n",id.c_str());return 9;}
        const auto& e=*it->second;
        if(e.title!=row.value("title",std::string{})||e.year!=row.value("year",0)||e.sources.size()!=row["sources"].size()||e.body.size()!=row["body"].size())return 10;
        if(e.event_semantics!=row.value("event_semantics",std::string{})||e.editorial_credit!=row.value("editorial_credit",std::string{})||e.factual_note!=row.value("factual_note",std::string{}))return 14;
        if(e.calendar_only!=row.value("calendar_only",false)||e.linked_exhibit_id!=row.value("linked_exhibit_id",std::string{}))return 22;
        if(row.contains("calendar")&&(e.calendar_month!=row["calendar"].value("month",0)||e.calendar_day!=row["calendar"].value("day",0)))return 23;
        if(row.contains("story_headings")&&e.story_headings!=row["story_headings"].get<std::vector<std::string>>())return 24;
        if(row.contains("soundtrack")){
            const auto&p=row["soundtrack"];
            if(e.soundtrack.title!=p.value("title",std::string{})||e.soundtrack.composer!=p.value("composer",std::string{})||e.soundtrack.curator_note!=p.value("curator_note",std::string{})||e.soundtrack.tracks.size()!=p["tracks"].size())return 34;
            ++playlists;
            for(std::size_t n=0;n<e.soundtrack.tracks.size();++n){
                const auto&track=e.soundtrack.tracks[n];const auto&original=p["tracks"][n];
                if(track.youtube_id!=original.value("youtube_id",std::string{})||track.title!=original.value("title",std::string{})||track.creator!=original.value("creator",std::string{})||track.source_page!=original.value("source_page",std::string{})||track.url!=original.value("url",std::string{}))return 35;
                if(!original.value("official_uploader_verified",false)||original.value("channel_url",std::string{}).empty())return 36;
                soundtrack_ids.insert(track.youtube_id);++soundtrack_records;
            }
        }else if(!e.soundtrack.tracks.empty())return 37;
        if(row.contains("date")){
            const auto& d=row["date"];
            if(e.month!=d.value("month",0)||e.day!=d.value("day",0)||e.precision!=d.value("precision",std::string{})||e.region!=d.value("region",std::string{}))return 11;
        }
        for(std::size_t i=0;i<e.sources.size();++i){const auto& s=row["sources"][i];if(e.sources[i].url!=s.value("url",std::string{})||e.sources[i].publisher!=s.value("publisher",std::string{})||e.sources[i].title!=s.value("title",std::string{})||e.sources[i].license!=s.value("license",std::string{})||e.sources[i].attribution!=s.value("attribution",std::string{}))return 12;}
        sources+=static_cast<unsigned>(e.sources.size());if(e.precision=="day")++days;
        for(std::size_t i=0;i<e.body.size();++i){if(e.body[i]!=row["body"][i].get<std::string>())return 15;words+=e.body[i].size();}
    }
    std::printf("Real parser retained %zu entries, %u sources, %u day-precision dates, %zu body bytes. Input %zu bytes.\n",loaded.size(),sources,days,words,bytes.size());
    std::printf("Soundtrack parser retained %u playlist records / %u track records / %zu unique official video IDs with titles, composers and source credits. Playback is not tested by this metadata audit.\n",playlists,soundtrack_records,soundtrack_ids.size());
    if(loaded.size()!=json["entries"].size())return 13;
    if(!calendar_checks(catalog,json,argc==3?argv[2]:nullptr))return 25;
    // Exercise bounds with real schema data and retain the previously loaded
    // collection if an oversized update is rejected.
    auto sample=json["entries"][0];sample["editorial_credit"]="Editorial fixture";
    sample["sources"][0]["license"]="CC BY-SA 4.0";sample["sources"][0]["attribution"]="Source fixture";
    nlohmann::json limit={{"entries",nlohmann::json::array()}};
    // A daily record can carry a large research/provenance inventory. The
    // count fixture intentionally excludes it so it cannot hit the byte cap.
    nlohmann::json compact={{"title","Count boundary fixture"},{"year",2000},{"editorial_credit",sample["editorial_credit"]},{"sources",nlohmann::json::array({sample["sources"][0]})},{"body",nlohmann::json::array()},{"summary",""}};
    for(int i=0;i<5000;++i){auto row=compact;row["id"]="fixture-"+std::to_string(i);limit["entries"].push_back(std::move(row));}
    // Use compact rows here, so the count boundary is tested independently of
    // the byte boundary and does not allocate thousands of full essays.
    for(auto& row:limit["entries"]){row["body"]=nlohmann::json::array();row["summary"]="";}
    museum::Catalog bounded;if(!bounded.parse(limit.dump())||bounded.entries.size()!=5000)return 16;
    const auto& credited=bounded.entries[0];if(credited.editorial_credit!="Editorial fixture"||credited.sources[0].license!="CC BY-SA 4.0"||credited.sources[0].attribution!="Source fixture")return 17;
    limit["entries"].push_back(sample);if(bounded.parse(limit.dump())||bounded.entries.size()!=5000||bounded.error.find("5,000")==std::string::npos)return 18;
    std::string too_big((16u<<20)+1,' ');if(bounded.parse(too_big)||bounded.error.find("16 MiB")==std::string::npos)return 19;
    std::puts("5,000-record acceptance, explicit count/byte rejection and source licence retention pass.");
    sample["models"]=nlohmann::json::array({{{"url","https://fixture.invalid/console.glb"},{"initial_tilt",.8},{"initial_angle",1.3},{"initial_zoom",1.4}},{{"url","https://fixture.invalid/default.glb"}},{{"url","https://fixture.invalid/clamped.glb"},{"initial_tilt",20.},{"initial_zoom",9.}},{{"url","https://fixture.invalid/minimum.glb"},{"initial_zoom",.1}}});
    if(!bounded.parse(nlohmann::json{{"entries",nlohmann::json::array({sample})}}.dump()))return 20;
    const auto& models=bounded.entries[0].models;
    if(models.size()!=4||std::abs(models[0].initial_tilt-.8f)>.0001f||std::abs(models[0].initial_angle-1.3f)>.0001f||std::abs(models[1].initial_tilt-.13f)>.0001f||models[1].initial_angle!=0||models[2].initial_tilt!=1.2f||std::abs(models[0].initial_zoom-1.4f)>.0001f||models[1].initial_zoom!=1.f||models[2].initial_zoom!=2.f||models[3].initial_zoom!=.5f)return 21;
    std::puts("Model initial angle/tilt/zoom, defaults and clamps pass.");
    const nlohmann::json dated={{"id","historical"},{"title","Historical game"},{"year",2023},{"date",{{"month",10},{"day",20},{"precision","day"}}}};
    auto scheduled=dated;scheduled["id"]="scheduled";scheduled["calendar_only"]=true;scheduled["calendar"]={{"month",10},{"day",20}};scheduled["date"]={{"month",0},{"day",0},{"precision","year"}};scheduled["linked_exhibit_id"]="historical";
    auto imprecise=dated;imprecise["id"]="year-only";imprecise["title"]="Year-only evidence";imprecise["date"]["precision"]="year";
    auto other=dated;other["id"]="other";other["title"]="Another literal anniversary";
    museum::Catalog calendar_fixture;
    if(!calendar_fixture.parse(nlohmann::json{{"entries",nlohmann::json::array({dated,scheduled,imprecise,other})}}.dump()))return 26;
    const auto today=calendar_fixture.on_this_day(10,20);
    if(today.size()!=2||calendar_fixture.entries[static_cast<std::size_t>(today[0])].id!="scheduled"||calendar_fixture.entries[static_cast<std::size_t>(today[1])].id!="other"){
        std::fputs("Calendar negative fixture failed: year-only evidence must not become a literal anniversary and linked historical records must not duplicate the scheduled story.\n",stderr);return 27;
    }
    if(!calendar_fixture.on_this_day(10,19).empty())return 28;
    std::puts("Calendar negative fixture: editorial date stays separate, year-only evidence excluded, linked duplicate suppressed, different day remains empty.");
    // A real regional launch date must win over a workbook's scheduling date.
    auto regional=dated;regional["id"]="gta-uk";regional["title"]="Regional release";regional["year"]=2009;regional["date"]={{"month",3},{"day",20},{"precision","day"},{"region","United Kingdom"}};
    auto misplaced=regional;misplaced["id"]="scheduled-gta";misplaced["calendar_only"]=true;misplaced["calendar"]={{"month",3},{"day",17}};misplaced["linked_exhibit_id"]="gta-uk";
    if(!calendar_fixture.parse(nlohmann::json{{"entries",nlohmann::json::array({regional,misplaced})}}.dump()))return 29;
    if(!calendar_fixture.on_this_day(3,17).empty())return 30;
    const auto release_day=calendar_fixture.on_this_day(3,20);
    if(release_day.size()!=1||calendar_fixture.entries[static_cast<std::size_t>(release_day[0])].day!=20)return 31;
    auto independent=misplaced;independent["id"]="independent-dated";independent["linked_exhibit_id"]="";
    if(!calendar_fixture.parse(nlohmann::json{{"entries",nlohmann::json::array({independent})}}.dump())||calendar_fixture.on_this_day(3,20).size()!=1||!calendar_fixture.on_this_day(3,17).empty())return 32;
    auto discovery=misplaced;discovery["id"]="undated-discovery";discovery["date"]={{"month",0},{"day",0},{"precision","year"}};discovery["linked_exhibit_id"]="";
    if(!calendar_fixture.parse(nlohmann::json{{"entries",nlohmann::json::array({discovery})}}.dump())||calendar_fixture.on_this_day(3,17).size()!=1||!calendar_fixture.on_this_day(3,20).empty())return 33;
    std::puts("Today adversarial fixtures: March17 schedule cannot override verified March20; canonical and scheduled copies deduplicate on the actual day; independent dated stories remain discoverable; undated editorial discoveries keep their own slot.");
    auto february=dated;february["id"]="february";february["date"]={{"month",2},{"day",7},{"precision","day"}};
    auto march=dated;march["id"]="march";march["date"]={{"month",3},{"day",13},{"precision","day"}};
    auto month=dated;month["id"]="month-only";month["date"]={{"month",2},{"day",31},{"precision","month"}};
    auto unknown=dated;unknown["id"]="unknown";unknown["date"]={{"month",12},{"day",25},{"precision","year"}};
    auto late=march;late["id"]="late";late["date"]["day"]=20;late["calendar_only"]=true;late["calendar"]={{"month",1},{"day",1}};
    if(!calendar_fixture.parse(nlohmann::json{{"entries",nlohmann::json::array({march,late,february,unknown,month})}}.dump()))return 38;
    const std::array<const char*,5> chronological={"unknown","month-only","february","march","late"};
    for(std::size_t i=0;i<chronological.size();++i)if(calendar_fixture.entries[i].id!=chronological[i])return 39;
    std::puts("Chronology: verified dates sort within each year; month/year-only precision and editorial slots never invent an exact day.");
    return 0;
}
