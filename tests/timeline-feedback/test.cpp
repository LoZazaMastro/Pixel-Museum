#include "ui/feedback.hpp"
#include "audio/museum_interface_mix.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
using namespace hui;
std::vector<float> render(audio::TactileEvent e){audio::ControllerFeedback p;p.enabled(true);assert(p.post(e));std::vector<float> s(48000);p.render_haptics(s.data(),24000);return s;}
double energy(const std::vector<float>&s,int channel){double sum=0;for(size_t i=channel;i<s.size();i+=2)sum+=s[i]*s[i];return sum;}
int main(){
 using audio::museum_original::interface_gain;
 assert(interface_gain(audio::Cue::focus,.4f)==interface_gain(audio::Cue::focus,1.f));
 assert(interface_gain(audio::Cue::type,1.f)==1.f);
 assert(interface_gain(audio::Cue::slider,1.f)==.6f);
 assert(interface_gain(audio::Cue::select,0.f)==0.f);
 assert(interface_gain(audio::Cue::invader_shot,.2f)==.2f);
 assert(interface_gain(audio::Cue::place,.4f)==.4f);
 ui::Feedback left,right,none,culture,games;left.timeline_step(-1);right.timeline_step(1);none.timeline_step(0);
 assert(none.tactile.empty()&&none.cues.empty());assert(left.tactile.size()==1&&right.tactile.size()==1);
 assert(left.speaker_cues.empty()&&right.speaker_cues.empty());
 const auto old=render({audio::Tactile::focus,.13f,.022f,.3f}),l=render(left.tactile[0]),r=render(right.tactile[0]);
 const double prior=energy(old,0)+energy(old,1),after=energy(r,0)+energy(r,1);
 assert(after>prior*8);assert(energy(l,0)>energy(l,1)*1.8);assert(energy(r,1)>energy(r,0)*1.8);
 int peak=0,last=0;for(size_t i=0;i<r.size();++i){assert(std::isfinite(r[i])&&std::abs(r[i])<=.7f);int pcm=int(std::clamp(r[i],-1.f,1.f)*32767);peak=std::max(peak,std::abs(pcm));if(pcm)last=int(i/2);}
 assert(peak>12000&&last>2400&&last<2700);assert(r.back()==0);
 culture.timeline_route(true);games.timeline_route(false);
 assert(culture.tactile.size()==1&&culture.tactile[0].pattern==audio::Tactile::rise);assert(games.tactile[0].pattern==audio::Tactile::fall);
 assert(culture.speaker_cues.size()==1&&games.speaker_cues.size()==1);
 audio::ControllerFeedback a,b;a.enabled(true);b.enabled(true);assert(a.post_speaker(culture.speaker_cues[0]));assert(b.post_speaker(games.speaker_cues[0]));
 std::vector<float> up(16000),down(16000);a.render_speaker(up.data(),16000);b.render_speaker(down.data(),16000);assert(up!=down);
 for(size_t n=0;n<up.size();++n){assert(std::isfinite(up[n])&&std::abs(up[n])<=.3f);if(n>=13000)assert(up[n]==0&&down[n]==0);}
 a.enabled(false);assert(!a.post_speaker(culture.speaker_cues[0]));
 std::printf("PASS timeline PCM detent: energy %.2fx old, peak %d/32767, active %.2fms; directional stereo and distinct original route gestures with bounded tails\n",after/prior,peak,last/48.f);
}
