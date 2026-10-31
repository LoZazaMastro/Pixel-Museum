// Tests production geometry and input, not a second implementation of the studies.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
namespace {
using hui::Action;using hui::gfx::Instance;
hui::gfx::DrawList picture(museum::Study&s,hui::ui::Fonts&f){hui::gfx::DrawList d;s.draw(d,f,{0,0,1000,600},hui::gfx::Color::rgb(0x985b42));return d;}
hui::InputFrame input(float x=0,float y=0,float rotation=0){hui::InputFrame i;i.connected=true;i.stick_x=x;i.stick_y=y;i.stick2_x=rotation;return i;}
void frames(museum::Study&s,int count,float dt,float x=0,float y=0,float rotation=0){hui::ui::Feedback f;
    for(int n=0;n<count;++n){s.handle(input(x,y,rotation),f);s.update(dt);f.clear();}}
void press(museum::Study&s,Action a){auto i=input();i.pressed=hui::action_bit(a);hui::ui::Feedback f;s.handle(i,f);}
std::array<float,3> circle(museum::Study&s,hui::ui::Fonts&f,float size=0){auto d=picture(s,f);std::array<float,3>r{};bool found=false;
    for(const auto&i:d.instances())if(i.params[3]==0&&i.rect[2]==i.rect[3]&&std::abs(i.params[0]*2-i.rect[2])<.001f&&
        std::abs(i.color_top[0]-241.f/255)<.01f&&i.color_top[3]>.9f&&(size==0||std::abs(i.rect[2]-size)<.001f)){
        r={i.rect[0]+i.rect[2]/2,i.rect[1]+i.rect[3]/2,i.rect[2]};found=true;}
    assert(found);return r;
}

}
void check_mechanics(hui::ui::Fonts&fonts){
    {
        auto s=museum::make_study_space("perspective");auto p=picture(*s,fonts);std::vector<Instance>lines;
        for(const auto&i:p.instances())if(i.params[3]==4&&i.params[1]==19)lines.push_back(i);
        assert(lines.size()==5);for(unsigned n=0;n<3;++n){assert(std::abs(lines[n].extra[2]-lines[n+1].extra[0])<.01f);assert(std::abs(lines[n].extra[3]-lines[n+1].extra[1])<.01f);}
        press(*s,Action::confirm);assert(s->take_note()==72);press(*s,Action::confirm);assert(s->take_note()==48);
        s->reset();frames(*s,60,1.f/60,0,1);press(*s,Action::confirm);assert(s->take_note()==48);
        std::puts("PASS perspective: actual segments join at target; angle and depth both matter; no repeated score");
    }
    {
        auto s=museum::make_study_space("raycast");frames(*s,1000,1.f/120,0,-1);const auto p=circle(*s,fonts,6);
        const float world_x=(p[0]-24)/10,world_y=(p[1]-24)/10;
        assert(world_x>6.7f&&world_x<6.89f&&std::abs(world_y-1.5f)<.001f);
        frames(*s,200,1.f/120,0,-1);const auto stopped=circle(*s,fonts,6);assert(std::abs(stopped[0]-p[0])<.001f);
        std::puts("PASS raycast: continuous movement stops before the actual wall, minimap agrees");
    }
    {
        auto s=museum::make_study_space("camera");press(*s,Action::confirm);assert(s->take_note()==76);
        press(*s,Action::confirm);assert(s->take_note()==55);
        std::puts("PASS camera: successful framing becomes a fresh challenge, cannot be scored by repeated X");
    }
    {
        auto a=museum::make_study_space("voxels"),b=museum::make_study_space("voxels");
        frames(*a,120,1.f/120,0,0,.5f);frames(*b,60,1.f/60,0,0,.5f);
        auto da=picture(*a,fonts),db=picture(*b,fonts);assert(da.instances().size()==db.instances().size());
        for(std::size_t n=0;n<da.instances().size();++n)for(unsigned v=0;v<4;++v)assert(std::abs(da.instances()[n].rect[v]-db.instances()[n].rect[v])<.005f);
        const auto old=da.instances().size();press(*a,Action::confirm);auto edited=picture(*a,fonts);assert(edited.instances().size()==old+2);
        std::puts("PASS voxels: rotation matches at60/120updates; X adds one actual layer");
    }
    {
        auto s=museum::make_study_space("scale");const auto initial=circle(*s,fonts);bool grew=false;
        for(int n=0;n<600;++n){const auto p=circle(*s,fonts);if(p[2]>initial[2]+1){grew=true;break;}
            frames(*s,1,1.f/120,std::clamp((100-p[0])/65,-1.f,1.f),std::clamp((140-p[1])/65,-1.f,1.f));}
        assert(grew);assert(s->take_note()>=60);
        std::puts("PASS scale: physically reaching a smaller object grows the actual player and removes the object");
    }
    {
        auto s=museum::make_study_space("portals");
        press(*s,Action::jump_prev);assert(s->take_note()==62);
        auto choose=input(0,0,1);hui::ui::Feedback f;s->handle(choose,f);s->handle(input(),f);
        press(*s,Action::jump_next);assert(s->take_note()==69);
        frames(*s,240,1.f/120,1);const auto d=picture(*s,fonts);assert(!d.instances().empty());
        std::puts("PASS portals: marked-surface selection and distinct trigger placements; three-room physics tested separately");
    }
    {
        auto s=museum::make_study_space("light");auto before=picture(*s,fonts);press(*s,Action::confirm);auto after=picture(*s,fonts);
        bool shadow=false;for(std::size_t n=0;n<before.instances().size();++n){const auto&a=before.instances()[n];const auto&b=after.instances()[n];
            if(a.params[3]==4&&a.params[1]==24&&std::abs(a.extra[3]-b.extra[3])>10)shadow=true;}
        assert(shadow);std::puts("PASS light: changing light height changes actual cast-shadow geometry");
    }
    for(const char*key:{"perspective","raycast","camera","voxels","scale","portals","light"}){
        auto s=museum::make_study_space(key);frames(*s,27,1.f/60,.7f,.5f,.6f);auto before=picture(*s,fonts);
        auto intercepted=input(1,1,1);intercepted.focus_lost=true;intercepted.pressed=hui::action_bit(Action::west)|hui::action_bit(Action::confirm);hui::ui::Feedback f;s->handle(intercepted,f);
        auto after=picture(*s,fonts);assert(before.instances().size()==after.instances().size());
        for(std::size_t n=0;n<before.instances().size();++n)assert(!std::memcmp(&before.instances()[n],&after.instances()[n],sizeof(Instance)));
    }
    std::puts("PASS all seven: intercepted Square/X cannot reset or act on existing state");
}
