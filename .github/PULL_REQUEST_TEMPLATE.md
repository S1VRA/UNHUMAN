## Description

A clear and concise description of your changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Refactor
- [ ] Documentation update
- [ ] Build / packaging

## Checklist

- [ ] My code follows PEP 8 style guidelines
- [ ] No bare `except:` — every exception is caught with a specific type or `Exception`
- [ ] No `print()` — diagnostics go through the `nhmodtool` logger
- [ ] Public functions have type hints
- [ ] I have tested my changes locally
- [ ] I have updated `CHANGELOG.md` under `[Unreleased]`
- [ ] I have updated the documentation if needed
- [ ] My commit messages follow Conventional Commits format

## Testing

How did you verify this?

```
python -m pytest tests/test_data_and_history.py tests/test_file_safety.py \
                 tests/test_packaging.py tests/test_paths_policy.py \
                 tests/test_zip_pack.py
python NHModTool.py --selftest
```
