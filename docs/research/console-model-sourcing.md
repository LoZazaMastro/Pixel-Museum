# Console model sourcing ? verified candidates

Checked 20 October 2026. This is an asset-selection record; the museum catalog has not been modified by this pass.

## Five original hardware models verified

[Open Console CAD](https://github.com/tiansongyu/open-console-cad), by tiansongyu, supplies genuine glTF2 binary meshes for the Atari 2600 Heavy Sixer, Japanese HVC-001 Famicom with round buttons, Japanese SCPH-1000 PlayStation, Japanese SCPH-10000 PlayStation 2, and original white RVL-001 Wii. All five files were downloaded from their exact published paths and their SHA-256 hashes match the publisher manifests. There are no required extensions, external texture dependencies or compressed geometry. The files contain detailed CAD geometry and coloured materials, including device-specific logos, openings, ports, vents and controls. These are approximations based on public references, not manufacturer scan data.

Publisher preview renders were visually inspected and are retained under `reference-images/console-cad/` for research. They are solid-colour engineering renders, not photorealistic texture scans. Native lighting quality must be checked independently before describing the resulting experience as finished. These assets represent their named Japanese variants; avoid silently relabelling them as US/every-region hardware.

Original model geometry is MIT, Copyright (c) 2026 tiansongyu. The repository explicitly states that third-party trademarks, logos, designs and source references retain their original rights. MIT, the third-party notice and the geometric-lettering DejaVu licence have been saved under `content/licenses/open-console-cad/`.

The full exports contain a console, related controllers/accessories and substantial hidden electronics. Preserve the authored exterior and do not reduce them to primitive boxes. The manifest `content/model-candidates-curation.json` lists confident filters using the publisher's own `node.extras.assembly` field. Those filters remove concealed board/wiring/optical assemblies; controllers are retained where useful. Merge equal-material primitives after selecting parts. The publisher's own `assembled` view includes hidden internals and is not an exterior optimization.

| Exhibit | Selected triangles | Nodes before material merging |
|---|---:|---:|
| Atari VCS |186396|94|
| Famicom with controllers |653110|262|
| PlayStation with controller/card |493674|375|
| PlayStation 2 with controller/card |240686|477|
| Wii with Remote / Nunchuk |415956|282|

Raw validated files are build-only research data at `build/research/model-validation/`; they should not be copied wholesale into a small package. Reference render images are research material, not exhibit images.

## Odyssey remains unfilled

No downloadable Odyssey model with a licence suitable for a public runtime model URL was verified. This is a specific 1972 Magnavox Odyssey gap, not permission to substitute an Odyssey 2 or later dedicated Pong system.

The CHM, Smithsonian and Science Museum Group collection records checked provide photographs/catalogue records, not a verified 3D scan. Their open metadata or image permissions do not imply permission for unrelated 3D models. Sketchfab candidates by JesseJimison and Vasco Silva had no verified reusable download. A university museum GitHub project includes an Odyssey exhibit but no reusable repository/model licence was found.

RetroFreak's [3D Warehouse Odyssey](https://embed-3dwarehouse-classic.sketchup.com/model/aafbbf78539372f34d54c88391b1fcc1/Magnavox-Odyssey) has a public GLB preview resource, but that does not authorize reuse. [SketchUp's official terms FAQ](https://help.sketchup.com/en/3d-warehouse/3d-warehouse-terms-use-faq) explicitly requires developer approval for research-project aggregation. No protected model download was bypassed.

A promising detailed free alternative is [helliocentrism's Odyssey on 3Dsky](https://3dsky.org/3dmodels/show/magnavox_odyssey): 125,312 polygons, OBJ and textures, 16 MB. Its [current terms](https://3dsky.org/faq/category/10005/show) permit some game uses but prohibit public distribution of the original 3D file and require protected proprietary packaging. This does not fit the current web-hosted GLB catalogue without specific author permission. Paid models by l3x56 / ImmortalSoul and 3DModels.org were recorded, but not bought or treated as freely redistributable.

All exact URLs, creators, license evidence, hashes, counts and remaining constraints are in `content/model-candidates-curation.json`. No creator was contacted and no money was spent.
