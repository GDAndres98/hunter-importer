#!/usr/bin/env python3
"""Imports MCC's Halo 1 maps with Hunter Importer and builds HunterCE for
Windows, into one folder to play from:

    python make_hunterce.py [<output folder>]

The folder (by default HunterCE/, next to this script) gets:
  halo.exe, SDL3.dll   HunterCE, built from the fork's mcc-testing branch
  maps/                every map the importer has the disc's values for
  mcc_maps/            MCC's own maps (not the disc's), for OpenCE's MCC loader
  import_report.txt    the importer's report: each map's fingerprint and BSPs
Start halo.exe there: the game finds maps/ next to it, and writes its
config.toml and debug.txt there.

It needs Python, ninja and LLVM (clang), as the Windows build does
(opence/port/windows/README.md), and git. Each option below can also be set by
the environment variable named in its help. The maps/ and mcc_maps/ of an earlier run are kept
as maps.previous/ and mcc_maps.previous/ (only the last one).
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_HUNTERCE_SRC = r"D:\Projects\OpenCE"
DEFAULT_MCC_HALO1 = r"D:\Games\SteamLibrary\steamapps\common\Halo The Master Chief Collection\halo1"
LLVM_BIN = Path(r"C:\Program Files\LLVM\bin")


def step(text):
    print(f"\n== {text}", flush=True)


def fail(text):
    sys.exit(f"make_hunterce: {text}")


def run(command, cwd=None):
    """a command, stopping the script if it fails"""
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        fail(f"{' '.join(str(part) for part in command)} failed (exit code {result.returncode})")


def build(checkout):
    """a Windows build of a checkout, configured as it is (a first one: a debug build)"""
    if not (checkout / "build.ninja").is_file():
        run([sys.executable, "configure.py"], cwd=checkout)
    run(["ninja", "windows"], cwd=checkout)


def import_maps(importer, halo1, out, jobs):
    """the importer's maps into out/maps, its output also written to out/import_report.txt"""
    out.mkdir(parents=True, exist_ok=True)
    staging = out / "import"
    shutil.rmtree(staging, ignore_errors=True)
    command = [sys.executable, "-u", str(importer / "import_mcc.py"),
               "--game", str(importer / "opence" / "build" / "windows" / "halo.exe"),
               "--from", halo1, "--out", str(staging)]
    if jobs:
        command += ["--jobs", str(jobs)]
    with open(out / "import_report.txt", "w", encoding="utf-8", newline="\n") as report:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            report.write(line)
        process.wait()
    if process.returncode != 0:
        fail(f"the import failed (exit code {process.returncode}); the maps/ of {out} is unchanged")
    # (maps/, and mcc_maps/ with MCC's own maps: each earlier one kept as
    # <name>.previous)
    for folder in ("maps", "mcc_maps"):
        if not (staging / folder).is_dir():
            continue
        previous = out / f"{folder}.previous"
        shutil.rmtree(previous, ignore_errors=True)
        if (out / folder).is_dir():
            (out / folder).rename(previous)
        (staging / folder).rename(out / folder)
    staging.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", nargs="?", default=str(ROOT / "HunterCE"),
                        help="the folder to play from (default: HunterCE/ next to this script)")
    parser.add_argument("--mcc", default=os.environ.get("MCC_HALO1", DEFAULT_MCC_HALO1),
                        help="MCC's halo1 folder, or 'steam' to find it through Steam (MCC_HALO1)")
    parser.add_argument("--hunterce-src", default=os.environ.get("HUNTERCE_SRC", DEFAULT_HUNTERCE_SRC),
                        help=f"the checkout of mcc-testing (HUNTERCE_SRC; default: {DEFAULT_HUNTERCE_SRC})")
    parser.add_argument("--importer", default=os.environ.get("IMPORTER_DIR", str(ROOT)),
                        help="Hunter Importer (IMPORTER_DIR; default: this script's folder)")
    parser.add_argument("--jobs", type=int, default=int(os.environ["JOBS"]) if os.environ.get("JOBS") else None,
                        help="maps imported at once (JOBS; default: import_mcc.py's)")
    arguments = parser.parse_args()

    out = Path(arguments.out).resolve()
    importer = Path(arguments.importer).resolve()
    source = Path(arguments.hunterce_src).resolve()
    halo1 = arguments.mcc

    # the tools and the folders
    if not shutil.which("clang") and (LLVM_BIN / "clang.exe").is_file():
        os.environ["PATH"] = str(LLVM_BIN) + os.pathsep + os.environ.get("PATH", "")
    for tool in ("ninja", "clang", "git"):
        if not shutil.which(tool):
            fail(f"{tool} is not on the PATH")
    if not (importer / "import_mcc.py").is_file():
        fail(f"{importer} is not Hunter Importer (it has no import_mcc.py)")
    if not (source / "configure.py").is_file():
        fail(f"{source} is not an OpenCE checkout (use --hunterce-src)")
    if halo1 != "steam" and not (Path(halo1) / "maps" / "a10.map").is_file():
        fail(f"{halo1} is not MCC's halo1 folder (use --mcc, or --mcc steam)")
    branch = subprocess.run(["git", "-C", str(source), "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
    if branch != "mcc-testing":
        fail(f"{source} is on '{branch}', not mcc-testing: check mcc-testing out first")
    if not (importer / "opence" / "configure.py").is_file():
        step("fetching the importer's OpenCE (the opence submodule)")
        run(["git", "-C", str(importer), "submodule", "update", "--init"])

    step(f"building the importer ({importer / 'opence'})")
    build(importer / "opence")
    step(f"building HunterCE ({source}, mcc-testing)")
    build(source)

    step(f"importing MCC's maps into {out}")
    import_maps(importer, halo1, out, arguments.jobs)

    step(f"copying HunterCE into {out}")
    for name in ("halo.exe", "SDL3.dll"):
        shutil.copy2(source / "build" / "windows" / name, out / name)

    step("done")
    print(f"Start {out / 'halo.exe'} to play. The import's report is {out / 'import_report.txt'}.")


if __name__ == "__main__":
    main()
