#!/usr/bin/env python3
"""Release guard rails for Robzone Xclean.

    release.py check VERSION      # verify the repo is ready to release VERSION
    release.py build VERSION ZIP  # build and verify the HACS archive

Exits non-zero with a readable list of problems, so a release can never be
published from an inconsistent state.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / "custom_components" / "robzone_xclean"
MANIFEST = INTEGRATION / "manifest.json"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_NOTES = ROOT / "RELEASE_NOTES.md"
HACS_JSON = ROOT / "hacs.json"

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
REQUIRED_IN_ZIP = ("manifest.json", "__init__.py", "config_flow.py", "const.py")
EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def _semver(value: str) -> tuple[int, int, int] | None:
    match = SEMVER.match(value)
    return tuple(int(p) for p in match.groups()) if match else None  # type: ignore[return-value]


def _released_versions() -> list[tuple[int, int, int]]:
    out = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    versions = [_semver(tag[1:]) for tag in out.split()]
    return sorted(v for v in versions if v)


def check(version: str) -> list[str]:
    errors: list[str] = []
    wanted = _semver(version)
    if wanted is None:
        return [f"Verze '{version}' neni ve formatu X.Y.Z (bez 'v')."]

    manifest_version = json.loads(MANIFEST.read_text(encoding="utf-8")).get("version")
    if manifest_version != version:
        errors.append(
            f"manifest.json ma version={manifest_version!r}, vydavas {version!r}."
        )

    changelog = CHANGELOG.read_text(encoding="utf-8")
    headings = re.findall(r"^## (\d+\.\d+\.\d+)\b", changelog, flags=re.M)
    if not headings:
        errors.append("CHANGELOG.md nema zadnou sekci '## X.Y.Z'.")
    elif headings[0] != version:
        errors.append(
            f"Prvni sekce CHANGELOG.md je {headings[0]}, ocekavano {version}."
        )

    notes = RELEASE_NOTES.read_text(encoding="utf-8")
    first_heading = next(
        (line for line in notes.splitlines() if line.startswith("#")), ""
    )
    if f"v{version}" not in first_heading:
        errors.append(
            f"RELEASE_NOTES.md nadpis '{first_heading.strip()}' neobsahuje v{version}."
        )

    hacs = json.loads(HACS_JSON.read_text(encoding="utf-8"))
    if not hacs.get("zip_release") or hacs.get("filename") != "robzone_xclean.zip":
        errors.append("hacs.json musi mit zip_release=true a filename=robzone_xclean.zip.")

    released = _released_versions()
    if wanted in released:
        errors.append(f"Tag v{version} uz existuje. Zvys verzi.")
    elif released and wanted < released[-1]:
        latest = ".".join(map(str, released[-1]))
        errors.append(f"v{version} je nizsi nez posledni vydana v{latest}.")

    return errors


def build(version: str, target: Path) -> list[str]:
    files = sorted(
        p for p in INTEGRATION.rglob("*")
        if p.is_file()
        and not EXCLUDED_PARTS.intersection(p.relative_to(INTEGRATION).parts)
        and p.suffix not in EXCLUDED_SUFFIXES
    )
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(INTEGRATION).as_posix())

    errors: list[str] = []
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
        for required in REQUIRED_IN_ZIP:
            if required not in names:
                errors.append(f"ZIP neobsahuje {required} v koreni archivu.")
        nested = [n for n in names if n.startswith("custom_components/")]
        if nested:
            errors.append(f"ZIP obsahuje vnorenou cestu custom_components/ ({nested[0]}).")
        if "manifest.json" in names:
            zipped = json.loads(archive.read("manifest.json")).get("version")
            if zipped != version:
                errors.append(f"manifest.json v ZIPu ma verzi {zipped!r}, ne {version!r}.")
    if not errors:
        print(f"Archiv {target.name}: {len(names)} souboru, layout OK.")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in {"check", "build"}:
        print(__doc__)
        return 2
    command, version = argv[1], argv[2].removeprefix("v")
    if command == "check":
        errors = check(version)
    else:
        if len(argv) != 4:
            print(__doc__)
            return 2
        errors = build(version, Path(argv[3]).resolve())

    if errors:
        print(f"::error::Release v{version} zastaven:")
        for error in errors:
            print(f"::error::  - {error}")
        return 1
    if command == "check":
        print(f"Kontrola v{version}: manifest, CHANGELOG, RELEASE_NOTES a tagy sedi.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
