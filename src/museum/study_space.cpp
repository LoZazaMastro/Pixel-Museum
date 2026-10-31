// Pixel Museum - original studies of composition, space and visual rules.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/study.hpp"
#include "museum/haptic_interactions.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <vector>
namespace museum {
struct PortalInspection;
struct SpaceFeedbackInspection;
namespace {
using namespace hui;using gfx::Color;using gfx::Rect;
constexpr float pi=3.14159265f;
// An original, side-on experiment in Portal's spatial rule. The chamber
// geometry, surface choices and objectives are authored, not random scenery.
class PortalStudy final:public Study {
    friend struct museum::PortalInspection;
    AcceptedMotionHaptics movement_;
    struct V {float x=0,y=0;};
    struct Surface {V p,n;};
    struct Trail {V p;bool after=false;};
    static constexpr float half_w=10,half_h=14,aperture=48,gravity=950;
    static constexpr int chamber_count=4;
    int chamber_=0,selected_=0,blue_=-1,orange_=-1,surface_count_=0,solid_count_=0;
    int crossings_=0,cube_crossings_=0,falls_=0,event_=0,pending_chamber_=-1,select_latch_=0;
    float clock_=0,axis_=0,cooldown_=0,burst_=0,rejected_=0,respawn_=-1,transition_=-1,trace_time_=0;
    float incoming_speed_=0,outgoing_speed_=0,cube_incoming_speed_=0,cube_outgoing_speed_=0,event_pan_=0;
    float gate_=0,cube_cooldown_=0,forecast_time_=0,completion_=0;int facing_=1;
    bool carrying_=false,cube_grounded_=true,plate_down_=false,touch_suppressed_=false;
    V cube_{},cube_velocity_{},cube_visual_{};
    std::array<V,45>forecast_{};unsigned forecast_count_=0;
    std::array<float,3>placement_{},selection_{};
    bool grounded_=true,complete_=false,left_trigger_=false,right_trigger_=false,paused_=false,horizontal_blocked_=false;
    V p_{},v_{},spawn_{},cube_spawn_{208,170};Rect exit_{},gate_rect_{};
    float plate_x_=704,plate_y_=300;
    std::array<Rect,8>solids_{};std::array<Surface,3>surfaces_{};
    std::array<Trail,70>trail_{};unsigned trace_head_=0,trace_count_=0;
    static float dot(V a,V b){return a.x*b.x+a.y*b.y;}
    static V tangent(V normal){return {-normal.y,normal.x};}
    static float speed(V a){return std::hypot(a.x,a.y);}
    static V through(V velocity,V entry,V exit){
        const float forward=-dot(velocity,entry),side=dot(velocity,tangent(entry));
        const V t=tangent(exit);
        return {exit.x*forward-t.x*side,exit.y*forward-t.y*side};
    }
    static float approach(float value,float target,float amount){return value<target?std::min(value+amount,target):std::max(value-amount,target);}
    bool has_cube()const{return chamber_==2;}
    void spawn(){p_=spawn_;v_={};grounded_=true;cooldown_=0;trace_count_=trace_head_=0;
        cube_=cube_spawn_;cube_visual_=cube_;cube_velocity_={};cube_grounded_=true;carrying_=plate_down_=false;gate_=cube_cooldown_=0;forecast_count_=0;forecast_time_=0;
    }
    void setup(int chamber){
        movement_.reset();chamber_=chamber;selected_=0;blue_=orange_=-1;crossings_=cube_crossings_=falls_=0;event_=0;
        clock_=axis_=cooldown_=burst_=rejected_=trace_time_=incoming_speed_=outgoing_speed_=0;
        respawn_=transition_=-1;pending_chamber_=-1;select_latch_=0;complete_=paused_=horizontal_blocked_=false;left_trigger_=right_trigger_=false;
        solids_={};surfaces_={};placement_={};selection_={1,0,0};completion_=0;facing_=1;touch_suppressed_=false;note_=-1;
        cube_spawn_={208,170};plate_x_=704;plate_y_=300;cube_incoming_speed_=cube_outgoing_speed_=0;
        solids_[0]={40,80,20,480};solids_[1]={940,80,20,480};
        if(chamber==0){
            solid_count_=4;solids_[2]={40,520,920,40};solids_[3]={440,120,120,400};
            surface_count_=2;surfaces_[0]={{440,486},{-1,0}};surfaces_[1]={{560,486},{1,0}};
            spawn_={160,506};exit_={900,464,36,56};
        }else if(chamber==1){
            solid_count_=6;solids_[2]={40,520,580,40};solids_[3]={60,200,270,20};
            solids_[4]={600,270,20,250};solids_[5]={850,470,110,20};
            surface_count_=2;surfaces_[0]={{480,520},{0,-1}};surfaces_[1]={{620,340},{1,0}};
            spawn_={170,186};exit_={900,414,36,56};
        }else if(chamber==2){
            solid_count_=7;solids_[2]={40,520,580,40};solids_[3]={60,180,270,20};
            solids_[4]={600,380,20,140};solids_[5]={800,520,160,40};solids_[6]={550,300,210,18};
            surface_count_=3;surfaces_[0]={{480,520},{0,-1}};surfaces_[1]={{620,430},{1,0}};surfaces_[2]={{870,520},{0,-1}};
            spawn_={170,166};exit_={590,244,36,56};
        }else{
            // A floor-to-ceiling loop builds speed. Reposition only its exit
            // to the far floor: that same speed becomes an upward fling.
            // The high ledge is outside the launch column, never a ceiling
            // blocking the fling, and cannot be reached by ordinary jumping.
            solid_count_=6;solids_[2]={40,520,360,40};solids_[3]={600,520,360,40};
            solids_[4]={60,100,340,20};solids_[5]={660,230,140,18};
            surface_count_=3;surfaces_[0]={{280,520},{0,-1}};surfaces_[1]={{280,120},{0,1}};surfaces_[2]={{850,520},{0,-1}};
            spawn_={280,506};exit_={696,174,36,56};
        }
        gate_rect_=exit_;
        spawn();
    }
    void place(bool blue,ui::Feedback&feedback){
        int&mine=blue?blue_:orange_;const int other=blue?orange_:blue_;
        if(mine==selected_)return;
        if(other==selected_){rejected_=.23f;feedback.feel(audio::Tactile::error,.10f,.035f);return;}
        mine=selected_;burst_=.25f;placement_[size_t(selected_)]=1;forecast_time_=0;sound(blue?62:69);
        feedback.feel(blue?audio::Tactile::rise:audio::Tactile::fall,.12f,.045f,blue?-.55f:.55f);feedback.speak(audio::SpeakerCue::portal_open,blue?.9f:1.15f,.12f);
    }
    bool traverse(V from,V to){
        if(blue_<0||orange_<0||cooldown_>0)return false;
        for(int pair=0;pair<2;++pair){
            const auto&in=surfaces_[size_t(pair?orange_:blue_)];const auto&out=surfaces_[size_t(pair?blue_:orange_)];
            const float before=dot({from.x-in.p.x,from.y-in.p.y},in.n),after=dot({to.x-in.p.x,to.y-in.p.y},in.n);
            if(before<half_h-.05f||after>half_h||dot(v_,in.n)>=-1.f||before-after<=.00001f)continue;
            const float fraction=std::clamp((before-half_h)/(before-after),0.f,1.f);
            const V hit{from.x+(to.x-from.x)*fraction,from.y+(to.y-from.y)*fraction};
            const float offset=dot({hit.x-in.p.x,hit.y-in.p.y},tangent(in.n));
            if(std::abs(offset)>aperture-half_h)continue;
            incoming_speed_=speed(v_);v_=through(v_,in.n,out.n);outgoing_speed_=speed(v_);
            const V t=tangent(out.n);p_={out.p.x+out.n.x*(half_h+1)-t.x*offset,out.p.y+out.n.y*(half_h+1)-t.y*offset};
            grounded_=false;cooldown_=.13f;burst_=.35f;event_=1;event_pan_=out.n.x*.65f;
            ++crossings_;sound(76);return true;
        }
        return false;
    }
    int collision_count()const{return solid_count_+(has_cube()&&!plate_down_?1:0);}
    Rect collision(int n)const{return n<solid_count_?solids_[size_t(n)]:gate_rect_;}
    void carry(ui::Feedback&feedback){
        if(!has_cube())return;
        if(carrying_){
            carrying_=false;cube_={p_.x+float(facing_)*25,p_.y-26};cube_velocity_=v_;cube_grounded_=false;
            feedback.feel(audio::Tactile::touch,.13f,.035f);sound(55);
        }else if(std::hypot(cube_.x-p_.x,cube_.y-p_.y)<54){
            carrying_=true;cube_grounded_=false;plate_down_=false;feedback.feel(audio::Tactile::touch,.11f,.035f);sound(64);
        }else feedback.feel(audio::Tactile::error,.07f,.025f);
    }
    void cube_physics(float dt){
        if(!has_cube())return;
        if(carrying_){cube_={p_.x,p_.y-30};cube_velocity_=v_;cube_grounded_=false;plate_down_=false;return;}
        constexpr float radius=10;
        cube_cooldown_=std::max(0.f,cube_cooldown_-dt);
        if(cube_grounded_)cube_velocity_.x=approach(cube_velocity_.x,0,dt*550);
        cube_velocity_.y=std::min(cube_velocity_.y+gravity*dt,1800.f);
        const V before=cube_,next{cube_.x+cube_velocity_.x*dt,cube_.y+cube_velocity_.y*dt};
        if(blue_>=0&&orange_>=0&&cube_cooldown_<=0){
            for(int pair=0;pair<2;++pair){
                const auto&in=surfaces_[size_t(pair?orange_:blue_)];const auto&out=surfaces_[size_t(pair?blue_:orange_)];
                const float a=dot({before.x-in.p.x,before.y-in.p.y},in.n),b=dot({next.x-in.p.x,next.y-in.p.y},in.n);
                if(a<radius-.05f||b>radius||dot(cube_velocity_,in.n)>=-1||a-b<=.00001f)continue;
                const float fraction=std::clamp((a-radius)/(a-b),0.f,1.f);const V hit{before.x+(next.x-before.x)*fraction,before.y+(next.y-before.y)*fraction};
                const float offset=dot({hit.x-in.p.x,hit.y-in.p.y},tangent(in.n));if(std::abs(offset)>aperture-radius)continue;
                cube_incoming_speed_=speed(cube_velocity_);cube_velocity_=through(cube_velocity_,in.n,out.n);cube_outgoing_speed_=speed(cube_velocity_);const auto t=tangent(out.n);
                cube_={out.p.x+out.n.x*(radius+1)-t.x*offset,out.p.y+out.n.y*(radius+1)-t.y*offset};cube_cooldown_=.13f;cube_grounded_=false;
                ++cube_crossings_;event_=7;event_pan_=out.p.x<500?-.55f:.55f;sound(73);return;
            }
        }
        cube_.x=next.x;
        for(int n=0;n<collision_count();++n){const auto r=collision(n);if(before.y+radius<=r.y+.01f||before.y-radius>=r.y+r.h-.01f)continue;
            if(cube_velocity_.x>0&&before.x+radius<=r.x+.01f&&cube_.x+radius>r.x){cube_.x=r.x-radius;cube_velocity_.x=0;}
            else if(cube_velocity_.x<0&&before.x-radius>=r.x+r.w-.01f&&cube_.x-radius<r.x+r.w){cube_.x=r.x+r.w+radius;cube_velocity_.x=0;}}
        cube_.y=next.y;cube_grounded_=false;
        for(int n=0;n<collision_count();++n){const auto r=collision(n);if(cube_.x+radius<=r.x+.01f||cube_.x-radius>=r.x+r.w-.01f)continue;
            if(cube_velocity_.y>=0&&before.y+radius<=r.y+.05f&&cube_.y+radius>r.y){cube_.y=r.y-radius;cube_velocity_.y=0;cube_grounded_=true;}
            else if(cube_velocity_.y<0&&before.y-radius>=r.y+r.h-.01f&&cube_.y-radius<r.y+r.h){cube_.y=r.y+r.h+radius;cube_velocity_.y=0;}}
        if(cube_.y>650){cube_=cube_spawn_;cube_visual_=cube_;cube_velocity_={};cube_grounded_=true;}
        const bool down=cube_grounded_&&std::abs(cube_.y-(plate_y_-radius))<.1f&&std::abs(cube_.x-plate_x_)<21;
        if(down&&!plate_down_){event_=4;sound(72);}plate_down_=down;
    }
    void forecast(){
        forecast_count_=0;if(complete_||respawn_>=0||blue_<0||orange_<0)return;
        // Predict with the SAME collision/portal integrator, without advancing
        // the real room, publishing feedback, or allocating in the frame loop.
        PortalStudy future=*this;future.event_=0;
        for(unsigned tick=0;tick<180&&!future.complete_&&future.respawn_<0;++tick){
            future.cooldown_=std::max(0.f,future.cooldown_-1.f/120);future.physics(1.f/120);
            if(tick%4==3)forecast_[forecast_count_++]=future.p_;
        }
    }
    void physics(float dt){
        cube_physics(dt);
        if(grounded_)v_.x=approach(v_.x,axis_*190,dt*(std::abs(axis_)>.01f?1600:1150));
        else if(std::abs(v_.x)<190||axis_*v_.x<0)v_.x+=axis_*95*dt;
        v_.y=std::min(v_.y+gravity*dt,1800.f);
        const bool was_grounded=grounded_;const float falling_speed=v_.y;
        const V before=p_,next{p_.x+v_.x*dt,p_.y+v_.y*dt};
        if(traverse(before,next))return;
        p_.x=next.x;
        for(int n=0;n<collision_count();++n){
            const auto r=collision(n);
            if(before.y+half_h<=r.y+.01f||before.y-half_h>=r.y+r.h-.01f)continue;
            if(v_.x>0&&before.x+half_w<=r.x+.01f&&p_.x+half_w>r.x){p_.x=r.x-half_w;if(!horizontal_blocked_&&!event_){event_=6;event_pan_=.65f;}horizontal_blocked_=true;v_.x=0;}
            else if(v_.x<0&&before.x-half_w>=r.x+r.w-.01f&&p_.x-half_w<r.x+r.w){p_.x=r.x+r.w+half_w;if(!horizontal_blocked_&&!event_){event_=6;event_pan_=-.65f;}horizontal_blocked_=true;v_.x=0;}
        }
        grounded_=false;p_.y=next.y;
        for(int n=0;n<collision_count();++n){
            const auto r=collision(n);
            if(p_.x+half_w<=r.x+.01f||p_.x-half_w>=r.x+r.w-.01f)continue;
            if(v_.y>=0&&before.y+half_h<=r.y+.05f&&p_.y+half_h>r.y){p_.y=r.y-half_h;grounded_=true;v_.y=0;}
            else if(v_.y<0&&before.y-half_h>=r.y+r.h-.01f&&p_.y-half_h<r.y+r.h){p_.y=r.y+r.h+half_h;v_.y=0;if(!event_){event_=6;event_pan_=0;}}
        }
        if(grounded_&&!was_grounded&&falling_speed>45&&!event_)event_=5;
        if(p_.y>650){++falls_;respawn_=0;event_=2;sound(40);return;}
        if((!has_cube()||plate_down_)&&grounded_&&p_.x>exit_.x&&p_.x<exit_.x+exit_.w&&p_.y+half_h>=exit_.y&&p_.y<exit_.y+exit_.h){
            complete_=true;v_={};event_=3;sound(chamber_==2?84:79);
        }
    }
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"completed",completion()==StudyCompletion::experience_complete?1u:0u}};}
    PortalStudy(){reset();}
    void reset()override{setup(0);}
    StudyCompletion completion()const override{return !complete_?StudyCompletion::playing:chamber_+1==chamber_count?StudyCompletion::experience_complete:StudyCompletion::level_complete;}
    int level_number()const override{return chamber_+1;}
    int level_count()const override{return chamber_count;}
    void continue_level()override{if(!complete_)return;if(chamber_+1==chamber_count)reset();else setup(chamber_+1);}
    void handle(const InputFrame&i,ui::Feedback&f)override{
        paused_=i.focus_lost||!i.connected;if(paused_){movement_.reset();event_=0;axis_=0;select_latch_=0;touch_suppressed_=true;left_trigger_=right_trigger_=true;return;}
        movement_.drain(f,event_!=0);
        if(event_){
            if(event_==1){f.feel(audio::Tactile::zoom_in,std::clamp(.12f+incoming_speed_*.00015f,.12f,.28f),.065f,event_pan_);f.speak(audio::SpeakerCue::portal_cross,std::clamp(.85f+incoming_speed_/1500.f,.85f,1.7f),.13f);}
            else if(event_==7){f.feel(audio::Tactile::zoom_in,.12f,.045f,event_pan_);f.speak(audio::SpeakerCue::portal_cross,std::clamp(.85f+cube_incoming_speed_/1500.f,.85f,1.7f),.10f);}
            else if(event_==2)f.feel(audio::Tactile::error,.12f,.05f);
            else if(event_==3)f.feel(audio::Tactile::confirm,.30f,.13f);
            else if(event_==5)f.feel(audio::Tactile::fall,.055f,.025f);
            else if(event_==6)f.feel(audio::Tactile::touch,.045f,.018f,event_pan_);
            else f.feel(audio::Tactile::touch,.18f,.07f);
            event_=0;
        }
        if(i.is_pressed(Action::west)){setup(chamber_);f.feel(audio::Tactile::back,.10f,.04f);return;}
        if(transition_>=0)return;
        if(complete_)return; // Shared completion sheet owns Continue / Exit.
        axis_=std::isfinite(i.stick_x)?std::clamp(i.stick_x,-1.f,1.f):0;
        if(std::abs(axis_)<.05f)axis_=float(i.is_held(Action::right))-float(i.is_held(Action::left));
        if(std::abs(axis_)>.05f)facing_=axis_>0?1:-1;
        const bool contact=i.touch.available&&i.touch.count>0;
        if(!contact)touch_suppressed_=false;
        if(contact&&!touch_suppressed_&&std::isfinite(i.touch.points[0].x)&&std::isfinite(i.touch.points[0].y)){
            const V point{std::clamp(i.touch.points[0].x,0.f,1.f)*1000,std::clamp(i.touch.points[0].y,0.f,1.f)*600};
            int closest=0;float distance=1e9f;
            for(int n=0;n<surface_count_;++n){const auto s=surfaces_[size_t(n)];const float q=std::hypot(s.p.x-point.x,s.p.y-point.y);if(q<distance){distance=q;closest=n;}}
            if(closest!=selected_){selected_=closest;f.feel(audio::Tactile::focus,.06f,.018f);}
        }
        if(i.is_pressed(Action::north))carry(f);
        const float sx=std::isfinite(i.stick2_x)?i.stick2_x:0,sy=std::isfinite(i.stick2_y)?i.stick2_y:0;
        const float choose=std::abs(sx)>std::abs(sy)?sx:sy;const int direction=choose>.55f?1:choose<-.55f?-1:0;
        if(!contact&&direction&&direction!=select_latch_){selected_=(selected_+surface_count_+direction)%surface_count_;select_latch_=direction;f.feel(audio::Tactile::focus,.07f,.018f);}
        if(std::abs(choose)<.3f)select_latch_=0;
        const bool left=(std::isfinite(i.trigger_l)&&i.trigger_l>.55f)||i.is_pressed(Action::jump_prev);
        const bool right=(std::isfinite(i.trigger_r)&&i.trigger_r>.55f)||i.is_pressed(Action::jump_next);
        if(left&&!left_trigger_)place(true,f);if(right&&!right_trigger_)place(false,f);
        left_trigger_=(std::isfinite(i.trigger_l)&&i.trigger_l>.25f)||i.is_held(Action::jump_prev);
        right_trigger_=(std::isfinite(i.trigger_r)&&i.trigger_r>.25f)||i.is_held(Action::jump_next);
        if(i.is_pressed(Action::confirm)&&grounded_&&respawn_<0){v_.y=-340;grounded_=false;sound(58);f.feel(audio::Tactile::touch,.10f,.035f);}
    }
    void update(float dt)override{
        if(paused_||!std::isfinite(dt)||dt<=0)return;dt=std::min(dt,.05f);movement_.advance(dt);clock_+=dt;
        burst_=std::max(0.f,burst_-dt);rejected_=std::max(0.f,rejected_-dt);
        for(auto&amount:placement_)amount=std::max(0.f,amount-dt*3);
        for(int n=0;n<surface_count_;++n)selection_[size_t(n)]=approach(selection_[size_t(n)],n==selected_?1.f:0.f,dt*7);
        completion_=approach(completion_,complete_?1.f:0.f,dt*4);
        gate_=approach(gate_,plate_down_?1.f:0.f,dt*4);
        if(transition_>=0){
            transition_+=dt;
            if(transition_>=.18f&&pending_chamber_>=0){const float time=transition_;const int chamber=pending_chamber_;setup(chamber);transition_=time;}
            if(transition_>=.36f)transition_=-1;return;
        }
        if(complete_)return;
        if(respawn_>=0){respawn_+=dt;if(respawn_>.3f){spawn();respawn_=-1;}return;}
        const auto previous_player=p_;if(std::abs(axis_)<.05f)horizontal_blocked_=false;
        const int count=std::max(1,int(std::ceil(dt*240)));const float step=dt/float(count);
        for(int n=0;n<count&&!complete_&&respawn_<0;++n){cooldown_=std::max(0.f,cooldown_-step);physics(step);}
        if(std::abs(p_.x-previous_player.x)>.05f)horizontal_blocked_=false;
        if(!event_&&respawn_<0)movement_.record(p_.x-previous_player.x,0,std::abs(axis_)>.15f);
        const float blend=1-std::exp(-dt*22);cube_visual_.x+=(cube_.x-cube_visual_.x)*blend;cube_visual_.y+=(cube_.y-cube_visual_.y)*blend;
        // Portal traversal is discontinuous in world coordinates: the cube
        // crosses with its carrier instead of visibly sweeping through walls.
        if(std::hypot(cube_visual_.x-cube_.x,cube_visual_.y-cube_.y)>150)cube_visual_=cube_;
        forecast_time_-=dt;if(forecast_time_<=0){forecast_time_=.09f;forecast();}
        trace_time_+=dt;
        if(!grounded_&&trace_time_>=1.f/30){trace_time_=0;trail_[trace_head_]={p_,crossings_>0};trace_head_=(trace_head_+1)%unsigned(trail_.size());trace_count_=std::min(unsigned(trail_.size()),trace_count_+1);}
    }
    const char*help()const override{return "Move, choose a marked surface with the right stick or touchpad, and place the two portals. Jump from solid ground. The dotted arc predicts the current route. Carry cubes with Triangle and leave them resting on pressure plates. In the final room connect the floor to the ceiling, fall once, then move the exit portal to the far floor and steer left onto the high ledge. Restart this chamber at any time.";}
    void draw(gfx::DrawList&d,ui::Fonts&f,Rect b,Color)override{
        const float scale=std::min(b.w/1000,b.h/600),ox=b.x+(b.w-1000*scale)/2,oy=b.y+(b.h-600*scale)/2;
        const Color paper=Color::rgb(0xf1efe7),quiet=Color::rgb(0x8a938c),base=Color::rgb(0x0d1310),blue=Color::rgb(0x7caeb8),orange=Color::rgb(0xc99370);
        d.push_clip(b);d.rounded_rect(b,0,base);d.push_transform(scale,0,0,ox,oy);d.rounded_rect({0,0,1000,600},0,base);
        static constexpr const char*titles[]={"Connect the two sides","Turn a fall into distance","A cube keeps the door open","Build speed, then redirect it"};
        const auto&display=f.display.font?f.display:f.semibold;float title_size=22;
        while(title_size>16&&display.measure(titles[chamber_],title_size)>570)title_size-=1;
        ui::text(d,display,titles[chamber_],244,40,title_size,paper);
        for(int n=0;n<chamber_count;++n){const float x=64+float(n)*26;d.bordered_rect({x,42,15,15},3,n<=chamber_?paper.with_alpha(n==chamber_?.9f:.32f):paper.with_alpha(0.f),1,paper.with_alpha(.3f));}
        if(complete_){d.line(482,53,495,65,2.4f,paper.with_alpha(completion_));d.line(495,65,520,39,2.4f,paper.with_alpha(completion_));}
        for(int n=0;n<solid_count_;++n){const auto r=solids_[size_t(n)];d.rounded_rect(r,0,Color::rgb(0x18201b));d.line(r.x,r.y,r.x+r.w,r.y,1.4f,paper.with_alpha(.45f));}
        if(chamber_==1||chamber_==2||chamber_==3)for(int n=0;n<20;++n){const float x=(chamber_==3?420.f:625.f)+float(n)*8;if(chamber_==2&&x>795)break;d.line(x,555,x+4,551,1,quiet.with_alpha(.28f));}
        const float clear_glow=complete_?.65f+.2f*std::sin(clock_*3):.42f;
        d.bordered_rect(exit_,3,paper.with_alpha(complete_?.10f:0.f),2,paper.with_alpha(clear_glow));
        if(has_cube()){
            const float gx=gate_rect_.x+gate_rect_.w/2;
            for(int n=0;n<3;++n){const float y=gate_rect_.y+gate_rect_.h*(float(n)+.5f)/3;d.line(gate_rect_.x+3,y,gx-8*gate_,y,1.3f,paper.with_alpha(.65f*(1-gate_)));d.line(gx+8*gate_,y,gate_rect_.x+gate_rect_.w-3,y,1.3f,paper.with_alpha(.65f*(1-gate_)));}
            const auto signal=paper.with_alpha(.15f+.48f*gate_);
            const float wire_y=plate_y_+18;
            d.line(plate_x_,plate_y_+7,plate_x_,wire_y,1,signal);d.line(plate_x_,wire_y,gx,wire_y,1,signal);d.line(gx,wire_y,gx,gate_rect_.y+gate_rect_.h,1,signal);
            d.bordered_rect({plate_x_-21,plate_y_-5+2*gate_,42,5},2,paper.with_alpha(.14f+.45f*gate_),1,paper.with_alpha(.6f));
            d.circle(plate_x_,plate_y_+10,2.5f,signal);
            const V c=cube_visual_;const float h=carrying_?11:10;
            d.bordered_rect({c.x-h,c.y-h,h*2,h*2},3,base,1.5f,paper.with_alpha(.8f));
            d.line(c.x-4,c.y,c.x+4,c.y,1,paper.with_alpha(.55f));d.line(c.x,c.y-4,c.x,c.y+4,1,paper.with_alpha(.55f));
            if(!carrying_&&std::hypot(cube_.x-p_.x,cube_.y-p_.y)<54){const float a=.4f+.2f*std::sin(clock_*4);for(int k=0;k<24;++k){const float u=float(k)*2*pi/24,v=float(k+1)*2*pi/24;d.line(c.x+17*std::cos(u),c.y+17*std::sin(u),c.x+17*std::cos(v),c.y+17*std::sin(v),1,paper.with_alpha(a));}}
        }
        const float ex=exit_.x+exit_.w/2,ey=exit_.y+exit_.h/2;
        d.line(ex-8,ey,ex+8,ey,1.5f,paper.with_alpha(.8f));d.line(ex+2,ey-6,ex+8,ey,1.5f,paper.with_alpha(.8f));d.line(ex+2,ey+6,ex+8,ey,1.5f,paper.with_alpha(.8f));

        for(int n=0;n<surface_count_;++n){
            const auto s=surfaces_[size_t(n)];const V t=tangent(s.n);const float chosen=selection_[size_t(n)];const bool occupied=n==blue_||n==orange_;
            const Color color=n==blue_?blue:n==orange_?orange:paper;
            const float expand=placement_[size_t(n)]*10;
            d.line(s.p.x-t.x*(aperture+5),s.p.y-t.y*(aperture+5),s.p.x+t.x*(aperture+5),s.p.y+t.y*(aperture+5),5,paper.with_alpha(.45f+.45f*chosen));
            if(chosen>.001f){
                const float alpha=rejected_>0?.75f:.24f+.10f*std::sin(clock_*4);
                d.line(s.p.x+s.n.x*20-t.x*(aperture+8),s.p.y+s.n.y*20-t.y*(aperture+8),s.p.x+s.n.x*20+t.x*(aperture+8),s.p.y+s.n.y*20+t.y*(aperture+8),1,paper.with_alpha(alpha*chosen));
                d.circle(s.p.x+s.n.x*28,s.p.y+s.n.y*28,2.5f,paper.with_alpha(chosen));
            }
            if(occupied){
                for(int a=0;a<36;++a){const float u=float(a)*2*pi/36,v=float(a+1)*2*pi/36;
                    d.line(s.p.x+t.x*(aperture+expand)*std::cos(u)+s.n.x*7*std::sin(u),s.p.y+t.y*(aperture+expand)*std::cos(u)+s.n.y*7*std::sin(u),s.p.x+t.x*(aperture+expand)*std::cos(v)+s.n.x*7*std::sin(v),s.p.y+t.y*(aperture+expand)*std::cos(v)+s.n.y*7*std::sin(v),2.6f,color.with_alpha(1-placement_[size_t(n)]));}
                d.line(s.p.x+s.n.x*15,s.p.y+s.n.y*15,s.p.x+s.n.x*29,s.p.y+s.n.y*29,1.2f,color.with_alpha(.75f));
            }
        }
        if(!grounded_||std::abs(v_.x)>8)for(unsigned n=0;n<forecast_count_;++n){const V q=forecast_[n];if(q.y<580&&q.x>45&&q.x<955)d.circle(q.x,q.y,1.3f,paper.with_alpha(.25f*(1-float(n)/float(forecast_count_))));}
        for(unsigned n=0;n<trace_count_;++n){const auto&point=trail_[(trace_head_+unsigned(trail_.size())-trace_count_+n)%unsigned(trail_.size())];const float alpha=.22f*float(n+1)/float(trace_count_);d.circle(point.p.x,point.p.y,1.7f,(point.after?orange:paper).with_alpha(alpha));}
        if(p_.y<625){
            const float alpha=respawn_<0?1.f:std::max(0.f,1-respawn_*5);
            d.rounded_rect({p_.x-half_w,p_.y-half_h,half_w*2,half_h*2},4,paper.with_alpha(alpha));
            d.line(p_.x-5,p_.y-6,p_.x+5,p_.y-6,2,base.with_alpha(alpha));
            if(!grounded_&&speed(v_)>270){const float length=std::min(65.f,speed(v_)*.065f),factor=length/std::max(1.f,speed(v_));d.line(p_.x,p_.y+18,p_.x+v_.x*factor,p_.y+18+v_.y*factor,1,orange.with_alpha(.55f));}
        }
        if(incoming_speed_>0){const float length=std::min(95.f,incoming_speed_*.09f);d.line(810,578,810+length,578,2,blue.with_alpha(.55f));d.line(810,584,810+length,584,2,orange.with_alpha(.55f));}
        d.circle(900,55,4,blue_<0?quiet.with_alpha(.3f):blue); // paired-state legend
        d.circle(924,55,4,orange_<0?quiet.with_alpha(.3f):orange);

        if(transition_>=0){const float veil=1-std::abs(transition_-.18f)/.18f;d.rounded_rect({0,0,1000,600},0,base.with_alpha(std::clamp(veil,0.f,1.f)));}
        d.pop_transform();d.pop_clip();
    }
};
class SpaceStudy final:public Study {
    friend struct museum::SpaceFeedbackInspection;
    AcceptedMotionHaptics movement_;
    int pending_growth_=0;float pending_impact_=0,roll_cooldown_=0;bool pending_roll_=false,suspended_=false,wall_latch_=false,was_moving_=false;
    int mode_=0,score_=0,cx_=3,cy_=3;float t_=0,x_=200,y_=300,vx_=0,vy_=0,angle_=0,other_=.4f,ax_=0,ay_=0,turn_=0,cool_=0,growth_=22;
    bool action_=false;std::array<int,64> blocks_{};std::array<bool,24> gathered_{};std::array<bool,3>survey_{};
    static constexpr float survey_points_[3][2]={{3.5f,1.5f},{5.5f,3.5f},{3.5f,5.5f}};
    static constexpr const char* map_[9]={"11111111","10000001","10111001","10001001","11001001","10000001","10011001","11111111","11111111"};
    bool wall(float x,float y)const{if(!std::isfinite(x)||!std::isfinite(y)||x<0||y<0||x>=8||y>=8)return true;const int xx=int(x),yy=int(y);return map_[yy][xx]=='1';}
    void counter(gfx::DrawList&d,ui::Fonts&f,Color color)const{
        const auto&display=f.display.font?f.display:f.semibold;char value[24];
        if(mode_==4)std::snprintf(value,sizeof(value),"%02d / 24",score_);else std::snprintf(value,sizeof(value),"%02d",score_);
        const float x=974-display.measure(value,25)-29,y=26;
        if(mode_==4){
            d.circle(x,y,8, color.with_alpha(.12f));d.ring(x,y,8,1.4f,color);
            d.rounded_rect({x-3,y-3,6,6},1,color);
            d.rounded_rect({x-15,y+3,4,4},1,color.with_alpha(.6f));
        }else if(mode_==2){
            d.bordered_rect({x-10,y-7,20,14},2,Color::rgb(0,0),1.4f,color);
            d.ring(x,y,4,1.2f,color);d.rounded_rect({x-6,y-10,7,3},1,color);
        }else{
            d.ring(x,y,8,1.3f,color);d.line(x-12,y,x-4,y,1.3f,color);d.line(x+4,y,x+12,y,1.3f,color);
            d.line(x,y-12,x,y-4,1.3f,color);d.line(x,y+4,x,y+12,1.3f,color);
        }
        ui::text(d,display,value,974,35,25,color,gfx::Align::right);
    }
    void cue(int n){sound(n);cool_=.5f;}
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return mode_==4?std::map<std::string,std::uint64_t>{{"completed",completion()==StudyCompletion::experience_complete?1u:0u}}:std::map<std::string,std::uint64_t>{};}
    explicit SpaceStudy(int m):mode_(m){reset();}
    StudyCompletion completion()const override{return (mode_==1&&score_>=3)||(mode_==4&&score_>=24)?StudyCompletion::experience_complete:StudyCompletion::playing;}
    void reset()override{movement_.reset();pending_impact_=0;pending_growth_=0;pending_roll_=false;roll_cooldown_=0;suspended_=wall_latch_=was_moving_=false;score_=0;t_=0;x_=mode_==1?1.5f:200;y_=mode_==1?1.5f:300;vx_=vy_=angle_=ax_=ay_=turn_=cool_=0;other_=.4f;action_=false;growth_=22;cx_=cy_=3;gathered_.fill(false);survey_.fill(false);blocks_.fill(0);blocks_[27]=2;blocks_[28]=1;blocks_[35]=1;note_=-1;}
    void handle(const InputFrame&i,ui::Feedback&f)override{
        suspended_=i.focus_lost||!i.connected;if(suspended_){movement_.reset();pending_impact_=0;pending_growth_=0;pending_roll_=false;roll_cooldown_=0;ax_=ay_=turn_=0;action_=false;return;}
        movement_.drain(f,pending_impact_>0||pending_growth_>0||pending_roll_);if(pending_growth_>0){f.feel(audio::Tactile::rise,std::min(.25f,.14f+pending_growth_*.025f),.065f);f.speak(audio::SpeakerCue::grow,std::clamp(.8f+(growth_-22.f)/84.f,.8f,1.8f),.12f);pending_growth_=0;pending_impact_=0;}else if(pending_impact_>0){f.feel(audio::Tactile::impact,pending_impact_,.035f);pending_impact_=0;}else if(pending_roll_)f.feel(audio::Tactile::scroll,std::min(.13f,.09f+(growth_-22.f)*.00045f),.035f);pending_roll_=false;
        if(i.is_pressed(Action::west)){reset();f.feel(hui::audio::Tactile::back,.12f,.045f);return;}
        ax_=std::isfinite(i.stick_x)?std::clamp(i.stick_x,-1.f,1.f):0;
        ay_=std::isfinite(i.stick_y)?std::clamp(i.stick_y,-1.f,1.f):0;
        if(std::abs(ax_)<.05f)ax_=float(i.is_held(Action::right))-float(i.is_held(Action::left));
        if(std::abs(ay_)<.05f)ay_=float(i.is_held(Action::down))-float(i.is_held(Action::up));
        if(mode_==3){
            const int old_x=cx_,old_y=cy_;
            if(i.nav==Direction::left)cx_=std::max(0,cx_-1);if(i.nav==Direction::right)cx_=std::min(7,cx_+1);
            if(i.nav==Direction::up)cy_=std::max(0,cy_-1);if(i.nav==Direction::down)cy_=std::min(7,cy_+1);
            if(old_x!=cx_||old_y!=cy_){movement_.step(float(cx_-old_x),float(cy_-old_y));movement_.drain(f,!f.tactile.empty());}
            turn_=std::isfinite(i.stick2_x)?std::clamp(i.stick2_x,-1.f,1.f):0;
        }
        if(i.is_pressed(Action::confirm)){
            if(mode_!=1&&mode_!=4)f.feel(hui::audio::Tactile::confirm,.13f,.05f);
            if(mode_==0){if(std::abs(std::sin(angle_))<.08f&&std::abs(other_-.4f)<.05f){++score_;sound(72);angle_+=.7f;other_=.72f;}else sound(48);}
            else if(mode_==2){if(std::abs(std::sin(angle_))<.15f&&std::abs(other_-.4f)<.12f){++score_;sound(76);angle_+=.65f;other_=.72f;}else sound(55);}
            else if(mode_==3){auto&h=blocks_[size_t(cy_*8+cx_)];h=(h+1)%5;sound(60+h*3);}
            else if(mode_==6){other_=std::clamp(other_+.2f,.2f,1.f);if(other_>=.99f)other_=.2f;sound(60+int(other_*12));}
            else{action_=true;sound(65);}
        }
    }
    void update(float dt)override{
        if(suspended_||!std::isfinite(dt)||dt<=0)return;dt=std::min(dt,.05f);movement_.advance(dt);const float before_x=x_,before_y=y_,before_angle=angle_,before_depth=other_;t_+=dt;cool_=std::max(0.f,cool_-dt);
        if(mode_==0){angle_+=ax_*dt;other_=std::clamp(other_+ay_*dt*.5f,0.f,1.f);}
        if(mode_==1){angle_+=ax_*dt*1.7f;const float speed=-ay_*dt*1.5f;
            const float nx=x_+std::cos(angle_)*speed,ny=y_+std::sin(angle_)*speed;
            if(!wall(nx+.12f,y_)&&!wall(nx-.12f,y_))x_=nx;if(!wall(x_,ny+.12f)&&!wall(x_,ny-.12f))y_=ny;
            for(unsigned n=0;n<survey_.size();++n)if(!survey_[n]&&std::hypot(x_-survey_points_[n][0],y_-survey_points_[n][1])<.30f){survey_[n]=true;++score_;cue(65+int(n)*4);pending_impact_=.10f;}
        }
        if(mode_==2){angle_+=ax_*dt;other_=std::clamp(other_+ay_*dt*.4f,0.f,1.f);}
        if(mode_==3)angle_+=turn_*dt*1.2f;
        if(mode_==4){
            vx_+=(ax_*460-vx_*2.3f)*dt;vy_+=(ay_*460-vy_*2.3f)*dt;x_=std::clamp(x_+vx_*dt,50.f,950.f);y_=std::clamp(y_+vy_*dt,50.f,550.f);
            if(mode_==4)for(int n=0;n<24;++n){const float px=100+float(n%8)*114,py=140+float(n/8)*154,sz=8+float(n%6)*8;
                if(!gathered_[size_t(n)]&&sz<growth_&&std::hypot(x_-px,y_-py)<growth_*.65f+sz){gathered_[size_t(n)]=true;growth_+=3.5f;++score_;++pending_growth_;sound(60+n%5*3);pending_impact_=.12f;}}
        }
        if(mode_==6)angle_+=ax_*dt;
        if(mode_==1){movement_.record(angle_-before_angle,-std::hypot(x_-before_x,y_-before_y)*(ay_>0?1:-1),std::abs(ax_)+std::abs(ay_)>.15f);const bool stopped=std::abs(ay_)>.25f&&std::hypot(x_-before_x,y_-before_y)<.00001f;if(stopped&&!wall_latch_&&was_moving_)pending_impact_=.045f;wall_latch_=stopped;was_moving_=std::hypot(x_-before_x,y_-before_y)>.00001f;}
        if(mode_==4){movement_.record(x_-before_x,y_-before_y,std::abs(ax_)+std::abs(ay_)>.15f);roll_cooldown_=std::max(0.f,roll_cooldown_-dt);if(std::abs(ax_)+std::abs(ay_)>.15f&&std::hypot(x_-before_x,y_-before_y)>.4f&&roll_cooldown_<=0){pending_roll_=true;roll_cooldown_=.23f;}}
        if(mode_==0||mode_==2)movement_.record(angle_-before_angle,other_-before_depth,std::abs(ax_)+std::abs(ay_)>.15f);
        if(mode_==3||mode_==6)movement_.record(angle_-before_angle,0,std::abs(mode_==3?turn_:ax_)>.15f);
        action_=false;
    }
    const char*help()const override{
        static constexpr const char*text[]={
            "Left / right: change angle. Up / down: change depth. X: test the joined silhouette. Square: reset.",
            "Left / right: turn. Up / down: move. Find the three marks on the plan and compare the map with the corridor. Square: return to the entrance.",
            "Left / right: orbit the camera. Up / down: change its height. X: frame the three markers. Square: reset.",
            "D-pad: select a tile. X: change its height. Right stick: turn the composition. Square: reset.",
            "Left stick / D-pad: roll. Collect objects smaller than you to change the scale. Square: reset.",
            "", // Portal has its own gravity simulation above.
            "Left / right: move the light. X: change its height and shadow length. Square: reset."};return text[mode_];
    }
    void draw(gfx::DrawList&d,ui::Fonts&f,Rect b,Color accent)override{
        const float scale=std::min(b.w/1000,b.h/600),ox=b.x+(b.w-1000*scale)/2,oy=b.y+(b.h-600*scale)/2;
        const Color white=Color::rgb(0xf1efe7),quiet=Color::rgb(0x929890),base=Color::rgb(0x101512);
        d.push_clip(b);d.rounded_rect(b,0,base);d.push_transform(scale,0,0,ox,oy);d.rounded_rect({0,0,1000,600},0,base);
        if(mode_==0){
            // Disconnected pieces share one silhouette only at the right angle.
            const float shift=std::sin(angle_)*180,depth=(other_-.4f)*100;
            constexpr float ends[5][4]={{300,440,300,160},{300,160,500,350},
                {500,350,690,160},{690,160,690,440},{300,440,690,440}};
            for(int n=0;n<5;++n){const float dx=shift*float(n-2)*.25f,dy=depth*float(n-2)*.6f;
                d.line(ends[n][0]+dx,ends[n][1]+dy,ends[n][2]+dx,ends[n][3]+dy,19,accent.with_alpha(.45f+float(n)*.1f));}
            d.bordered_rect({280,115,440,340},0,Color::rgb(0,0),1,white.with_alpha(.15f));
        }else if(mode_==1){
            const Color rust=white.with_alpha(1),wall_dark=Color::rgb(0x151a17);
            // Widen the camera's field of view, not the authored geometry:
            // the original centre and projection plane retain their scale.
            const float view_left=(b.x-ox)/scale,view_right=(b.x+b.w-ox)/scale;
            constexpr float column_width=1000.f/180;
            const float projection_plane=500/std::tan(.575f);
            const int first_column=int(std::floor(view_left/column_width)),last_column=int(std::ceil(view_right/column_width));
            const int column_count=last_column-first_column;
            d.gradient_rect({view_left,0,view_right-view_left,300},0,Color::rgb(0x151a17),wall_dark);d.gradient_rect({view_left,300,view_right-view_left,300},0,wall_dark,Color::rgb(0x101512));
            std::vector<float> depth(size_t(column_count),0.f);
            for(int n=0;n<column_count;++n){const float sx=(float(first_column+n)+.5f)*column_width;
                const float ray=angle_+std::atan((sx-500)/projection_plane);float distance=.03f;
                for(int step=0;step<130&&!wall(x_+std::cos(ray)*distance,y_+std::sin(ray)*distance);++step)distance+=.045f;
                const float hx=x_+std::cos(ray)*distance,hy=y_+std::sin(ray)*distance;
                const float u=std::min(hx-std::floor(hx),hy-std::floor(hy));
                distance*=std::cos(ray-angle_);depth[size_t(n)]=distance;const float h=std::min(580.f,360/std::max(.08f,distance));
                const Color face=gfx::mix(rust,wall_dark,std::clamp(distance/8+(u<.045f?.14f:0),0.f,.9f));
                d.rounded_rect({float(first_column+n)*column_width,300-h/2,column_width+1,h},0,face);
                d.rounded_rect({float(first_column+n)*column_width,300-h*.31f,column_width+1,std::max(1.f,h*.012f)},0,white.with_alpha(.075f));
            }
            // The plan and eye-level view share these exact world coordinates.
            // Paint a survey beacon only through columns not hidden by a wall.
            std::array<unsigned,3> order{0,1,2};
            std::sort(order.begin(),order.end(),[&](unsigned a,unsigned b){return std::hypot(survey_points_[a][0]-x_,survey_points_[a][1]-y_)>std::hypot(survey_points_[b][0]-x_,survey_points_[b][1]-y_);});
            for(const auto n:order)if(!survey_[n]){
                const float dx=survey_points_[n][0]-x_,dy=survey_points_[n][1]-y_;
                const float forward=dx*std::cos(angle_)+dy*std::sin(angle_);
                if(forward<=.08f)continue;
                const float side=-dx*std::sin(angle_)+dy*std::cos(angle_);
                const float sx=500+side/forward*projection_plane;
                const float height=std::min(480.f,220/forward),width=height*.30f,base_y=300+180/forward;
                if(sx+width<view_left||sx-width>view_right)continue;
                const int left=std::clamp(int(std::floor((sx-width)/column_width))-first_column,0,column_count-1),right=std::clamp(int(std::ceil((sx+width)/column_width))-first_column,0,column_count);
                int run=-1;
                for(int column=left;column<=right;++column){
                    const bool visible=column<right&&forward<depth[size_t(column)]-.035f;
                    if(visible&&run<0)run=column;
                    if(!visible&&run>=0){
                        d.push_clip({float(first_column+run)*column_width,0,float(column-run)*column_width,600});
                        d.line(sx,base_y-height*.18f,sx,base_y,2,accent.with_alpha(.65f));
                        const float diamond[]={sx,base_y-height,sx+width*.62f,base_y-height*.7f,sx,base_y-height*.40f,sx-width*.62f,base_y-height*.7f};
                        d.polygon(diamond,4,accent.with_alpha(.8f));
                        d.line(sx,base_y-height,sx,base_y-height*.40f,1,white.with_alpha(.8f));
                        d.line(sx-width*.62f,base_y-height*.7f,sx+width*.62f,base_y-height*.7f,1,white.with_alpha(.6f));
                        d.line(sx-width*.5f,base_y,sx+width*.5f,base_y,2,accent.with_alpha(.6f));
                        d.pop_clip();run=-1;
                    }
                }
            }
            d.rounded_rect({16,16,97,97},3,Color::rgb(0x172025,.9f));
            for(int yy=0;yy<8;++yy)for(int xx=0;xx<8;++xx)if(map_[yy][xx]=='1')d.rounded_rect({24+float(xx)*10,24+float(yy)*10,9,9},0,white.with_alpha(.3f));
            for(unsigned n=0;n<survey_.size();++n)if(!survey_[n])d.ring(24+survey_points_[n][0]*10,24+survey_points_[n][1]*10,3,1,accent);
            d.circle(24+x_*10,24+y_*10,3,white);
            d.line(24+x_*10,24+y_*10,24+x_*10+std::cos(angle_)*9,24+y_*10+std::sin(angle_)*9,1,white);
            for(unsigned n=0;n<survey_.size();++n){const float x=900+float(n)*34,y=33;const float points[]={x,y-8,x+6,y,x,y+8,x-6,y};
                d.polygon(points,4,(survey_[n]?accent:white).with_alpha(survey_[n]?.9f:.20f));
                d.line(x,y-8,x+6,y,1.2f,white);d.line(x+6,y,x,y+8,1.2f,white);d.line(x,y+8,x-6,y,1.2f,white);d.line(x-6,y,x,y-8,1.2f,white);}
        }else if(mode_==2){
            d.line(100,460,900,460,1,white.with_alpha(.18f));
            const float elevation=other_*190;
            for(int n=0;n<3;++n){const float a=angle_+float(n)*2.0944f,px=500+std::sin(a)*260,py=370+std::cos(a)*elevation;
                d.line(px,py,px,py-100,2,accent);d.circle(px,py-100,14,accent);d.circle(px,py,7,white.with_alpha(.3f));}
            d.bordered_rect({250,130,500,310},0,Color::rgb(0,0),1,white.with_alpha(.35f));d.line(500,130,500,440,1,white.with_alpha(.12f));
        }else if(mode_==3){
            for(int row=0;row<8;++row)for(int col=0;col<8;++col){const float dx=float(col)-3.5f,dy=float(row)-3.5f;
                const float rx=dx*std::cos(angle_)-dy*std::sin(angle_),ry=dx*std::sin(angle_)+dy*std::cos(angle_);
                const float px=500+(rx-ry)*34,py=310+(rx+ry)*16;const int h=blocks_[size_t(row*8+col)];
                d.line(px-27,py,px,py+13,1,white.with_alpha(.15f));d.line(px,py+13,px+27,py,1,white.with_alpha(.15f));
                for(int k=0;k<h;++k){d.rounded_rect({px-20,py-float(k+1)*23,40,23},0,gfx::mix(accent,white,float(k)*.14f));d.line(px-20,py-float(k+1)*23,px+20,py-float(k+1)*23,1,white.with_alpha(.5f));}
                if(row==cy_&&col==cx_)d.circle(px,py-float(h)*23-10,5,white);
            }
        }else if(mode_==4){
            for(int n=0;n<24;++n)if(!gathered_[size_t(n)]){const float px=100+float(n%8)*114,py=140+float(n/8)*154,sz=8+float(n%6)*8;d.rounded_rect({px-sz/2,py-sz/2,sz,sz},2,sz<growth_?accent:quiet.with_alpha(.35f));}
            d.circle(x_,y_,growth_,accent.with_alpha(.2f));d.circle(x_,y_,growth_*.65f,white);d.line(x_,y_,x_+vx_*.13f,y_+vy_*.13f,2,accent);
        }else{
            const float lx=500+std::sin(angle_)*440,ly=80+other_*90;
            d.circle(lx,ly,14,accent);
            for(int n=0;n<6;++n){const float px=220+float(n)*110,py=350+std::sin(float(n)*1.4f)*45;
                const float length=100+(1-other_)*190;const float dx=(px-lx)*.38f;
                d.line(px,py,px+dx,py+length,24,Color::rgb(0,.35f));d.rounded_rect({px-13,py-45,26,45},0,white);
                d.line(lx,ly,px,py-45,.7f,accent.with_alpha(.12f));}
        }
        if(mode_==0||mode_==2||mode_==4)counter(d,f,quiet);
        d.pop_transform();d.pop_clip();
    }
};
constexpr const char* SpaceStudy::map_[9];
}
std::unique_ptr<Study> make_study_space(const std::string&id){
    if(id=="portals")return std::make_unique<PortalStudy>();
    const char*names[]={"perspective","raycast","camera","voxels","scale",nullptr,"light"};for(int n=0;n<7;++n)if(names[n]&&id==names[n])return std::make_unique<SpaceStudy>(n);return {};
}
}
