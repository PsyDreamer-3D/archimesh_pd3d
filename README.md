# Archimesh (PD3D)

A maintained fork of [Archimesh](https://projects.blender.org/extensions/archimesh) by Antonio Vazquez (antonioya). Archimesh was part of the [Blender 4.1 bundled add-ons](https://docs.blender.org/manual/en/4.1/addons/) and is published upstream on the [Extensions platform](https://extensions.blender.org/add-ons/archimesh).

This fork exists because upstream is community-maintained with no active support, and it is broken on Blender 5.x (edit panels never appear, Room from Draw fails, several materials render unwired).

## Compatibility

- **Minimum Blender version: 5.2.** Older versions are not supported. Blender 5.0 changed how `bpy.props` data and annotations are accessed, so supporting both 4.x and 5.x would mean keeping two code paths.
- **Don't enable this alongside upstream Archimesh.** The extension id is different (`archimesh_pd3d`), so the two install as separate extensions. But the operator names (`mesh.archimesh_*`) and object properties (`RoomGenerator`, `DoorObjectGenerator`, ...) are deliberately the same as upstream's, so rooms, doors and windows in existing .blend files stay editable. That means only one of the two can be registered at a time.

## Installing and updates

Add this fork as a remote repository so Blender offers updates:

1. Preferences → Get Extensions → Repositories (the drop-down at the top right) → **+** → **Add Remote Repository**.
2. URL: `https://github.com/PsyDreamer-3D/archimesh_pd3d/releases/latest/download/index.json`
3. Turn on **Check for Updates on Startup** if you want Blender to check automatically.
4. Install "Archimesh (PD3D)" from the Get Extensions list.

Every GitHub Release carries an `index.json` next to the zip, and the `latest/download` URL always points at the newest release, so Blender sees each new version as an update. To install one version by hand without updates, drag that release's zip into Blender instead.

## Changes from upstream 1.2.5

See [CHANGELOG.md](CHANGELOG.md). It lists every fix and feature the fork adds, including one breaking change to the roller curtain operator.

## Building

The add-on package is `archimesh_pd3d/`. For a one-off zip:

```bash
<path_to_blender> -c extension build --source-dir=./archimesh_pd3d --output-dir=./dist
```

`scripts/build_dev.sh` makes a local `-alpha.N` build from the latest release tag. It needs `blender` on your `PATH`. For more about building extensions, see the [documentation](https://docs.blender.org/manual/en/latest/extensions/getting_started.html).

## Releasing

1. While working, log changes under `## [Unreleased]` in `CHANGELOG.md`.
2. On `main` with a clean tree, run `scripts/prepare_release.sh X.Y.Z`. It dates the changelog section, sets the manifest version and commits `Release vX.Y.Z`. It doesn't push.
3. Push that commit to `main` directly or through a rebase merge. The commit message has to stay exactly `Release vX.Y.Z`; a merge commit or a squash with a different PR title won't trigger the release. `.github/workflows/auto-tag-release.yml` checks that the manifest and changelog agree, tags the commit and runs `release.yml`, which builds the zip with Blender 5.2.3 and publishes a GitHub Release with the zip and `index.json` attached, using that changelog section as the notes.

As a fallback, pushing a `vX.Y.Z` tag by hand also runs `release.yml`.

---

Licensed GPL-2.0-or-later, same as upstream.
