// Pixel Museum ? bounded, main-thread interface localization.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string>
#include <string_view>
namespace museum::i18n {
// Returned views remain valid until the next load(). Unknown keys return the
// caller's English view, so pass a literal or a string that outlives drawing.
bool load(const std::string& app_root,std::string_view locale);
std::string_view tr(std::string_view english);
// Curatorial music metadata only; unknown keys retain their original spelling.
std::string_view music(std::string_view english);
// Room titles only: preserve named music overrides and the proper-name suffix.
std::string music_room_title(std::string_view english);
std::string_view locale();
std::string_view error();
bool supported(std::string_view locale);
// This invitation previews the focused language before it is committed.
// Keep it independent of the currently loaded interface dictionary.
inline std::string_view language_choice_heading(int focus){
    constexpr std::string_view headings[]={
        "Choose your language.","Scegli la tua lingua.","Elige tu idioma.",
        "Choisissez votre langue.","W\u00e4hle deine Sprache."
    };
    return headings[focus>=0&&focus<5?focus:0];
}
}
