# Contributing

Thanks for helping improve Drift Training Pad.

## Development workflow

1. Create a focused branch from `main`.
2. Make the smallest coherent change.
3. Run:
   - `python -m unittest discover -s tests -v`
   - `python scripts/generate_level.py --check`
   - `python scripts/validate_level.py`
   - `python scripts/package_mod.py --output dist/drift_training_pad.zip`
4. If level runtime data changed, test the packaged ZIP in BeamNG.drive with other mods disabled and inspect `beamng.log`.
5. Open a pull request describing the exercise/behavior changed and the validation performed.

## Design principles

- This is a training facility, not a drift circuit.
- Exercises should be understandable from road markings and spawn-point names without requiring a tutorial mission.
- Keep asphalt physics ordinary and predictable.
- Prefer progressive difficulty: donut → large circle → figure-eight → transitions → single corner → training loop.
- Avoid unnecessary custom assets and dependencies.
