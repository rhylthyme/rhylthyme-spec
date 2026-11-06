#!/usr/bin/env bash
# Release rhylthyme-spec to PyPI: what is merged on origin/main, at the version
# its pyproject.toml already names.
#
#   make release              # release origin/main
#   DRY_RUN=1 make release    # build and test it, publish nothing
#
# The version is chosen in the pull request that changes the schemas: it sets
# `version` in pyproject.toml and `__version__` in src/rhylthyme_spec/__init__.py
# and adds a "## Package <version> - unreleased" heading to CHANGELOG.md. This
# script dates that heading and builds the package from a temporary checkout of
# origin/main, so your branch and uncommitted files don't matter. It installs
# the wheel in a throwaway virtualenv and runs the tests against it, then asks
# once before it pushes the release commit and tag and uploads. YES=1 skips the
# question.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PACKAGE=rhylthyme-spec
MODULE=rhylthyme_spec
die() { echo "release: $*" >&2; exit 1; }

if [ -n "${PYTHON:-}" ]; then PY=$PYTHON
elif [ -n "${VIRTUAL_ENV:-}" ]; then PY=$VIRTUAL_ENV/bin/python
elif [ -x ../.venv/bin/python ]; then PY=$PWD/../.venv/bin/python
else PY=python3
fi
TWINE=${TWINE:-$PY -m twine}
"$PY" -m build --version >/dev/null || die "the build package isn't installed in $PY"
$TWINE --version >/dev/null || die "twine isn't installed in $PY"

git fetch origin --tags --quiet
base=$(git rev-parse origin/main)

# Everything up to the push happens in a temporary checkout of origin/main.
tmp=$(mktemp -d)
wt=$tmp/$PACKAGE
keep_dist=
cleanup() {
    git worktree remove --force "$wt" 2>/dev/null || true
    git worktree prune
    if [ -n "$keep_dist" ]; then rm -rf "$tmp/venv"; else rm -rf "$tmp"; fi
}
trap cleanup EXIT
git worktree add -q --detach "$wt" "$base"

# --- The version, and whether it's still unreleased.
version=$(sed -n 's/^version = "\(.*\)"$/\1/p' "$wt/pyproject.toml" | head -1)
[ -n "$version" ] || die "no version found in pyproject.toml"
pep440=$("$PY" -c 'import sys; from packaging.version import Version; print(Version(sys.argv[1]))' "$version" 2>/dev/null) \
    || die "pyproject.toml's version isn't a PEP 440 version: $version"
init=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$wt/src/$MODULE/__init__.py" | head -1)
[ "$init" = "$version" ] || die "pyproject.toml says $version but src/$MODULE/__init__.py says ${init:-nothing}"
tag=v$pep440
next="start the next one in pyproject.toml, src/$MODULE/__init__.py and a \"## Package <version> - unreleased\" heading in CHANGELOG.md"
! git rev-parse -q --verify "refs/tags/$tag" >/dev/null || die "$version is already released (tag $tag); $next"
status=$(curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/$PACKAGE/$pep440/json") || true
[ "$status" != 200 ] || die "$pep440 is already on PyPI; $next"
[ "$status" = 404 ] || die "couldn't ask PyPI whether $pep440 exists (HTTP $status)"

# --- CHANGELOG.md: this version's entry is the newest, and gets today's date.
dated=$("$PY" - "$wt/CHANGELOG.md" "$version" "$(date +%F)" <<'EOF'
import re, sys

path, version, today = sys.argv[1:]
with open(path, encoding="utf-8") as fh:
    text = fh.read()
# "## Package 0.2.4-alpha - unreleased: video timelines" -> 0.2.4-alpha, unreleased
headings = list(re.finditer(r"^## Package (\S+) - ([^\s:]+)", text, re.M))
if not headings or headings[0].group(1) != version:
    sys.exit(f"the newest entry in CHANGELOG.md has to be '## Package {version} - unreleased'"
             f" (it's {headings[0].group(0)!r})" if headings else "CHANGELOG.md has no '## Package' entries")
stale = [h.group(1) for h in headings[1:] if h.group(2) == "unreleased"]
if stale:
    sys.exit(f"CHANGELOG.md still has unreleased entries for {', '.join(stale)}")
when = headings[0].group(2)
if when == "unreleased":
    text = text[: headings[0].start(2)] + today + text[headings[0].end(2):]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(today)
elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
    print("")
else:
    sys.exit(f"can't read the date in {headings[0].group(0)!r}: use 'unreleased' or YYYY-MM-DD")
EOF
) || die "fix CHANGELOG.md on main first"
if [ -n "$dated" ]; then
    git -C "$wt" commit -q -m "Release $version" -- CHANGELOG.md
fi
release=$(git -C "$wt" rev-parse HEAD)

echo "==> Releasing $PACKAGE $version ($pep440) from origin/main $(git log -1 --format='%h %s' "$base")"

# --- Build and check the package.
echo "==> Build"
"$PY" -m build --outdir "$tmp/dist" "$wt" >"$tmp/build.log" 2>&1 \
    || { cat "$tmp/build.log" >&2; die "the build failed"; }
artifacts=("$tmp/dist/$MODULE-$pep440-py3-none-any.whl" "$tmp/dist/$MODULE-$pep440.tar.gz")
for a in "${artifacts[@]}"; do [ -f "$a" ] || die "the build didn't make $(basename "$a"): $(ls "$tmp/dist")"; done
$TWINE check --strict "${artifacts[@]}"

# --- Test what will be uploaded: the wheel, installed on its own.
echo "==> Tests, against the installed wheel"
"$PY" -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install -q --disable-pip-version-check "${artifacts[0]}" pytest
"$tmp/venv/bin/python" - "$wt/src/$MODULE/schemas" "$version" <<'EOF'
import os, sys
import rhylthyme_spec as spec

source, version = sys.argv[1:]
assert "site-packages" in spec.__file__, f"imported {spec.__file__}, not the wheel"
assert spec.__version__ == version, f"the wheel says {spec.__version__}"
missing = [f for f in sorted(os.listdir(source)) if not os.path.isfile(spec.get_schema_path(f))]
assert not missing, f"the wheel is missing {', '.join(missing)}"
EOF
# The tests read rhylthyme-examples beside the checkout when it's there.
[ ! -d ../rhylthyme-examples ] || ln -s "$(cd ../rhylthyme-examples && pwd)" "$tmp/rhylthyme-examples"
(cd "$tmp" && "$tmp/venv/bin/python" -m pytest -q -p no:cacheprovider "$wt/tests")

if [ -n "${DRY_RUN:-}" ]; then
    echo "==> Dry run passed: $pep440 would be published. Nothing was pushed."
    exit 0
fi

# --- PyPI versions can't be replaced, so this is the one question it asks.
if [ -z "${YES:-}" ]; then
    read -r -p "Publish $PACKAGE $version to PyPI? This can't be undone. [y/N] " answer || answer=
    [ "$answer" = y ] || [ "$answer" = Y ] || die "cancelled; nothing was pushed"
fi

git tag -a "$tag" -m "$PACKAGE $version" "$release"
# Atomic: if main moved since the fetch, neither main nor the tag is pushed.
git push -q --atomic origin "$release:refs/heads/main" "refs/tags/$tag" || {
    git tag -d "$tag" >/dev/null
    die "the push failed, so nothing was published; if main moved, run make release again"
}

echo "==> Upload"
keep_dist=1
$TWINE upload "${artifacts[@]}" || die "the upload failed. main and $tag are pushed, so retry with:
  $TWINE upload --skip-existing ${artifacts[*]}"
keep_dist=
echo "==> Published https://pypi.org/project/$PACKAGE/$pep440/"

# Bring the local main up to the release commit where that's a fast-forward.
if [ "$(git branch --show-current)" = main ]; then
    git merge -q --ff-only origin/main 2>/dev/null || echo "==> Run git pull on main to get the release commit."
else
    git fetch -q origin main:main 2>/dev/null || echo "==> Run git pull on main to get the release commit."
fi
