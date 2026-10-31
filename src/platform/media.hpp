// Pixel Museum - Bounded online exhibits and native YouTube presentation.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
namespace hui::gfx { class Renderer; }
namespace museum::media {
enum class State : unsigned char { idle, loading, ready, failed };
struct Asset {
    State state = State::idle;
    std::string path;
    std::string error;
    std::uint32_t texture = 0;
    int width = 0;
    int height = 0;
    int source_width = 0, source_height = 0; // Original decoded size; no synthetic enlargement.
};
struct ImageDownload {
    bool active=false, clearing=false;
    std::size_t total=0, completed=0, failed=0;
};
struct Connection {
    State state=State::idle;
    bool signed_in=false;
    bool saved=false;
    std::string user_code;
    std::string verification_url;
    std::string qr_url;
    std::string error;
};
// One worker, 16 queued requests, 12 MiB network / 32 MiB local images / 160 MiB documents,
// 384 MiB persistent cache, at most 24 image textures and 96 MiB image residency.
// request() is idempotent; image=false is useful for JSON and GLB files.
// Photos retain up to4096long-edge/16M pixels; linear-light area filtering only
// reduces larger sources. Pending RGBA is bounded64MiB in addition to the one
// decode job (64 Mi-pixel source: at most512MiB for decoder/output RGBA copies,
// plus encoded bytes and decoder scratch). Only upload_pending touches OpenGL.
// Photo payload transfers are at most2MiB per frame; partial textures remain
// private and the existing preview survives until the replacement is complete.
// Cold packaged photos publish their local preview first. The first visible
// photo preempts stale queued/incomplete background work before master promotion.
class RemoteCache {
  public:
    RemoteCache();
    ~RemoteCache();
    bool start(const std::string &cache_directory);
    bool images_from_package(const std::string& install_root);
    std::string image_identity(const std::string& url) const; // Manifest content SHA256, then packaged path, then URL; no image IO.
    void stop();
    Asset request(const std::string &https_url, bool image = true);
    Asset get(const std::string &https_url) const;
    void retry(const std::string &https_url); // Explicit reset; still honours a temporary host cooldown.
    // HTTP429/500/502/503/504 photos retry at5/20/60s only while visible (three retries).
    // Other failures and documents require retry(); no background retry loop.
    void set_visible(const std::vector<std::string>& urls); // Main photo first; lower priority photos may wait under the residency budget.
    std::size_t set_model_pressure(bool enabled); // Main GL thread: trim only nonvisible GPU photos; disk masters remain.
    void upload_pending(hui::gfx::Renderer &renderer);
    void release_textures(); // Main thread, before deleting the GL context.
    // Disk-only work: no texture uploads or GPU residency for neighbouring exhibits.
    void prefetch_images(const std::vector<std::string>& urls);
    void download_images(const std::vector<std::string>& urls);
    void cancel_download();
    void clear_images(const std::vector<std::string>& urls);
    ImageDownload image_download() const;
  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
// All resolving and decoding runs off the frame thread. upload_pending is
// the only GL call. mix_audio ADDS 48 kHz stereo float PCM; it never locks.
class Video {
  public:
    Video();
    ~Video();
    bool start(const std::string &data_directory, const std::string &install_root);
    void stop();
    void open(const std::string &youtube_id, bool audio_only=false, double start_seconds=0, double end_seconds=0);
    void play_range(double start_seconds, double end_seconds); // Reuse the ready stream; seek and reset its PCM budget atomically.
    void volume(float gain); // 0..1, smoothed on the audio callback; default0.6
    void close();
    void pause(bool paused);
    void seek(double seconds);
    void update(float dt);
    std::size_t set_model_pressure(bool enabled); // Main GL thread: trim only nonvisible GPU photos; disk masters remain.
    void upload_pending(hui::gfx::Renderer &renderer);
    void mix_audio(float *stereo, unsigned frames);
    State state() const;
    std::string error() const;
    std::string stage() const;
    std::uint32_t texture() const;
    int width() const;
    int height() const;
    double time() const;
    double duration() const;
    float audio_level() const;
    bool paused() const;
    bool ended() const;
    void caption_language(std::string locale); // Non-English museum locale; safe before start.
    std::string caption_text() const; // Active decoder-clock cue; empty for audio-only.
    std::string caption_status() const;
    void release_texture();
    Connection connection() const;
    void request_sign_in(); // User explicitly chooses Connect. Never called at startup.
    void cancel_sign_in();
    void sign_out();
    void restore_connection(); // User opens a previously saved connection.
  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace museum::media
