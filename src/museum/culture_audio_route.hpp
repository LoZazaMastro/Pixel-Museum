// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
namespace museum {
class CultureAudioRoute {
public:
    void snap(bool pad){mix_=pad?1.f:0.f;}
    void process(const float* input,float* tv,float* pad,unsigned frames,bool to_pad){
        const float target=to_pad&&pad?1.f:0.f;
        for(unsigned n=0;n<frames;++n){
            mix_+=std::clamp(target-mix_,-1.f/960.f,1.f/960.f);
            tv[n*2]+=input[n*2]*(1.f-mix_);tv[n*2+1]+=input[n*2+1]*(1.f-mix_);
            if(pad)pad[n]+=(input[n*2]+input[n*2+1])*.5f*mix_;
        }
    }
private:
    float mix_=0.f;
};
}
