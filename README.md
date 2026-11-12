# OpenCE MCC import

Play [OpenCE](https://github.com/OpenCommunityEdition/OpenCE) with your Steam copy of Halo: The
Master Chief Collection (MCC), without the Xbox disc, and play together with players who have
the disc.

The importer reads MCC's Halo 1 maps and writes a `maps` folder of Xbox maps for OpenCE. It
gives each map the Xbox disc's values, then compares the map's gameplay data with the disc's
through a fingerprint. A map that matches is the disc's map: it plays online and in co-op with
disc players. A map that does not match never plays with them.

## Status

Early. The conversion is OpenCE's own code, from the `mcc-extractor` branch of the OpenCE fork
(the `opence` submodule), run once per map. See [ROADMAP.md](ROADMAP.md) for what comes next.
The first goal is the whole campaign matching the disc.

## Use

You need:
- MCC installed through Steam;
- an OpenCE build of the `mcc-extractor` branch (it has the `--import-mcc` option);
- Python 3.

Build OpenCE from the submodule (`opence/`, see its README), then:

```sh
python import_mcc.py --game opence/build/windows/halo.exe --from steam --out <game data folder>
```

- `--from` is MCC's `halo1` folder, or `steam` to find it through Steam's libraries.
- The maps are written to `<game data folder>/maps.partial`, which becomes `maps` when every map
  is written.
- The importer refuses to write over an existing `maps` folder.
- At the end, a table tells, for each map, whether it is the disc's map, and whether all its BSPs
  load.

To play the maps, use an OpenCE build of the fork's `mcc-testing` branch, with its game data
folder set to the one you imported into.

## What is in this repository

- `import_mcc.py`: the command above.
- `opence/`: OpenCE (the fork's `mcc-extractor` branch): the converter's code, and the disc's
  values it applies (`port/assets/mcc`).

The disc's values are numbers, names, offsets, orders and hashes only, never pixels, sounds,
models or geometry. MCC's files are only read, and nothing of MCC's is in this repository.

## Licence

AGPL-3.0-or-later, as OpenCE, whose code it builds. See [LICENSE](LICENSE).
