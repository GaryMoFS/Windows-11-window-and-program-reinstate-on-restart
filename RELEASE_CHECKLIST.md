# Release Checklist

Use this checklist before publishing a new version.

## 1. Code Quality

- [ ] Pull latest `main`
- [ ] Run static checks/lint (if configured)
- [ ] Run test/verification scripts
- [ ] Confirm app starts from `python src/main.py`

## 2. Functional Validation

- [ ] Save preset works
- [ ] Restore preset works
- [ ] Manage Presets opens and supports rename/delete
- [ ] Tray menu restores/preset list refreshes
- [ ] Context menu actions work
- [ ] Startup restore path works (if enabled)

## 3. Packaging and Docs

- [ ] Update `README.md` if behavior changed
- [ ] Update `requirements.txt` if deps changed
- [ ] Confirm `LICENSE` is present
- [ ] Update changelog/release notes

## 4. Versioning

- [ ] Bump version identifier (if used in app metadata)
- [ ] Create commit for release
- [ ] Create git tag: `vX.Y.Z`
- [ ] Push branch and tag to remote

## 5. Publish

- [ ] Create GitHub release from tag
- [ ] Attach binaries/artifacts (if any)
- [ ] Publish release notes
