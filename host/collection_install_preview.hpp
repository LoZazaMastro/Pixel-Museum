// Local-only capture of the real collection installation UI; no Screen or catalog.
#pragma once
#include "museum/collection_install_view.hpp"
#include "museum/localization.hpp"
#include "gfx/renderer.hpp"
#include "third_party/stb/stb_image_write.h"
#include <filesystem>
#include <iostream>

namespace museum {
inline bool capture_collection_install_previews(hui::gfx::Renderer& renderer,
    const hui::ui::Fonts& fonts,const std::string& output="build/previews"){
    using namespace hui;
    if(!fonts.regular.font||!fonts.semibold.font||!fonts.mono.font)return false;
    gfx::Canvas canvas;if(!canvas.create(1920,1080,1))return false;
    std::filesystem::create_directories(output);
    const auto previous_resolver=ui::text_resolver;const std::string previous_locale(i18n::locale());
    ui::text_resolver=i18n::tr;
    bool good=true;int frames=0;
    for(const char*locale:{"en","it","fr","de","es"}){
        if(!i18n::load(".",locale)){good=false;break;}
        for(int phase=0;phase<6;++phase)for(int dark=0;dark<2;++dark){
            CollectionInstallViewState s;s.phase=static_cast<CollectionInstallPhase>(phase);
            s.total_bytes=10780367913ULL;s.downloaded_bytes=4419950844ULL;
            s.bytes_per_second=13421772;s.pack_index=2;s.pack_count=12;
            s.error=CollectionInstallError::network;
            gfx::DrawList list;draw_collection_install_view(list,fonts,s,float(dark),4.2f);
            if(list.empty()){good=false;continue;}++frames;
            const bool screenshot=(std::string(locale)=="en"&&phase==2)||
                (std::string(locale)=="it"&&(phase==4||phase==5)&&!dark);
            if(!screenshot)continue;
            renderer.begin();renderer.draw(list);renderer.present(canvas.framebuffer(),1920,1080);
            std::vector<unsigned char> rgba(1920*1080*4);
            glBindFramebuffer(GL_FRAMEBUFFER,canvas.framebuffer());
            glReadPixels(0,0,1920,1080,GL_RGBA,GL_UNSIGNED_BYTE,rgba.data());
            stbi_flip_vertically_on_write(1);
            const auto path=output+"/collection-install-"+locale+"-"+std::to_string(phase)+(dark?"-dark.png":"-light.png");
            if(!stbi_write_png(path.c_str(),1920,1080,4,rgba.data(),1920*4))good=false;
        }
    }
    i18n::load(".",previous_locale);ui::text_resolver=previous_resolver;canvas.destroy();
    std::cout<<(good?"PASS":"FAIL")<<": collection installation DrawList, "<<frames<<" states, five locales, two themes.\n";
    return good&&frames==60;
}
}
