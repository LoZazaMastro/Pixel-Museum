// Original eight-command chart. Positions are half-beats on the audio clock.
#pragma once
#include <array>
#include <cmath>
#include <cstddef>
namespace museum {
struct RhythmChart {
 struct Note { unsigned half; unsigned lane; };
 // Two-beat count-in, directions and faces introduced separately, then mixed
 // syncopation. No simultaneous chords: all eight commands stay readable.
 static constexpr std::array<Note,48> notes{{
  {4,4},{6,0},{8,1},{10,2},{12,3},{14,0},{16,2},{18,1},
  {20,4},{22,5},{24,6},{26,7},{28,4},{30,6},{32,5},{34,7},
  {36,0},{37,4},{38,1},{40,5},{41,2},{42,6},{44,3},{46,7},
  {48,0},{49,1},{50,4},{51,5},{52,2},{54,6},{55,3},{56,7},
  {57,4},{58,0},{59,6},{60,2},{61,5},{62,1},{63,7},{64,3},
  {65,0},{66,4},{67,2},{68,6},{69,1},{70,5},{71,3},{72,7}
 }};
 static constexpr float perfect=.075f,good=.16f;
 static constexpr unsigned phrase_beats=38;
 std::array<unsigned char,notes.size()> judged{};
 int score=0,combo=0,last=-1,award=0;unsigned hits=0,misses=0;
 void reset(){judged.fill(0);score=combo=award=0;last=-1;hits=misses=0;}
 bool expire(float seconds,float beat){bool missed=false;for(size_t n=0;n<notes.size();++n){
  if(!judged[n]&&seconds>notes[n].half*beat*.5f+good){judged[n]=1;last=int(n);award=0;combo=0;++misses;missed=true;}}
  return missed;}
 bool press(unsigned lane,float seconds,float beat){
  int closest=-1;float error=good+.0001f;
  for(size_t n=0;n<notes.size();++n)if(!judged[n]){const float e=std::abs(seconds-notes[n].half*beat*.5f);if(e<error){error=e;closest=int(n);}}
  if(closest<0)return false;
  last=closest;judged[size_t(closest)]=1;
  award=notes[size_t(closest)].lane!=lane?0:error<=perfect?100:50;
  if(award)++hits;else ++misses;
  score+=award;combo=award?combo+1:0;return true;
 }
};
}
