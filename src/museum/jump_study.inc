// Original platform study: power-ups, breakable masonry and a hidden room.
// Included inside study_motion.cpp's private namespace.
class Jump final:public Motion {
 friend struct MotionHapticsInspection;
 friend struct MarioInspection;
 friend struct MotionInspection;
 struct Platform{float x,y,w;};
 static constexpr std::array<Platform,4> pipes{{{550,490,60},{1110,460,62},{1570,430,64},{2600,460,64}}};
 static constexpr std::array<Platform,10> platforms{{{40,550,800},{920,550,440},{1450,550,550},{2090,550,700},{2890,550,530},{3510,550,820},{280,430,200},{1770,410,160},{2260,410,160},{2980,410,200}}};
 static constexpr std::array<Point,35>lights{{{305,380},{350,380},{395,380},{440,380},{720,475},{765,475},{810,475},{970,485},{1015,485},{1060,485},{1280,430},{1325,400},{1370,390},{1415,400},{1460,430},{1795,360},{1840,360},{1885,360},{2285,360},{2330,360},{2375,360},{2420,360},{2700,465},{2745,465},{2790,465},{2835,465},{3005,360},{3050,360},{3095,360},{3140,360},{3600,480},{3645,480},{3690,480},{4000,340},{4045,340}}};
 static constexpr std::array<Point,8>blocks{{{185,430},{360,430},{1770,410},{1850,410},{2260,410},{2340,410},{2980,410},{3060,410}}};
 static constexpr std::array<float,4>enemy_starts{{730,1230,2480,3280}};
 static constexpr std::array<Point,0>spikes{};
 struct Shard{Point p;float vx=0,vy=0,life=0;};
 Point p_{};float vx_=0,vy_=0,coyote_=0,buffer_=0,immune_=0;
 int landed_=0,checkpoint_=0,collected_=0,falls_=0,score_=0,flag_score_=0;
 std::array<bool,lights.size()>taken_{};std::array<bool,8>block_used_{};std::array<bool,4>enemy_down_{};
 std::array<std::array<bool,5>,4>brick_broken_{};std::array<Shard,80>shards_{};
 std::array<float,8>coin_pop_{};
 bool grounded_=true,finished_=false,running_=false,run_feedback_=false,large_=false,crouching_=false;
 float pipe_hold_=0,pipe_time_=0,finish_time_=0;int pipe_from_=-1,pipe_to_=-1;bool pipe_ready_=true;
 bool secret_=false,secret_pipe_descended_=false;std::array<bool,10>secret_taken_{};
 Point mushroom_{};float mushroom_vx_=76,mushroom_vy_=0,mushroom_emerge_=0;bool mushroom_active_=false;
 float half_height()const{return crouching_?(large_?15.f:9.f):(large_?30.f:15.f);}
 static constexpr Point secret_coin(unsigned n){return{320+n*65.f,n%2?460.f:425.f};}
 static float enemy_x(unsigned n,float t){return enemy_starts[n]+38*std::sin(t*1.3f+n);}
 bool question_tile(float x,float y)const{for(const auto b:blocks)if(b.x==x&&b.y==y)return true;return false;}
 template<class F>void solids(F&&f){
  for(unsigned n=0;n<6;++n){const auto b=platforms[n];f(Rect{b.x,b.y,b.w,150},0,int(n),0);}
  for(unsigned n=6;n<platforms.size();++n){const auto b=platforms[n];for(unsigned k=0;k<unsigned(b.w/40);++k)
   if(!brick_broken_[n-6][k]&&!question_tile(b.x+k*40,b.y))f(Rect{b.x+k*40,b.y,40,40},1,int(n-6),int(k));}
  for(unsigned n=0;n<blocks.size();++n){const auto b=blocks[n];f(Rect{b.x,b.y,40,40},2,int(n),0);}
  for(const auto b:pipes)f(Rect{b.x,b.y,b.w,550-b.y},0,-1,0);
  for(int n=0;n<5;++n){const float y=510-n*30.f;f(Rect{3770+n*40.f,y,40,550-y},0,-1,0);}
 }
 void coin(){++collected_;score_+=100;sound(84);pulse(hui::audio::Tactile::touch,.11f,.025f);speak(hui::audio::SpeakerCue::coin,1.f+.04f*(collected_%5));}
 void break_brick(int row,int tile,Rect r){
  brick_broken_[size_t(row)][size_t(tile)]=true;score_+=50;unsigned emitted=0;
  for(auto&s:shards_)if(s.life<=0&&emitted<4){const unsigned n=emitted++;s={{r.x+10+(n%2)*20,r.y+10+(n/2)*20},n%2?110.f:-110.f,n<2?-260.f:-185.f,.95f};}
  sound(55);pulse(hui::audio::Tactile::impact,.13f,.04f);
 }
 void strike_question(unsigned n){if(block_used_[n]){pulse(hui::audio::Tactile::touch,.055f,.018f);return;}
  block_used_[n]=true;const auto b=blocks[n];
  if(n==0){mushroom_active_=true;mushroom_={b.x+20,b.y+40};mushroom_vx_=76;mushroom_vy_=mushroom_emerge_=0;sound(74);}
  else{coin_pop_[n]=0;coin();}
 }
 void resize(bool big){const float bottom=p_.y+half_height();large_=big;p_.y=bottom-half_height();if(big&&!crouching_&&!can_stand()){crouching_=true;p_.y=bottom-half_height();}}
 void damage(){if(immune_>0)return;if(large_){resize(false);immune_=1.1f;event(50);}else respawn();}
 void respawn(){p_={105,535};vx_=vy_=buffer_=0;grounded_=true;coyote_=.1f;immune_=.75f;large_=crouching_=false;secret_=false;pipe_from_=pipe_to_=-1;checkpoint_=0;
  // A lost life restarts the route, including its first power-up; a previously
  // used block must not make growth unavailable on the next attempt.
  block_used_.fill(false);enemy_down_.fill(false);taken_.fill(false);secret_taken_.fill(false);for(auto&r:brick_broken_)r.fill(false);shards_.fill({});coin_pop_.fill(-1);mushroom_active_=false;
  ++falls_;event(50);}
 bool can_stand(){const float bottom=p_.y+half_height(),top=bottom-(large_?60.f:30.f);bool clear=true;
  if(!secret_)solids([&](Rect r,int,int,int){if(p_.x+12>r.x&&p_.x-12<r.x+r.w&&top<r.y+r.h&&bottom>r.y+.5f)clear=false;});return clear;}
 void animate_objects(float dt){
  for(auto&t:coin_pop_)if(t>=0){t+=dt;if(t>.65f)t=-1;}
  for(auto&s:shards_)if(s.life>0){s.life-=dt;s.vy+=700*dt;s.p.x+=s.vx*dt;s.p.y+=s.vy*dt;}
  if(!mushroom_active_)return;
  if(mushroom_emerge_<.5f){mushroom_emerge_=std::min(.5f,mushroom_emerge_+dt);mushroom_.y=blocks[0].y+40-80*mushroom_emerge_;return;}
  const float old_x=mushroom_.x,old_bottom=mushroom_.y;mushroom_.x+=mushroom_vx_*dt;mushroom_vy_+=1450*dt;mushroom_.y+=mushroom_vy_*dt;bool bounced=false;
  solids([&](Rect r,int,int,int){if(mushroom_.x+13<=r.x||mushroom_.x-13>=r.x+r.w)return;
   if(mushroom_vy_>=0&&old_bottom<=r.y+.5f&&mushroom_.y>=r.y){mushroom_.y=r.y;mushroom_vy_=0;}
   else if(!bounced&&mushroom_.y>r.y+.5f&&mushroom_.y-26<r.y+r.h){
    if(old_x+13<=r.x){mushroom_.x=r.x-13;mushroom_vx_=-std::abs(mushroom_vx_);bounced=true;}
    else if(old_x-13>=r.x+r.w){mushroom_.x=r.x+r.w+13;mushroom_vx_=std::abs(mushroom_vx_);bounced=true;}}
  });
  if(mushroom_.y>800)mushroom_active_=false;
  if(!secret_&&pipe_from_<0&&std::abs(p_.x-mushroom_.x)<25&&p_.y+half_height()>mushroom_.y-26&&p_.y-half_height()<mushroom_.y){mushroom_active_=false;resize(true);score_+=1000;event(79);}
 }
 void draw_actor(DrawList&d,float x,Color accent){if(pipe_from_>=0||(immune_>0&&int(time_*10)%2!=0))return;const float hh=half_height();d.rounded_rect({x-13,p_.y-hh,26,hh*2},crouching_?4:6,accent);d.circle(x+5,p_.y-hh+10,2,ink);}
 void update_secret(float dt){const float before=p_.x;
  const int steps=std::max(1,int(std::ceil(dt/.012f)));const float h=dt/steps;
  for(int n=0;n<steps;++n){buffer_=std::max(0.f,buffer_-h);if(buffer_>0&&grounded_){buffer_=0;vy_=-650;grounded_=false;sound(69);pulse(hui::audio::Tactile::rise,.13f,.04f);}
   vx_+=(input_x_*(running_?390.f:255.f)-vx_)*std::min(1.f,h*(grounded_?13.f:7.f));p_.x=std::clamp(p_.x+vx_*h,100.f,1140.f);vy_+=1450*h;p_.y+=vy_*h;
   if(p_.y+half_height()>=550){p_.y=550-half_height();vy_=0;grounded_=true;}
   for(unsigned c=0;c<secret_taken_.size();++c)if(!secret_taken_[c]&&distance(p_,secret_coin(c))<25){secret_taken_[c]=true;coin();}
   if(p_.x>=1125&&grounded_&&input_x_>.25f){pipe_from_=3;pipe_to_=3;pipe_time_=0;vx_=vy_=buffer_=0;secret_=false;pulse(hui::audio::Tactile::rise,.18f,.08f);break;}
  }motion_haptics_.record(p_.x-before,0,active_input_&&std::abs(input_x_)>.2f);
 }
 void draw_secret(DrawList&d,Color accent){
  d.rounded_rect({80,550,1230,150},0,paper.with_alpha(.045f));d.line(80,550,1310,550,2,paper.with_alpha(.7f));
  d.bordered_rect({150,105,60,155},2,ink,2,accent);d.bordered_rect({145,250,70,16},2,ink,2,accent);
  d.rounded_rect({1140,500,150,60},0,ink);d.line(1140,500,1230,500,2,accent);d.line(1140,560,1290,560,2,accent);
  d.line(1230,500,1230,105,2,accent);d.line(1290,560,1290,105,2,accent);d.bordered_rect({1130,495,16,70},2,ink,2,accent);
  for(unsigned n=0;n<secret_taken_.size();++n)if(!secret_taken_[n]){auto c=secret_coin(n);d.ring(c.x,c.y,8,1.5f,accent);}draw_actor(d,p_.x,accent);
 }
public:
 std::map<std::string,std::uint64_t> trophy_stats()const override{return {{"secret_pipe_descents",secret_pipe_descended_?1u:0u}};}
 Jump(){reset();}
 StudyCompletion completion()const override{return finished_&&finish_time_>=2.1f?StudyCompletion::experience_complete:StudyCompletion::playing;}
 void reset()override{clear();p_={105,535};vx_=vy_=buffer_=immune_=0;coyote_=.1f;landed_=checkpoint_=collected_=falls_=0;taken_.fill(false);block_used_.fill(false);enemy_down_.fill(false);for(auto&r:brick_broken_)r.fill(false);shards_.fill({});coin_pop_.fill(-1);grounded_=true;finished_=running_=run_feedback_=large_=crouching_=false;score_=flag_score_=0;pipe_hold_=pipe_time_=finish_time_=0;pipe_from_=pipe_to_=-1;pipe_ready_=true;secret_=secret_pipe_descended_=false;secret_taken_.fill(false);mushroom_active_=false;}
 const char*help()const override{return "Jump, run and crouch. The first question block releases a moving mushroom; collect it to grow and break bricks. Other question blocks release coins. Hold down on the second pipe to enter the hidden room. Damage shrinks a grown character; another hit returns to the start.";}
 void handle(const hui::InputFrame&i,hui::ui::Feedback&f)override{if(common(i,f,false))return;running_=i.is_held(Action::west);
  const bool duck=input_y_>.5f;if(duck!=crouching_&&(duck||can_stand())){const float bottom=p_.y+half_height();crouching_=duck;p_.y=bottom-half_height();}
  if(i.is_pressed(Action::confirm)&&!finished_)buffer_=.13f;
  if((i.released&hui::action_bit(Action::confirm))&&vy_<-220){vy_=-220;f.feel(hui::audio::Tactile::touch,.045f,.018f);}
 }
 void update(float dt)override{dt=bounded_dt(dt);tick(dt);if(!active_input_)return;animate_objects(dt);
  if(finished_){finish_time_+=dt;if(finish_time_<.8f)p_.y=std::min(550-half_height(),p_.y+330*dt);else p_.x=std::min(4270.f,p_.x+120*dt);return;}
  if(pipe_from_>=0){pipe_time_+=dt;if(pipe_from_==1){const auto source=pipes[1];p_={source.x+source.w*.5f,source.y-half_height()+std::min(pipe_time_,.4f)*110};if(pipe_time_>=.4f){secret_=true;p_={180,300};vx_=vy_=0;grounded_=false;pipe_from_=pipe_to_=-1;pulse(hui::audio::Tactile::fall,.17f,.08f);}}
   else{if(pipe_time_<.35f)p_={1135+pipe_time_*300,550-half_height()};else p_={1240,550-half_height()-(pipe_time_-.35f)*650};if(pipe_time_>=1.f){const auto exit=pipes[3];p_={exit.x+exit.w*.5f,exit.y-half_height()};pipe_from_=pipe_to_=-1;grounded_=true;coyote_=.1f;immune_=.75f;pulse(hui::audio::Tactile::rise,.20f,.09f);}}return;}
  if(secret_){update_secret(dt);return;}
  if(input_y_<.25f)pipe_ready_=true;
  if(grounded_&&input_y_>.5f&&pipe_ready_){const auto b=pipes[1];const bool aligned=std::abs(p_.x-(b.x+b.w*.5f))<18&&std::abs(p_.y+half_height()-b.y)<1;pipe_hold_=aligned?pipe_hold_+dt:0;if(pipe_hold_>=.22f){secret_pipe_descended_=true;pipe_from_=1;pipe_to_=3;pipe_ready_=false;pipe_time_=pipe_hold_=0;vx_=vy_=buffer_=0;pulse(hui::audio::Tactile::fall,.15f,.08f);return;}}
  else pipe_hold_=0;
  immune_=std::max(0.f,immune_-dt);const float feedback_x=p_.x;const int steps=std::max(1,int(std::ceil(dt/.012f)));const float h=dt/steps;
  for(int step=0;step<steps;++step){coyote_=grounded_?.10f:std::max(0.f,coyote_-h);buffer_=std::max(0.f,buffer_-h);
   if(buffer_>0&&coyote_>0){vy_=-650;grounded_=false;coyote_=buffer_=0;sound(69);pulse(hui::audio::Tactile::rise,.13f,.04f);}
   const float target=input_x_*(running_?390.f:255.f)*(crouching_&&grounded_?.35f:1.f);vx_+=(target-vx_)*std::min(1.f,h*(grounded_?13.f:7.f));
   const float hh=half_height(),old_bottom=p_.y+hh,old_top=p_.y-hh,old_x=p_.x;const bool was_grounded=grounded_;p_.x=std::clamp(p_.x+vx_*h,55.f,4300.f);vy_+=1450*h;p_.y+=vy_*h;grounded_=false;
   solids([&](Rect r,int type,int index,int tile){if(p_.x+12<=r.x||p_.x-12>=r.x+r.w)return;
    if(vy_>=0&&old_bottom<=r.y+.5f&&p_.y+hh>=r.y){p_.y=r.y-hh;vy_=0;grounded_=true;if(index>=0&&type==0)landed_=index;}
    else if(vy_<0&&old_top>=r.y+r.h-.5f&&p_.y-hh<=r.y+r.h){
     if(type==1&&large_)break_brick(index,tile,r);else if(type==2)strike_question(unsigned(index));
     p_.y=r.y+r.h+hh;vy_=45;pulse(hui::audio::Tactile::touch,.07f,.025f);}
    else if(p_.y+hh>r.y+.5f&&p_.y-hh<r.y+r.h){if(old_x+12<=r.x){p_.x=r.x-12;vx_=0;}else if(old_x-12>=r.x+r.w){p_.x=r.x+r.w+12;vx_=0;}}
   });
   if(!was_grounded&&grounded_)pulse(hui::audio::Tactile::touch,.085f,.025f);
   for(size_t n=0;n<lights.size();++n)if(!taken_[n]&&std::abs(p_.x-lights[n].x)<24&&lights[n].y>p_.y-hh-10&&lights[n].y<p_.y+hh+10){taken_[n]=true;coin();}
   for(unsigned n=0;n<enemy_starts.size();++n)if(!enemy_down_[n]&&std::abs(p_.x-enemy_x(n,time_))<25&&p_.y+hh>521&&p_.y-hh<550){if(vy_>0&&old_bottom<=531){enemy_down_[n]=true;vy_=-350;score_+=200;grounded_=false;sound(67);pulse(hui::audio::Tactile::impact,.15f,.045f);}else if(immune_<=0){damage();if(!large_&&p_.x==105)return;}}
   if(p_.y>760){respawn();return;}
   if(p_.x>=4120&&p_.y+hh>=275&&p_.y-hh<=550){flag_score_=std::clamp(int((550-p_.y)*25),100,5000);score_+=flag_score_;finished_=true;p_.x=4120;finish_time_=0;vx_=vy_=0;event(81);speak(hui::audio::SpeakerCue::bonus);break;}
  }const float dx=p_.x-feedback_x;motion_haptics_.record(dx,0,active_input_&&std::abs(input_x_)>.2f);if(std::abs(dx)>.01f&&run_feedback_!=running_){run_feedback_=running_;pulse(hui::audio::Tactile::touch,.075f,.025f);}
 }
 void draw(DrawList&d,hui::ui::Fonts&f,Rect r,Color accent)override{Canvas canvas(d,r);const Color stone=paper.with_alpha(.045f);if(secret_||pipe_from_==3){draw_secret(d,accent);return;}
  const float camera=std::clamp(p_.x-430,0.f,2930.f);
  for(unsigned n=0;n<6;++n){const auto b=platforms[n];d.rounded_rect({b.x-camera,b.y,b.w,150},0,stone);d.line(b.x-camera,b.y,b.x+b.w-camera,b.y,2,paper.with_alpha(.65f));}
  for(unsigned n=6;n<platforms.size();++n){const auto b=platforms[n];for(unsigned k=0;k<unsigned(b.w/40);++k){const float x=b.x+k*40-camera;if(brick_broken_[n-6][k]||question_tile(b.x+k*40,b.y))continue;d.bordered_rect({x,b.y,40,40},1,stone,1.2f,paper.with_alpha(.65f));d.line(x,b.y+20,x+40,b.y+20,1,paper.with_alpha(.3f));d.line(x+20,b.y,x+20,b.y+20,1,paper.with_alpha(.3f));}}
  for(const auto pipe:pipes){const float x=pipe.x-camera;d.bordered_rect({x,pipe.y+10,pipe.w,550-pipe.y-10},2,ink,1.5f,accent.with_alpha(.7f));d.bordered_rect({x-5,pipe.y,pipe.w+10,16},2,ink,2,accent);d.line(x+8,pipe.y+18,x+8,548,1,accent.with_alpha(.3f));}
  for(unsigned n=0;n<blocks.size();++n){const auto b=blocks[n];const float x=b.x-camera;d.bordered_rect({x,b.y,40,40},2,ink,1.5f,block_used_[n]?muted:accent);if(!block_used_[n])label(d,f,"?",x+12,b.y+29,27,paper);if(coin_pop_[n]>=0){const float y=b.y-12-80*std::sin(coin_pop_[n]/.65f*pi);d.ring(x+20,y,8,2,accent);}}
  for(int n=0;n<5;++n){const float x=3770+n*40.f-camera,y=510-n*30.f;d.bordered_rect({x,y,40,550-y},1,stone,1.5f,paper.with_alpha(.7f));}
  for(unsigned n=0;n<enemy_starts.size();++n)if(!enemy_down_[n]){const float x=enemy_x(n,time_)-camera;d.rounded_rect({x-13,524,26,25},5,accent.with_alpha(.45f));d.circle(x-4,531,2,paper);d.circle(x+4,531,2,paper);}
  for(size_t n=0;n<lights.size();++n)if(!taken_[n]){const auto b=lights[n];d.ring(b.x-camera,b.y,8,1.3f,accent);}
  if(mushroom_active_){const float x=mushroom_.x-camera,y=mushroom_.y;const bool emerging=mushroom_emerge_<.5f;if(emerging)d.push_clip({0,0,1400,blocks[0].y});d.rounded_rect({x-6,y-12,12,12},2,paper);d.rounded_rect({x-14,y-27,28,17},7,accent);d.rounded_rect({x-8,y-23,5,5},1,paper);d.rounded_rect({x+4,y-21,5,5},1,paper);if(emerging)d.pop_clip();}
  for(const auto&s:shards_)if(s.life>0)d.rounded_rect({s.p.x-camera-4,s.p.y-4,8,8},0,paper.with_alpha(std::min(1.f,s.life*3)));
  draw_actor(d,p_.x-camera,accent);d.line(4120-camera,275,4120-camera,550,3,paper);d.triangle({4120-camera,finished_?510.f:275.f,45,28},accent,0,pi*.5f);d.bordered_rect({4240-camera,480,70,70},2,stone,2,paper.with_alpha(.65f));d.bordered_rect({4260-camera,510,26,40},9,ink,1.5f,accent);
 }
};
