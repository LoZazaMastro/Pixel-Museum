// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <array>
#include "museum/localization.hpp"

namespace museum {
inline constexpr std::array<const char*,10> preference_labels={
    "Language", "Appearance", "Volumes", "YouTube connection",
    "Replay introduction", "Check for updates", "Remove downloaded data", "Reset trophies", "Credits", "Support the museum"
};
inline constexpr int remove_collection_setting=6,general_credits_setting=8,reset_trophies_setting=7,museum_support_setting=9;
inline constexpr int database_update_setting=5;
inline constexpr const char* museum_support_url="https://ko-fi.com/lozazamastro";
inline constexpr const char* general_credits_text=R"(Thanks to my father for passing on his passion for technology. Thanks to my mother for giving me the sensitivity to appreciate art and look at the world with wonder. Thanks to my friends Jacopo and Renoy for sharing with me an important and lasting passion, the pleasure of discovery and the magic of wonder. Thanks to the Spartans (Alessandro, Elia, Federico, Giacomo) for sharing thoughts and opinions about the world every day and supporting me. Special thanks to the owner of Play Point, the former game shop on Via Padova in Milan, for introducing me to an incredible world and recommending wonderful games.

Special thanks to the YouTube channel The Pixel Playback for its documentaries on the history of videogames, consoles and the people who created them.
https://www.youtube.com/@ThePixelPlayback

Editorial curation, Development, Graphic design, Music: Andrea Sgarro

Content was originally written in English and subsequently translated into the supported languages using AI.

The music tracks on the music cards and the accompanying videos are streamed from their respective publications on YouTube. This content is not included in the app package or redistributed as audio or video files. The respective rights remain with their owners.

This educational work is a tribute to video games, the people, development studios, companies, art, cinema, music and inventions throughout history that have made this medium important. All images retain the © of their respective owners and/or licensors, and have been included in the app to complement the text and place it in its corresponding historical context. Any omission of any kind that is identified will be corrected in future editions.

This app is 100% unofficial and in no way endorsed by Nintendo, Sony, Microsoft, SEGA and other companies featured. All games featured are the property of the © owners. Their images have been used respectfully purely for review purposes under fair use law.)";
inline std::string_view general_credits_body(){
    constexpr std::string_view key="General credits full text";
    const auto translated=i18n::tr(key);
    return translated==key?std::string_view(general_credits_text):translated;
}
}
