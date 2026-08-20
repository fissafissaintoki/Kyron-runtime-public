from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.verify_red_team_public_offer import (
    OFFER_CONFIG,
    OFFER_DOCUMENT,
    PublicOfferError,
    require_release_eligibility,
    validate_public_offer,
)
from scripts.verify_release import verify_repository


ROOT = Path(__file__).resolve().parents[1]


class PublicRedTeamOfferTests(unittest.TestCase):
    def copy_offer(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        candidate = Path(temporary.name) / "repo"
        shutil.copytree(ROOT, candidate, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        return candidate

    def test_owner_gated_offer_content_is_safe_and_has_one_real_cta(self) -> None:
        receipt = validate_public_offer(ROOT)

        self.assertEqual(receipt.product_id, "KYRON_MCP_APP_GOVERNANCE_AUDIT")
        self.assertTrue(receipt.primary_cta_ready)
        self.assertEqual(receipt.unresolved_owner_gates, ("privacy", "support", "payment"))
        self.assertFalse(receipt.release_eligible)

    def test_release_eligibility_fails_closed_until_owner_gates_are_resolved(self) -> None:
        with self.assertRaisesRegex(PublicOfferError, "privacy, support, payment"):
            require_release_eligibility(ROOT)

    def test_offer_files_pass_the_public_repository_safety_scan_when_staged(self) -> None:
        candidate = self.copy_offer()
        files = verify_repository(candidate)

        self.assertIn(OFFER_DOCUMENT.as_posix(), files)
        self.assertIn(OFFER_CONFIG.as_posix(), files)

    def test_unresolved_cta_placeholder_is_rejected(self) -> None:
        candidate = self.copy_offer()
        config_path = candidate / OFFER_CONFIG
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["primary_cta"]["status"] = "BLOCKED_OWNER_INPUT"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        with self.assertRaisesRegex(PublicOfferError, "primary CTA"):
            validate_public_offer(candidate)

    def test_second_link_and_price_literal_are_rejected(self) -> None:
        candidate = self.copy_offer()
        document_path = candidate / OFFER_DOCUMENT
        original = document_path.read_text(encoding="utf-8")
        document_path.write_text(
            original + "\n[Another action](RED_TEAM_MCP_APP_GOVERNANCE_AUDIT_INTAKE.md)\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(PublicOfferError, "exactly one"):
            validate_public_offer(candidate)

        document_path.write_text(
            original + "\nEUR 42\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(PublicOfferError, "price literal"):
            validate_public_offer(candidate)


if __name__ == "__main__":
    unittest.main()
