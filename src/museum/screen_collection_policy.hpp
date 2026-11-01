// Pixel Museum - presentation policy; readiness remains owned by the async installer.
#pragma once
#include "museum/collection_installer.hpp"
namespace museum {
struct CollectionStartupPresentation {
 bool quiet_validation=false;
 void begin(bool introduction_complete){quiet_validation=introduction_complete;}
 void replay(){quiet_validation=false;}
 void observe(const CollectionInstaller::Status&state,bool media_error){
  using Phase=CollectionInstaller::Phase;
  if(media_error||state.phase==Phase::downloading||state.phase==Phase::extracting||state.phase==Phase::failed||state.phase==Phase::paused||state.phase==Phase::cancelled||
     (state.phase==Phase::verifying&&state.stage.rfind("Checking",0)!=0))quiet_validation=false;
 }
 float completion_delay()const{return quiet_validation?0.f:.6f;}
};
}
