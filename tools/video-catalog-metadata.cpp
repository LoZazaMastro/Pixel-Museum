// Public museum-film metadata, using the same unsigned client as the app.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "yt/innertube.hpp"
#include "yt/codec.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cstdio>
#include <set>
#include <string>
int main(int argc,char**argv){
    if(argc!=3)return 2;
    yt::InnerTube client;client.set_timeout(5);client.set_region("US","en");
    nlohmann::json output;
    if(std::string(argv[1])=="--search"){
        yt::FeedPage page;const bool ok=client.search(argv[2],&page);output["ok"]=ok;output["status"]=client.last_status();output["error"]=client.last_error();output["entries"]=nlohmann::json::array();
        for(const auto&item:page.items){if(item.video_id.empty()||item.is_channel())continue;output["entries"].push_back({{"id",item.video_id},{"title",item.title},{"channel",item.author},{"channel_id",item.channel_id},{"duration",item.length_s},{"live",item.live}});}
    }else if(std::string(argv[1])=="--player"){
        yt::VideoInfo info;const bool ok=client.player(argv[2],&info);std::set<std::string> codecs,audio_codecs;std::size_t video_formats=0,avc_formats=0,aac_formats=0;
        for(const auto&format:info.formats)if(format.height>0&&!format.url.empty()){++video_formats;codecs.insert(yt::codec_label(format.codec));}
        for(const auto&format:info.formats)if(!format.url.empty()){if(format.codec==yt::Codec::avc)++avc_formats;if(format.codec==yt::Codec::aac)++aac_formats;if(yt::is_audio_codec(format.codec))audio_codecs.insert(yt::codec_label(format.codec));}
        yt::CodecChoice choice;choice.avc=true;choice.vp9=false;choice.av1=false;choice.max_height=1080;choice.decode=yt::DecodeMode::software;const auto*selected=yt::select_video_format(info.formats,choice);
        output={{"ok",ok},{"status",client.last_status()},{"error",client.last_error()},{"id",info.video_id},{"title",info.title},{"channel",info.author},{"channel_id",info.channel_id},{"duration",info.length_s},{"description",info.description.substr(0,1600)},{"client",info.client},{"live",info.live},{"format_count",info.formats.size()},{"playable_video_formats",video_formats},{"video_codecs",codecs},{"audio_codecs",audio_codecs},{"avc_format_count",avc_formats},{"aac_format_count",aac_formats},{"native_compatible_avc_aac",selected!=nullptr&&aac_formats>0},{"native_selection",yt::describe_selection(selected,choice)},{"publish_date",info.publish_date},{"preroll_wait_s",info.preroll_wait_s},{"verification_scope","Unsigned app player metadata and format URLs resolved; no stream bytes or console playback tested"}};
    }else return 2;
    std::puts(output.dump().c_str());return 0;
}
