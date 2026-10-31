#include "museum/localization.hpp"
#include "museum/study_catalog.hpp"
#include "museum/catalog.hpp"
#include "ui/fonts.hpp"
#include "ui/glyphs.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
static std::string read(const std::string&p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
int main(){
    using namespace hui::ui;
    text_resolver=&museum::i18n::tr;
    install_inline_controls();
    hui::gfx::Font face;assert(face.load(read("assets/fonts/inter-regular.huifont")));FontRef font{&face,0};
    hui::gfx::Font semibold,mono;assert(semibold.load(read("assets/fonts/inter-semibold.huifont")));assert(mono.load(read("assets/fonts/dejavu-sans-mono.huifont")));
    unsigned checks=0;
    const char*coins[]={"MONETE 7   PUNTI 1200","MONEDAS 7   PUNTOS 1200","PIÈCES 7   SCORE 1200","MÜNZEN 7   PUNKTE 1200"};
    const char*checkpoint[]={"CHECKPOINT SALVATO","PUNTO DE CONTROL GUARDADO","POINT DE CONTRÔLE SAUVEGARDÉ","KONTROLLPUNKT GESPEICHERT"};
    const char*dates[]={"23 settembre 1889","23 de septiembre de 1889","23 septembre 1889","23. September 1889"};
    unsigned locale=0;
    for(const char*l:{"it","es","fr","de"}){
        assert(museum::i18n::load(".",l));char result[2048];
        for(const auto&study:museum::study_catalog())if(study.explanation.find('{')!=std::string::npos){
            const auto translated=resolve_text(study.explanation);const auto lines=paragraph_lines(font,study.explanation,21,548,999);std::string joined;for(const auto&line:lines.lines){if(!joined.empty())joined+=' ';joined+=line;assert(font.measure(line,21)<=548);}
            assert(joined==translated);++checks;
        }
        assert(font.measure("{cross}",21)==button_width(Button::cross,23.1f)+8);
        assert(font.measure("{unknown}",21)==face.measure("{unknown}",21));
        hui::gfx::DrawList symbol;const float symbol_width=text(symbol,font,"{touchpad}",0,30,21,hui::gfx::Color::rgb(0x111111));assert(symbol_width==font.measure("{touchpad}",21));assert(!symbol.instances().empty());
        museum::Entry event;event.year=1889;event.month=9;event.day=23;event.precision="day";assert(museum::date_label(event)==dates[locale]);event.precision="year";assert(museum::date_label(event)=="1889");
        format(result,"COINS %d   SCORE %d",7,1200);assert(result==std::string(coins[locale]));
        format(result,"%s   FALLS %d","CHECKPOINT SAVED",3);assert(std::string(result).starts_with(checkpoint[locale]));assert(std::string(result).ends_with("3"));
        format(result,"Volume %d %%",70);assert(std::string(result).find("70 %")!=std::string::npos);
        format(result,"Sensitivity  %.2fx",1.25);assert(std::string(result).find("1.25x")!=std::string::npos);
        for(const auto&study:museum::study_catalog()){
            assert(resolve_text(study.title)!=study.title);assert(resolve_text(study.explanation)!=study.explanation);
            assert(paragraph_lines(font,study.title,22,478,99).lines.size()<=2);
            auto lines=paragraph_lines(font,study.explanation,21,548,999);assert(!lines.truncated);
            std::cout<<l<<" / "<<study.id<<" / full description lines "<<lines.lines.size()<<"\n";++checks;
        }
        for(size_t n=0;n<museum::study_catalog().size();++n)for(float focus:{0.f,1.f}){
            char number[32];std::snprintf(number,sizeof(number),"%02d",int(n)+1);std::vector<hui::gfx::GlyphQuad>digits;mono.layout(number,610,0,16,hui::gfx::Align::right,digits);
            float digit_left=610;for(const auto&q:digits)digit_left=std::min(digit_left,q.x0);
            const float available=610-mono.measure(number,16)-32-110;const auto title=resolve_text(museum::study_catalog()[n].title);float size=23+6*focus;while(semibold.measure(title,size)>available&&size>22)--size;
            auto lines=semibold.measure(title,size)>available?semibold.wrap(title,22,available):std::vector<std::string>{std::string(title)};if(lines.size()>1)size=22;assert(lines.size()<=2);
            for(const auto&line:lines){std::vector<hui::gfx::GlyphQuad>quads;semibold.layout(line,110,0,size,hui::gfx::Align::left,quads);for(const auto&q:quads)assert(digit_left-q.x1>=20);}
            ++checks;
        }
        for(const char*message:{"Experience complete","Level complete","Exit experience","Choose surface","Restart chamber","A cube beyond the wall","Build speed, then redirect it"}){assert(resolve_text(message)!=message);assert(font.measure(message,30)<1200);++checks;}
        for(const char*message:{"Both programs passed. Try swapping rules in the middle of a falling pattern.","Catch each light. Swap programs to make the same contact a mistake.","Let eight lights pass untouched. Swap back to make contact useful.","Three briefs passed. A useful design balances what it can show with what it can afford.","Use light level 3 or 4 and motion level 2 or more. Stay within 100 design units.","Use motion level 3 or 4 and at least four shades. Stay within 100 design units.","Keep four shades and motion level 2 or more, using no more than 58 design units.","The route is complete. Rest, walking and running share one continuing musical clock.","The flag is reached. Some lights remain along the route.","Rest: the phrase leaves space. Start walking to add notes without restarting the clock.","Walking adds a second pulse. Run, then jump across the gaps.","Running adds a quicker subdivision. The phrase follows your action, keeping its place in the bar.","Three flags reached. Compare the pale trace with your next combination of settings.","Reach three flags. Compare the pale trace of a landing with your next attempt.","Change the outline, then look at the small preview. Does the shape still read? Four shades must carry both an edge and the space beside it."}){
            const auto lines=paragraph_lines(font,message,17,220,99);assert(!lines.truncated);std::cout<<l<<" panel "<<lines.lines.size()<<" / "<<message<<"\n";assert(lines.lines.size()*22<=230);++checks;
        }
        ++locale;
    }
    const std::string root="build/ui-format-invalid";std::filesystem::create_directories(root+"/content/ui-locales");
    for(const char*bad:{"%s","%zu","%d %d","%n"}){
        std::ofstream out(root+"/content/ui-locales/de.json");out<<"{\"locale\":\"de\",\"strings\":{\"Continue\":\"Weiter\",\"COINS %d\":\""<<bad<<"\"}}";out.close();
        assert(!museum::i18n::load(root,"de"));assert(museum::i18n::locale()=="en");assert(resolve_text("Continue")=="Continue");++checks;
    }
    std::ofstream bad(root+"/content/ui-locales/de.json");bad<<"{\"locale\":\"de\",\"strings\":{\"Use {cross}\":\"Nutze {square}\"}}";bad.close();assert(!museum::i18n::load(root,"de"));assert(museum::i18n::locale()=="en");++checks;
    std::cout<<"PASS "<<checks<<" causal localization checks; four languages; no changing-value fallback\n";
}
