#include "museum/study_motion.cpp"
#include <cassert>
namespace museum { namespace {
struct RhythmInspection {
 static void run(){
  hui::ui::Feedback feedback;hui::InputFrame input;input.connected=true;
  for(unsigned lane=0;lane<8;++lane){Rhythm study;size_t index=0;while(RhythmChart::notes[index].lane!=lane)++index;
   study.clock_=RhythmChart::notes[index].half*Rhythm::beat*.5f;
   // Resolve earlier notes as misses, leaving the selected command available.
   study.chart_.expire(study.clock_,Rhythm::beat);
   input.pressed=hui::action_bit(Rhythm::actions[lane]);study.handle(input,feedback);
   assert(study.chart_.score==100&&study.chart_.award==100);study.handle(input,feedback);assert(study.chart_.score==100);
  }
  for(float error:{-.12f,.12f}){Rhythm study;study.clock_=Rhythm::beat*2+error;input.pressed=hui::action_bit(hui::Action::confirm);study.handle(input,feedback);assert(study.chart_.score==50);}
  Rhythm wrong;wrong.clock_=Rhythm::beat*2;input.pressed=hui::action_bit(hui::Action::west);wrong.handle(input,feedback);assert(wrong.chart_.score==0&&wrong.chart_.judged[0]&&wrong.clock_>0);
  Rhythm expired;expired.clock_=Rhythm::beat*2+.17f;input.pressed=0;expired.handle(input,feedback);assert(expired.chart_.judged[0]&&expired.chart_.award==0);
  ExperienceAudio audio;Rhythm real;real.attach_audio(&audio);std::array<float,512> pcm{};
  // Audio generation leads what is heard by the calibrated 200 ms. The same
  // offset must govern visual motion and judgement, independently of UI dt.
  assert(real.audible_clock()==0);
  for(const auto note:RhythmChart::notes){const auto target=unsigned(std::llround((note.half*double(Rhythm::beat)*.5+Rhythm::output_latency)*48000));
   while(unsigned(std::llround(audio.time_s()*48000))<target){const auto at=unsigned(std::llround(audio.time_s()*48000));pcm.fill(0);audio.render(pcm.data(),std::min(256u,target-at));}
   real.update(.001f);input.pressed=hui::action_bit(Rhythm::actions[note.lane]);real.handle(input,feedback);assert(real.chart_.award==100);
  }
  assert(real.chart_.score==4800&&real.chart_.combo==48);
  unsigned end=unsigned(std::llround(double(Rhythm::beat)*RhythmChart::phrase_beats*48000));
  auto render_until=[&](unsigned target){while(unsigned(std::llround(audio.time_s()*48000))<target){const auto at=unsigned(std::llround(audio.time_s()*48000));pcm.fill(0);audio.render(pcm.data(),std::min(256u,target-at));}};
  render_until(end);real.update(.001f);assert(real.completion()==StudyCompletion::playing);
  render_until(end+unsigned(std::llround(Rhythm::output_latency*48000))+1);real.update(.001f);assert(real.completion()==StudyCompletion::experience_complete);
  std::puts("PASS actual Rhythm: eight actions, good/automatic miss/wrong/duplicate; all 48 notes score perfectly at the audible clock, 200ms after generation and independent of UI dt.");
 }
};
}}
int main(){museum::RhythmInspection::run();}
