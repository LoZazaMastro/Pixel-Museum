#include "museum/study_arcade.cpp"
#include "audio/controller_feedback.hpp"
#include "museum/study_controls.hpp"
#include <cassert>
#include <numeric>
namespace museum {namespace {
struct ArcadeHapticsInspection {
 static hui::InputFrame input(){hui::InputFrame i;i.connected=true;return i;}
 static void run(){
  for(int hz:{30,60,120}){
   const float dt=1.f/hz;auto i=input();hui::ui::Feedback f;
   {Formation g;i.held=hui::action_bit(Action::confirm);g.handle(i,f);g.update(dt);assert(g.take_note()==-1);f.clear();i.held=0;g.handle(i,f);assert(f.tactile.size()==1&&f.tactile[0].strength>=.4f);assert(f.cues.size()==1&&f.cues[0].cue==hui::audio::Cue::invader_shot);assert(f.speaker_cues.size()==1&&f.speaker_cues[0].cue==hui::audio::SpeakerCue::invader_shot);}
   {Formation g;g.shots_[0]={{90,62+390*dt},true};g.update(dt);g.handle(i,f);assert(g.hits_==1);assert(f.tactile.back().strength>=.38f);f.clear();}
   {Formation g;g.bonus_active_=true;g.bonus_x_=340;g.shots_[0]={{340+82*dt,26+390*dt},true};g.update(dt);g.handle(i,f);assert(g.bonus_hits_==1&&f.tactile.back().strength>=.48f);f.clear();}
   {Formation g;g.hostile_[0]={{340,354-170*dt},true};g.update(dt);g.handle(i,f);assert(g.shield_==2&&f.tactile.back().strength>=.52f);f.clear();}
   {Bricks g;g.running_=true;g.ball_={8,220};g.velocity_={-100,0};g.update(dt);g.handle(i,f);assert(f.tactile.size()==1&&f.tactile[0].strength>=.22f);f.clear();}
   {Bricks g;g.running_=true;g.ball_={340,347};g.velocity_={0,200};g.update(dt);g.handle(i,f);assert(g.velocity_.y<0&&f.tactile.back().strength>=.38f);f.clear();}
   {Bricks g;g.running_=true;g.ball_={40,23};g.velocity_={0,200};g.update(dt);g.handle(i,f);assert(g.broken_==1&&f.tactile.back().strength>=.44f);f.clear();}
   {Bricks g;g.running_=true;g.ball_={340,400};g.velocity_={0,200};g.update(dt);g.handle(i,f);assert(!g.running_&&f.tactile.back().strength>=.5f);f.clear();}
   Maze maze;
   assert(maze.neighbour(11*Maze::w+13,2)==-1); // Player cannot cross the door.
   assert(maze.neighbour(Maze::house,0,true)==13*Maze::w+13);
   std::array<bool,Maze::w*Maze::h> visited{};std::vector<int> queue{maze.player_.cell};visited[size_t(queue[0])]=true;
   for(size_t at=0;at<queue.size();++at)for(int direction=0;direction<4;++direction){const int next=maze.neighbour(queue[at],direction);if(next>=0&&!visited[size_t(next)]){visited[size_t(next)]=true;queue.push_back(next);}}
   int dots=0;for(size_t n=0;n<maze.dots_.size();++n)if(maze.dots_[n]){assert(visited[n]&&!Maze::pen(int(n)));++dots;}
   assert(dots==240&&maze.remaining_==244);
   assert(!Maze::pen(maze.ghosts_[0].cell));for(unsigned n=1;n<maze.ghosts_.size();++n)assert(Maze::pen(maze.ghosts_[n].cell));
   for(int frame=0;frame<hz*8;++frame)for(unsigned n=0;n<maze.ghosts_.size();++n){auto&g=maze.ghosts_[n];g.rest=std::max(0.f,g.rest-dt);maze.advance(g,3.f*dt,false,n);}
   for(const auto&ghost:maze.ghosts_)assert(!Maze::pen(ghost.cell)&&!Maze::pen(ghost.next));
   maze.reset();
   hui::audio::ControllerFeedback pcm;pcm.enabled(true);
   for(int x=1;x<=12;++x){const int cell=5*Maze::w+x;maze.player_={cell,cell,1,0,0};maze.collect();assert(maze.take_note()>=0);f.clear();maze.handle(input(),f);
    assert(f.tactile.size()==1&&f.tactile[0].strength>=.18f&&f.speaker_cues.size()==1);
    assert(pcm.post(f.tactile[0])&&pcm.post_speaker(f.speaker_cues[0]));std::array<float,4096> tactile{};std::array<float,2048> speaker{};pcm.render_haptics(tactile.data(),2048);pcm.render_speaker(speaker.data(),2048);
    const auto energy=[](const auto&samples){float e=0;for(float sample:samples)e+=sample*sample;return e;};assert(energy(tactile)>.001f&&energy(speaker)>.001f);
    maze.collect();assert(maze.take_note()==-1);f.clear();maze.handle(input(),f);assert(f.tactile.empty()&&f.speaker_cues.empty());
   }
   const int cell=5*Maze::w+13;maze.player_={cell,cell,1,0,0};maze.collect();maze.event({1,1},79,.5f);maze.rumble_=.55f;f.clear();maze.handle(input(),f);
   assert(f.tactile.size()==3&&f.speaker_cues.size()==1);bool pellet=false;for(const auto&e:f.tactile)pellet|=e.pattern==hui::audio::Tactile::touch&&e.strength==.18f;assert(pellet);
   assert(pcm.dropped()==0);
   Gravity falling;f.clear();auto up=input();up.pressed=hui::action_bit(Action::up);up.nav=Direction::up;falling.handle(up,f);
   const auto occupied=[&](){return std::count_if(falling.board_.begin(),falling.board_.end(),[](unsigned cell){return cell!=0;});};
   assert(occupied()==4);up.pressed=0;up.held=hui::action_bit(Action::up);up.nav_repeat=true;for(int n=0;n<hz;++n)falling.handle(up,f);assert(occupied()==4);
   up=input();up.pressed=hui::action_bit(Action::north);falling.handle(up,f);assert(occupied()==4);
   up=input();up.nav=Direction::up;falling.handle(up,f);assert(occupied()==8);
   bool drop_hint=false;for(const auto&control:study_controls("gravity"))if(std::string_view(control.hint.label)=="Drop"){assert(control.hint.button==hui::ui::Button::dpad&&control.up);drop_hint=true;}assert(drop_hint);
   std::printf("ARCADE_FEEDBACK_CAGE_PASS hz=%d reachable_dots=%d each12pellets=TVnote+speakerPCM+hapticPCM, simultaneous pulses retained\n",hz,dots);
  }
 }
};
}}
int main(){museum::ArcadeHapticsInspection::run();}
