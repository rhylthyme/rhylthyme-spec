PY := python

.PHONY: test release

test:
	$(PY) -m pytest -q tests/

# Publish origin/main to PyPI at the version pyproject.toml names.
# DRY_RUN=1 make release builds and tests it without publishing. See scripts/release.sh.
release:
	./scripts/release.sh
