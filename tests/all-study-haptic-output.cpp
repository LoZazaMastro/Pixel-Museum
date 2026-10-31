// Exercise the real factory and PCM synthesis; this is not a physical-pad test.
#include "museum/study.hpp"
#include "audio/controller_feedback.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
int main(){
 const char*keys[]={"paddle","bricks","formation","maze","gravity","orbit","wireframe","jump","momentum","dash","rhythm","sequencer","wind","portals","perspective","raycast","camera","voxels","scale","light","pixels","cartridge-rules","pocket-budget","adaptive-pulse","jump-lab","city-system"};
 for(const char*key:keys){
  auto study=museum::make_study(key);assert(study);hui::audio::ControllerFeedback output;output.enabled(true);unsigned events=0,nonzero=0;double energy=0;float peak=0;
  for(unsigned n=0;n<720;++n){
   hui::InputFrame i;i.connected=true;i.stick_x=std::sin(float(n)*.07f);i.stick_y=std::cos(float(n)*.05f);i.nav=n%20==0?hui::Direction::right:n%20==10?hui::Direction::down:hui::Direction::none;
   if(n%30==0)i.pressed=hui::action_bit(hui::Action::confirm);if(n%120<20)i.held=hui::action_bit(hui::Action::confirm);
   if(n%120==45)i.pressed|=hui::action_bit(hui::Action::north);if(n%120==75)i.pressed|=hui::action_bit(hui::Action::page_next);
   hui::ui::Feedback f;study->handle(i,f);study->update(1.f/120);
   for(const auto&e:f.tactile){assert(output.post(e));++events;}
   std::array<float,800>pcm{};output.render_haptics(pcm.data(),400);
   for(float value:pcm){assert(std::isfinite(value)&&std::abs(value)<=.7f);peak=std::max(peak,std::abs(value));energy+=value*value;if(std::abs(value)>.001f)++nonzero;}
  }
  std::printf("Study %s: %u action events, %u driven samples, peak %.4f RMS %.5f\n",key,events,nonzero,peak,std::sqrt(energy/(720*800)));
  assert(events>0&&nonzero>0&&peak>.01f);
 }
 puts("PASS26 real study factories produce bounded tactile PCM from active controls, without generic Square-reset/focus shortcuts. Accepted-action detail remains covered by family-specific mechanics tests; physical intensity unverified.");
}
