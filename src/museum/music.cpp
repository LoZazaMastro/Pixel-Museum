// Pixel Museum - synchronized original decade soundtrack.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/music.hpp"
#include "third_party/stb/vorbis.h"

#include <algorithm>
#include <cmath>
#include <cstdio>

namespace museum {
namespace {
constexpr unsigned kFrames = Music::kSourceRate * Music::kSeconds;
constexpr unsigned kOutputFrames = Music::kOutputRate * Music::kSeconds;
constexpr float kGainStep = 1.0f / (Music::kOutputRate * 0.08f);
struct Technology { float low_alpha, dc_alpha, stereo, drive, level; };
float filter_alpha(float hz) {
    return 1.0f-std::exp(-6.28318530718f*hz/Music::kOutputRate);
}
// Cutoffs/colour are curatorial approximations, not measured transfer functions.
// LOC describes acoustic recording to 1925 as mechanical, roughly 100-2500 Hz:
// https://www.loc.gov/loc/lcib/1106/records.html
// https://www.loc.gov/collections/emile-berliner/articles-and-essays/gramophone/
// The decoded source is 24 kHz: "digital" means transparent to that source,
// not a claim that this player reconstructs frequencies absent from its stems.
const std::array<Technology, Music::kTechnologyCount> kTechnologies = {{
    {1, 0, 1, 0, .72f},                                     // pre-1877 acoustic room
    {filter_alpha(2500), filter_alpha(200), 0, .35f, .82f},    // 1877 phonograph
    {filter_alpha(2500), filter_alpha(100), 0, .18f, .86f},    // 1887 gramophone
    {filter_alpha(6500), filter_alpha(60), 0, .07f, .95f},     // 1925 electrical
    {filter_alpha(11000), filter_alpha(30), 0, .025f, 1},     // 1950 tape / hi-fi mono
    {filter_alpha(11000), filter_alpha(20), 1, .015f, 1},     // 1958 stereo records
    {1, 0, 1, 0, 1},                                       // 1982 digital delivery
}};
float bounded(float value, float low, float high, float fallback) {
    return std::isfinite(value) ? std::clamp(value, low, high) : fallback;
}
}

bool Music::init(const std::string &directory) {
    ready_ = false;
    error_.clear();
    frame_ = 0;
    gain_ = 0;
    archival_mix_=1.f;
    culture_mix_=0;
    onboarding_mix_=0;composition_started_=false;
    filters_ = {};
    technology_weights_.fill(0); technology_from_.fill(0);
    target_technology_ = kTechnologyCount; technology_remaining_ = 0;
    weights_.fill(0);
    fade_from_.fill(0);
    target_era_ = kEraCount;
    fade_remaining_ = 0;
    // Decode into temporary storage so partially loaded sets are never audible.
    std::array<std::vector<std::int16_t>, kEraCount> decoded;
    std::array<std::vector<std::int16_t>, kEraCount> cultural;
    std::vector<std::int16_t> intro;
    for(unsigned collection=0;collection<3&&error_.empty();++collection){
    for (unsigned era = 0; era < (collection==2?1u:kEraCount); ++era) {
        const std::string filename = collection==2?directory+"/onboarding/intro.ogg":directory + (collection?"/culture/":"/") + std::to_string(1950 + era*10) + ".ogg";
        FILE *file = std::fopen(filename.c_str(), "rb");
        if (!file) { error_ = "Missing museum music: " + filename; break; }
        if (std::fseek(file, 0, SEEK_END) != 0) {
            std::fclose(file);error_ = "Cannot size museum music: " + filename;break;
        }
        const long length = std::ftell(file);
        if (length <= 0 || length > 4L*1024L*1024L || std::fseek(file, 0, SEEK_SET) != 0) {
            std::fclose(file);
            error_ = "Invalid museum music file size: " + filename;
            break;
        }
        std::vector<unsigned char> bytes(static_cast<std::size_t>(length));
        const std::size_t received = std::fread(bytes.data(), 1, bytes.size(), file);
        std::fclose(file);
        if (received != bytes.size()) { error_ = "Cannot read museum music: " + filename;break; }
        int code = 0;
        stb_vorbis *stream = stb_vorbis_open_memory(bytes.data(), static_cast<int>(bytes.size()), &code, nullptr);
        if (!stream) { error_ = "Cannot decode museum music: " + filename; break; }
        const auto info = stb_vorbis_get_info(stream);
        if (info.sample_rate != kSourceRate || info.channels != 2 ||
            stb_vorbis_stream_length_in_samples(stream) != kFrames) {
            stb_vorbis_close(stream);
            error_ = "Museum music must be 64-second 24 kHz stereo: " + filename;
            break;
        }
        auto& destination=collection==2?intro:collection?cultural[era]:decoded[era];
        destination.resize(static_cast<std::size_t>(kFrames)*2);
        unsigned done = 0;
        while (done < kFrames) {
            const int count = stb_vorbis_get_samples_short_interleaved(stream, 2,
                destination.data() + static_cast<std::size_t>(done)*2,
                static_cast<int>((kFrames-done)*2));
            if (count <= 0) break;
            done += static_cast<unsigned>(count);
        }
        stb_vorbis_close(stream);
        if (done != kFrames) { error_ = "Truncated museum music: " + filename; break; }
    }
    }
    if (!error_.empty()) {
        for (auto &stem : pcm_) std::vector<std::int16_t>().swap(stem);
        for (auto &stem : culture_pcm_) std::vector<std::int16_t>().swap(stem);
        std::vector<std::int16_t>().swap(onboarding_pcm_);
        return false;
    }
    onboarding_pcm_.swap(intro);
    pcm_.swap(decoded);
    culture_pcm_.swap(cultural);
    ready_ = true;
    return true;
}

std::size_t Music::pcm_bytes() const {
    std::size_t bytes = onboarding_pcm_.size()*sizeof(std::int16_t);
    for (const auto &stem : pcm_) bytes += stem.size()*sizeof(std::int16_t);
    for (const auto &stem : culture_pcm_) bytes += stem.size()*sizeof(std::int16_t);
    return bytes;
}
void Music::select_year(float year) {
    year_.store(bounded(year, 1833, 2024, 1980), std::memory_order_relaxed);
}
void Music::volume(float gain) {
    volume_.store(bounded(gain, 0, 1, 0.42f), std::memory_order_relaxed);
}
void Music::archival_ambient_gain(float gain){archival_gain_.store(bounded(gain,0,1,1),std::memory_order_relaxed);}

void Music::render(float *out, unsigned frames) {
    if (!out) return;
    if (!ready_) { std::fill(out, out + static_cast<std::size_t>(frames)*2, 0.0f); return; }
    const float year = year_.load(std::memory_order_relaxed);
    const float era = (std::max(year, 1950.0f)-1950.0f)/10.0f;
    const unsigned selected = std::min(static_cast<unsigned>(era), kEraCount-1);
    // These are changes in sound recording, not arbitrary decade boundaries.
    // Before 1877 there is no recording-device colour: a quiet acoustic room.
    const unsigned technology = year < 1877 ? 0 : year < 1887 ? 1 :
        year < 1925 ? 2 : year < 1950 ? 3 : year < 1958 ? 4 : year < 1982 ? 5 : 6;
    if (technology != target_technology_) {
        if (target_technology_ == kTechnologyCount) {
            technology_weights_.fill(0); technology_weights_[technology] = 1;
        } else {
            technology_from_ = technology_weights_;
            technology_remaining_ = kCrossfadeFrames;
        }
        target_technology_ = technology;
    }
    if (selected != target_era_) {
        if (target_era_ == kEraCount) {
            // The master entrance already has its own click-free gain ramp.
            weights_.fill(0);weights_[selected] = 1;
        } else {
            fade_from_ = weights_;
            fade_remaining_ = kCrossfadeFrames;
        }
        target_era_ = selected;
    }
    const float wanted = (mute_.load(std::memory_order_relaxed) ||
        listening_.load(std::memory_order_relaxed)) ? 0.0f :
        volume_.load(std::memory_order_relaxed) * (video_.load(std::memory_order_relaxed) ? 0.03162278f : 1.0f);
    const float timeline_target=culture_.load(std::memory_order_relaxed)?1.f:0.f;
    const float intro_target=onboarding_.load(std::memory_order_relaxed)?1.f:0.f;
    const float archival_target=archival_gain_.load(std::memory_order_relaxed);
    // Start directly in the selected composition: no gaming notes leak into
    // the first callback before the onboarding bed has faded up.
    if(!composition_started_){onboarding_mix_=intro_target;composition_started_=true;}
    for (unsigned f = 0; f < frames; ++f) {
        if (fade_remaining_) {
            const float progress = 1.0f - float(--fade_remaining_)/float(kCrossfadeFrames);
            for (unsigned e = 0; e < kEraCount; ++e)
                weights_[e] = fade_from_[e]*(1-progress) + (e == target_era_ ? progress : 0.0f);
        }
        // The archival layer supplies its one-second PCM-driven entry curve.
        // Do not smooth that downward curve again. Recovery retains200ms.
        const bool archival_entering=archival_target<archival_mix_;
        if(archival_entering)archival_mix_=archival_target;
        else archival_mix_+=std::min(archival_target-archival_mix_,1.f/float(kCrossfadeFrames));
        gain_ += (wanted*archival_mix_-gain_)*kGainStep;
        if(archival_entering)gain_=std::min(gain_,wanted*archival_mix_);
        culture_mix_+=std::clamp(timeline_target-culture_mix_,-1.f/float(kCrossfadeFrames),1.f/float(kCrossfadeFrames));
        onboarding_mix_+=std::clamp(intro_target-onboarding_mix_,-1.f/float(kCrossfadeFrames),1.f/float(kCrossfadeFrames));
        const unsigned index = frame_ / 2;
        const unsigned next = index+1 == kFrames ? 0 : index+1;
        const float fraction = (frame_ & 1u) ? .5f : 0.0f;
        float left=0, right=0;
        for (unsigned e = 0; e < kEraCount; ++e) {
            const auto &p = pcm_[e];
            const auto &c = culture_pcm_[e];
            // Fetch both compositions at this exact shared sample position,
            // even with zero gain. No seek, restart, decode or I/O on a switch.
            const float gl=p[index*2]+(p[next*2]-p[index*2])*fraction;
            const float gr=p[index*2+1]+(p[next*2+1]-p[index*2+1])*fraction;
            const float cl=c.empty()?0.f:c[index*2]+(c[next*2]-c[index*2])*fraction;
            const float cr=c.empty()?0.f:c[index*2+1]+(c[next*2+1]-c[index*2+1])*fraction;
            left += (gl*(1-culture_mix_)+cl*culture_mix_)*weights_[e];
            right += (gr*(1-culture_mix_)+cr*culture_mix_)*weights_[e];
        }
        if(onboarding_mix_>0&&!onboarding_pcm_.empty()){
            const auto&p=onboarding_pcm_;
            const float il=p[index*2]+(p[next*2]-p[index*2])*fraction;
            const float ir=p[index*2+1]+(p[next*2+1]-p[index*2+1])*fraction;
            left=left*(1-onboarding_mix_)+il*onboarding_mix_;
            right=right*(1-onboarding_mix_)+ir*onboarding_mix_;
        }
        left /= 32768.0f; right /= 32768.0f;
        if (technology_remaining_) {
            const float progress = 1.0f - float(--technology_remaining_)/float(kCrossfadeFrames);
            for (unsigned t = 0; t < kTechnologyCount; ++t)
                technology_weights_[t] = technology_from_[t]*(1-progress) +
                    (t == target_technology_ ? progress : 0.0f);
        }
        float l=0, r=0;
        for (unsigned t = 0; t < kTechnologyCount; ++t) {
            const auto &profile = kTechnologies[t];
            const float mid = (left+right)*.5f;
            const float input[2] = {mid+(left-mid)*profile.stereo,
                mid+(right-mid)*profile.stereo};
            auto &state = filters_[t];
            for (unsigned ch=0; ch<2; ++ch) {
                float value = input[ch];
                if (profile.low_alpha < 1) {
                    state.low1[ch] += (value-state.low1[ch])*profile.low_alpha;
                    state.low2[ch] += (state.low1[ch]-state.low2[ch])*profile.low_alpha;
                    value = state.low2[ch];
                }
                if (profile.dc_alpha > 0) {
                    state.dc[ch] += (value-state.dc[ch])*profile.dc_alpha;
                    value -= state.dc[ch];
                }
                // Gentle continuous saturation suggests acoustic horn limits;
                // it never substitutes digital bit crushing for old records.
                value = value*(1+profile.drive)/(1+profile.drive*std::abs(value));
                value *= profile.level*technology_weights_[t];
                if (ch==0) l += value; else r += value;
            }
        }
        out[f*2] = l*gain_;
        out[f*2+1] = r*gain_;
        if (++frame_ == kOutputFrames) frame_ = 0;
    }
}
} // namespace museum
