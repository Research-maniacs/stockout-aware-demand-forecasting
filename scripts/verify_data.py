"""Check that the local Parquet files are the ones the saved results were produced with.

The expected sizes and SHA-256 hashes are read from the run E provenance manifest. Run from the
repository root; set FRN_DATA_DIR to check a folder other than data/. Exits with status 1 if a file
is missing or does not match.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "results" / "phase0_9_5k" / "phase0_4" / "manifests" / "provenance.json"
DATA_DIR = Path(os.environ.get("FRN_DATA_DIR") or ROOT / "data")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check(path: Path, expected: dict) -> str | None:
    """Return a problem description, or None if the file matches."""
    if not path.is_file():
        return "missing"
    size = path.stat().st_size
    if size != expected["bytes"]:
        return f"size {size:,} bytes, expected {expected['bytes']:,}"
    digest = sha256(path)
    if digest != expected["sha256"]:
        return f"SHA-256 {digest}, expected {expected['sha256']}"
    return None


def main() -> int:
    source_files = json.loads(PROVENANCE.read_text(encoding="utf-8"))["source_files"]
    failures = 0
    for name, expected in source_files.items():
        problem = check(DATA_DIR / name, expected)
        if problem is None:
            print(f"OK    {name}  {expected['sha256']}")
        else:
            failures += 1
            print(f"FAIL  {name}  {problem}")
    if failures:
        print(f"\n{failures} file(s) in {DATA_DIR} do not match {PROVENANCE.relative_to(ROOT)}.")
        print("Download Version 1.0 of FreshRetailNet-50K; see data/README.md.")
        return 1
    print(f"\nAll files in {DATA_DIR} match the recorded versions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
