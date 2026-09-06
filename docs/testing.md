# Testing

## Static checks

The repository keeps generated level data and assets under automated checks:

- every line of every `items.level.json` must be valid JSON;
- `info.json` must reference spawn objects that exist;
- the default spawn must exist and be listed;
- all local material references must resolve;
- generated COLLADA meshes must parse and contain the expected material/geometry;
- generated asphalt PNG textures must be present and valid;
- the asphalt material must keep the ordinary `ASPHALT` ground type and reference only level-local visual textures;
- guide/label/scenery meshes must stay non-colliding;
- the outer boundary mesh must be the only new colliding presentation mesh in the readability pass;
- visual cone instances stay non-colliding for v0.1;
- no level-local ground-model override may enter the MVP;
- no absolute Windows paths or authoring/cache folders may enter the distributable tree;
- generated level data/assets must match the deterministic generator;
- the package ZIP must contain `levels/drift_training_pad/` directly at archive root.

## Runtime smoke test

Static validation cannot prove that BeamNG accepts every serialized object, imported COLLADA shape or PBR texture. Before a public release, test the packaged ZIP in BeamNG.drive with unrelated mods disabled:

1. Remove/move older ZIPs and any unpacked working copy of the level from the BeamNG user folder.
2. Install only the new generated ZIP.
3. Clear cache after structural/material changes.
4. Start BeamNG.drive and load Drift Training Pad.
5. Verify the default and exercise spawn points.
6. Verify textured asphalt renders without warning materials and still behaves as ordinary asphalt.
7. Verify white exercise guides, yellow labels/zone corners, visual cones and outer grass scenery are visible.
8. Drive across white/yellow graphics and through visual cones; none should affect the car.
9. Hit the outer low barrier at low speed once to confirm it has collision and no invisible collision extends into the pad.
10. Inspect `beamng.log` for `drift_training_pad`, missing assets, invalid JSON, warning materials, failed shape imports, or failed object creation.

The runtime smoke test is the gate that turns a statically valid build into a release candidate.
