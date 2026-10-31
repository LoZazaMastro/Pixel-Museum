#include "museum/rhythm_chart.hpp"
#include "museum/experience_audio.hpp"
#include <cassert>
#include <cstdio>
int main(){
 using museum::RhythmChart;constexpr float beat=museum::ExperienceAudio::beat_seconds;
 static_assert(RhythmChart::phrase_beats==museum::ExperienceAudio::phrase_beats);
 static_assert(RhythmChart::phrase_beats>=28);
 RhythmChart chart;unsigned mask=0;unsigned early=0,late=0;
 for(size_t n=0;n<chart.notes.size();++n){const auto note=chart.notes[n];mask|=1u<<note.lane;
  if(n&&note.half-chart.notes[n-1].half==1){if(note.half<36)++early;else++late;}
  const float t=note.half*beat*.5f;
  assert(chart.press(note.lane,t,beat)&&chart.award==100);
  const int score=chart.score;assert(!chart.press(note.lane,t,beat)&&chart.score==score);
 }
 assert(mask==255&&early==0&&late>=16&&chart.score==4800&&chart.combo==48);
 for(float offset:{-.12f,.12f}){chart.reset();assert(chart.press(4,2*beat+offset,beat));assert(chart.award==50&&chart.score==50);}
 chart.reset();assert(chart.press(0,2*beat,beat)&&chart.award==0&&chart.score==0);
 assert(!chart.press(4,2*beat,beat)); // wrong command consumes this note once
 chart.reset();assert(chart.expire(2*beat+.17f,beat)&&chart.score==0&&chart.judged[0]);
 assert(!chart.press(4,2*beat+.17f,beat));
 chart.reset();assert(!chart.press(4,0,beat)&&chart.score==0); // no count-in scoring
 chart.expire(beat*RhythmChart::phrase_beats,beat);for(auto done:chart.judged)assert(done);
 std::printf("PASS 48-note progressive eight-command chart: 0/50/100, early/late windows, wrong inputs, duplicate prevention, automatic misses, %g seconds (original15.4).\n",beat*RhythmChart::phrase_beats);
}
