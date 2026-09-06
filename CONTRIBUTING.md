# Contributing

Thanks for helping improve Drift Training Pad.

## Before changing the map

- Read `AGENTS.md` and `docs/roadmap.md`.
- Keep the project focused on structured drift practice rather than turning it into a general-purpose drift circuit.
- Preserve ordinary BeamNG asphalt behavior. Do not make the surface artificially easier to drift.
- Prefer deterministic/self-contained assets or stable built-in BeamNG runtime systems over fragile third-party dependencies.

## Validation

For code or generated-level changes, run the same checks used by CI:

```bash
python -m compileall -q scripts tests
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

For runtime-facing map changes, also test the packaged ZIP in the target BeamNG.drive version and inspect `beamng.log`. Pay particular attention to missing materials/shapes, invisible collision, warning materials, and any presentation asset that changes how the car drives.

## Feedback that is especially useful

- Whether an exercise is easy to find and understand from its spawn point.
- Whether the guide geometry makes radius/transition mistakes obvious.
- Whether any visual marker or boundary produces unexpected collision.
- Whether the asphalt feels like ordinary BeamNG asphalt rather than a custom drift surface.
- Screenshots and `beamng.log` excerpts for rendering or asset-loading problems.
