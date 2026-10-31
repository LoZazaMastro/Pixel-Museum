#!/usr/bin/env bash
# Exact isolated comparison: preserve the production source/binary until PASS.
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
out=build/research/uniform-packing-probe
mkdir -p "$out"
python3 - <<'PY'
from pathlib import Path
out=Path('build/research/uniform-packing-probe')
source=Path('src/museum/object_scene.cpp').read_text()
pack_begin=source.index('    // Preserve every sampled8-bit data channel.')
uniform_begin=source.index('    if(job.source.rgba.size()>=4){')
tail=source.index('    job.prepare_ms=elapsed_ms(started);return true;',uniform_begin)
pack=source[pack_begin:uniform_begin]
uniform=source[uniform_begin:tail]
old='pack(job.source.rgba,job.packed_base);for(const auto&level:job.levels[1]){MipPixels packed;packed.width=level.width;packed.height=level.height;pack(level.bytes,packed.bytes);job.packed_levels.push_back(std::move(packed));}'
new='''if(job.uniform_roles[1]){
            // All original RGBA texels and every mip are already verified
            // identical. Pack only the sampled texel; retain the original
            // RGBA/mips for the exact unsupported-format fallback.
            job.packed_base.resize(job.packed_components);
            for(unsigned c=0;c<job.packed_components;++c)job.packed_base[c]=job.source.rgba[job.packed_channels[c]];
        }else{
            pack(job.source.rgba,job.packed_base);for(const auto&level:job.levels[1]){MipPixels packed;packed.width=level.width;packed.height=level.height;pack(level.bytes,packed.bytes);job.packed_levels.push_back(std::move(packed));}
        }'''
if uniform_begin < pack_begin:
    # Production may already contain the proven optimization. Reconstruct
    # only the old preparation order in this private baseline copy.
    uniform=source[uniform_begin:pack_begin]
    pack=source[pack_begin:tail]
    assert pack.count(new)==1
    pack=pack.replace(new,old)
    source=source[:uniform_begin]+pack+uniform+source[tail:]
    pack_begin=source.index('    // Preserve every sampled8-bit data channel.')
    uniform_begin=source.index('    if(job.source.rgba.size()>=4){',pack_begin)
    tail=source.index('    job.prepare_ms=elapsed_ms(started);return true;',uniform_begin)
assert pack.count(old)==1
optimized=source[:pack_begin]+uniform+pack.replace(old,new)+source[tail:]
old_stats='if(uniform){const auto original_bytes=allocation_bytes;allocation_bytes='
new_stats='''if(uniform){
                // Account for the full equivalent packed chain even when its
                // redundant CPU copy was never allocated.
                std::size_t original_bytes=allocation_bytes;
                if(job.compact_active){original_bytes=job.source.rgba.size()/4*job.packed_components;for(const auto&level:job.levels[1])original_bytes+=level.bytes.size()/4*job.packed_components;}
                allocation_bytes='''
if old_stats in optimized:
    assert optimized.count(old_stats)==1
    optimized=optimized.replace(old_stats,new_stats)
else:
    assert optimized.count(new_stats)==1
cpu=r'''
extern "C" void uniform_packing_probe_cpu(){
    std::atomic<std::uint64_t> revision{1};
    for(unsigned iteration=0;iteration<5;++iteration){
        museum::ImageUpload job;job.serial=1;job.use_cache=false;
        job.source.width=4096;job.source.height=4096;job.source.roles=2;job.source.data_channels=6;
        job.source.rgba.resize(4096u*4096u*4);
        for(std::size_t n=0;n<job.source.rgba.size();n+=4){job.source.rgba[n]=37;job.source.rgba[n+1]=119;job.source.rgba[n+2]=201;job.source.rgba[n+3]=255;}
        if(!museum::prepare_mips(job,revision)||!job.uniform_roles[1]||job.packed_components!=2)std::abort();
        std::size_t original=job.source.rgba.size(),packed=job.packed_base.size();
        for(const auto&level:job.levels[1])original+=level.bytes.size();
        for(const auto&level:job.packed_levels)packed+=level.bytes.size();
        if(job.packed_base[0]!=119||job.packed_base[1]!=201)std::abort();
        for(std::size_t n=0;n<job.source.rgba.size();++n)if(job.source.rgba[n]!=std::array<unsigned char,4>{37,119,201,255}[n%4])std::abort();
        for(const auto&level:job.levels[1])for(std::size_t n=0;n<level.bytes.size();++n)if(level.bytes[n]!=std::array<unsigned char,4>{37,119,201,255}[n%4])std::abort();
        std::printf("UNIFORM_PACKING iteration=%u original_rgba_mip_bytes=%zu packed_cpu_bytes=%zu prepare_ms=%.3f exact_rgba_mips=PASS\n",iteration,original,packed,job.prepare_ms);
    }
}
'''
(out/'reference.cpp').write_text(source+cpu)
(out/'compact.cpp').write_text(optimized+cpu)
(out/'production-before.cpp').write_text(source)
test=Path('tests/object-scene/test.cpp').read_text()
needle='int main(int argc,char **argv)'
assert test.count(needle)==1
test=test.replace(needle,'extern "C" void uniform_packing_probe_cpu();\n'+needle)
begin=test.index('{',test.index(needle))+1
test=test[:begin]+'\n    if(argc>1&&std::string(argv[1])=="--cpu-uniform-probe"){uniform_packing_probe_cpu();return 0;}\n'+test[begin:]
(out/'test.cpp').write_text(test)
PY
for variant in reference compact; do
 clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 \
  -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" \
  "$out/test.cpp" "$out/$variant.cpp" src/gfx/gl_program.cpp src/yt/image.cpp host/platform_host.cpp \
  -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o "$out/$variant"
done
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
for variant in reference compact; do
 "$out/$variant" --cpu-uniform-probe > "$out/cpu-$variant.log" 2>&1
 "$out/$variant" models/playstation-5.glb 'node:Sketchfab Model.002_108,node:Sketchfab Model.001_100' --size=3840x2160 --yaw=-.35 --tilt=.2 --zoom=1.3 --adaptive-upload > "$out/ps5-$variant.log" 2>&1
 for angle in 0 1; do cp "models/playstation-5.glb-$angle.png" "$out/ps5-$variant-$angle.png"; done
 "$out/$variant" models/wii-u-gamepad.glb --size=3840x2160 --yaw=-.35 --tilt=.13 --zoom=1.3 --adaptive-upload > "$out/gamepad-$variant.log" 2>&1
 for angle in 0 1; do cp "models/wii-u-gamepad.glb-$angle.png" "$out/gamepad-$variant-$angle.png"; done
done
for model in ps5 gamepad; do
 for angle in 0 1; do cmp "$out/$model-reference-$angle.png" "$out/$model-compact-$angle.png"; done
done
printf '%s\n' 'PASS isolated 4K uniform packing: exact original RGBA+mips, two angles PS5/GamePad byte-identical, GL/state/cache/revisit/cancellation checks.'
