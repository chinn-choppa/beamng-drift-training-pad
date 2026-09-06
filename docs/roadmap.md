# Roadmap

## v0.1 — Playable and readable training-pad MVP

Goal: a small, deterministic BeamNG.drive 0.39.4 level that loads as a normal freeroam map and provides clearly separated practice zones.

Planned zones:

1. Donut Basic — concentric 8 m / 10 m / 12 m guide circles.
2. Large Circle — concentric 15 m / 20 m / 25 m guide circles.
3. Figure Eight Easy — wide, slow transition geometry.
4. Figure Eight Normal — tighter figure-eight requiring earlier and cleaner transitions.
5. Transition Lane — repeated left/right transition markers.
6. Single Corner — approach, one sustained corner, and marked exit.
7. Training Loop — short sequence combining the fundamentals.

MVP acceptance criteria:

- Level uses the modern `levels/<id>/main/` structure.
- At least one valid default `SpawnSphere` is exposed through `info.json`.
- Each exercise has a named spawn point.
- Ground is a flat asphalt `GroundPlane` with ordinary BeamNG asphalt physics.
- Exercise guides are generated deterministically and do not alter vehicle collision/grip.
- The training facility has a readable perimeter, numbered zone labels and visual reference objects.
- Asphalt appearance uses level-local generated textures while keeping the stock `ASPHALT` physical ground type.
- No level-local ground model override is allowed for the MVP.
- Level-generation output is deterministic and checked in CI.
- Static validator catches malformed NDJSON, missing spawn references, invalid materials/assets, unsafe package paths, and accidental authoring files.
- CI builds a distributable ZIP with `levels/drift_training_pad/` at archive root.
- Packaged ZIP passes in-game smoke testing on BeamNG.drive 0.39.4 before the first public release.

Runtime progress:

- Smoke #1: level/spawns/GroundPlane loaded; projected DecalRoad guides were invisible.
- Smoke #2: TSStatic fallback guides rendered and were confirmed non-obstructive while driving.
- Smoke #3: validate the readability pass (textured asphalt, zone labels, cones, scenery and perimeter barrier).

## v0.2 — Teaching aids and presentation

- Per-exercise preview images.
- Optional on-map instruction boards with concise technique cues.
- Replace visual-only cones with appropriate lightweight physical props if they improve training and performance remains good.
- Improve facility dressing without reducing visibility or frame rate.
- Optional bilingual/community translations.

## v0.3 — Community/BeamMP polish

- Validate BeamMP distribution and multiplayer spawn behavior.
- Add tandem-friendly practice area without turning the map into a full circuit.
- Community feedback pass and BeamNG Repository release preparation.
