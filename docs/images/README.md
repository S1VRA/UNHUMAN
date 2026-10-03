# Screenshots

UI screenshots for the project live in this folder. They are referenced from
the **Screenshots** section of `README.md`.

## Current state

Only `assets/banner.png` is committed. No UI screenshots have been captured
yet, so `README.md` does not embed any — adding a `![...](docs/images/...)`
line before the file exists renders a broken image on GitHub and on
npm-style mirrors.

## Capture checklist

Capture at 1100×720 (the app's default window size) on a dark desktop, with
no personal paths visible.

| Filename | Screen | What it should show |
|----------|--------|---------------------|
| `home.png` | Home | Game detected badge, the four feature shortcuts, empty-state card |
| `photos-gallery.png` | Photo Mods | Character card grid with the `show masks` checkbox on |
| `photo-preview.png` | Photo Mods | A character selected, **IN GAME (CURRENT)** vs **NEW IMAGE** on the checkerboard |
| `zip-pack.png` | Photo Pack (ZIP) | A loaded ZIP with matched / unmatched counts |
| `mod-manager.png` | Mod Manager | Backup list with restore and cache actions |
| `game-status.png` | Game Status | Verify result and characters-ready count |

The photo-preview screenshot is the most valuable one: it is the only place
where a transparent PNG is visibly rendered against the checkerboard.

## Adding them

1. Save the PNGs into this folder using the names above.
2. Add a `## Screenshots` section to `README.md` with both language variants,
   mirroring the existing bilingual structure:

```markdown
## Screenshots

<p align="center">
  <img src="docs/images/home.png" alt="Home screen" width="49%">
  <img src="docs/images/photos-gallery.png" alt="Photo Mods gallery" width="49%">
</p>
```

3. Cross-check the tab names against `locales/en.json` before capturing — the
   UI is fully localized, so a stale screenshot is easy to leave behind.
