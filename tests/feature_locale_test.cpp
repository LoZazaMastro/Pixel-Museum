// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/catalog.hpp"
#include "core/save_file.hpp"
#include <cstdio>
#include <string>

int main(int argc,char**argv){
    if(argc!=2)return 2;
    museum::Catalog catalog;
    const std::string source=R"({"entries":[{"id":"parent","title":"Original","year":1989,"body":["Parent body"],"story_headings":["Parent heading"],"editorial_features":[{"id":"feature","title":"Feature","summary":"Summary","editorial_credit":"Credit","body":["First","Second"],"story_headings":["One","Two"],"images":[{"url":"https://example.org/photo.jpg","story_paragraph":1}],"sources":[{"url":"https://example.org/source","title":"Source"}]}]}]})";
    if(!catalog.parse(source))return 3;
    const auto original=catalog.entries.front();
    if(!catalog.set_locale(argv[1],"it")||!catalog.locale_error().empty())return 4;
    const auto&translated=catalog.entries.front();const auto&feature=translated.editorial_features.front();
    if(translated.title!=original.title||feature.title!="Approfondimento"||feature.body!=std::vector<std::string>{"Primo","Secondo"}||feature.story_headings!=std::vector<std::string>{"Uno","Due"}||feature.editorial_credit!="Credito")return 5;
    if(feature.image_indices!=original.editorial_features.front().image_indices||feature.sources.front().url!=original.editorial_features.front().sources.front().url||translated.images.front().story_paragraph!=1)return 6;
    if(!catalog.set_locale(argv[1],"de")||catalog.locale_error().empty())return 7;
    const auto&partial=catalog.entries.front().editorial_features.front();
    if(partial.title!="Vertiefung"||partial.body!=original.editorial_features.front().body)return 8;
    if(!catalog.set_locale(argv[1],"en"))return 9;
    const auto&reset=catalog.entries.front().editorial_features.front();const auto&english=original.editorial_features.front();
    if(reset.title!=english.title||reset.summary!=english.summary||reset.body!=english.body||reset.story_headings!=english.story_headings||reset.editorial_credit!=english.editorial_credit)return 10;
    if(catalog.set_locale(argv[1],"xx")||catalog.entries.front().editorial_features.front().body!=english.body)return 11;
    std::puts("PASS: independent feature localization, media indices, malformed paragraph fallback, language switching and exact English restoration");
}
