#!/usr/bin/env python3
"""Fail-closed checks for the KYRON public repository and release payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
REQUIRED_REPOSITORY_FILES = {
    ".github/CODEOWNERS",
    ".github/workflows/verify-release.yml",
    "CHANGELOG.md",
    "README.md",
    "RIGHTS.md",
    "SECURITY.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/TRUST_MODEL.md",
    "schemas/release_manifest.schema.json",
    "scripts/verify_release.py",
}
FORBIDDEN_PATH_PARTS = {
    "approvals",
    "artifacts",
    "config",
    "continuous",
    "knowledge",
    "kyron_core",
    "memory",
    "ops_core",
    "private",
    "proposals",
    "registry",
    "runtime",
    "secrets",
    "source_snapshot",
}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".env",
    ".key",
    ".map",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}
ALLOWED_PAYLOAD_SUFFIXES = {
    ".css",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".md",
    ".mp4",
    ".pdf",
    ".png",
    ".svg",
    ".txt",
    ".webp",
    ".woff2",
}
IMPLEMENTATION_SUFFIXES = {".ps1", ".py", ".sh", ".zsh"}


class PublicReleaseError(ValueError):
    """Raised when public repository or release validation fails."""


def _content_patterns() -> tuple[re.Pattern[bytes], ...]:
    # Sensitive literal fragments are assembled so this validator can scan its
    # own source without allowlisting itself.
    literals = (
        b"OPENAI" + b"_API_KEY",
        b"ANTHROPIC" + b"_API_KEY",
        b"GITHUB" + b"_TOKEN",
        b"/" + b"Volumes/",
        b"/" + b"Users/",
        b"smb" + b"://",
        b"quick" + b"connect",
        b"GMC" + b"4EVER",
        b"Raschel" + b"wald",
        b"KYRON_RUNTIME" + b"_V02",
    )
    regexes = [
        rb"sk-[A-Za-z0-9_-]{20,}",
        rb"ghp_[A-Za-z0-9]{20,}",
        rb"github_pat_[A-Za-z0-9_]{20,}",
        rb"AKIA[0-9A-Z]{16}",
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        rb"\b(?:" + b"local" + rb"host|127\.0\.0\.1)\b",
    ]
    return tuple(re.compile(re.escape(value), re.IGNORECASE) for value in literals) + tuple(
        re.compile(value, re.IGNORECASE) for value in regexes
    )


CONTENT_PATTERNS = _content_patterns()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicReleaseError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicReleaseError(f"cannot load JSON {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def _exact_keys(value: Any, expected: set[str], label: str) -> None:
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == expected, f"{label} fields do not match the contract")


def _parse_utc(value: Any, label: str) -> None:
    _require(isinstance(value, str) and value.endswith("Z"), f"{label} must end in Z")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise PublicReleaseError(f"invalid timestamp: {label}") from exc


def _safe_relative(value: Any) -> PurePosixPath:
    _require(isinstance(value, str) and value, "file path must be non-empty")
    _require("\\" not in value and not value.startswith("/"), f"unsafe path: {value}")
    path = PurePosixPath(value)
    _require(path.as_posix() == value, f"path is not normalized: {value}")
    _require(all(part not in {"", ".", "..", ".git"} for part in path.parts), f"unsafe path: {value}")
    return path


def _scan_content(path: str, content: bytes) -> None:
    for pattern in CONTENT_PATTERNS:
        _require(pattern.search(content) is None, f"sensitive content pattern in {path}")


def _walk_files(root: Path) -> dict[str, Path]:
    _require(root.is_dir(), f"directory does not exist: {root}")
    _require(not root.is_symlink(), f"directory must not be a symlink: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        _require(not path.is_symlink(), f"symlink is forbidden: {relative.as_posix()}")
        if path.is_file():
            result[relative.as_posix()] = path
    return result


def _tracked_files(root: Path) -> dict[str, Path]:
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        _require(result.returncode == 0, "git ls-files failed")
        paths = [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]
        tracked: dict[str, Path] = {}
        for relative in paths:
            safe = _safe_relative(relative).as_posix()
            path = root / safe
            _require(path.exists(), f"tracked file is missing: {safe}")
            _require(not path.is_symlink(), f"tracked symlink is forbidden: {safe}")
            _require(path.is_file(), f"tracked entry is not a regular file: {safe}")
            tracked[safe] = path
        return tracked
    return _walk_files(root)


def verify_manifest(manifest_path: Path, artifact_dir: Path) -> list[str]:
    data = load_json(manifest_path)
    _exact_keys(
        data,
        {
            "schema_version",
            "release_id",
            "created_at",
            "state",
            "source_evidence_sha256",
            "target_repository",
            "files",
            "checks",
            "approval",
        },
        "manifest",
    )
    _require(data["schema_version"] == "kyron.public-release-manifest.v1", "manifest version mismatch")
    _require(re.fullmatch(r"KYRON-PUBLIC-[A-Z0-9-]+", str(data["release_id"])) is not None, "invalid release_id")
    _parse_utc(data["created_at"], "created_at")
    _require(data["state"] == "PUBLIC_APPROVED", "official release must be PUBLIC_APPROVED")
    _require(
        isinstance(data["source_evidence_sha256"], str)
        and SHA256_RE.fullmatch(data["source_evidence_sha256"]) is not None,
        "invalid source evidence digest",
    )
    _require(data["target_repository"] == "fissafissaintoki/Kyron-runtime-public", "wrong target repository")

    checks = data["checks"]
    check_names = {
        "secret_scan_green",
        "disclosure_review_green",
        "personal_data_review_green",
        "third_party_rights_green",
        "hash_verification_green",
    }
    _exact_keys(checks, check_names, "checks")
    _require(all(value is True for value in checks.values()), "all release checks must be green")

    approval = data["approval"]
    _exact_keys(approval, {"human_owner", "owner_approved", "publish_authorized", "approved_at"}, "approval")
    _require(approval["human_owner"] == "Operator Fischer", "wrong release owner")
    _require(approval["owner_approved"] is True, "owner approval is required")
    _require(approval["publish_authorized"] is True, "publication authorization is required")
    _parse_utc(approval["approved_at"], "approved_at")

    entries = data["files"]
    _require(isinstance(entries, list) and entries, "release files must be non-empty")
    required_entry_keys = {
        "path",
        "sha256",
        "media_type",
        "disclosure_class",
        "origin",
        "rights_status",
        "personal_data_reviewed",
        "metadata_removed",
    }
    indexed: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        _exact_keys(entry, required_entry_keys, f"files[{index}]")
        relative = _safe_relative(entry["path"]).as_posix()
        _require(relative not in indexed, f"duplicate payload path: {relative}")
        indexed[relative] = entry

    actual = _walk_files(artifact_dir)
    _require(set(actual) == set(indexed), "every payload file must be manifested exactly once")
    origin_rights = {
        "OWNER_CREATED": "OWNED",
        "LICENSED_THIRD_PARTY": "LICENSED_FOR_PUBLICATION",
        "PUBLIC_DOMAIN": "PUBLIC_DOMAIN",
    }
    evidence: list[str] = []
    for relative, entry in sorted(indexed.items()):
        suffix = PurePosixPath(relative).suffix.lower()
        _require(suffix in ALLOWED_PAYLOAD_SUFFIXES, f"unapproved payload type: {relative}")
        _require(entry["disclosure_class"] in {"PUBLIC", "PUBLIC_REVIEW_REQUIRED"}, f"bad disclosure class: {relative}")
        _require(entry["origin"] in origin_rights, f"bad origin: {relative}")
        _require(entry["rights_status"] == origin_rights[entry["origin"]], f"rights mismatch: {relative}")
        _require(entry["personal_data_reviewed"] is True, f"PII review missing: {relative}")
        _require(entry["metadata_removed"] is True, f"metadata review missing: {relative}")
        _require(isinstance(entry["media_type"], str) and entry["media_type"], f"media type missing: {relative}")
        _require(isinstance(entry["sha256"], str) and SHA256_RE.fullmatch(entry["sha256"]), f"bad digest: {relative}")
        content = actual[relative].read_bytes()
        _scan_content(relative, content)
        digest = hashlib.sha256(content).hexdigest()
        _require(digest == entry["sha256"], f"SHA-256 mismatch: {relative}")
        evidence.append(f"{relative}:{digest}")
    return evidence


def verify_repository(root: Path) -> list[str]:
    files = _tracked_files(root)
    missing = REQUIRED_REPOSITORY_FILES - set(files)
    _require(not missing, f"required public repository files missing: {sorted(missing)}")

    for relative, path in sorted(files.items()):
        parts = {part.lower() for part in PurePosixPath(relative).parts}
        _require(not (parts & FORBIDDEN_PATH_PARTS), f"private-system path rejected: {relative}")
        suffix = PurePosixPath(relative).suffix.lower()
        _require(suffix not in FORBIDDEN_SUFFIXES, f"sensitive file type rejected: {relative}")
        if suffix in IMPLEMENTATION_SUFFIXES:
            _require(
                PurePosixPath(relative).parts[0] in {"scripts", "tests"},
                f"implementation source outside verifier/test boundary: {relative}",
            )
        _scan_content(relative, path.read_bytes())

    workflow = files[".github/workflows/verify-release.yml"].read_text(encoding="utf-8")
    _require("permissions:\n  contents: read\n" in workflow, "workflow must have contents: read only")
    for forbidden in (
        "pages: write",
        "id-token: write",
        "secrets: inherit",
        "runs-on: self-hosted",
        "actions/deploy-pages@",
    ):
        _require(forbidden not in workflow, f"forbidden workflow capability: {forbidden}")

    releases = root / "releases"
    if releases.is_dir():
        for manifest in releases.glob("*/release-manifest.json"):
            verify_manifest(manifest, manifest.parent / "payload")
    return sorted(files)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-safety", action="store_true")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.repository_safety and args.manifest is None:
        raise SystemExit("VERIFY RED: choose --repository-safety or --manifest")
    try:
        if args.repository_safety:
            files = verify_repository(args.repository_root)
            print(f"PUBLIC REPOSITORY GREEN — {len(files)} tracked files")
        if args.manifest is not None:
            if args.artifact_dir is None:
                raise PublicReleaseError("--artifact-dir is required with --manifest")
            evidence = verify_manifest(args.manifest, args.artifact_dir)
            print(f"PUBLIC RELEASE GREEN — {len(evidence)} files")
    except PublicReleaseError as exc:
        raise SystemExit(f"VERIFY RED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
