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

## Building

```bash
<path_to_blender> -c extension build --source-dir=./source
```

For more information about building extensions, see the [documentation](https://docs.blender.org/manual/en/latest/extensions/getting_started.html).

---

Licensed GPL-2.0-or-later, same as upstream.
