# Roadmap

The goal: the imported `maps` folder matches the Xbox disc's as closely as possible, so MCC
players play with disc players. The campaign comes first.

| # | Step | Status |
| --- | --- | --- |
| M0 | This repository: the import command over OpenCE's `--import-mcc` (staged, several maps at once, a report of each map) | done |
| M1 | Every campaign BSP loads. In a10, a50, b40, c40, d20 and d40, a BSP did not fit above the tags, because Halo PC's settings screens were kept: MCC's pause menu opens them. The import now leaves out the rows of the disc's menu lists that the disc's map has not, and the screens behind them. | done |
| M2 | The campaign matches the disc. Each level differed in a few tags (the cyborg's passenger pose, the field generator's collision, the unused flamethrower). They change nothing the host decides, and are accepted: left out of the fingerprint, and listed in opence/port/assets/mcc/README.md. | done: all 10 levels are the disc's |
| M3 | No marks in the maps' headers: the HUD's digits, message icons and scope masks written at the disc's size | done |
| M3b | The multiplayer maps' bases. chillout, longest, prisoner, putput, ratrace and wizard differ from the disc only in the flag bases (2 a map) and chillout's 3 teleporter bases: on the disc a low solid pad (flag base about 1.5 m wide and 17 cm high, teleporter base a 34 cm wedge), in MCC no collision at all, so MCC players walk through them. No MCC map has the disc's version. Options to discuss: accept the difference, build a simple collision from MCC's own model, or keep them MCC's own. Until then they are held back (import_mcc.py's HELD_BACK). | to discuss |
| M4 | The menus map: bitmap frames in the disc's order; the campaign pause menu made the disc's | to do |
| M5 | Maps that do not match (Halo PC's 7 rebuilt multiplayer maps): left out of `maps`, or kept as MCC's own files for OpenCE's MCC map support | to decide |
| M6 | The importer's own build, without the game: an MCC-only loader, script names from a generated table, geometry without Direct3D. Releases for Windows and Linux, with checksums. | later |

OpenCE itself needs only small changes to play these maps. They are made on the fork, one branch
each, and offered to OpenCE one at a time:
- the menus over a menus map that lacks some of the Xbox's tags;
- a setting for the high-res HUD over the disc's layout with other pixels.
