#!/usr/bin/env python3
"""Imports the Halo 1 maps of a Steam install of Halo: The Master Chief
Collection as Xbox maps, into a game data folder for OpenCE:

    python import_mcc.py --game <OpenCE build> --from <halo1 folder | steam> --out <data folder> [<map>...]

The conversion itself is OpenCE's `halo --import-mcc` (the `opence`
submodule, branch mcc-extractor), run once per map, several at once. The
maps are written to <out>/maps.partial, which becomes <out>/maps only when
every map is written; a failure or Ctrl-C leaves no maps folder.

At the end, each map is reported:
- whether it is the disc's map (its fingerprint matches the disc's: it plays
  with players who have the disc), or MCC's own (it does not);
- whether every structure BSP fits above its tags (the game refuses one that
  does not when the level switches to it).

The maps by default: every map the importer has the disc's values for (the
submodule's port/assets/mcc/<map>.p2), but those held back (HELD_BACK),
which are imported only when named. With no map named, the maps that are
not the disc's (those held back, and the multiplayer maps MCC has from Halo
PC) are also written as MCC's own, a package for OpenCE's MCC loader in
<out>/mcc_maps/mcc_multiplayer: MCC's map files with their sounds given back
from MCC's banks (one sounds.map), and MCC's bitmaps.map. They play only with
other MCC players.
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys
import threading
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "opence" / "port" / "assets" / "mcc"
PARTIAL = "maps.partial"
# the Xbox's tag cache: its address and size (OpenCE's physical_memory_map.h),
# and a cache file's sector (a structure BSP is read in whole sectors)
TAG_CACHE_ADDRESS = 0x803A6000
TAG_CACHE_SIZE = 0x1600000
SECTOR = 0x800


# maps left out of maps/ unless named, and why (ROADMAP.md): they are not the
# disc's, so they play only with other MCC players, as MCC's own maps in the
# package below
HELD_BACK = dict(
    {name: "its flag bases have no collision in MCC (ROADMAP.md, the bases)"
     for name in ("chillout", "longest", "prisoner", "putput", "ratrace", "wizard")},
    **{name: "Halo PC's rebuild, with other collision than the disc's"
       for name in ("beavercreek", "bloodgulch", "boardingaction", "carousel", "damnation", "hangemhigh",
                    "sidewinder")})
# the maps written as MCC's own, a package for OpenCE's MCC loader
# (mcc_maps/<PACKAGE>: the game's --mcc-package): those held back, and the
# multiplayer maps MCC has from Halo PC that the disc has not
PACKAGE = "mcc_multiplayer"
PACKAGED = sorted(HELD_BACK) + ["dangercanyon", "deathisland", "gephyrophobia", "icefields", "infinity", "timberland"]
PACKAGE_PARTIAL = "mcc_maps.partial"


def default_maps():
    """every map the importer has the disc's values for but those held back,
    the menus' map last"""
    names = sorted(path.stem for path in DATA.glob("*.p2") if path.stem not in HELD_BACK)
    return [name for name in names if name != "ui"] + (["ui"] if "ui" in names else [])


def write_package(game, halo1, out):
    """MCC's own maps into <out>/mcc_maps.partial/<PACKAGE>, with their
    sounds.map and MCC's bitmaps.map: (written, lines)"""
    folder = out / PACKAGE_PARTIAL / PACKAGE
    shutil.rmtree(out / PACKAGE_PARTIAL, ignore_errors=True)
    folder.mkdir(parents=True)
    environment = dict(os.environ, HALO_DATA_ROOT=str(out))
    command = [str(game), "--mcc-package", f"d:\\{PACKAGE_PARTIAL}\\{PACKAGE}", "--from", str(halo1), *PACKAGED]
    result = subprocess.run(command, env=environment, capture_output=True, text=True, errors="replace")
    lines = (result.stdout + result.stderr).splitlines()
    # (MCC's folder as the game found it: Steam's, for --from steam)
    source = next((line.split("mcc import: from ", 1)[1] for line in lines if line.startswith("mcc import: from ")),
                  str(halo1))
    bitmaps = Path(source) / "maps" / "bitmaps.map"
    if result.returncode != 0 or not bitmaps.is_file():
        return False, lines + ([] if bitmaps.is_file() else [f"{bitmaps} is missing"])
    shutil.copyfile(bitmaps, folder / "bitmaps.map")
    return True, lines


def mcc_size(halo1, name):
    path = Path(halo1) / "maps" / f"{name}.map"
    return path.stat().st_size if path.is_file() else 0


def import_one(game, halo1, out, name, lock):
    """one map, by its own copy of the game: (name, written, lines)"""
    environment = dict(os.environ, HALO_DATA_ROOT=str(out))
    command = [str(game), "--import-mcc", "d:\\" + PARTIAL, "--from", str(halo1), name]
    result = subprocess.run(command, env=environment, capture_output=True, text=True, errors="replace")
    lines = (result.stdout + result.stderr).splitlines()
    written = result.returncode == 0 and any(f"mcc import: {name}: " in line and " structure bsps, " in line
                                             for line in lines)
    with lock:
        print(f"  {name}: {'written' if written else 'FAILED (exit code %d)' % result.returncode}", flush=True)
    return name, written, lines


def bsp_check(path):
    """each structure BSP's (index, size, fits) against the game's rule"""
    raw = path.read_bytes()
    data = raw[:0x800] + zlib.decompressobj().decompress(raw[0x800:])
    offset, size = struct.unpack_from("<ii", data, 0x10)
    tags = data[offset:offset + size]
    instances, scenario_handle = struct.unpack_from("<II", tags, 0)
    scenario = struct.unpack_from("<I", tags, instances - TAG_CACHE_ADDRESS + (scenario_handle & 0xFFFF) * 0x20 + 0x14)[0]
    count, references = struct.unpack_from("<II", tags, scenario - TAG_CACHE_ADDRESS + 0x5A4)
    results = []
    for index in range(count):
        file_size, base_address = struct.unpack_from("<iI", tags, references - TAG_CACHE_ADDRESS + index * 0x20 + 4)
        read = (file_size + SECTOR - 1) & ~(SECTOR - 1)
        fits = TAG_CACHE_ADDRESS + size <= base_address and base_address + read <= TAG_CACHE_ADDRESS + TAG_CACHE_SIZE
        results.append((index, file_size, fits))
    return results


def report(out, results):
    """the maps' table: the disc's or MCC's, and their BSPs"""
    print("\nmap            fingerprint            BSPs")
    for name, written, lines in results:
        if not written:
            print(f"{name:<14} not written")
            continue
        verdict = next((line.split("differ from the disc's: ")[1] for line in lines
                        if f"mcc import: {name}: " in line and "parts of the fingerprint differ" in line), "?")
        kind = "the disc's" if verdict == "the disc's map" else "MCC's own"
        # (each once: a map larger than its cache file is imported again)
        differing = list(dict.fromkeys(line.split("differs from the disc's: ")[1].split("\t")[1] for line in lines
                                       if "differs from the disc's: TAG\t" in line))
        refused = [f"{index} (0x{size:X})" for index, size, fits in bsp_check(Path(out) / "maps" / f"{name}.map")
                   if not fits]
        print(f"{name:<14} {kind:<22} {'all fit' if not refused else 'REFUSED: ' + ', '.join(refused)}")
        for tag in differing:
            print(f"{'':<14}   differs: {tag}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--game", required=True, help="an OpenCE build with --import-mcc (halo or halo.exe)")
    parser.add_argument("--from", dest="halo1", required=True,
                        help="MCC's halo1 folder, or 'steam' to find it through Steam's libraries")
    parser.add_argument("--out", required=True, help="the game data folder the maps folder is written to")
    parser.add_argument("--jobs", type=int, default=max(1, min((os.cpu_count() or 2) - 1, 12)),
                        help="maps imported at once (each takes up to 1 GB of memory)")
    parser.add_argument("maps", nargs="*", help="the maps (default: every map the importer has values for, and "
                        "the package of MCC's own maps)")
    arguments = parser.parse_args()

    game, out = Path(arguments.game).resolve(), Path(arguments.out).resolve()
    halo1 = arguments.halo1
    if halo1 != "steam" and not (Path(halo1) / "maps" / "a10.map").is_file():
        sys.exit(f"{halo1} is not MCC's halo1 folder (it has no maps/a10.map)")
    package = not arguments.maps
    for folder in ["maps"] + (["mcc_maps"] if package else []):
        if (out / folder).exists():
            sys.exit(f"{out / folder} exists: move it aside first (the import writes a whole {folder} folder)")
    names = arguments.maps or default_maps()
    if package:
        for name, why in sorted(HELD_BACK.items()):
            print(f"  {name}: not in maps ({why}): MCC's own, in mcc_maps\\{PACKAGE}")
    if halo1 != "steam":
        names.sort(key=lambda name: -mcc_size(halo1, name))
    partial = out / PARTIAL
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)

    print(f"importing {len(names)} maps, {arguments.jobs} at once, into {partial}")
    lock = threading.Lock()
    try:
        with ThreadPoolExecutor(max_workers=arguments.jobs) as pool:
            results = list(pool.map(lambda name: import_one(game, halo1, out, name, lock), names))
    except KeyboardInterrupt:
        shutil.rmtree(partial, ignore_errors=True)
        sys.exit("cancelled: nothing written")
    failed = [name for name, written, _ in results if not written]
    if failed:
        for name, written, lines in results:
            if not written:
                print(f"\n{name}:\n  " + "\n  ".join(lines[-8:]))
        shutil.rmtree(partial, ignore_errors=True)
        sys.exit(f"{len(failed)} of {len(names)} maps failed ({', '.join(failed)}): nothing written")
    package_lines = []
    if package:
        print(f"writing {len(PACKAGED)} maps as MCC's own into {out / PACKAGE_PARTIAL / PACKAGE}", flush=True)
        written, package_lines = write_package(game, halo1, out)
        if not written:
            print("\n  " + "\n  ".join(package_lines[-8:]))
            shutil.rmtree(partial, ignore_errors=True)
            shutil.rmtree(out / PACKAGE_PARTIAL, ignore_errors=True)
            sys.exit("the package of MCC's own maps failed: nothing written")
    partial.rename(out / "maps")
    if package:
        (out / PACKAGE_PARTIAL).rename(out / "mcc_maps")
    report(out, sorted(results))
    if package:
        print(f"\nMCC's own maps, in mcc_maps\\{PACKAGE} (they play with other MCC players only):")
        for line in package_lines:
            if line.startswith("mcc package: ") and (" sounds given " in line or "sounds.map: " in line):
                print("  " + line[len("mcc package: "):])
    return 0


if __name__ == "__main__":
    sys.exit(main())
