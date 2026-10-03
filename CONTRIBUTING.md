# Contributing to NH Mod Tool

Thank you for considering contributing to NH Mod Tool! This document outlines the guidelines for contributing to this project.

## How to Contribute

### Fork & Branch

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/S1VRA/UNHUMAN.git
   ```
3. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

### Development Setup

```bash
cd UNHUMAN
pip install -r requirements.txt
python NHModTool.py
```

### Running Tests

```bash
# Unit tests
python -m pytest tests/test_data_and_history.py tests/test_file_safety.py \
                 tests/test_packaging.py tests/test_paths_policy.py \
                 tests/test_zip_pack.py

# Application self-test
python NHModTool.py --selftest

# Asset decoding test (reads the real game file)
python NHModTool.py --assettest
```

`tests/` also holds ad-hoc `memory_*.py` / demo scripts that are **not**
collectable by pytest (`memory_fixed_test.py` references a symbol that no
longer exists and breaks collection). Run the `test_*.py` files explicitly.

### Continuous Integration

`.github/workflows/python-test.yml` runs on every push and pull request to
`main` (Windows, Python 3.14). It byte-compiles `NHModTool.py` and `theme.py`
only — the pytest suite is **not** executed by CI, so run the commands above
locally before opening a PR.

### Building the Release

Two steps; the first script only covers step 1.

```bash
# 1) Nuitka standalone build + SHA-256 of the exe
build_release.bat
```

Output: `dist/NHModTool.dist/NHModTool.exe` **plus its dependency folders**.
This is a standalone *folder* build, not a single-file executable — ship the
whole `dist/NHModTool.dist/` directory.

```bash
# 2) Inno Setup installer from that folder
iscc installer.iss
```

Output: `dist/NHModTool_v<version>_Setup.exe` (EN + TR wizard languages,
Start Menu entry, uninstaller).

`scripts/verify_build.py` performs the post-build checks (embedded icon,
`--selftest`, `--assettest`, SHA-256). Note it still looks for the obsolete
`dist/NHModTool.exe` path, so correct its `EXE` constant before relying on it.

### Code Style

- Follow **PEP 8** for all Python code.
- Use **Conventional Commits** for commit messages:
  - `feat: add new mod import flow`
  - `fix: resolve backup date display issue`
  - `docs: update installation guide`
  - `refactor: extract theme logic into theme.py`
  - `chore: update dependencies`

### Pull Requests

1. Ensure your branch is up to date with `main`.
2. Write a clear description of your changes.
3. Reference any related issues (e.g., `Closes #12`).
4. Submit the PR and wait for review.

### Reporting Issues

Use the [Bug Report](https://github.com/S1VRA/UNHUMAN/issues/new?template=bug_report.md) template for bugs or the [Feature Request](https://github.com/S1VRA/UNHUMAN/issues/new?template=feature_request.md) template for suggestions.

## Code of Conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.
