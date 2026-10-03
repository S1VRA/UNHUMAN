# Usage Guide

NH Mod Tool has six screens, reachable from the left sidebar.

| Screen | Purpose |
|--------|---------|
| **Home** | Overview, game detection, shortcuts |
| **Photo Mods** | Replace one character's in-game photo at a time |
| **Photo Pack (ZIP)** | Replace many characters from a single ZIP |
| **Mod Manager** | Backups, restore points, thumbnail cache |
| **Game Status** | Verify the game file, see what changed |
| **Settings** | Game file path, language |

---

## Getting Started

1. On first launch the tool scans for the game's `sharedassets0.assets` in
   `%LOCALAPPDATA%\Games\No, I'm not a Human\` and in your Steam libraries.
2. If nothing is found, open **Settings** and press **Browse…** to select
   `sharedassets0.assets` (it lives inside `NoImNotAHuman_Data`).
3. Close the game before applying mods — the file cannot be written while the
   game holds it open.

## Home

Shows whether the game was detected, plus shortcuts to **Photo Mods**,
**Photo Pack (ZIP)**, **Mod Manager** and **Game Status**.

Also available here: *Open game folder*, *Restore backup*, *Clear cache* and
*Open data folder*.

---

## Photo Mods

The main screen for replacing a single character photo.

1. Pick a **character** from the gallery on the left. The card shows the
   texture's pixel size and its Unity format.
2. Press **Photo…** and choose an image
   (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`).
3. The preview shows **IN GAME (CURRENT)** beside **NEW IMAGE** on a
   checkerboard, so transparency is visible.
4. Press **APPLY TO GAME** and confirm.

Details:

- **show masks** — include the `*_mask` companion textures in the gallery.
- `Ctrl` + mouse wheel (or `Ctrl` + `−` / `+`) resizes the cards.
- Your image is scaled to fit the texture's own pixel dimensions and centred on
  a transparent background, so the aspect ratio is never stretched.

### Transparent photos

Transparency is preserved for the formats the game uses for its portraits
(`DXT5`, `RGBA32`): a PNG with a cut-out background stays cut out in-game,
at its original opacity.

A few textures are stored in formats that physically have no alpha channel
(`DXT1`, `ETC_RGB`, `ATC_RGB`, `ASTC_RGB`, `RGB24`, `PVRTC_RGB*`). For those,
transparency is flattened to fully opaque and a warning is written to the log.
Check `%APPDATA%\NHModTool\logs\app.log` if a photo looks less transparent than
you expected.

---

## Photo Pack (ZIP)

Apply many characters at once.

1. Press **Choose ZIP…** and select a `.zip` archive.
2. The tool lists the images it found and matches each file name against the
   character/texture names (e.g. `fake_neighbour1.png`). Matched and
   unmatched counts are shown.
3. Press **APPLY ZIP TO GAME**.

To build a pack: put the character images in a folder, name each file exactly
after the character, and zip the folder.

The archive is validated before anything is written: ZIP-slip path traversal,
symlinks, reserved Windows names, password-protected entries and ZIP bombs are
all rejected, and every member's magic bytes must match its extension.

---

## Mod Manager

| Action | Description |
|--------|-------------|
| **BACK UP GAME FILE NOW** | Copy the current `sharedassets0.assets` into `data\backups` with a timestamp. |
| **Restore selected backup** | Replace the game file with a chosen backup. |
| **Copy to data\backups** | Duplicate a listed backup into your own backup folder. |
| **Delete backup** | Remove a backup from the list. |
| **Clear cache** | Delete the generated thumbnail cache in `data\cache`. |
| **Open backups folder** / **Open data folder** | Jump to the folder in Explorer. |

Note: the automatic `sharedassets0.assets.bak` that sits next to the game file
is always kept as the pristine original and is never rotated away by the
manual backups above.

---

## Game Status

- Whether the game file was found, and the current scan state.
- **Verify game file** — re-reads the game file and reports its state.
- How many characters are ready to be modded.
- Restore entries for backups applied from this screen.

---

## Settings

| Setting | Description |
|---------|-------------|
| **Game file** | Path to `sharedassets0.assets`. **Browse…** to pick it manually, **Scan again** to re-run auto-detection. |
| **Restore original game file from backup** | Reverts to the `.bak` next to the game file. |
| **Language** | English or Türkçe. A restart is required for the change to take effect. |

If `settings.json` is corrupt, the tool renames it to `settings.json.bak`,
falls back to defaults and tells you where the old file went.

---

## Safety Model

Every apply follows the same sequence:

1. The photo is written into a temporary copy.
2. The copy is re-read and compared against the original — the operation is
   rejected unless **exactly** the intended texture changed.
3. A `.bak` of the game file is created if one does not already exist.
4. The new file is moved into place atomically.

If verification fails, the game file is left untouched.

---

## Where Data Lives

| Install type | Data folder |
|--------------|-------------|
| Installer | `%APPDATA%\NHModTool` |
| From source | `<repo>\data` |

Contains `settings.json`, `backups\`, `cache\`, `mod_history.json` and
`logs\app.log`.

## Troubleshooting

| Symptom | What to do |
|---------|------------|
| Injection fails | Close the running game and retry. |
| Character shows the old photo | Open **Mod Manager** and restore a backup, then re-apply. |
| Photo looks fully opaque | The texture format has no alpha channel — see *Transparent photos* above. |
| Any other failure | Attach `%APPDATA%\NHModTool\logs\app.log` to your bug report. |
