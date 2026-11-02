#pragma once
#if defined(_WIN32)

#include "yt/types.hpp"
#include <functional>
#include <string>

namespace hui::windows
{
// Use the maintained yt-dlp EJS solver when the small console interpreter
// cannot execute the current player. The child has no filesystem/network
// permissions and receives only the public player script and URL parameters.
bool transform_youtube_streams(const std::string &install_root,
                               const std::string &player_js_url,
                               const yt::Format &video, const yt::Format *audio,
                               const std::function<bool()> &cancelled,
                               std::string *video_url, std::string *audio_url,
                               std::string *error);
}
#endif
