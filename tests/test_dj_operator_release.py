from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.generate_dj_operator_release import (
    MANIFEST_PATH,
    PAYLOAD_ROOT,
    SOURCE_EVIDENCE_SHA256,
    generate_manifest,
)
from scripts.verify_release import verify_manifest


ROOT = Path(__file__).resolve().parents[1]


class DjOperatorPublicReleaseTests(unittest.TestCase):
    def test_manifest_generation_is_hash_bound_and_owner_approved(self) -> None:
        manifest = generate_manifest()

        self.assertEqual(manifest["state"], "PUBLIC_APPROVED")
        self.assertEqual(
            manifest["release_id"],
            "KYRON-PUBLIC-DJ-OPERATOR-V0-1",
        )
        self.assertEqual(
            manifest["source_evidence_sha256"],
            SOURCE_EVIDENCE_SHA256,
        )
        self.assertEqual(manifest["approval"]["human_owner"], "Operator Fischer")
        self.assertTrue(manifest["approval"]["owner_approved"])
        self.assertTrue(manifest["approval"]["publish_authorized"])
        self.assertEqual(len(manifest["files"]), 8)
        self.assertEqual(
            {entry["path"] for entry in manifest["files"]},
            {
                "app.js",
                "engine.js",
                "icon.svg",
                "index.html",
                "manifest.webmanifest",
                "service-worker.js",
                "session.js",
                "styles.css",
            },
        )

    def test_generated_release_passes_public_verifier(self) -> None:
        manifest = generate_manifest()
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        evidence = verify_manifest(MANIFEST_PATH, PAYLOAD_ROOT)
        self.assertEqual(len(evidence), 8)

    def test_public_payload_contains_no_audio_or_external_provider_contract(self) -> None:
        files = [path for path in PAYLOAD_ROOT.rglob("*") if path.is_file()]
        self.assertFalse(any(path.suffix.lower() in {".mp3", ".wav", ".aiff", ".flac"} for path in files))
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in files
            if path.suffix.lower() in {".html", ".css", ".js", ".json", ".webmanifest", ".svg"}
        )
        self.assertNotIn("API_KEY", combined)
        self.assertNotIn("WebSocket", combined)
        self.assertIn("AUDIO BLEIBT AUF DIESEM GERÄT", combined)
        self.assertIn("LOCAL_METADATA_ONLY_NO_AUDIO", combined)

    def test_pages_workflow_is_production_guarded(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "dj-operator-pages.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("actions/configure-pages@v5", workflow)
        self.assertIn("enablement: true", workflow)
        self.assertIn("actions/upload-pages-artifact@v4", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertGreaterEqual(
            workflow.count("if: github.event_name != 'pull_request'"),
            3,
        )
        self.assertNotIn("secrets.", workflow)


if __name__ == "__main__":
    unittest.main()
