#!/usr/bin/env python3
"""Verify a KYRON public release artifact against its manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    artifact = args.artifact_dir / data["artifact"]
    actual = sha256(artifact)
    expected = data["sha256"]

    if actual != expected:
        raise SystemExit(
            f"VERIFY FAIL\nexpected={expected}\nactual={actual}"
        )

    print(f"VERIFY GREEN: {artifact.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
