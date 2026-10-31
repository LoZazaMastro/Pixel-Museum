// Targeted tests run the production update/collision code with controlled scenes.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study_arcade.cpp"
#include <cassert>
namespace museum { namespace {
struct ArcadeInspection {
 static void run(){
  hui::ui::Feedback feedback;InputFrame neutral;neutral.connected=true;
  Maze maze;assert(Maze::w==28&&Maze::h==31&&maze.ghosts_.size()==4);
  assert(std::count(maze.dots_.begin(),maze.dots_.end(),true)==240);
  assert(std::count(maze.powers_.begin(),maze.powers_.end(),true)==4&&maze.remaining_==244);
  maze.player_={28+2,28+2,0,0,0};maze.collect();
  assert(maze.take_note()<0); // ordinary dot has no TV cue
  assert(maze.speaker_pending_==int(hui::audio::SpeakerCue::tool)); // controller remains audible
  maze.reset();
  for(size_t n=0;n<maze.dots_.size();++n)assert(!(maze.dots_[n]&&maze.powers_[n]));
  assert(maze.neighbour(14*28,3)==14*28+27&&maze.neighbour(14*28+27,1)==14*28);
  assert(maze.neighbour(11*28+13,2)==-1);
  const auto first=maze.position(maze.player_);maze.handle(neutral,feedback);maze.update(.05f);assert(maze.position(maze.player_).x<first.x);
  maze.reset();for(auto&g:maze.ghosts_)g.rest=100;
  auto up=neutral;up.held=hui::action_bit(Action::up);
  maze.handle(up,feedback);maze.update(.05f);assert(maze.player_.dir==3); // no up passage at spawn
  for(int n=0;n<28;++n){maze.handle(up,feedback);maze.update(1.f/60);}
  assert(maze.player_.dir==0&&maze.position(maze.player_).y<23); // turn stays buffered until x12
  auto right=neutral;right.held=hui::action_bit(Action::right);const auto before_reverse=maze.position(maze.player_);maze.handle(right,feedback);
  // Explicit horizontal reversal must keep the same continuous position.
  maze.player_={23*28+13,23*28+12,3,.4f,0};const auto before=maze.position(maze.player_);maze.handle(right,feedback);assert(norm(maze.position(maze.player_)-before)<.0001f);
  (void)before_reverse;
  maze.reset();maze.player_={3*28+1,3*28+1,0,0,0};maze.collect();assert(maze.power_==7.5f&&maze.points_==50&&maze.remaining_==243);
  for(const auto&g:maze.ghosts_)assert(g.progress==0);
  for(unsigned n=0;n<4;++n){maze.ghosts_[n]=maze.player_;maze.update(.001f);assert(maze.chain_==int(n)+1&&maze.ghosts_[n].rest>1);}
  assert(maze.points_==50+200+400+800+1600);
  maze.power_=0;maze.immune_=0;maze.ghosts_[0]=maze.player_;maze.update(.001f);assert(maze.lives_==2&&maze.power_==0);
  maze.reset();maze.eaten_=69;maze.player_={28+2,28+2,0,0,0};maze.collect();assert(maze.fruit_round_==1&&maze.fruit_==9.5f);
  maze.player_={Maze::fruit_cell,Maze::fruit_cell,0,0,0};const int points=maze.points_;maze.collect();assert(maze.fruit_==0&&maze.points_==points+100);
  maze.eaten_=169;maze.player_={28+3,28+3,0,0,0};maze.collect();assert(maze.fruit_round_==2&&maze.fruit_==9.5f);
  const float tunnel_speed=maze.ghost_speed({14*28+1,14*28+1,1,0,0},0);assert(tunnel_speed<maze.ghost_speed({28+1,28+1,1,0,0},0));
  maze.reset();for(auto&g:maze.ghosts_)g.rest=10000;
  std::array<bool,Maze::w*Maze::h>visited{};std::array<int,Maze::w*Maze::h>queue{};int head=0,tail=1;
  queue[0]=maze.player_.cell;visited[size_t(queue[0])]=true;
  while(head<tail){const int cell=queue[size_t(head++)];maze.player_={cell,cell,0,0,0};maze.collect();
   for(int dir=0;dir<4;++dir){const int next=maze.neighbour(cell,dir);if(next>=0&&!visited[size_t(next)]){visited[size_t(next)]=true;queue[size_t(tail++)]=next;}}}
  assert(maze.won_&&maze.remaining_==0&&maze.eaten_==244);
  std::puts("PASS classic maze:28x31,240+4 separate pellets,4 ghosts,bufferedturns,wrap,200/400/800/1600,70/170 cherries100,tunnelslowdown,allpelletsreachable");
  Gravity falling;assert(falling.level()==0&&std::abs(falling.gravity_interval()-.8f)<.00001f);
  const int levels[]={0,1,8,9,10,12,13,15,16,18,19,28,29,40};const int frames[]={48,43,8,6,5,5,4,4,3,3,2,2,1,1};
  for(unsigned n=0;n<std::size(levels);++n){falling.lines_=levels[n]*10;assert(falling.level()==levels[n]&&std::abs(falling.gravity_interval()-frames[n]/60.f)<.00001f);}
  falling.lines_=9;assert(falling.level()==0);falling.lines_=10;assert(falling.level()==1);falling.reset();assert(falling.level()==0);
  for(int n=0;n<15;++n)falling.update(.05f);assert(falling.y_==0);falling.update(.05f);falling.update(.001f);assert(falling.y_==1);
  Formation timed;const float speed=timed.formation_speed();timed.time_=75;assert(timed.formation_speed()>speed*2&&timed.formation_speed()<=speed*2.8f);
  timed.hits_=20;assert(timed.formation_speed()<=speed*2.8f);timed.reset();assert(timed.formation_speed()==speed);
  std::puts("PASS level0+onelevelper10lines,NESframecurve,timeindependentgravity,andformationtimed2.8xspeed");
  Formation formation;formation.update(.05f);assert(!formation.bonus_active_);
  for(int n=0;n<61;++n)formation.update(.05f);assert(formation.bonus_active_);
  formation.shots_[0]={{formation.bonus_x_+.82f,36},true};formation.update(.01f);
  assert(formation.bonus_hits_==1&&formation.points_==150&&!formation.bonus_active_);
  formation.update(.05f);assert(formation.bonus_hits_==1); // cannot double-score the same object
  std::puts("PASS formation: timed mothership can be hit once for an actual +150 bonus");
  Formation all;for(unsigned n=0;n<all.alive_.size();++n){
   all.fire_wait_=all.enemy_wait_=100;all.direction_=0;
   all.shots_[0]={{all.origin_+float(n%7)*72,all.depth_+float(n/7)*49+1},true};
   const int old=all.points_;all.update(.001f);assert(!all.alive_[n]&&all.points_>old);
   const int points=all.points_;all.update(.001f);assert(all.points_==points);
  }assert(all.points_==735&&all.hits_==21);
  std::puts("PASS all 21 formation ships award row-specific points exactly once, total735");

 }
};
}}
namespace museum { namespace {
struct ArcadeTouchInspection {
 static void run(){
  hui::InputFrame i;i.connected=true;i.touch.available=true;i.touch.count=1;
  hui::ui::Feedback f;Paddle p;Bricks b;
  i.touch.points[0].y=0;p.handle(i,f);assert(p.player_==38);assert(!f.tactile.empty());
  p.update(.1f);i.touch.points[0].y=1;p.handle(i,f);assert(p.player_==352);
  i.touch.points[0].x=0;b.handle(i,f);assert(b.paddle_==51);
  i.touch.points[0].x=1;b.handle(i,f);assert(b.paddle_==629);
  i.focus_lost=true;i.touch.points[0].x=0;b.handle(i,f);assert(b.paddle_==629);
  b.reset();b.running_=true;b.ball_={45,44};b.velocity_={0,-230};b.update(.01f);assert(b.broken_==1);
  const int score=b.broken_*100;b.update(.01f);assert(b.broken_*100==score);
  std::puts("PASS production touch paddles clamp and respect focus; real brick collision awards100 once");
 }
};
}}
int main(){museum::ArcadeInspection::run();museum::ArcadeTouchInspection::run();}
