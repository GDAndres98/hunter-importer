#!/usr/bin/env bash
# make_hunterce.sh: imports MCC's Halo 1 maps with Hunter Importer and builds
# HunterCE for Windows, into one folder to play from:
#
#     ./make_hunterce.sh [<output folder>]
#
# The folder (by default HunterCE/, next to this script) gets:
#   halo.exe, SDL3.dll   HunterCE, built from the fork's mcc-testing branch
#   maps/                every map the importer has the disc's values for
#   import_report.txt    the importer's report: each map's fingerprint and BSPs
# Start halo.exe there: the game finds maps/ next to it, and writes its
# config.toml and debug.txt there.
#
# Run it from Git Bash on Windows. It needs Python, ninja and LLVM (clang), as
# the Windows build does (opence/port/windows/README.md). These can be set:
#   MCC_HALO1     MCC's halo1 folder, or "steam" to find it through Steam
#   HUNTERCE_SRC  the checkout of mcc-testing (default: D:\Projects\OpenCE)
#   IMPORTER_DIR  Hunter Importer (default: this script's folder)
#   JOBS          maps imported at once (default: import_mcc.py's)
# The maps/ of an earlier run is kept as maps.previous/ (only the last one).
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUT=${1:-$SCRIPT_DIR/HunterCE}
IMPORTER_DIR=${IMPORTER_DIR:-$SCRIPT_DIR}
HUNTERCE_SRC=${HUNTERCE_SRC:-/d/Projects/OpenCE}
MCC_HALO1=${MCC_HALO1:-"/d/Games/SteamLibrary/steamapps/common/Halo The Master Chief Collection/halo1"}

step() { printf '\n== %s\n' "$*"; }
fail() { printf 'make_hunterce: %s\n' "$*" >&2; exit 1; }

# the tools and the folders
if ! command -v clang >/dev/null && [ -x "/c/Program Files/LLVM/bin/clang.exe" ]; then
	PATH="/c/Program Files/LLVM/bin:$PATH"
fi
for tool in python ninja clang git; do
	command -v "$tool" >/dev/null || fail "$tool is not on the PATH"
done
[ -f "$IMPORTER_DIR/import_mcc.py" ] || fail "$IMPORTER_DIR is not Hunter Importer (it has no import_mcc.py)"
[ -f "$HUNTERCE_SRC/configure.py" ] || fail "$HUNTERCE_SRC is not an OpenCE checkout (set HUNTERCE_SRC)"
if [ "$MCC_HALO1" != steam ] && [ ! -f "$MCC_HALO1/maps/a10.map" ]; then
	fail "$MCC_HALO1 is not MCC's halo1 folder (set MCC_HALO1, or MCC_HALO1=steam)"
fi
branch=$(git -C "$HUNTERCE_SRC" branch --show-current)
[ "$branch" = mcc-testing ] || fail "$HUNTERCE_SRC is on '$branch', not mcc-testing: check mcc-testing out first"
if [ ! -f "$IMPORTER_DIR/opence/configure.py" ]; then
	step "fetching the importer's OpenCE (the opence submodule)"
	git -C "$IMPORTER_DIR" submodule update --init
fi

# a Windows build of a checkout, configured as it is (a first one: a debug build)
build() {
	[ -f "$1/build.ninja" ] || (cd "$1" && python configure.py)
	(cd "$1" && ninja windows)
}

step "building the importer ($IMPORTER_DIR/opence)"
build "$IMPORTER_DIR/opence"
step "building HunterCE ($HUNTERCE_SRC, mcc-testing)"
build "$HUNTERCE_SRC"

step "importing MCC's maps into $OUT"
mkdir -p "$OUT"
rm -rf "$OUT/import"
python -u "$IMPORTER_DIR/import_mcc.py" --game "$IMPORTER_DIR/opence/build/windows/halo.exe" --from "$MCC_HALO1" \
	--out "$OUT/import" ${JOBS:+--jobs "$JOBS"} | tee "$OUT/import_report.txt"
rm -rf "$OUT/maps.previous"
if [ -d "$OUT/maps" ]; then
	mv "$OUT/maps" "$OUT/maps.previous"
fi
mv "$OUT/import/maps" "$OUT/maps"
rmdir "$OUT/import"

step "copying HunterCE into $OUT"
cp "$HUNTERCE_SRC/build/windows/halo.exe" "$HUNTERCE_SRC/build/windows/SDL3.dll" "$OUT/"

step "done"
echo "Start $OUT/halo.exe to play. The import's report is $OUT/import_report.txt."
