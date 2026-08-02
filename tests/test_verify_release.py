from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.verify_release import (
    PublicReleaseError,
    verify_manifest,
    verify_repository,
)


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approved_manifest(payload: Path) -> dict:
    release_file = payload / "guide.md"
    return {
        "schema_version": "kyron.public-release-manifest.v1",
        "release_id": "KYRON-PUBLIC-TEST-001",
        "created_at": "2026-08-02T00:00:00Z",
        "state": "PUBLIC_APPROVED",
        "source_evidence_sha256": "a" * 64,
        "target_repository": "fissafissaintoki/Kyron-runtime-public",
        "files": [
            {
                "path": "guide.md",
                "sha256": digest(release_file),
                "media_type": "text/markdown",
                "disclosure_class": "PUBLIC",
                "origin": "OWNER_CREATED",
                "rights_status": "OWNED",
                "personal_data_reviewed": True,
                "metadata_removed": True,
            }
        ],
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
            "approved_at": "2026-08-02T01:00:00Z",
        },
    }


class PublicRepositoryTests(unittest.TestCase):
    def test_current_public_repository_contract_is_green(self) -> None:
        files = verify_repository(ROOT)
        self.assertIn("RIGHTS.md", files)
        self.assertIn(".github/CODEOWNERS", files)
        self.assertIn(".github/workflows/verify-release.yml", files)

    def test_private_path_and_secret_content_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "repo"
            shutil.copytree(ROOT, candidate, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            leak = candidate / "knowledge" / "raw.md"
            leak.parent.mkdir()
            leak.write_text("not public", encoding="utf-8")
            with self.assertRaisesRegex(PublicReleaseError, "private-system path"):
                verify_repository(candidate)

            shutil.rmtree(leak.parent)
            secret = candidate / "docs" / "leak.txt"
            secret.write_text("sk-" + "A" * 32, encoding="utf-8")
            with self.assertRaisesRegex(PublicReleaseError, "sensitive content pattern"):
                verify_repository(candidate)

    def test_symlinks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "repo"
            shutil.copytree(ROOT, candidate, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            outside = Path(temp) / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            os.symlink(outside, candidate / "docs" / "link.md")
            with self.assertRaisesRegex(PublicReleaseError, "symlink"):
                verify_repository(candidate)


class PublicManifestTests(unittest.TestCase):
    def write_release(self, root: Path) -> tuple[Path, Path, dict]:
        payload = root / "payload"
        payload.mkdir()
        (payload / "guide.md").write_text("# Approved guide\n", encoding="utf-8")
        manifest = approved_manifest(payload)
        manifest_path = root / "release-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return payload, manifest_path, manifest

    def test_approved_hash_bound_manifest_is_green(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            payload, manifest_path, _ = self.write_release(Path(temp))
            evidence = verify_manifest(manifest_path, payload)
            self.assertEqual(len(evidence), 1)

    def test_unapproved_or_changed_payload_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            payload, manifest_path, manifest = self.write_release(Path(temp))
            manifest["approval"]["publish_authorized"] = False
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(PublicReleaseError, "publication authorization"):
                verify_manifest(manifest_path, payload)

            manifest["approval"]["publish_authorized"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (payload / "guide.md").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(PublicReleaseError, "SHA-256 mismatch"):
                verify_manifest(manifest_path, payload)

    def test_unmanifested_payload_and_unsafe_path_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            payload, manifest_path, manifest = self.write_release(Path(temp))
            (payload / "extra.md").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(PublicReleaseError, "manifested exactly once"):
                verify_manifest(manifest_path, payload)

            (payload / "extra.md").unlink()
            manifest["files"][0]["path"] = "../guide.md"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(PublicReleaseError, "unsafe path"):
                verify_manifest(manifest_path, payload)

    def test_manifest_schema_is_closed_and_owner_bound(self) -> None:
        schema = json.loads((ROOT / "schemas/release_manifest.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["target_repository"]["const"],
            "fissafissaintoki/Kyron-runtime-public",
        )
        self.assertEqual(
            schema["properties"]["approval"]["properties"]["human_owner"]["const"],
            "Operator Fischer",
        )


if __name__ == "__main__":
    unittest.main()
