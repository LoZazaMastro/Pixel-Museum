// Actual Screen preference restoration, independent of parser-only fixtures.
#pragma once
namespace museum {
inline bool ScreenInspection::verify_catalog_aliases(Screen&s){
 const auto require=[](bool pass,const char*message){if(!pass)std::fprintf(stderr,"Saved alias check failed: %s\n",message);return pass;};
 const std::string data=s.data_,initial=s.initial_exhibit_;auto original=std::move(s.catalog_);
 const auto restore=[&]{s.catalog_=std::move(original);s.data_=data;s.initial_exhibit_=initial;};
 const char*fixture=R"({"entries":[{"id":"famicom","title":"Family Computer","year":1983},{"id":"psp","title":"PlayStation Portable","year":2004}],"entry_aliases":{"nes":"famicom","workbook-05-13-playstation-portable-psp":"psp","legacy-nes":"nes","cycle-a":"cycle-b","cycle-b":"cycle-a","dangling":"missing"}})";
 if(!require(s.catalog_.parse(fixture),"fixture catalogue loads")){restore();return false;}
 s.data_="build/catalog-alias-preferences";hui::save::ensure_directory(s.data_);
 for(const auto&test:std::array<std::pair<const char*,const char*>,7>{{{"nes","famicom"},{"legacy-nes","famicom"},{"workbook-05-13-playstation-portable-psp","psp"},{"psp","psp"},{"cycle-a","keep-current"},{"dangling","keep-current"},{"missing","keep-current"}}}){
  s.initial_exhibit_="keep-current";
  const auto preferences=nlohmann::json{{"exhibit",test.first}}.dump();
  if(!require(hui::save::write_atomic(s.data_+"/preferences.json",preferences).empty(),"fixture preferences persist")){restore();return false;}
  s.load_settings();
  if(!require(s.initial_exhibit_==test.second,"legacy saved ID canonicalizes or safely retains current selection")){restore();return false;}
  if(!require(s.catalog_.entries.size()==2,"restoring preferences does not add duplicate timeline stops")){restore();return false;}
 }
 restore();std::puts("PASS actualScreen saved aliases: NES/PSP/direct/chained IDs restore canonical exhibits; cycle/dangling/unknown preserve current selection; timeline count unchanged.");return true;
}
}
