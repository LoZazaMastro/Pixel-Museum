#include "museum/study_workshops.cpp"
#include <cassert>
#include <set>
namespace museum {
struct WorkshopInspection {
 static void run(){
  hui::InputFrame i;i.connected=true;hui::ui::Feedback f;
  PixelDrawing pixels;assert(pixels.cells_.size()==256&&pixels.changes()==0);for(auto c:pixels.cells_)assert(c==0);
  std::set<unsigned> colours(PixelDrawing::palette_.begin(),PixelDrawing::palette_.end());assert(colours.size()==PixelDrawing::palette_.size()&&!colours.count(0xffffff));
  const int palette_count=int(PixelDrawing::palette_.size());
  std::set<unsigned> supplied(pixel_palette::provided.begin(),pixel_palette::provided.end());supplied.erase(0xffffff);
  assert(pixel_palette::provided.size()==64&&colours==supplied&&colours.size()>=16);
  i.pressed=hui::action_bit(hui::Action::confirm);pixels.handle(i,f);assert(pixels.cells_[0]==1&&pixels.changes()==1);
  i={};i.connected=true;i.touch.available=true;i.touch.count=1;i.touch.points[0]={1,1,0};i.pressed=hui::action_bit(hui::Action::touch);pixels.handle(i,f);assert(pixels.x_==0&&pixels.y_==0&&pixels.changes()==1);
  // Drive the real input path through every unique colour from the original64.
  for(int n=0;n<palette_count;++n){pixels.x_=0;pixels.y_=0;i={};i.connected=true;i.pressed=hui::action_bit(hui::Action::confirm);pixels.handle(i,f);assert(pixels.cells_[0]==n+1);i.pressed=hui::action_bit(hui::Action::page_next);pixels.handle(i,f);}assert(pixels.brush_==0);
  i.pressed=hui::action_bit(hui::Action::page_prev);pixels.handle(i,f);assert(pixels.brush_==palette_count-1);i.pressed=hui::action_bit(hui::Action::page_next);pixels.handle(i,f);assert(pixels.brush_==0);
  pixels.brush_=palette_count-1;
  i.pressed=hui::action_bit(hui::Action::confirm);pixels.handle(i,f);assert(pixels.cells_[0]==pixels.brush_+1&&pixels.changes()==1);
  i.pressed=hui::action_bit(hui::Action::back);pixels.handle(i,f);assert(pixels.cells_[0]==0&&pixels.changes()==0);
  pixels.brush_=1;pixels.x_=1;i.pressed=hui::action_bit(hui::Action::confirm);pixels.handle(i,f);assert(pixels.cells_[1]==2);
  // Shoulder hold repeats at the same elapsed rate and stops immediately on release.
  for(int hz:{30,60,120}){
   PixelDrawing held;hui::InputFrame shoulder;shoulder.connected=true;shoulder.pressed=shoulder.held=hui::action_bit(hui::Action::page_next);
   held.handle(shoulder,f);assert(held.brush_==1);shoulder.pressed=0;
   for(int tick=0;tick<hz;++tick){held.update(1.f/hz);held.handle(shoulder,f);}
   assert(held.brush_>=10&&held.brush_<=12);const int stopped=held.brush_;shoulder.held=0;held.handle(shoulder,f);
   for(int tick=0;tick<hz;++tick){held.update(1.f/hz);held.handle(shoulder,f);}assert(held.brush_==stopped);
   shoulder.pressed=shoulder.held=hui::action_bit(hui::Action::page_prev);held.handle(shoulder,f);assert(held.brush_==stopped-1);shoulder.pressed=0;
   for(int tick=0;tick<hz;++tick){held.update(1.f/hz);held.handle(shoulder,f);}assert(held.brush_!=stopped-1);
   shoulder.focus_lost=true;held.handle(shoulder,f);const int unfocused=held.brush_;held.update(.05f);assert(held.brush_==unfocused&&held.brush_hold_==0);
  }
  i.pressed=hui::action_bit(hui::Action::west);pixels.handle(i,f);assert(!pixels.grid_&&pixels.cells_[1]==2);
  i.focus_lost=true;i.pressed=hui::action_bit(hui::Action::north);pixels.handle(i,f);assert(pixels.changes()==1);
  i.focus_lost=false;pixels.handle(i,f);assert(pixels.grid_&&pixels.changes()==0);for(auto c:pixels.cells_)assert(c==0);
  i.pressed=0;i.nav=hui::Direction::right;for(int n=0;n<40;++n)pixels.handle(i,f);i.nav=hui::Direction::down;for(int n=0;n<40;++n)pixels.handle(i,f);assert(pixels.x_==15&&pixels.y_==15);
  i={};i.connected=true;
  CartridgeRules rules;i.touch.available=true;i.touch.count=1;i.touch.points[0].x=.25f;
  rules.handle(i,f);assert(std::abs(rules.player_-160)<.1f);
  rules.tiles_[0]={160,292,true};rules.update(1.f/60);assert(rules.correct_[0]==1&&rules.mistakes_[0]==0);
  i.pressed=hui::action_bit(hui::Action::confirm);rules.handle(i,f);assert(rules.mode_==1);
  rules.tiles_[0]={160,292,true};rules.update(1.f/60);assert(rules.correct_[1]==0&&rules.mistakes_[1]==1);
  rules.tiles_[0]={600,327,true};rules.update(1.f/60);assert(rules.correct_[1]==1&&rules.correct_[0]==1);
  PocketBudget budget;i={};i.connected=true;i.pressed=hui::action_bit(hui::Action::confirm);budget.handle(i,f);assert(budget.completed_==0);
  const auto tune=[&](float x,float y){i={};i.connected=true;i.touch.available=true;i.touch.count=1;i.touch.points[0]={x,y,0};budget.handle(i,f);};
  const auto test=[&](){i={};i.connected=true;i.pressed=hui::action_bit(hui::Action::confirm);budget.handle(i,f);};
  tune(.67f,.6f);test();assert(budget.completed_==1&&budget.brief_==0&&budget.completion()==StudyCompletion::level_complete);budget.continue_level();assert(budget.brief_==1);
  tune(.67f,.4f);test();assert(budget.completed_==3&&budget.brief_==1&&budget.completion()==StudyCompletion::level_complete);budget.continue_level();assert(budget.brief_==2);
  tune(.34f,.4f);tune(0,.6f);test();assert(budget.completed_==7&&budget.cost()<=58&&budget.completion()==StudyCompletion::experience_complete);
  budget.take_note();const int silent_cost=budget.cost();budget.update(.05f);assert(budget.take_note()<0);
  tune(1,.9f);budget.take_note();assert(budget.cost()==silent_cost+12);int budget_notes=0;
  for(int n=0;n<180;++n){budget.update(1.f/120);budget_notes+=budget.take_note()>=0;}assert(budget_notes>=2);
  JumpLab defaults,tuned;
  assert(defaults.impulse()*defaults.impulse()/(2*defaults.gravity())<110);
  tuned.tuning_={.1f,.95f,.9f};
  assert(tuned.impulse()*tuned.impulse()/(2*tuned.gravity())>110);
  for(int hz:{30,60,120}){
   JumpLab route;route.tuning_={.1f,.95f,.9f};
   for(int tick=0;tick<hz*25&&route.checkpoint_<3;++tick){
    if(route.completion()==StudyCompletion::level_complete)route.continue_level();
    hui::InputFrame input;input.connected=true;input.held=hui::action_bit(hui::Action::confirm);
    const auto&from=JumpLab::platforms_[size_t(route.checkpoint_)];const auto&to=JumpLab::platforms_[size_t(route.checkpoint_+1)];
    input.stick_x=route.grounded_?1.f:std::clamp((to.x+to.w*.5f-route.x_)*.018f,-1.f,1.f);
    if(route.grounded_&&route.x_>from.x+from.w-32)input.pressed=hui::action_bit(hui::Action::confirm);
    route.handle(input,f);route.update(1.f/hz);
   }
   assert(route.checkpoint_==3&&route.completion()==StudyCompletion::experience_complete);route.continue_level();assert(route.checkpoint_==0&&route.completion()==StudyCompletion::playing);
  }
  JumpLab held,tapped;
  const auto jump=[&](JumpLab&s,bool keep){for(int n=0;n<140;++n){hui::InputFrame input;input.connected=true;if(n==0)input.pressed=hui::action_bit(hui::Action::confirm);if(keep)input.held=hui::action_bit(hui::Action::confirm);s.handle(input,f);s.update(1.f/120);}};
  jump(held,true);jump(tapped,false);assert(held.last_height_>tapped.last_height_+25&&held.ghost_count_>2);
  held.x_=270;held.y_=175;held.vy_=80;held.grounded_=false;held.update(.04f);assert(held.checkpoint_==1&&held.landings_==1&&held.grounded_);
  AdaptivePulse rest,moving;int quiet_notes=0,active_notes=0;
  for(int n=0;n<960;++n){hui::InputFrame input;input.connected=true;rest.handle(input,f);rest.update(1.f/120);quiet_notes+=rest.take_note()>=0;input.stick_x=.2f;input.trigger_r=1;moving.handle(input,f);moving.update(1.f/120);active_notes+=moving.take_note()>=0;}
  assert(active_notes>quiet_notes*2&&moving.time_>7.9f);
  // Each real gap is reachable with a short press and no run trigger,
  // leaving a human-sized takeoff margin rather than a last-pixel jump.
  for(const int hz:{30,60,120})for(size_t gap=0;gap+1<AdaptivePulse::ground_.size();++gap){
   AdaptivePulse route;route.x_=AdaptivePulse::ground_[gap].right-24;bool landed=false;
   for(int frame=0;frame<hz*2;++frame){hui::InputFrame input;input.connected=true;input.stick_x=1;
    if(frame==0)input.pressed=hui::action_bit(hui::Action::confirm);
    route.handle(input,f);route.update(1.f/float(hz));
    assert(route.x_>AdaptivePulse::ground_[gap].right-25); // no fall/reset
    if(route.x_>AdaptivePulse::ground_[gap+1].left+8&&route.grounded_){landed=true;break;}
   }
   assert(landed);
  }
  AdaptivePulse finished;finished.x_=2111;assert(finished.completion()==StudyCompletion::experience_complete); // No collectibles required.
  AdaptivePulse late;late.x_=335;late.grounded_=false;late.coyote_=.08f;
  i={};i.connected=true;i.pressed=hui::action_bit(hui::Action::confirm);late.handle(i,f);late.update(1.f/120);assert(late.vy_<-300);
  AdaptivePulse buffered;buffered.x_=500;buffered.y_=269;buffered.vy_=100;buffered.grounded_=false;
  buffered.handle(i,f);buffered.update(1.f/60);assert(buffered.grounded_);
  i.pressed=0;buffered.handle(i,f);buffered.update(1.f/60);assert(buffered.vy_<-300&&!buffered.grounded_);
  const float before=moving.time_;i={};i.connected=true;i.focus_lost=true;moving.handle(i,f);moving.update(.05f);assert(moving.time_==before&&moving.move_==0);
  std::printf("Workshop mechanics: shared-rule inversion / touch / three budgets / variable jump / landing checkpoint / adaptive clock / all four gaps with tap at30/60/120Hz / coyote time / buffered jump / focus isolation PASS\n");
 }
};
}
void check_workshop_mechanics(){museum::WorkshopInspection::run();}
