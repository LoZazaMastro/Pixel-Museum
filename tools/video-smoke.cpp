// Pixel Museum - Live, unsigned YouTube resolver check; no playback claim.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#include "yt/innertube.hpp"
#include "yt/codec.hpp"
#include "yt/log.hpp"
#include "yt/decipher.hpp"
#include "yt/http.hpp"
#include <cstdio>
#include <vector>
#include <algorithm>
int main(int argc,char **argv) {
    if(argc!=2) { std::fprintf(stderr,"usage: video-smoke VIDEO_ID\n"); return 2; }
    yt::InnerTube tube; tube.set_timeout(5); tube.set_region("US","en");
    std::vector<yt::VideoInfo> variants; std::string reason;
    const bool ok=tube.player_variants(argv[1],&variants,&reason);
    const yt::VideoInfo info=variants.empty()?yt::VideoInfo{}:variants.front();
    yt::CodecChoice choice; choice.avc=true; choice.vp9=true; choice.av1=false; choice.max_height=720;choice.decode=yt::DecodeMode::software;
    const auto *selected=yt::select_video_format(info.formats,choice);
    std::printf("resolver=%s http=%ld formats=%zu eligible720pAVC=%s\n",ok?"ok":"failed",tube.last_status(),info.formats.size(),selected?"yes":"no");
    // Deliberately never print signed stream URLs or auth material.
    if(!ok) std::printf("reason=%s\n",tube.last_error().c_str());
    bool stream_ok=false;
    for(const auto &variant:variants) {
      std::vector<yt::Format> remaining=variant.formats;
      yt::Descrambler decipher;bool n_probe=false;
      for(unsigned attempt=0;attempt<4&&!stream_ok;++attempt){
        auto probe_choice=choice;if(attempt==3)probe_choice.exact_itag=18;
        const auto *candidate=yt::select_video_format(remaining,probe_choice);
        if(!candidate) continue;
        const int attempted_itag=candidate->itag;
        std::printf("selected client=%s itag=%d height=%d codec=%s url_kind=%s preroll=%.1fs\n",variant.client.c_str(),candidate->itag,candidate->height,yt::codec_label(candidate->codec),candidate->ciphered?"ciphered":"plain",variant.preroll_wait_s);
        std::string url=candidate->url;
        if(candidate->ciphered) {
            std::string error;
            if(!decipher.prepare(variant.player_js_url,&error)) { std::printf("descrambler=%s\n",error.c_str()); continue; }
            url=decipher.descramble(candidate->url,candidate->cipher_s,candidate->cipher_sp,&error);
            if(url.empty()) { std::printf("descrambler=%s\n",error.c_str()); continue; }
        }
        yt::http::Request request; request.url=url; request.max_bytes=4096; request.timeout_s=6;
        request.headers.push_back({"Range","bytes=0-1023"});
        request.headers.push_back({"User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"});
        const auto response=yt::http::perform(request);
        std::printf("stream_probe_http=%ld bytes=%zu transport=%s\n",response.status,response.body.size(),response.error.c_str());
        if(response.http_ok() && !response.body.empty()) { stream_ok=true; break; }
        const bool has_n=url.find("?n=")!=std::string::npos||url.find("&n=")!=std::string::npos||url.find("/n/")!=std::string::npos;
        if(!n_probe&&has_n&&!candidate->ciphered&&response.status==403){
            n_probe=true;std::string error;
            if(decipher.prepare(variant.player_js_url,&error)){
                const auto transformed=decipher.descramble(url,"","",&error);
                std::printf("plain_n_transform changed=%s error=%s\n",!transformed.empty()&&transformed!=url?"yes":"no",error.c_str());
                if(!transformed.empty()&&transformed!=url){request.url=transformed;const auto retry=yt::http::perform(request);std::printf("n_transform_probe_http=%ld bytes=%zu\n",retry.status,retry.body.size());if(retry.http_ok()&&!retry.body.empty())stream_ok=true;}
            }else std::printf("plain_n_prepare=%s\n",error.c_str());
        }
        remaining.erase(std::remove_if(remaining.begin(),remaining.end(),[&](const yt::Format&f){return f.itag==attempted_itag;}),remaining.end());
      }
      if(stream_ok)break;
    }
    return ok&&selected&&stream_ok?0:1;
}
