# Roadmap

## v0.1 — Playable training-pad MVP

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
- Exercise guides use simple native level objects and no third-party dependencies.
- Level-generation output is deterministic and checked in CI.
- Static validator catches malformed NDJSON, missing spawn references, invalid materials, unsafe package paths, and accidental authoring files.
- CI builds a distributable ZIP with `levels/drift_training_pad/` at archive root.
- Packaged ZIP passes an in-game smoke test on BeamNG.drive 0.39.4 before the first public release.

## v0.2 — Visual polish and teaching aids

- Better exercise signage/labels.
- Physical cones/pylons where they improve spatial reference.
- Per-exercise preview images.
- Improved staging area and map presentation.
- Optional bilingual/community translations.

## v0.3 — Community/BeamMP polish

- Validate BeamMP distribution and multiplayer spawn behavior.
- Add tandem-friendly practice area without turning the map into a full circuit.
- Community feedback pass and BeamNG Repository release preparation.
