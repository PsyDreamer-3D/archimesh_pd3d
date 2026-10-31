# Archimesh (PD3D)

A maintained fork of [Archimesh](https://projects.blender.org/extensions/archimesh) by Antonio Vazquez (antonioya). Archimesh was part of the [Blender 4.1 bundled add-ons](https://docs.blender.org/manual/en/4.1/addons/) and is published upstream on the [Extensions platform](https://extensions.blender.org/add-ons/archimesh).

This fork exists because upstream is community-maintained with no active support, and it is broken on Blender 5.x (edit panels never appear, Room from Draw fails, several materials render unwired).

## Compatibility

- **Minimum Blender version: 5.2.** Older versions are not supported. Blender 5.0 changed how `bpy.props` data and annotations are accessed, so supporting both 4.x and 5.x would mean keeping two code paths.
- **Don't enable this alongside upstream Archimesh.** The extension id is different (`archimesh_pd3d`), so the two install as separate extensions. But the operator names (`mesh.archimesh_*`) and object properties (`RoomGenerator`, `DoorObjectGenerator`, ...) are deliberately the same as upstream's, so rooms, doors and windows in existing .blend files stay editable. That means only one of the two can be registered at a time.

## Changes from upstream 1.2.5

- Room, Door, Rail Window, Panel Window and Venetian edit panels show in the sidebar again on 5.x.
- Room from Draw reads strokes from the Annotate tool (`Scene.annotation`).
- Material builders no longer delete the Material Output node. Handles, hidden control boxes and lamp bulbs get working materials.
- Brick material inputs are set by name, so brick width and row height are correct.
- Manifest declares the `files` permission (room import/export, kitchen inventory export).
- Editing a door, window or room no longer breaks Auto Holes. These objects are rebuilt whenever a parameter changes. Wall and baseboard Booleans are now reconnected to the rebuilt cutters, door/window groups stay parented to the room, and hole cutters are refit when frame or wall thickness changes. (Upstream bug, predates Blender 5.)
- Editing a room, door, window or venetian blind keeps the materials you assigned (including per-face assignments when the face count doesn't change). Before, the defaults came back, or the materials were cleared when "Create materials" was off. Parts that are new in the edit, such as a second leaf after switching to a double door, get the defaults. Materials linked to the object rather than the mesh aren't covered. (Upstream bug, predates Blender 5.)
- Venetian blind Color applies to that blind only and recolors its material in place, instead of creating a new `Plastic_venetian_material.00x` on every edit.
- Roller curtains are editable after creation from a "Roller curtain" sidebar panel, like the Venetian blind. New controls: Extend (how far the fabric is unrolled), Color, and Opacity (sheer to blackout). Each roller gets its own fabric material, so recoloring one doesn't recolor the rest. Width and height are no longer operator arguments, so scripts calling `mesh.archimesh_roller(width=...)` need to set `RollerObjectGenerator[0]` on the new object instead. Rollers made with older versions stay one-shot objects.
- Venetian slats tilt both ways (Angle −85 to 85; positive tips the front edge down), and a Closed toggle tilts them until neighboring slats overlap with a 0.5 mm gap, in the direction of Angle. The closed angle depends on slat depth (about 89° at the default 4 cm), so it can't be a fixed slider value. A 90° angle would make the slats coplanar and z-fight.
- Curtain fabrics reuse the bundled weave texture instead of loading a `fabric_diffuse.png.001` copy and an unused legacy texture each time.

## Building

```bash
<path_to_blender> -c extension build --source-dir=./source
```

For more information about building extensions, see the [documentation](https://docs.blender.org/manual/en/latest/extensions/getting_started.html).

---

Licensed GPL-2.0-or-later, same as upstream.
