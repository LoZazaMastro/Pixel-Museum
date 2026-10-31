// Pixel Museum - bounded photographic image preparation. SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace museum::media::detail {
inline constexpr unsigned kPhotoEdge=4096;
inline constexpr std::size_t kPhotoPixels=16u<<20;
// Source decoding is temporary worker memory, separate from retained GPU pixels.
inline constexpr std::size_t kPhotoSourcePixels=64u<<20;
inline constexpr unsigned kPhotoSourceEdge=16384;
inline constexpr std::size_t kPhotoLocalBytes=32u<<20;
bool prepare_photo(const std::string& encoded,int*width,int*height,int*source_width,int*source_height,std::vector<std::uint8_t>*rgba,std::string*error);
// Exact pixel-area integration, linear-light RGB and premultiplied alpha.
bool reduce_photo(const std::vector<std::uint8_t>&source,int width,int height,int target_width,int target_height,std::vector<std::uint8_t>*result);
}
