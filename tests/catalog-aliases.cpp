// Retired saved IDs resolve without creating or replacing timeline entries.
#include "museum/catalog.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cassert>
#include <cstdio>
using Json=nlohmann::json;
int main(){
 Json entries=Json::array({{{"id","famicom"},{"title","Famicom"},{"year",1983}},
                          {{"id","psp"},{"title","PlayStation Portable"},{"year",2004}},
                          {{"id","actual"},{"title","Real entry takes precedence"},{"year",1990}}});
 Json aliases={{"nes","famicom"},{"workbook-05-13-playstation-portable-psp","psp"},
               {"chain","nes"},{"actual","psp"},{"self","self"},{"cycle-a","cycle-b"},
               {"cycle-b","cycle-a"},{"dangling","missing"},{"bad-number",3},{"bad-bool",true},
               {"bad-empty",""},{"","famicom"},{std::string(193,'x'),"psp"},{"long-target",std::string(193,'y')},
               {"nul",std::string("psp\0x",5)}};
 for(unsigned n=0;n<32;++n)aliases["hop-"+std::to_string(n)]=n==31?"psp":"hop-"+std::to_string(n+1);
 aliases["one-too-many"]="hop-0";
 museum::Catalog catalog;
 assert(catalog.parse(Json{{"entries",entries},{"entry_aliases",aliases},{"initial_id","chain"}}.dump()));
 assert(catalog.entries.size()==3&&catalog.initial_id=="famicom");
 assert(catalog.resolve_entry_id("nes")=="famicom"&&catalog.resolve_entry_id("chain")=="famicom");
 assert(catalog.resolve_entry_id("workbook-05-13-playstation-portable-psp")=="psp");
 assert(catalog.find_entry("nes")&&catalog.find_entry("nes")->id=="famicom");
 assert(catalog.find_entry("actual")->id=="actual");
 assert(catalog.resolve_entry_id("hop-0")=="psp"&&catalog.resolve_entry_id("one-too-many").empty());
 for(const char*id:{"self","cycle-a","cycle-b","dangling","bad-number","bad-bool","bad-empty","long-target","nul",""})assert(catalog.resolve_entry_id(id).empty()&&!catalog.find_entry(id));
 assert(catalog.resolve_entry_id(std::string(193,'x')).empty());
 assert(!catalog.parse("{broken")&&catalog.resolve_entry_id("nes")=="famicom"&&catalog.entries.size()==3);
 assert(catalog.parse(Json{{"entries",entries}}.dump())&&catalog.resolve_entry_id("nes").empty());
 Json boundary=Json::object();for(unsigned n=0;n<museum::kEntryAliasLimit;++n)boundary["alias-"+std::to_string(n)]="psp";
 assert(catalog.parse(Json{{"entries",entries},{"entry_aliases",boundary}}.dump()));
 assert(catalog.resolve_entry_id("alias-0")=="psp"&&catalog.resolve_entry_id("alias-4095")=="psp");
 boundary["overflow"]="psp";
 assert(catalog.parse(Json{{"entries",entries},{"entry_aliases",boundary}}.dump()));
 assert(catalog.resolve_entry_id("alias-0").empty()&&catalog.resolve_entry_id("overflow").empty()&&catalog.entries.size()==3);
 assert(catalog.parse(Json{{"entries",entries},{"entry_aliases",Json::array({"nes","famicom"})}}.dump())&&catalog.resolve_entry_id("nes").empty());
 std::puts("Catalog aliases PASS: canonical lookup/initial ID, actual-entry precedence, exact32hop/4096record bounds, cycles/dangling/malformed/oversized rejection, reload and failed-parse preservation; no duplicate timeline entries.");
}
