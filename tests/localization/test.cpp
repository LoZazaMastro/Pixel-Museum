#include "museum/catalog.hpp"
#include "museum/localization.hpp"
#include "core/save_file.hpp"
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <array>
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);std::abort();}++checks;}while(0)
int main(int argc,char**argv){int checks=0;const std::string root=argc==2?argv[1]:".";museum::Catalog c;CHECK(c.load(root+"/content/catalog.json"));const auto original=c.entries;CHECK(original.size()>1000);
for(const char*locale:{"it","es","fr","de","en"}){CHECK(c.set_locale(root,locale));CHECK(c.entries.size()==original.size());for(size_t i=0;i<original.size();++i){const auto&a=original[i];const auto&b=c.entries[i];CHECK(a.id==b.id&&a.year==b.year&&a.month==b.month&&a.day==b.day);CHECK(a.body.size()==b.body.size());CHECK(a.images.size()==b.images.size()&&a.sources.size()==b.sources.size()&&a.models.size()==b.models.size());}}
CHECK(!c.set_locale(root,"../../bad"));CHECK(c.entries[0].title==original[0].title);CHECK(c.locale()=="en");
for(const char*l:{"it","es","fr","de"}){CHECK(museum::i18n::load(root,l));CHECK(museum::i18n::locale()==l);CHECK(museum::i18n::tr("Options")!="");CHECK(museum::i18n::tr("Untranslated source title")=="Untranslated source title");}
CHECK(museum::i18n::load(root,"en"));CHECK(museum::i18n::tr("Back")=="Back");CHECK(!museum::i18n::load(root,"../bad"));CHECK(museum::i18n::locale()=="en");
// The invitation previews any focused option without committing a locale or
// inheriting the previously saved language. Compare with real dictionaries.
const std::array<const char*,5> language_options={"en","it","es","fr","de"};
std::array<std::string,5> invitations;
for(size_t n=0;n<language_options.size();++n){CHECK(museum::i18n::load(root,language_options[n]));invitations[n]=museum::i18n::tr("Choose your language.");}
for(const char*saved:language_options){CHECK(museum::i18n::load(root,saved));for(int focus=0;focus<5;++focus){CHECK(museum::i18n::language_choice_heading(focus)==invitations[size_t(focus)]);CHECK(museum::i18n::locale()==saved);}}
CHECK(museum::i18n::language_choice_heading(-1)==invitations[0]);CHECK(museum::i18n::language_choice_heading(5)==invitations[0]);
const std::string tmp="build/localization-malformed";std::filesystem::create_directories(tmp+"/content/locales");std::ofstream(tmp+"/content/locales/it.json")<<"{\"locale\":\"it\",\"entries\":{\""+original[0].id+"\":{\"body\":[\"wrong paragraph count\"],\"title\":42}}}";CHECK(c.set_locale(tmp,"it"));CHECK(c.entries[0].title==original[0].title);CHECK(c.entries[0].body==original[0].body);CHECK(!c.locale_error().empty());
std::printf("Localization checks passed: %d assertions / %zu exhibits / UTF-8 five-language UI\n",checks,original.size());}
