# Changelog

All notable changes to Archimesh (PD3D) will be documented here. Version 2.0.0 is the first release of the fork; it's based on upstream Archimesh 1.2.5.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] — 2026-10-31

### Added

- Roller curtains are editable after creation from a "Roller curtain" sidebar panel, like the Venetian blind. New controls: Extend (how far the fabric is unrolled), Color, and Opacity (sheer to blackout). Each roller gets its own fabric material, so recoloring one doesn't recolor the rest.
- Venetian slats tilt both ways (Angle −85 to 85; positive tips the front edge down), and a Closed toggle tilts them until neighboring slats overlap with a 0.5 mm gap, in the direction of Angle. The closed angle depends on slat depth (about 89° at the default 4 cm), so it can't be a fixed slider value. A 90° angle would make the slats coplanar and z-fight.
- Release tooling shared with the other PsyDreamer-3D add-ons: `scripts/` and GitHub Actions workflows that build the extension zip and publish a GitHub Release from a `Release vX.Y.Z` commit or a pushed tag.

### Changed

- Forked as Archimesh (PD3D), extension id `archimesh_pd3d`. Minimum Blender version is 5.2. Blender 5.0 changed how `bpy.props` data and annotations are accessed, so supporting 4.x as well would mean keeping two code paths.
- **Breaking:** `mesh.archimesh_roller` no longer takes width and height arguments. Scripts should set `RollerObjectGenerator[0]` on the new object instead. Rollers made with older versions stay one-shot objects.
- Manifest declares the `files` permission (room import/export, kitchen inventory export).

### Fixed

- Room, Door, Rail Window, Panel Window and Venetian edit panels show in the sidebar again on 5.x.
- Room from Draw reads strokes from the Annotate tool (`Scene.annotation`).
- Material builders no longer delete the Material Output node. Handles, hidden control boxes and lamp bulbs get working materials.
- Brick material inputs are set by name, so brick width and row height are correct.
- Editing a door, window or room no longer breaks Auto Holes. Wall and baseboard Booleans are reconnected to the rebuilt cutters, door/window groups stay parented to the room, and hole cutters are refit when frame or wall thickness changes. (Upstream bug, predates Blender 5.)
- Editing a room, door, window or venetian blind keeps the materials you assigned, including per-face assignments when the face count doesn't change. Parts that are new in the edit get the defaults. Materials linked to the object rather than the mesh aren't covered. (Upstream bug, predates Blender 5.)
- Venetian blind Color applies to that blind only and recolors its material in place, instead of creating a new `Plastic_venetian_material.00x` on every edit.
- Raising a room's Number of Walls no longer prints an `IndexError` traceback. The room rebuilt partway through adding the new walls. (Upstream bug, predates Blender 5.)
- Curtain fabrics reuse the bundled weave texture instead of loading a `fabric_diffuse.png.001` copy and an unused legacy texture each time.
