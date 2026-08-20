#!/usr/bin/env python3
"""Validate the public Red Team Auditor offer without enabling a live offer.

``--content`` verifies that the owner-gated draft is safe to review in this
repository. ``--release-eligible`` is intentionally stricter: it refuses any
attempt to treat the offer as public-release eligible while an owner gate is
unresolved. It never contacts a support, payment, or publishing service.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OFFER_DOCUMENT = Path("docs/RED_TEAM_MCP_APP_GOVERNANCE_AUDIT.md")
OFFER_CONFIG = Path("docs/RED_TEAM_MCP_APP_GOVERNANCE_AUDIT_PUBLIC_OFFER.v1.json")
REQUIRED_SECTIONS = (
    "Hero",
    "Scope",
    "Deliverables",
    "Trust and data boundary",
    "Synthetic Golden Case",
    "Primary next step",
)
OWNER_GATES = ("privacy", "support", "payment")
CTA_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
PRICE_LITERAL_RE = re.compile(
    r"(?:[€$£]\s*\d|\b(?:EUR|USD|GBP|CHF)\s*\d|\b\d+(?:[.,]\d+)?\s*(?:EUR|USD|GBP|CHF)\b)",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"\[?(?:owner[ _-]?input|tbd|todo|placeholder)\]?", re.IGNORECASE)


class PublicOfferError(ValueError):
    """Raised when public-offer content or release eligibility is unsafe."""


@dataclass(frozen=True)
class PublicOfferReceipt:
    schema_version: str
    product_id: str
    public_offer_status: str
    primary_cta_ready: bool
    unresolved_owner_gates: tuple[str, ...]
    release_eligible: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicOfferError(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicOfferError(f"cannot load public offer metadata: {path}") from exc
    _require(isinstance(value, dict), "public offer metadata must be an object")
    return value


def _require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == expected, f"{label} fields do not match the contract")
    return value


def _safe_repo_path(root: Path, value: Any, label: str) -> Path:
    _require(isinstance(value, str) and value and not value.startswith("/"), f"{label} must be repository relative")
    path = Path(value)
    _require(path.as_posix() == value and not {".", ".."}.intersection(path.parts), f"{label} must be normalized")
    candidate = (root / value).resolve()
    root_resolved = root.resolve()
    _require(root_resolved in candidate.parents and candidate.is_file(), f"{label} does not resolve to a public file")
    return candidate


def _validate_owner_gate(name: str, value: Any) -> bool:
    expected = {"status", "required_owner_inputs", "values"}
    if name == "payment":
        expected.add("payments_enabled")
    gate = _require_exact_keys(value, expected, f"{name} owner gate")
    status = gate["status"]
    _require(status in {"BLOCKED_OWNER_INPUT", "READY"}, f"{name} owner gate has unsupported status")
    required = gate["required_owner_inputs"]
    values = gate["values"]
    _require(isinstance(required, list) and required and all(isinstance(item, str) and item for item in required), f"{name} required owner inputs are invalid")
    _require(isinstance(values, dict) and set(values) == set(required), f"{name} values must match required owner inputs")
    complete = all(
        isinstance(values[field], str)
        and values[field].strip()
        and PLACEHOLDER_RE.search(values[field].strip()) is None
        for field in required
    )
    if name == "payment":
        _require(isinstance(gate["payments_enabled"], bool), "payment enablement must be boolean")
        if status == "BLOCKED_OWNER_INPUT":
            _require(gate["payments_enabled"] is False, "payment must remain disabled while owner input is blocked")
    if status == "READY":
        _require(complete, f"{name} owner gate is marked READY with unresolved values")
    else:
        _require(not complete, f"{name} owner gate is blocked but has no unresolved owner input")
    return status == "READY" and complete


def validate_public_offer(root: Path = ROOT) -> PublicOfferReceipt:
    """Validate safe draft content and return its non-live release state."""

    root = root.resolve()
    metadata = _load_json(root / OFFER_CONFIG)
    _require_exact_keys(
        metadata,
        {
            "schema_version",
            "product_id",
            "display_name",
            "commercial_status",
            "public_offer_status",
            "primary_cta",
            "owner_gates",
        },
        "public offer metadata",
    )
    _require(metadata["schema_version"] == "kyron.public-red-team-offer.v1", "public offer metadata version mismatch")
    _require(metadata["product_id"] == "KYRON_MCP_APP_GOVERNANCE_AUDIT", "unexpected product identifier")
    _require(metadata["display_name"] == "KYRON MCP/App Governance Audit", "unexpected public display name")
    _require(metadata["commercial_status"] == "COMMERCIAL_HYPOTHESIS", "commercial status must remain a hypothesis")
    _require(metadata["public_offer_status"] in {"OWNER_GATED_DRAFT", "READY_FOR_OWNER_REVIEW"}, "unexpected public offer status")

    cta = _require_exact_keys(
        metadata["primary_cta"],
        {"status", "label", "href", "destination_type"},
        "primary CTA",
    )
    _require(cta["status"] == "AVAILABLE", "primary CTA must be available; unresolved CTA placeholders are not publishable")
    _require(
        isinstance(cta["label"], str)
        and cta["label"].strip()
        and PLACEHOLDER_RE.search(cta["label"].strip()) is None,
        "primary CTA label is unresolved",
    )
    _require(cta["destination_type"] == "PUBLIC_DOCUMENT", "primary CTA must lead to a public document")
    cta_target = _safe_repo_path(root, cta["href"], "primary CTA href")

    gates = _require_exact_keys(metadata["owner_gates"], set(OWNER_GATES), "owner gates")
    unresolved = tuple(name for name in OWNER_GATES if not _validate_owner_gate(name, gates[name]))

    document = (root / OFFER_DOCUMENT).read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        _require(f"## {section}\n" in document, f"public offer is missing required section: {section}")
    _require(PRICE_LITERAL_RE.search(document) is None, "public offer must not contain a price literal")
    links = CTA_LINK_RE.findall(document)
    _require(len(links) == 1, "public offer must contain exactly one primary CTA link")
    label, href = links[0]
    _require(label == cta["label"], "public offer CTA label does not match metadata")
    document_target = _safe_repo_path((root / OFFER_DOCUMENT).parent, href, "public offer CTA href")
    _require(document_target == cta_target, "public offer CTA target does not match metadata")

    return PublicOfferReceipt(
        schema_version="kyron.public-red-team-offer-receipt.v1",
        product_id=metadata["product_id"],
        public_offer_status=metadata["public_offer_status"],
        primary_cta_ready=True,
        unresolved_owner_gates=unresolved,
        release_eligible=not unresolved,
    )


def require_release_eligibility(root: Path = ROOT) -> PublicOfferReceipt:
    """Return only a fully owner-ready offer; otherwise stop before release."""

    receipt = validate_public_offer(root)
    _require(
        receipt.release_eligible,
        "public offer release is blocked by unresolved owner gates: " + ", ".join(receipt.unresolved_owner_gates),
    )
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--content", action="store_true", help="validate the safe owner-gated draft")
    mode.add_argument("--release-eligible", action="store_true", help="require all owner gates before a release")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = require_release_eligibility(args.repository_root) if args.release_eligible else validate_public_offer(args.repository_root)
    except PublicOfferError as exc:
        print(f"PUBLIC OFFER RED: {exc}")
        return 2
    print(json.dumps(receipt.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
