// Pixel Museum - bounded, static GLB exhibit viewer.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <GL/glcorearb.h>
#include <memory>
#include <string>
#include <vector>
#include <cstddef>

namespace museum {
class ObjectScene {
public:
    ObjectScene();
    ~ObjectScene();
    ObjectScene(const ObjectScene &) = delete;
    ObjectScene &operator=(const ObjectScene &) = delete;
    // All instance methods require the app's current GL context on the main
    // thread. Load and upload outside the UI draw/batch phase.
    bool init();
    // Queue CPU parsing/decode on a worker; newer requests supersede older
    // results. Main thread calls upload_pending() outside the draw phase.
    // Plain include_groups select CAD extras.assembly values; node:NAME selects
    // an authored glTF node subtree, retaining all descendants. Empty selects all.
    // Interactive requests whose conservative model residency exceeds768MiB
    // upload existing role-specific mips at2048max; source masters/cache stay intact.
    void request(const std::string &path, const std::vector<std::string> &include_groups = {});
    bool upload_pending(double budget_ms=2.0, bool adaptive=false); // Also drains deferred GPU retirement; call even when no exhibit is selected.
    void swap(ObjectScene& other) noexcept; // Stable worker state; main GL thread only.
    void cancel(); // Input-safe cancellation; GPU deletes are deferred to upload_pending.
    void release_render_target(); // Cache geometry/artwork, retire only the offscreen framebuffer.
    bool loading() const;
    // Synchronous original-resolution path for offline/master validation.
    bool load(const std::string &path, const std::vector<std::string> &include_groups = {});
    struct Stats { std::size_t vertices=0,triangles=0,draw_calls=0,geometry_bytes=0,texture_bytes=0,srgb_textures=0,linear_textures=0,dual_role_texture_bytes=0,tangent_vertices=0,sampler_objects=0,deduplicated_images=0; };
    Stats stats() const;
    struct Timings {
        double read_decode_ms=0,last_upload_ms=0,max_upload_ms=0,last_render_ms=0,max_render_ms=0,target_allocation_ms=0,last_retire_ms=0,mip_prepare_ms=0,image_decode_ms=0,last_gpu_ms=0,max_gpu_ms=0;
        bool gpu_timing_supported=false;
        std::size_t upload_calls=0,uploaded_bytes=0,pending_images=0,last_upload_bytes=0,max_upload_bytes=0,gpu_samples=0,gpu_rejected=0,pending_gpu_deletes=0,encoded_model_bytes=0,peak_staged_image_bytes=0;
        int render_width=0,render_height=0,render_samples=0;
        bool coverage_post_aa=false;
        double last_storage_ms=0,max_storage_ms=0,max_transfer_ms=0,max_delete_ms=0;
        std::size_t artwork_cache_hits=0,compact_cache_fallbacks=0;double total_cache_decode_ms=0;
        double source_read_ms=0,source_hash_ms=0,parse_ms=0,total_image_decode_ms=0,total_mip_prepare_ms=0,total_upload_cpu_ms=0,total_storage_ms=0,total_transfer_ms=0,load_ready_ms=0;
        double upload_budget_ms=2.0,transfer_bytes_per_ms=0;std::size_t upload_budget_bytes=2u<<20;bool adaptive_upload=false;
        std::size_t storage_calls=0,transfer_chunk_bytes=512u<<10,estimated_gpu_bytes=0,peak_estimated_gpu_bytes=0,planned_gpu_bytes=0;
        std::size_t uniform_texture_views=0,uniform_saved_logical_bytes=0;
    };
    Timings timings() const; // Main-thread CPU wall times; not GPU timer results.
    // Radians; returns an upright transparent texture using OpenGL's normal
    // bottom-left texture origin. Full-resolution single-sample geometry with
    // GPU silhouette AA; opaque texture detail is retained. No CPU blit/resolve.
    // Center offsets are normalized device coordinates, allowing the full-width
    // transparent target to position an object without clipping it to a small card.
    // 0 indicates no loaded object or render error.
    GLuint render(float angle, int width, int height, float tilt = .13f, bool source_z_up = false, float zoom = 1.0f, float center_x = 0.0f, float center_y = 0.0f, bool pin_studio = false);
    void release();
    const std::string &error() const;
    std::string stage() const; // Locked progress snapshot; safe across worker handoffs.
    const std::string &material_notes() const; // Unsupported optional material extensions, if any.
    bool ready() const;
    // CPU-only preflight for network cache/tests; does not require GL context.
    static bool validate(const std::string &path, std::string *error, const std::vector<std::string> &include_groups = {});
private:
    friend struct ObjectSceneBudgetInspection;
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace museum
