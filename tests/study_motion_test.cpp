// Focused CPU-only behavior checks for the actual production studies.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>
#include <string>

using hui::Action;
constexpr hui::gfx::Rect area{0,0,1400,700};
constexpr hui::gfx::Color accent{.8f,.2f,.15f,1};
hui::ui::Fonts fonts{}; // drawing is safe without text; no GL/font loading needed
hui::ui::Feedback feedback;
hui::InputFrame input(float x=0,float y=0){hui::InputFrame i;i.connected=true;i.stick_x=x;i.stick_y=y;return i;}
void press(museum::Study&s,Action a,float x=0,float y=0){auto i=input(x,y);i.pressed= i.held=hui::action_bit(a);s.handle(i,feedback);}
void run(museum::Study&s,int frames,float x=0,float y=0,bool held=false){
    for(int n=0;n<frames;++n){auto i=input(x,y);if(held)i.held=hui::action_bit(Action::confirm);s.handle(i,feedback);s.update(1.f/120);}
}
hui::gfx::DrawList draw(museum::Study&s){hui::gfx::DrawList d;s.draw(d,fonts,area,accent);return d;}
std::array<float,2> body(museum::Study&s,float w,float h){
    auto d=draw(s);std::array<float,2>p{};bool found=false;
    for(const auto&i:d.instances())if(std::abs(i.rect[2]-w)<.01f&&(std::abs(i.rect[3]-h)<.01f||(w==26&&h==30&&i.rect[3]>=26&&i.rect[3]<=32))){p={i.rect[0]+i.rect[2]*.5f,i.rect[1]+i.rect[3]*.5f};found=true;}
    assert(found);return p;
}
void nav(museum::Study&s,hui::Direction direction){auto i=input();i.nav=direction;s.handle(i,feedback);}
int main(){
    assert(!museum::make_study_motion("not-a-study"));
    auto jump=museum::make_study_motion("jump");const float y0=body(*jump,26,30)[1];
    press(*jump,Action::confirm);run(*jump,20,0,0,true);const float high=body(*jump,26,30)[1];assert(high<y0-60);
    jump->reset();press(*jump,Action::confirm);run(*jump,1,0,0,true);
    auto release=input();release.released=hui::action_bit(Action::confirm);jump->handle(release,feedback);run(*jump,19);
    const float low=body(*jump,26,30)[1];assert(low>high+35); // release changes actual jump arc
    run(*jump,220);assert(std::abs(body(*jump,26,30)[1]-y0)<.1f);
    std::puts("PASS jump: hold/release produces different height and lands on real platform");

    auto roll=museum::make_study_motion("momentum");run(*roll,70,1);auto moving=draw(*roll);
    run(*roll,30);auto coasting=draw(*roll);
    bool changed=moving.instances().size()!=coasting.instances().size();for(std::size_t n=0;n<std::min(moving.instances().size(),coasting.instances().size());++n)
        if(std::memcmp(&moving.instances()[n],&coasting.instances()[n],sizeof(hui::gfx::Instance)))changed=true;
    assert(changed); // no input still changes the actual rolling scene
    std::puts("PASS momentum: body and terrain continue under inertia with neutral input");

    auto dash=museum::make_study_motion("dash");const auto before=body(*dash,26,30);
    press(*dash,Action::confirm);run(*dash,20,0,0,true);assert(body(*dash,26,30)[1]<before[1]-60);
    press(*dash,Action::page_next,1);assert(dash->take_note()==74);run(*dash,23,1);
    assert(body(*dash,26,30)[0]>before[0]+200);
    press(*dash,Action::page_next,1);assert(dash->take_note()==-1); // one charge cannot be spammed
    run(*dash,120);assert(dash->take_note()==76); // actual landing restores the charge
    press(*dash,Action::page_next,1);assert(dash->take_note()==74);
    std::puts("PASS dash: physical jump, directed burst, one air charge and landing recharge");

    auto rhythm=museum::make_study_motion("rhythm");run(*rhythm,264);rhythm->take_note();
    press(*rhythm,Action::confirm);assert(rhythm->take_note()==62);
    press(*rhythm,Action::confirm);assert(rhythm->take_note()==-1); // same beat cannot score twice
    run(*rhythm,105);rhythm->take_note();press(*rhythm,Action::confirm);assert(rhythm->take_note()==50);
    std::puts("PASS rhythm: on-time event, duplicate rejection, off-time event differ");

    auto sequence=museum::make_study_motion("sequencer");nav(*sequence,hui::Direction::down);nav(*sequence,hui::Direction::right);
    press(*sequence,Action::confirm);sequence->take_note();run(*sequence,80);assert(sequence->take_note()==77);
    press(*sequence,Action::north);auto paused=draw(*sequence);run(*sequence,180);auto still=draw(*sequence);
    assert(paused.instances().size()==still.instances().size());
    for(std::size_t n=0;n<paused.instances().size();++n)assert(!std::memcmp(&paused.instances()[n],&still.instances()[n],sizeof(hui::gfx::Instance)));
    std::puts("PASS sequencer: edited 2x2 square clears on scanner, Triangle freezes scanner");

    auto wind=museum::make_study_motion("wind");run(*wind,120);const float drifting=body(*wind,16,16)[1];
    wind->reset();run(*wind,120,0,0,true);const float rising=body(*wind,16,16)[1];assert(rising<drifting-40);
    std::puts("PASS wind: lift changes flight independently of horizontal drift");

    for(const char*key:{"jump","momentum","dash","rhythm","sequencer","wind"}){
        auto s=museum::make_study_motion(key);assert(s&&std::strlen(s->help())>20);
        for(int n=0;n<3600;++n){auto i=input(std::sin(n*.03f),std::cos(n*.017f));
            if(n%67==0)i.pressed=hui::action_bit(Action::confirm);
            if(n%90<55)i.held=hui::action_bit(Action::confirm);
            s->handle(i,feedback);s->update(n==20?std::numeric_limits<float>::quiet_NaN():1.f/60);
            if(n%120==0){auto d=draw(*s);if(d.instances().size()>=1000||d.mesh_vertices().size()>=1000)std::fprintf(stderr,"geometry %s frame%d instances%zu mesh%zu\n",key,n,d.instances().size(),d.mesh_vertices().size());assert(d.instances().size()<1000&&d.mesh_vertices().size()<1000);
                for(const auto&a:d.instances())for(float v:a.rect)assert(std::isfinite(v));}
        }
        auto before_loss=draw(*s);auto lost=input(1,1);lost.focus_lost=true;
        lost.pressed=hui::action_bit(Action::west)|hui::action_bit(Action::confirm);s->handle(lost,feedback);
        auto blocked=draw(*s);assert(before_loss.instances().size()==blocked.instances().size());
        for(std::size_t n=0;n<blocked.instances().size();++n)assert(!std::memcmp(&before_loss.instances()[n],&blocked.instances()[n],sizeof(hui::gfx::Instance)));
        if(std::string(key)=="jump")s->reset();else press(*s,Action::west);auto reset=draw(*s);s->reset();auto clean=draw(*s);
        assert(reset.instances().size()==clean.instances().size());
        for(std::size_t n=0;n<clean.instances().size();++n)assert(!std::memcmp(&reset.instances()[n],&clean.instances()[n],sizeof(hui::gfx::Instance)));
    }
    std::puts("PASS all six: one-minute input stress, NaN dt, bounded geometry, intercepted Square/X ignored, deterministic reset");
}
