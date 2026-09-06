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

The repository generates the complete level structure and schematic preview from source, validates them statically, and builds a deterministic BeamNG mod ZIP in CI. The next release gate is an in-game smoke test of the packaged ZIP.

See [the roadmap](docs/roadmap.md) and [issue #1](https://github.com/chinn-choppa/beamng-drift-training-pad/issues/1).

## Design principles

- Training facility, not a full drift track.
- Ordinary BeamNG asphalt physics — no artificially drift-friendly surface.
- Simple guide geometry that makes radius and transition errors visible.
- No third-party runtime dependencies for the MVP.
- Small and BeamMP-friendly by design.
- Deterministic generated level files, so map changes are reviewable.

## Install a CI build

1. Open the latest successful **CI** workflow run on GitHub Actions.
2. Download the `drift-training-pad` artifact.
3. Put the contained `drift_training_pad.zip` into your BeamNG user-folder `mods` directory.
4. Make sure no unpacked development copy of `levels/drift_training_pad` is active at the same time.
5. Start BeamNG.drive and select **Drift Training Pad**.

No physics mods are required.

## Development

CI generates the distributable map using the modern BeamNG level structure:

```text
levels/
└── drift_training_pad/
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
python scripts/validate_level.py
python -m unittest discover -s tests -v
python scripts/package_mod.py --output dist/drift_training_pad.zip
```

The project intentionally uses only Python's standard library for generation, validation, tests, preview rendering, and packaging.

## Runtime testing

Static CI checks cannot prove that BeamNG accepts every serialized object. Before a public release, the packaged ZIP must be tested in BeamNG.drive with unrelated mods disabled and `beamng.log` inspected for level-specific errors.

See [docs/testing.md](docs/testing.md).

## Contributing

Community feedback is welcome, especially from drivers learning drift on a wheel. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
