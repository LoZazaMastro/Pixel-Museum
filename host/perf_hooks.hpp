// Pixel Museum - host-only counters for driver fallback regression tests.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
namespace museum::host {
struct TransferCounts { std::uint64_t blits=0,read_pixels=0,get_texture=0,copy_images=0; };
void reset_transfers();
void count_transfers(bool);
TransferCounts transfers();
}
