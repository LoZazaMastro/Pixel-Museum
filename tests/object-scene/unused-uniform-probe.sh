#!/usr/bin/env bash
# Isolated renderer comparison; production sources and source GLBs stay intact.
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
out=build/research/model-uniform-probe
mkdir -p "$out"
python3 - <<'PY'
from pathlib import Path
out=Path('build/research/model-uniform-probe')
source=Path('src/museum/object_scene.cpp').read_text()
marker='namespace museum {'
probe='''std::size_t model_probe_vec4_calls=0;
void model_probe_uniform4fv(GLint location,GLsizei count,const GLfloat*values){++model_probe_vec4_calls;glUniform4fv(location,count,values);}
#define glUniform4fv model_probe_uniform4fv
'''
assert source.count(marker)==1
source=source.replace(marker,probe+marker)
old='glUniform4fv(p.restore_regions,4,part.restore.regions[0].data());glUniform4fv(p.restore_details,4,part.restore.details[0].data());glUniform4fv(p.restore_ink,4,part.restore.ink[0].data());glUniform4fv(p.restore_colour,1,part.restore.colour_roughness.data());glUniform3i(p.restore_counts,part.restore.region_count,part.restore.detail_count,part.restore.ink_count);'
new='''glUniform3i(p.restore_counts,part.restore.region_count,part.restore.detail_count,part.restore.ink_count);
        if(part.restore.region_count>0){
            glUniform4fv(p.restore_regions,part.restore.region_count,part.restore.regions[0].data());
            if(part.restore.detail_count>0)glUniform4fv(p.restore_details,part.restore.detail_count,part.restore.details[0].data());
            if(part.restore.ink_count>0)glUniform4fv(p.restore_ink,part.restore.ink_count,part.restore.ink[0].data());
            glUniform4fv(p.restore_colour,1,part.restore.colour_roughness.data());
        }'''
if old not in source:
    begin=source.index('glUniform3i(p.restore_counts,')
    end=source.index('glUniform1f(p.roughness,',begin)
    source=source[:begin]+old+'\n        '+source[end:]
assert source.count(old)==1
(out/'reference.cpp').write_text(source)
(out/'guarded.cpp').write_text(source.replace(old,new))
test=Path('tests/object-scene/test.cpp').read_text()
test=test.replace('int main(int argc,char **argv)', 'extern std::size_t model_probe_vec4_calls;\nint main(int argc,char **argv)')
benchmark='''double sum=0,worst=0;std::size_t calls=0;
        for(unsigned frame=0;frame<24;++frame){model_probe_vec4_calls=0;assert(object.render(yaw+float(frame)*.013f,width,height,tilt,z_up,zoom));glFinish();assert(glGetError()==GL_NO_ERROR);if(frame>=4){const auto t=object.timings();sum+=t.last_render_ms;worst=std::max(worst,t.last_render_ms);calls+=model_probe_vec4_calls;}}
        std::printf("UNIFORM_PROBE: CPU render submission mean%.4fms max%.4fms / vec4calls%zu per20frames / original%zu drawcalls / softwareGLnotPS5\\n",sum/20,worst,calls,stats.draw_calls);
        '''
assert test.count('const auto rendered=object.timings();')==1
(out/'test.cpp').write_text(test.replace('const auto rendered=object.timings();',benchmark+'const auto rendered=object.timings();'))
PY
for variant in reference guarded; do
 clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 \
 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" \
 "$out/test.cpp" "$out/$variant.cpp" src/gfx/gl_program.cpp src/yt/image.cpp host/platform_host.cpp \
 -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o "$out/$variant"
done
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
for variant in reference guarded; do
 "$out/$variant" models/playstation-5.glb 'node:Sketchfab Model.002_108,node:Sketchfab Model.001_100' --size=3840x2160 --yaw=-.35 --tilt=.2 --zoom=1.3 --adaptive-upload > "$out/ps5-$variant.log" 2>&1
 for angle in 0 1; do cp "models/playstation-5.glb-$angle.png" "$out/ps5-$variant-$angle.png"; done
 "$out/$variant" models/wii-u-gamepad.glb --size=3840x2160 --yaw=-.35 --tilt=.13 --zoom=1.3 --adaptive-upload > "$out/gamepad-$variant.log" 2>&1
 for angle in 0 1; do cp "models/wii-u-gamepad.glb-$angle.png" "$out/gamepad-$variant-$angle.png"; done
 "$out/$variant" models/playstation-3-clean-surface.glb --size=3840x2160 --yaw=-.35 --tilt=.13 --zoom=1.3 --adaptive-upload > "$out/ps3-$variant.log" 2>&1
 for angle in 0 1; do cp "models/playstation-3-clean-surface.glb-$angle.png" "$out/ps3-$variant-$angle.png"; done
done
for model in ps5 gamepad ps3; do
 for angle in 0 1; do cmp "$out/$model-reference-$angle.png" "$out/$model-guarded-$angle.png"; done
done
printf '%s\n' 'PASS exact4Ktwoangle pixel parity PS5/GamePad/PS3active-restoration; GL/state/cache/revisit/cancellation checks pass. Compare CPU logs without physicalPS5 claims.'
