// youtube-tv - Subtitles: a caption track's timed text, fetched in the
// background and looked up by playback position.
// Copyright (C) 2026 SponsorBlock for PS5 contributors
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include <memory>
#include <string>
#include <string_view>
#include <vector>
#include "yt/types.hpp"

namespace yt::captions
{

struct Cue
{
    double start_s = 0.0;
    double end_s = 0.0;
    std::string text;
    int window_id = 0;
};

struct Selection
{
    std::string url;
    std::string language;
    bool translated = false;
    std::vector<std::string> alternatives; // Other offered tracks in the same requested language.
    std::vector<std::string> english_fallbacks; // Explicitly labelled, never misreported as the requested translation.
};
// Matching authored or automatic tracks are preferred in every language,
// including English; translation uses only advertised target languages.
std::string normalize_language(std::string_view locale);
Selection select_track(const VideoInfo &info, std::string_view locale);

// YouTube's "json3" timed text: events with tStartMs, dDurationMs and segs of
// utf8 text. Returns false for an answer that is not that shape.
bool parse_json3(std::string_view body, std::vector<Cue> *out);
// Real timedtext responses can be JSON3, WebVTT, srv1 or srv3 XML.
bool parse_timed_text(std::string_view body, std::vector<Cue> *out);

// One persistent worker with one replaceable request; load/clear never wait
// on HTTP. Every generation change invalidates cues and in-flight answers.
class Loader
{
  public:
    Loader();
    ~Loader();
    Loader(const Loader &) = delete;
    Loader &operator=(const Loader &) = delete;

    void load(const std::string &track_url, const std::vector<std::string>& alternatives = {},
              const std::vector<std::string>& english_fallbacks = {});
    void clear();
    // The text on screen at `position_s` (lines joined with '\n'), or empty.
    std::string text_at(double position_s);
    // "", "loading", "ok", "unavailable", "error: ...", "fallback: en",
    // or "fallback: en (translation rate limited)" for the log and menu.
    // Identical active/completed loads are no-ops. clear hides cues immediately
    // but retains session endpoint cooldowns and one bounded source-track cache.
    std::string status();

    struct Shared; // shared with the bounded worker

  private:
    std::shared_ptr<Shared> shared_;
    struct Worker;
    std::unique_ptr<Worker> worker_;
};

} // namespace yt::captions
