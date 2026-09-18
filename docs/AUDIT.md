# FINAL PERFORMANCE + PHOTO PACK AUDIT

Date: 2026-09-17
Build: `dist\NHModTool.exe` (91.0 MB) &middot; SHA-256 `80bcdcaa8626ced0d3014cdb7141a20dc52ac133bc96be8a11c58e27c8e785d3`

## REMOVE BACKGROUND

- Reworked to a single-flight safe pipeline: one inference at a time (global
  lock), lazy model load (never at startup), ONNX session reused across calls,
  ONNX thread caps (`intra-op` &le; 4, `inter-op` 1) so CPU isn't
  oversubscribed.
- Removed the original double-trigger race: "Remove background" toggle and the
  photo picker now bump a per-request generation id; stale results for a
  previous photo/state are discarded instead of being applied to the new
  selection. Rapid toggle ON&rarr;OFF&rarr;ON is covered by tests.
- Cache keyed by image **content hash + model version** (`bria-rmbg` +
  `2.0.84`); corrupt cache entries are deleted and regenerated; re-importing
  the same image hits cache instantly.
- Unchecking the toggle (even mid-inference) restores the original image
  immediately; state resets cleanly when picking a new photo or closing the
  app (worker threads are daemonic, no shutdown hang).
- Verified: `tests\test_bg_concurrency.py` (18 tests) and frozen-exe `--bgtest`
  (import, thread caps, **session reuse, real rembg removal, transparency
  alpha=0 corners / alpha=254 subject** all PASS).

## PHOTO PACK

- ZIP members are read from memory &mdash; never extracted to disk &mdash; so
  path traversal is impossible; additionally `../`, absolute-path and
  drive-letter member names are rejected and reported.
- Matching rule matches the README: leaf file name without extension
  (e.g. `fake_neighbour1.png`, `chars/fake_neighbour1.jpg`). Supported: PNG,
  JPG/JPEG, WebP, BMP, GIF. Validated before any write; whole-archive
  validation aborts before touching the game file on any bad member.
- Clear UI reporting: matched vs skipped, duplicates (last file wins), unsafe
  paths, oversized members (&gt; 32 MB), missing characters, with distinct
  messages for corrupt / password-protected / unsupported-compression /
  unreadable-image members.
- Concurrency guarded: cannot re-pick a photo/ZIP or start a second apply while
  one is running.
- Apply/verify/commit now release UnityPy handles before the atomic
  `os.replace`, fixing the Windows `PermissionError [WinError 5]` that occurred
  when a reader was still open. `_atomic_replace` retries after `gc.collect()`.
- E2E proof: on a pristine **copy** of the real `sharedassets0.assets`
  (+ `.resS`), one full cycle apply &rarr; verify-only-reference-changed
  &rarr; restriction applied &rarr; restore from backup is byte-identical
  (MD5 + size checks). **The real game file was never opened for writing.** The
  real file hash is asserted by `tests\test_guards.py` and left untouched.

## TESTS

- Suite: `python -m unittest discover -s tests` &rarr; **64/64 PASS**
  (26 pre-existing + 18 background/removal matrix + 20 photo-pack/ZIP matrix).
- Frozen exe: `--selftest` 12/12 PASS; `--bgtest` PASS (real model inference
  inside the exe); `--assettest` PASS (760 Texture2D scanned, 405 `fake_*`
  matched, 40/40 sample textures decoded to RGBA thumbs).
- Source-mode extra runs: same three headless modes PASS before rebuild.

## EXE

- Size **91.0 MB** (unchanged, no regression) &mdash; torch, torchvision,
  torchaudio, numba, llvmlite, matplotlib remain excluded; runtime verified in
  build logs and by size bound (20&ndash;300 MB check in
  `tests\test_packaging.py`).
- Icon embedded; SHA-256 checksum written to `dist\SHA256SUMS.txt`.
- GUI smoke: launched the fresh exe against an empty cache &rarr; all
  thumbnails regenerated (proves photo tab decodes every texture), app stayed
  alive across a 45 s window, closed cleanly.

## RELEASE STATUS

- **RELEASE-READY** on this machine. The release blocker (ZIP apply
  `PermissionError`) is fixed and verified with a full MD5 round-trip E2E.
- **NOT TESTABLE:** clean Windows VM (no Steam/game install drift vs real
  first-run download path) &mdash; background model downloads to
  `%USERPROFILE%\.u2net` on first removal; not exercised on a clean machine.
- Temp/diagnostic files (locktest scripts, stray screenshots, report JSONs in
  the repo root, empty-copy leftovers) removed.