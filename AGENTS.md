# AGENTS.md

## Project goal
Build and maintain a compact BeamNG.drive drift-training level focused on structured practice rather than a full drift circuit.

## Source of truth
- Target game version for initial development: BeamNG.drive 0.39.4.
- Prefer current official BeamNG level/modding documentation over historical forum snippets.
- Keep the distributable level self-contained except for standard BeamNG game assets/runtime systems.

## Development rules
- Use lowercase_snake_case for BeamNG level IDs and generated object names.
- Treat `levels/drift_training_pad/` as generated/distributable game content.
- Keep generation deterministic. `python scripts/generate_level.py --check` and `python scripts/apply_visual_polish.py --check` must pass before merging changes that affect their outputs.
- `items.level.json` files are newline-delimited JSON: one JSON object per line, never a JSON array.
- Do not commit editor caches, autosaves, cooked cache files, or authoring binaries unless intentionally required by the mod.
- Prefer simple native BeamNG objects and deterministic self-contained assets over fragile external runtime dependencies.
- Do not change tyre/ground physics to make drifting easier. The training pad must keep ordinary `ASPHALT` behavior; visual texture changes must not introduce a custom ground-model override.
- Keep exercise guides, zone labels, scenery, and visual training markers non-colliding unless a physical obstacle is explicitly part of the exercise design and separately runtime-tested.
- Human-facing repository documentation and issue/PR discussion should be in English so the public project is accessible to the BeamNG community. Code identifiers stay in English.

## Validation contract
Before considering a change ready:
1. Run unit tests.
2. Run the base generator in check mode.
3. Apply/check deterministic visual polish when relevant.
4. Run the static level validator.
5. Build the distributable ZIP.
6. For changes that affect runtime level data, perform an in-game smoke test when a BeamNG runtime is available and inspect `beamng.log` for level-specific errors.

## Release contract
The release ZIP must contain `levels/drift_training_pad/...` at its root. It must not contain repository docs, `.git*`, `source/`, build caches, or an extra top-level wrapper directory.
