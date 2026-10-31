#include "museum/volume_preferences.hpp"
#include <cassert>
#include <cstdio>
using nlohmann::json;
int main(){
 auto v=museum::VolumePreferences::load(json::object());assert(v.master==1&&v.sfx==1&&v.music==.48f&&v.culture==1&&v.pad==1&&!v.culture_on_pad);
 v=museum::VolumePreferences::load(json{{"volume",.27f},{"muted",true},{"reduced_motion",true}});assert(v.music==0&&v.master==1&&v.sfx==1&&v.culture==1);
 v=museum::VolumePreferences::load(json{{"music_volume",.7f},{"muted",true},{"volume",.2f},{"master_volume",4},{"sfx_volume",-2},{"culture_volume",.3}});assert(v.music==.7f&&v.master==1&&v.sfx==0&&v.culture==.3f);
 v.pad=.25f;v.culture_on_pad=true;
 json saved=json::object();v.save(saved);auto restored=museum::VolumePreferences::load(saved);assert(restored.master==v.master&&restored.sfx==v.sfx&&restored.music==v.music&&restored.culture==v.culture&&restored.pad==.25f&&restored.culture_on_pad);assert(!saved.contains("muted")&&!saved.contains("reduced_motion"));
 v=museum::VolumePreferences::load(json{{"music_volume","invalid"},{"volume",.25},{"master_volume",nullptr}});assert(v.music==.25f&&v.master==1);
 std::puts("PASS volumes:defaults,legacy mute migration,new-field precedence,clamping,invalid values,persistent5-level+route-toggle roundtrip;no reduced-motion preference");
}
