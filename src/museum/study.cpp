// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include "museum/study_workshops.hpp"
#include "museum/study_city_system.hpp"
namespace museum {
std::unique_ptr<Study> make_study(const std::string&key){
    if(auto result=make_study_arcade(key))return result;
    if(auto result=make_study_motion(key))return result;
    if(auto result=make_study_workshops(key))return result;
    if(auto result=make_study_city_system(key))return result;
    return make_study_space(key);
}
}
