#pragma once
#include "third_party/nlohmann/json.hpp"
#include <algorithm>
#include <cmath>
namespace museum {
struct VolumePreferences {
    float master=1.f,sfx=1.f,music=.48f,culture=1.f;
    float pad=1.f;
    bool culture_on_pad=false;
    static float value(const nlohmann::json&j,const char*key,float fallback){
        const auto found=j.find(key);
        if(found==j.end()||!found->is_number())return fallback;
        const float v=found->get<float>();return std::isfinite(v)?std::clamp(v,0.f,1.f):fallback;
    }
    static VolumePreferences load(const nlohmann::json&j){
        VolumePreferences v;
        v.master=value(j,"master_volume",1.f);v.sfx=value(j,"sfx_volume",1.f);v.culture=value(j,"culture_volume",1.f);
        const bool legacy_muted=j.value("muted",nlohmann::json(false))==true;
        v.music=value(j,"music_volume",legacy_muted?0.f:value(j,"volume",.48f));
        v.pad=value(j,"pad_volume",1.f);
        if(j.contains("culture_audio_on_pad")&&j["culture_audio_on_pad"].is_boolean())v.culture_on_pad=j["culture_audio_on_pad"].get<bool>();
        return v;
    }
    void save(nlohmann::json&j)const{
        j["master_volume"]=master;j["sfx_volume"]=sfx;j["music_volume"]=music;j["culture_volume"]=culture;
        j["pad_volume"]=pad;j["culture_audio_on_pad"]=culture_on_pad;
        j["volume"]=music; // Older versions can still read the ambient level.
    }
};
}
