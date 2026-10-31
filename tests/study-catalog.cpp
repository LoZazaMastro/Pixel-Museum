// Public catalog entries must open a real study through the production factory.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include "museum/study_catalog.hpp"
#include "museum/study_controls.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <set>
int main(){
    std::set<std::string> ids;unsigned missing=0;
    hui::ui::Feedback feedback;
    for(const auto&info:museum::study_catalog()){
        assert(ids.insert(info.id).second&&!info.entry_id.empty()&&!info.explanation.empty());
        auto study=museum::make_study(info.id);
        if(!study){std::printf("MISSING public study factory: %s\n",info.id.c_str());++missing;continue;}
        assert(!museum::study_controls(info.id,true).empty());
        hui::InputFrame input;input.connected=true;
        for(unsigned n=0;n<120;++n){study->handle(input,feedback);study->update(1.f/120);}
        study->reset();std::printf("PASS public study: %s\n",info.id.c_str());
    }
    assert(ids.size()==19);assert(!ids.count("momentum")&&!museum::make_study("momentum"));
    std::printf("Public catalog: %zu entries / %u missing factories\n",ids.size(),missing);
    return missing?1:0;
}
