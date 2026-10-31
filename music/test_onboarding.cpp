// Actual onboarding renderer regression checks. SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/music.hpp"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
namespace museum {struct MusicInspection {
 static float intro(const Music&m){return m.onboarding_mix_;}
 static unsigned clock(const Music&m){return m.frame_;}
 static void no_game(Music&m){for(auto&p:m.pcm_)std::fill(p.begin(),p.end(),0);for(auto&p:m.culture_pcm_)std::fill(p.begin(),p.end(),0);}
};}
int main(int argc,char**argv){
 assert(argc==2);using museum::Music;using I=museum::MusicInspection;
 Music a,b,pads;assert(a.init(argv[1])&&b.init(argv[1])&&pads.init(argv[1]));
 for(auto*m:{&a,&b,&pads}){m->select_year(2020);m->onboarding_active(true);}
 I::no_game(pads);
 std::vector<float>x(24000*2),y(x.size()),only(x.size());
 a.render(x.data(),24000);pads.render(only.data(),24000);
 assert(x==only); // Every first-half-second sample excludes ALL gaming/culture voices.
 for(unsigned done=0;done<24000;){unsigned n=std::min(137u,24000-done);b.render(y.data()+done*2,n);done+=n;}
 assert(x==y&&I::intro(a)==1);
 float step=0,prior=x[x.size()-2];double energy=0;
 for(unsigned turn=0;turn<8;++turn){
  bool intro=turn==2||turn==3; a.onboarding_active(intro);b.onboarding_active(intro);
  a.select_timeline(turn%2);b.select_timeline(turn%2);
  a.render(x.data(),24000);
  for(unsigned done=0;done<24000;){unsigned n=std::min(137u,24000-done);b.render(y.data()+done*2,n);done+=n;}
  assert(x==y&&I::clock(a)==I::clock(b));
  assert(std::abs(I::intro(a)-(intro?1.f:0.f))<1e-4f);
  for(unsigned n=0;n<24000;++n){float v=x[n*2];assert(std::isfinite(v));step=std::max(step,std::abs(v-prior));prior=v;energy+=v*v;}
 }
 assert(step<.025f&&energy>1);
 a.onboarding_active(true);a.listening_room(true);
 for(int n=0;n<8;++n)a.render(x.data(),24000);
 for(float v:x)assert(std::abs(v)<1e-8f);
 a.listening_room(false);a.muted(true);
 for(int n=0;n<8;++n)a.render(x.data(),24000);
 for(float v:x)assert(std::abs(v)<1e-8f);
 // Kind-driven archival ownership fades the bed without changing its slider.
 Music ambient;assert(ambient.init(argv[1]));ambient.select_year(2020);
 for(int n=0;n<4;++n)ambient.render(x.data(),24000);
 ambient.archival_ambient_gain(0);
 for(int n=0;n<4;++n)ambient.render(x.data(),24000);
 for(float v:x)assert(std::abs(v)<1e-8f);
 ambient.archival_ambient_gain(.35f);
 for(int n=0;n<4;++n)ambient.render(x.data(),24000);
 double restored=0;for(float v:x)restored+=v*v;assert(restored>0);
 ambient.archival_ambient_gain(1);
 for(int n=0;n<4;++n)ambient.render(x.data(),24000);
 double full=0;for(float v:x)full+=v*v;assert(full>0);
 std::printf("PASS actual17 decoded streams: onboarding first24000frames exactly excludes game/culture PCM; 200ms shared crossfade chunk-invariant; max adjacent step%.8f; listening-room/mute silence; continuous clock.\n",step);
}
