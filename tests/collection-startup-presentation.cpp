#include "museum/screen_collection_policy.hpp"
#include <cassert>
#include <cstdio>
int main(){
 using P=museum::CollectionInstaller::Phase;using State=museum::CollectionInstaller::Status;museum::CollectionStartupPresentation view;State state;
 // Existing installation: only background validation, no 100% screen or delay.
 view.begin(true);state.phase=P::idle;view.observe(state,false);assert(view.quiet_validation);state.phase=P::verifying;state.stage="Checking installed collection";view.observe(state,false);assert(view.quiet_validation);state.stage="Checking downloaded collection";view.observe(state,false);assert(view.quiet_validation);state.phase=P::ready;view.observe(state,false);assert(view.quiet_validation&&view.completion_delay()==0);
 // Fresh install and explicit introduction replay retain their completion step.
 view.begin(false);view.observe(state,false);assert(!view.quiet_validation&&view.completion_delay()==.6f);view.begin(true);view.replay();view.observe(state,false);assert(!view.quiet_validation&&view.completion_delay()==.6f);
 // Missing/corrupt installs reveal actual repair/error states, never fake READY.
 for(auto phase:{P::downloading,P::extracting,P::failed,P::paused,P::cancelled}){view.begin(true);state.phase=phase;view.observe(state,false);assert(!view.quiet_validation&&view.completion_delay()==.6f);state.phase=P::ready;view.observe(state,false);assert(!view.quiet_validation);}
 view.begin(true);state.phase=P::verifying;state.stage="Verifying images-001";view.observe(state,false);assert(!view.quiet_validation);view.begin(true);state.phase=P::ready;view.observe(state,true);assert(!view.quiet_validation);
 std::puts("PASS normalreopen quietasyncvalidation->READY withoutdownloadcompletion; fresh/replay100percentstep; repair/error/migration visible; readinessunchanged");
}
