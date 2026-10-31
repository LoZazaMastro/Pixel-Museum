// Pixel Museum - Original interpretive studies, linked to collection exhibits.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string>
#include <vector>

namespace museum {
struct StudyInfo {
    std::string id,title,entry_id,explanation,controls;
    std::string discipline,group;
};
// The explanation is shown on the exhibit card. These are original
// interactive illustrations of design ideas, never executable original games.
const std::vector<StudyInfo>& study_catalog();
}
