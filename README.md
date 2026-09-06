# Drift Training Pad

A compact, structured drift-training map for **BeamNG.drive** focused on learning vehicle control rather than driving a full drift circuit.

## Why this map exists

Most drift maps assume that the driver can already link corners. Drift Training Pad starts earlier and provides repeatable reference geometry for fundamental exercises:

1. **Donut Basic** — 8 m / 10 m / 12 m concentric guide circles.
2. **Large Circle** — 15 m / 20 m / 25 m steady-state drift guides.
3. **Figure Eight — Easy** — wide geometry for slow, deliberate transitions.
4. **Figure Eight — Normal** — tighter transitions.
5. **Transition Lane** — repeated alternating markers.
6. **Single Corner** — approach, sustained corner, and marked exit.
7. **Training Loop** — a short sequence combining the fundamentals.

Each exercise has its own BeamNG spawn point so practice can stay focused and repeatable.

## Status

**v0.1 MVP is under development for BeamNG.drive 0.39.4.**

Runtime smoke testing has confirmed that the level loads from the packaged ZIP, spawn points work, the flat GroundPlane has collision, and the generated guide geometry is visible without affecting the car. The current draft adds the first readability/presentation pass: textured asphalt, numbered exercise-zone labels, visual cones, a staging area, grass outside the pad, and a low perimeter barrier.

See [the roadmap](docs/roadmap.md) and [issue #1](https://github.com/chinn-choppa/beamng-drift-training-pad/issues/1).

## Design principles

- Training facility, not a full drift track.
- Ordinary BeamNG asphalt physics — no artificially drift-friendly surface.
- Simple guide geometry that makes radius and transition errors visible.
- Clear exercise numbering, staging and boundaries without cluttering the driving surface.
- No third-party runtime dependencies for the MVP.
- Small and BeamMP-friendly by design.
- Deterministic generated level files and assets, so map changes are reviewable.

## Install a CI build

1. Open the latest successful **CI** workflow run on GitHub Actions.
2. Download the `drift-training-pad` artifact.
3. Put the contained `drift_training_pad.zip` into your BeamNG user-folder `mods` directory.
4. Make sure no older ZIP or unpacked development copy of `levels/drift_training_pad` is active at the same time.
5. Clear BeamNG cache after structural/material changes.
6. Start BeamNG.drive and select **Drift Training Pad**.

No physics mods are required.

## Development

CI generates the complete distributable map, including level data, meshes, textures and preview:

```text
levels/
└── drift_training_pad/
    ├── art/
    │   ├── shapes/
    │   │   ├── facility_boundaries.dae
    │   │   ├── facility_graphics.dae
    │   │   ├── facility_scenery.dae
    │   │   ├── training_cone.dae
    │   │   └── training_markings.dae
    │   └── textures/
    │       ├── asphalt_b.color.png
    │       └── asphalt_r.data.png
    ├── info.json
    ├── main.materials.json
    ├── preview.png
    └── main/
        ├── items.level.json
        └── MissionGroup/
            └── items.level.json
```

`items.level.json` files are newline-delimited JSON (NDJSON), matching current BeamNG level serialization.

Generated level data comes from the scripts in `scripts/`:

```bash
python scripts/generate_level.py
python scripts/generate_preview.py
python scripts/generate_level.py --check
python scripts/generate_preview.py --check
python -m unittest discover -s tests -v
python scripts/apply_visual_polish.py
python scripts/apply_visual_polish.py --check
python scripts/validate_level.py
python scripts/package_mod.py --output dist/drift_training_pad.zip
```

The project intentionally uses only Python's standard library for generation, validation, tests, preview rendering, asset generation, and packaging.

## Runtime testing

Static CI checks cannot prove that BeamNG accepts every serialized object or imported mesh. Before a public release, the packaged ZIP must be tested in BeamNG.drive with unrelated mods disabled and `beamng.log` inspected for level-specific errors.

See [docs/testing.md](docs/testing.md).

## Contributing

Community feedback is welcome, especially from drivers learning drift on a wheel. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
