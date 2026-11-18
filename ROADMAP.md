# Roadmap

The goal: the imported `maps` folder matches the Xbox disc's as closely as possible, so MCC
players play with disc players. The campaign comes first.

| # | Step | Status |
| --- | --- | --- |
| M0 | This repository: the import command over OpenCE's `--import-mcc` (staged, several maps at once, a report of each map) | done |
| M1 | Every campaign BSP loads. In a10, a50, b40, c40, d20 and d40, a BSP did not fit above the tags, because Halo PC's settings screens were kept: MCC's pause menu opens them. The import now leaves out the rows of the disc's menu lists that the disc's map has not, and the screens behind them. | done |
| M2 | The campaign matches the disc. Each level differed in a few tags (the cyborg's passenger pose, the field generator's collision, the unused flamethrower). They change nothing the host decides, and are accepted: left out of the fingerprint, and listed in opence/port/assets/mcc/README.md. The passenger pose stays MCC's: one still seated pose, the disc's first frame (until 2026-11-18 the `.p2` gave it the disc's 40-frame header without the frames, so the import left it with no nodes and the Chief stood up in the Warthog's passenger seat with a rifle). | done: all 10 levels are the disc's |
| M3 | No marks in the maps' headers: the HUD's digits, message icons and scope masks written at the disc's size | done |
| M3b | The multiplayer maps' bases. chillout, longest, prisoner, putput, ratrace and wizard differed from the disc only in the flag bases (2 a map) and chillout's 3 teleporter bases: on the disc a low solid pad, in MCC no collision at all, so MCC players walked through them. No MCC map has the disc's version. The import now builds each one's collision from MCC's own visible model (the `.p2`'s `collision_hull` lines, `mcc_import_collision.c`): within a few centimetres of the disc's. Played on 2026-11-18 (chillout locally, prisoner and wizard over the internet): the bases stop players. The difference is accepted in the fingerprint, so these six maps are the disc's and in `maps`. | done |
| M4 | The menus map's option pictures in the disc's frame order (`bitmap_frames`), and the campaign pause screens made the disc's (`.p2` operations and `alias` lines) | done 2026-11-17 |
| M5 | Maps that do not match: not in `maps`, but MCC's own, a package for OpenCE's MCC loader (`mcc_maps/mcc_multiplayer`): Halo PC's 7 rebuilds and MCC's 6 Halo PC maps, their sounds given back from MCC's banks (one `sounds.map`) and MCC's `bitmaps.map`. They play with other MCC players only. | done |
| M6 | The importer's own build, without the game: an MCC-only loader, script names from a generated table, geometry without Direct3D. Releases for Windows and Linux, with checksums. | later |

OpenCE itself needs only small changes to play these maps. They are made on the fork, one branch
each, and offered to OpenCE one at a time:
- the menus over a menus map that lacks some of the Xbox's tags;
- a setting for the high-res HUD over the disc's layout with other pixels.
