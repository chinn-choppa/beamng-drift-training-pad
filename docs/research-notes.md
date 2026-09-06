# Research notes

## BeamNG level structure

The initial implementation follows current BeamNG level serialization conventions:

- level metadata in `levels/<id>/info.json`;
- scene object hierarchy below `levels/<id>/main/`;
- `items.level.json` stored as newline-delimited JSON rather than one JSON array;
- named `SpawnSphere` objects referenced by `info.json`;
- distributable ZIP rooted directly at `levels/`.

## Runtime findings

### Smoke test #1 — projected guide failure

BeamNG.drive 0.39.4 discovered and loaded the packaged level, resolved the named spawn points, and provided working GroundPlane collision. However, the generated white `DecalRoad` exercise guides were not visible.

The practical cause is that `DecalRoad` is projected geometry and is not a reliable rendering primitive for this map's deliberately terrain-free `GroundPlane` design. The solution keeps the deterministic guide splines as source data but also generates a collision-free `TSStatic` COLLADA mesh for runtime display.

The first runtime log also exposed a texture-less `CloudLayer` warning and missing environment-map fallback. The MVP now avoids that CloudLayer and defines `DefaultSkyCubemap` on `theLevelInfo`.

### Smoke test #2 — visual guide fallback works

The generated `TSStatic` guide fallback rendered successfully in BeamNG.drive 0.39.4. The Donut Basic concentric guide circles were visible and the vehicle could drive over the white geometry without any physical interference. No obvious runtime errors were reported during the test.

The remaining usability problem is presentation rather than basic level loading: the pad is too visually bare and lacks strong boundaries, zone identification, surface detail, and spatial reference objects.

## v0.1 readability approach

The next pass therefore remains deterministic and self-contained while preserving ordinary asphalt physics:

- generated level-local asphalt base-color and roughness textures affect appearance only;
- the material keeps BeamNG's ordinary `ASPHALT` ground type and no level-local ground-model override is introduced;
- numbered yellow zone labels and corner-bracket frames are generated as collision-free mesh graphics;
- lightweight generated visual cones provide reference points without introducing obstacle collision in v0.1;
- a staging area and facility perimeter make orientation clearer;
- grass-colored visual scenery outside the pad makes the asphalt facility boundary legible;
- only the low outer perimeter barrier is intended to add presentation collision and must be verified in the next in-game smoke test.

This keeps the training surface suitable for technique practice and later A/B testing of tyre-physics mods rather than baking easier drift physics into the map.
