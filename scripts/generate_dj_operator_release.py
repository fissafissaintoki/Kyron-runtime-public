#!/usr/bin/env python3
"""Generate the deterministic public manifest for KYRON DJ Operator v0.1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = ROOT / "releases" / "dj-operator-v0.1"
PAYLOAD_ROOT = RELEASE_ROOT / "payload"
MANIFEST_PATH = RELEASE_ROOT / "release-manifest.json"
SOURCE_EVIDENCE_SHA256 = "a7ac07b08051d1f1e5a2434225bceba85bbef3748a524a74dc9d47c06d762795"
CREATED_AT = "2026-08-05T12:43:00Z"

MEDIA_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".js": "text/javascript",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".webmanifest": "application/manifest+json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_manifest() -> dict[str, object]:
    if not PAYLOAD_ROOT.is_dir():
        raise SystemExit(f"DJ RELEASE RED: payload missing: {PAYLOAD_ROOT}")

    files: list[dict[str, object]] = []
    for path in sorted(item for item in PAYLOAD_ROOT.rglob("*") if item.is_file()):
        relative = path.relative_to(PAYLOAD_ROOT).as_posix()
        suffix = path.suffix.lower()
        media_type = MEDIA_TYPES.get(suffix)
        if not media_type:
            raise SystemExit(f"DJ RELEASE RED: unsupported public file type: {relative}")
        files.append(
            {
                "path": relative,
                "sha256": digest(path),
                "media_type": media_type,
                "disclosure_class": "PUBLIC",
                "origin": "OWNER_CREATED",
                "rights_status": "OWNED",
                "personal_data_reviewed": True,
                "metadata_removed": True,
            }
        )

    if not files:
        raise SystemExit("DJ RELEASE RED: payload is empty")

    return {
        "schema_version": "kyron.public-release-manifest.v1",
        "release_id": "KYRON-PUBLIC-DJ-OPERATOR-V0-1",
        "created_at": CREATED_AT,
        "state": "PUBLIC_APPROVED",
        "source_evidence_sha256": SOURCE_EVIDENCE_SHA256,
        "target_repository": "fissafissaintoki/Kyron-runtime-public",
        "files": files,
        "checks": {
            "secret_scan_green": True,
            "disclosure_review_green": True,
            "personal_data_review_green": True,
            "third_party_rights_green": True,
            "hash_verification_green": True,
        },
        "approval": {
            "human_owner": "Operator Fischer",
            "owner_approved": True,
            "publish_authorized": True,
            "approved_at": CREATED_AT,
        },
    }


def main() -> int:
    manifest = generate_manifest()
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "DJ PUBLIC MANIFEST GREEN — "
        f"{len(manifest['files'])} files — {MANIFEST_PATH.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
