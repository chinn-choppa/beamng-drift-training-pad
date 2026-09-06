# Research notes

Initial implementation choices were checked against current BeamNG.drive level documentation and existing open-source tooling before development began.

## Current BeamNG guidance used

- Modern levels should use `levels/<level_name>/main/` as their scene-tree entry point.
- `items.level.json` is newline-delimited JSON: one complete object per line.
- `SpawnSphere` objects are referenced from `info.json` through `defaultSpawnPointName` / `spawnPoints[].objectname`.
- A minimal outdoor environment can use `TimeOfDay`, `LevelInfo`, `ScatterSky`, and `CloudLayer`.
- `GroundPlane` is suitable for small test scenes and avoids needing a binary `.ter` terrain asset for the MVP.
- PBR materials can use `baseColorFactor` without texture files, which keeps the prototype dependency-free and easy to diff.
- The packaged ZIP should have `levels/<level_name>/...` directly at archive root and should be tested independently of the unpacked working tree.

## Existing solutions reviewed

- `MoonSolo/beamng-custom-mapping`: automated BeamNG map generation/package concepts.
- `alexkleinwaechter/BeamNG_LevelCleanUp`: modern level-format references and tooling ideas, especially deterministic validation/cleanup.
- `Grille/BeamNG_LevelTemplateCreator`: level-template generation concepts.
- Public BeamNG/BeamMP map packages: modern serialized `GroundPlane`, `DecalRoad`, and scene-tree examples.

## MVP implementation direction

The first version intentionally avoids custom meshes and texture binaries. A flat asphalt `GroundPlane` provides the driving surface and native `DecalRoad` objects provide training guides. This keeps the first release small, inspectable, and easy to validate in CI. Physical cones/signage can be added after the first in-game validation pass.
