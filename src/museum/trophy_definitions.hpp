// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "museum/trophies.hpp"
namespace museum {
// Uses the currently loaded i18n dictionary. Rebuild after a language change;
// stable IDs and persistent progress remain independent of translated text.
std::vector<TrophyDefinition> make_trophy_definitions();
}
