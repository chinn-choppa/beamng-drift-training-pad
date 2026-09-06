# Testing

## Static checks

The repository will keep all generated level data under automated checks:

- every line of every `items.level.json` must be valid JSON;
- `info.json` must reference spawn objects that exist;
- the default spawn must exist and be listed;
- all local material references must resolve;
- no absolute Windows paths or authoring/cache folders may enter the distributable tree;
- generated level data must match the deterministic generator;
- the package ZIP must contain `levels/drift_training_pad/` directly at archive root.

## Runtime smoke test

Static validation cannot prove that BeamNG accepts every serialized object. Before a public release, test the packaged ZIP in BeamNG.drive with unrelated mods disabled:

1. Remove/move any unpacked working copy of the level from the BeamNG user folder.
2. Install only the generated ZIP.
3. Clear cache after structural/material changes when necessary.
4. Start BeamNG.drive and load Drift Training Pad.
5. Verify the default and exercise spawn points.
6. Drive across all marked zones and check that the ground has normal asphalt grip/collision.
7. Inspect `beamng.log` for `drift_training_pad`, missing assets, invalid JSON, warning materials, or failed object creation.

The runtime smoke test is the gate that turns a statically valid build into a release candidate.
