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
python -m pytest tests/

# Application self-test
python NHModTool.py --selftest

# Asset decoding test
python NHModTool.py --assettest
```

### Building the EXE

```bash
build_release.bat
```

Output: `dist/NHModTool.exe` (single-file, no dependencies required)

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
