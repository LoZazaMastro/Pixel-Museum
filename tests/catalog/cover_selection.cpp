// Focused parser regression: no renderer, network or production catalogue writes.
#include "museum/catalog.hpp"
#include <fstream>
#include <sstream>
#include <cstdio>
#include <cstdlib>
static void require(bool ok,const char*message){if(!ok){std::fprintf(stderr,"FAIL %s\n",message);std::exit(1);}}
int main(int argc,char**argv){
    require(argc==2,"fixture argument");std::ifstream file(argv[1]);std::ostringstream bytes;bytes<<file.rdbuf();museum::Catalog catalog;require(catalog.parse(bytes.str()),"real Catalog::parse accepts fixture");
    for(const char*id:{"cover-art","cover-role","kind-cover","role-cover"}){
        const auto*e=catalog.find_entry(id);require(e&&e->preferred_image==0,"small semantic cover wins over large gameplay");require(e->images.size()==3,"all photographs retained");require(e->images[0].story_paragraph==-1,"selected cover reserved as hero");require(e->images[1].story_paragraph==0&&e->images[1].url=="https://example.org/gameplay.jpg","first paragraph keeps its real gameplay image");require(e->images[2].story_paragraph==1,"later narrative image retained");
    }
    const auto*explicit_game=catalog.find_entry("explicit-game");require(explicit_game&&explicit_game->preferred_image==2,"explicit game override preserved");require(explicit_game->images[0].story_paragraph==0,"unselected image placement unchanged");
    const auto*explicit_cover=catalog.find_entry("explicit-cover");require(explicit_cover&&explicit_cover->preferred_image==0&&explicit_cover->images[0].story_paragraph==-1,"explicit cover selection preserved and reserved");
    const auto*hardware=catalog.find_entry("hardware");require(hardware&&hardware->preferred_image==1&&hardware->images[0].story_paragraph==0,"hardware keeps size auto-selection and photo placement");
    const auto*organization=catalog.find_entry("organization");require(organization&&organization->preferred_image==1&&organization->images[0].story_paragraph==0,"nongame selection unchanged");
    const auto*ordinary=catalog.find_entry("ordinary-game");require(ordinary&&ordinary->preferred_image==1&&ordinary->images[0].story_paragraph==0,"unflagged games retain existing size fallback");
    const auto*hardware_override=catalog.find_entry("hardware-override");require(hardware_override&&hardware_override->preferred_image==0&&hardware_override->images[0].story_paragraph==0,"explicit hardware override untouched");
    std::puts("PASS semantic game covers, explicit overrides, hardware/nongame fallback, paragraph0 gameplay and no image loss");
}
