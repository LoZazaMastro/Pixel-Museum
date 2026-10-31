#include "museum/study_space.cpp"
#include <cassert>
namespace museum {
struct SpaceFeedbackInspection {
 static void run(){for(int hz:{30,60,120}){SpaceStudy s(4);hui::InputFrame i;i.connected=true;hui::ui::Feedback f;float pitch=0;
  for(int target:{0,8}){s.x_=100+float(target%8)*114;s.y_=140+float(target/8)*154;s.vx_=s.vy_=0;s.update(1.f/hz);f.clear();s.handle(i,f);assert(f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::grow);assert(f.speaker_cues[0].pitch>pitch);pitch=f.speaker_cues[0].pitch;assert(f.tactile.size()==1&&f.tactile[0].pattern==hui::audio::Tactile::rise);f.clear();s.handle(i,f);assert(f.speaker_cues.empty()&&f.tactile.empty());}
  SpaceStudy rolling(4);rolling.gathered_.fill(true);rolling.x_=400;rolling.y_=300;hui::InputFrame moving;moving.connected=true;moving.stick_x=1;unsigned pulses=0;
  for(int n=0;n<hz;++n){f.clear();rolling.handle(moving,f);rolling.update(1.f/hz);for(const auto&e:f.tactile)if(e.pattern==hui::audio::Tactile::scroll){assert(e.strength>=.09f&&e.strength<=.13f&&e.seconds==.035f);++pulses;}}
  assert(pulses>=3&&pulses<=5);rolling.pending_roll_=false;rolling.ax_=rolling.ay_=rolling.vx_=rolling.vy_=0;moving.stick_x=0;f.clear();rolling.handle(moving,f);rolling.update(1.f/hz);f.clear();rolling.handle(moving,f);assert(f.tactile.empty());
  s.pending_growth_=1;i.focus_lost=true;s.handle(i,f);i.focus_lost=false;f.clear();s.handle(i,f);assert(f.speaker_cues.empty());
 }}
};
struct PortalInspection {
 static void run(){PortalStudy s;hui::InputFrame i;i.connected=true;hui::ui::Feedback f;s.place(true,f);assert(f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::portal_open);f.clear();s.place(true,f);assert(f.speaker_cues.empty()&&f.tactile.empty());s.selected_=1;s.place(false,f);f.clear();s.v_={200,0};assert(s.traverse({420,486},{430,486}));s.handle(i,f);assert(f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::portal_cross&&f.tactile[0].pattern==hui::audio::Tactile::zoom_in);f.clear();s.handle(i,f);assert(f.speaker_cues.empty());s.event_=1;i.focus_lost=true;s.handle(i,f);f.clear();i.focus_lost=false;s.handle(i,f);assert(f.speaker_cues.empty());}
};}
int main(){museum::SpaceFeedbackInspection::run();museum::PortalInspection::run();std::puts("PASS growth pitch follows real pickups 30/60/120; portal open/cross semantic cues, same-placement/focus silent");}
