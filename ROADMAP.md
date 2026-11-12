# Roadmap

The goal: the imported `maps` folder matches the Xbox disc's as closely as possible, so MCC
players play with disc players. The campaign comes first.

| # | Step | Status |
| --- | --- | --- |
| M0 | This repository: the import command over OpenCE's `--import-mcc` (staged, several maps at once, a report of each map) | done |
| M1 | Every campaign BSP loads. In a10, a50, b40, c40, d20 and d40, a BSP does not fit above the tags, because Halo PC menu tags that a campaign map does not need are kept. Leave them out. | next |
| M2 | The campaign matches the disc. Each level differs in 3 to 6 tags (a few objects' animations and collision). Make them the disc's by values, or show they do not change the simulation. | to do |
| M3 | No marks in the maps' headers: the HUD's digits, message icons and scope masks written at the disc's size | to do |
| M4 | The menus map: bitmap frames in the disc's order; the campaign pause menu made the disc's | to do |
| M5 | Maps that do not match (Halo PC's 7 rebuilt multiplayer maps): left out of `maps`, or kept as MCC's own files for OpenCE's MCC map support | to decide |
| M6 | The importer's own build, without the game: an MCC-only loader, script names from a generated table, geometry without Direct3D. Releases for Windows and Linux, with checksums. | later |

OpenCE itself needs only small changes to play these maps. They are made on the fork, one branch
each, and offered to OpenCE one at a time:
- the menus over a menus map that lacks some of the Xbox's tags;
- a setting for the high-res HUD over the disc's layout with other pixels.
