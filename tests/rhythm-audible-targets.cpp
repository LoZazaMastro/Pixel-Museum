// Every visual target must be an audible target on TV and pad, including halves.
#include "museum/experience_audio.hpp"
#include "museum/rhythm_chart.hpp"
#include "audio/controller_feedback.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
int main(){
 using museum::ExperienceAudio;using museum::RhythmChart;
 const unsigned length=unsigned(std::ceil(double(ExperienceAudio::beat_seconds)*ExperienceAudio::phrase_beats*48000));
 const auto render=[&](unsigned block){ExperienceAudio audio;audio.start();std::vector<float> pcm(length*3),tv(block*2),pad(block);
  for(unsigned at=0;at<length;at+=block){const unsigned n=std::min(block,length-at);std::fill(tv.begin(),tv.end(),0);audio.render(tv.data(),n,pad.data());for(unsigned k=0;k<n;++k){pcm[(at+k)*3]=tv[k*2];pcm[(at+k)*3+1]=tv[k*2+1];pcm[(at+k)*3+2]=pad[k];}}
  return pcm;
 };
 const auto source=render(256);assert(source==render(997));
 for(unsigned n=0;n<ExperienceAudio::controller_delay_frames;++n)assert(source[n*3+2]==0);
 std::array<bool,76> chart{};for(const auto&note:RhythmChart::notes)chart[note.half]=true;
 unsigned verified=0,half_notes=0;
 for(unsigned slot=4;slot<76;++slot){const unsigned at=unsigned(std::ceil(slot*double(ExperienceAudio::beat_seconds)*24000));double pad_energy=0,correlation=0;unsigned onset=1440;
  for(unsigned k=0;k<1440&&at+k+ExperienceAudio::controller_delay_frames<length;++k){const float pad=source[(at+k+ExperienceAudio::controller_delay_frames)*3+2],tv=source[(at+k)*3];pad_energy+=pad*pad;correlation+=pad*tv;if(std::abs(pad)>.0001f&&onset==1440)onset=k;}
  if(chart[slot]){assert(pad_energy>.005&&onset<32&&correlation>0);++verified;half_notes+=slot%2;}
  else assert(pad_energy<.000001);
 }
 assert(verified==48&&half_notes>0);
 // Reproduce the real producer/consumer grains: no resampling or hidden
 // offset may move one pad cue relative to the source samples.
 hui::audio::ControllerFeedback bus;bus.enabled(true);std::array<float,256> block{},heard{};
 for(unsigned at=0;at<length;at+=256){const unsigned n=std::min(256u,length-at);for(unsigned k=0;k<n;++k)block[k]=source[(at+k)*3+2];bus.submit_speaker(block.data(),n);bus.render_speaker(heard.data(),n);for(unsigned k=0;k<n;++k)assert(heard[k]==block[k]);}
 assert(bus.dropped()==0);
 // A deliberately stalled consumer cannot replay a40ms backlog.
 block.fill(.1f);for(int n=0;n<3;++n)bus.submit_speaker(block.data(),256);assert(bus.dropped()==256);bus.render_speaker(heard.data(),256);for(float v:heard)assert(v==0);
 block.fill(.2f);bus.submit_speaker(block.data(),256);bus.render_speaker(heard.data(),256);for(float v:heard)assert(v==.2f);
 std::printf("RHYTHM_AUDIBLE_TARGETS_PASS all48 TV/pad correlated onsets<32samples after200ms controller compensation, halfbeat targets=%u, 256/997grain identical; real256grain pad ring exact/no drop; stalled queue clears within512frames(10.7ms). Physical device latency unmeasured.\n",half_notes);
}
