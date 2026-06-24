"""Compact proof records for completed agent reviews."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .agent_review_artifacts import agent_review_artifact_path
from .agent_ran_proof import lint_agent_review_artifact, source_sha256
from .docstrings import LintIssue
from .version import __version__


DEFAULT_AGENT_REVIEW_MANIFEST = Path("tests") / "agentic_review_manifest.jsonl"
CONTRACT_DOCUMENT_PATHS = ("README.md", "pyproject.toml")
REQUIRED_FIELDS = (
    "path",
    "source_sha256",
    "status",
    "linter_version",
    "review_contract_sha256",
    "reviewer",
)


@dataclass(frozen=True)
class ManifestRecord:
    """A parsed review attestation record."""

    line: int
    values: dict[str, str]


def agent_review_manifest_path(repo_root: Path, manifest_path: Path | None = None) -> Path:
    """Return the default persisted review manifest path."""

    root = Path(repo_root).resolve()
    path = manifest_path if manifest_path is not None else DEFAULT_AGENT_REVIEW_MANIFEST
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    return path


def review_contract_sha256(repo_root: Path | None = None) -> str:
    """Return a digest for the linter behavior and documentation contract."""

    digest = hashlib.sha256()
    for label, path in _review_contract_files(repo_root):
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def record_agent_review_attestations(
    files: Iterable[Path],
    repo_root: Path,
    reviewer: str,
    manifest_path: Path | None = None,
    artifact_root: Path | None = None,
) -> tuple[Path, int, list[LintIssue]]:
    """Write compact pass records for reviewed local artifacts."""

    root = Path(repo_root).resolve()
    manifest = agent_review_manifest_path(root, manifest_path)
    reviewer = reviewer.strip()
    if not reviewer:
        return (
            manifest,
            0,
            [
                _manifest_issue(
                    manifest,
                    root,
                    1,
                    "missing_reviewer",
                    "reviewer identity is required",
                )
            ],
        )

    contract_hash = review_contract_sha256(root)
    selected_files = sorted({Path(file).resolve() for file in files})
    records: list[dict[str, str]] = []
    issues: list[LintIssue] = []

    for test_file in selected_files:
        artifact_issues = lint_agent_review_artifact(
            test_file,
            repo_root=root,
            artifact_root=artifact_root,
        )
        if artifact_issues:
            issues.extend(artifact_issues)
            continue

        artifact_text = agent_review_artifact_path(test_file, root, artifact_root).read_text(
            encoding="utf-8"
        )
        status = _plain_value(artifact_text, "Status").lower()
        records.append(
            {
                "path": _relative_path(test_file, root).as_posix(),
                "source_sha256": source_sha256(test_file),
                "status": status,
                "linter_version": __version__,
                "review_contract_sha256": contract_hash,
                "reviewer": reviewer,
            }
        )

    if issues:
        return manifest, 0, issues

    existing_records, parse_issues = _read_manifest_records(manifest, root, missing_is_issue=False)
    if parse_issues:
        return manifest, 0, parse_issues

    records_by_path: dict[str, dict[str, str]] = {}
    for record in existing_records:
        path = record.values.get("path", "")
        if not path:
            return (
                manifest,
                0,
                [
                    _manifest_issue(
                        manifest,
                        root,
                        record.line,
                        "invalid_agent_review_attestation",
                        "review attestation is missing path",
                    )
                ],
            )
        if not (root / path).exists():
            continue
        records_by_path[path] = record.values
    for record in records:
        records_by_path[record["path"]] = record

    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(
            json.dumps(_ordered_record(records_by_path[path]), separators=(", ", ": ")) + "\n"
            for path in sorted(records_by_path)
        ),
        encoding="utf-8",
    )
    return manifest, len(records), []


def lint_agent_review_manifest(
    files: Iterable[Path],
    repo_root: Path,
    manifest_path: Path | None = None,
) -> list[LintIssue]:
    """Return issues when compact review attestations are missing or stale."""

    root = Path(repo_root).resolve()
    manifest = agent_review_manifest_path(root, manifest_path)
    records, issues = _read_manifest_records(manifest, root, missing_is_issue=True)
    if issues:
        return issues

    records_by_path: dict[str, ManifestRecord] = {}
    current_contract_hash = review_contract_sha256(root)
    for record in records:
        path = record.values.get("path", "")
        for field in record.values:
            if field not in REQUIRED_FIELDS:
                issues.append(
                    _manifest_issue(
                        manifest,
                        root,
                        record.line,
                        "invalid_agent_review_attestation",
                        f"review attestation has unsupported field {field}",
                    )
                )
        for field in REQUIRED_FIELDS:
            if not record.values.get(field):
                issues.append(
                    _manifest_issue(
                        manifest,
                        root,
                        record.line,
                        "invalid_agent_review_attestation",
                        f"review attestation is missing {field}",
                    )
                )
        if record.values.get("status") and record.values.get("status") != "pass":
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "agent_review_not_approved",
                    f"review attestation for {path or '<missing path>'} must have status pass",
                )
            )
        linter_version = record.values.get("linter_version", "")
        if linter_version and _version_is_older(linter_version, __version__):
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "stale_linter_review_attestation",
                    (
                        f"review attestation for {path or '<missing path>'} was "
                        f"recorded by linter version {linter_version}; expected at least {__version__}"
                    ),
                )
            )
        contract_hash = record.values.get("review_contract_sha256", "")
        if contract_hash and contract_hash != current_contract_hash:
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "stale_review_contract_attestation",
                    (
                        f"review attestation for {path or '<missing path>'} was "
                        "recorded with an old review contract SHA256"
                    ),
                )
            )
        if path and not (root / path).exists():
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "orphaned_agent_review_attestation",
                    f"review attestation points to missing file {path}",
                )
            )
        if path in records_by_path:
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "duplicate_agent_review_attestation",
                    f"duplicate review attestation for {path}",
                )
            )
            continue
        records_by_path[path] = record

    for test_file in sorted({Path(file).resolve() for file in files}):
        relative_path = _relative_path(test_file, root).as_posix()
        record = records_by_path.get(relative_path)
        if record is None:
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    1,
                    "missing_agent_review_attestation",
                    f"missing review attestation for {relative_path}",
                )
            )
            continue

        values = record.values
        expected_hash = source_sha256(test_file)
        if values.get("source_sha256") != expected_hash:
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "stale_agent_review_attestation",
                    f"review attestation for {relative_path} must match the current test file SHA256",
                )
            )

    return issues


def _read_manifest_records(
    manifest: Path,
    repo_root: Path,
    *,
    missing_is_issue: bool,
) -> tuple[list[ManifestRecord], list[LintIssue]]:
    if not manifest.exists():
        if not missing_is_issue:
            return [], []
        return (
            [],
            [
                _manifest_issue(
                    manifest,
                    repo_root,
                    1,
                    "missing_agent_review_manifest",
                    "agent review manifest is missing",
                )
            ],
        )

    records: list[ManifestRecord] = []
    issues: list[LintIssue] = []
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            issues.append(
                _manifest_issue(
                    manifest,
                    repo_root,
                    line_number,
                    "invalid_agent_review_manifest",
                    f"could not parse JSONL record: {error}",
                )
            )
            continue
        if not isinstance(value, dict):
            issues.append(
                _manifest_issue(
                    manifest,
                    repo_root,
                    line_number,
                    "invalid_agent_review_manifest",
                    "each JSONL record must be an object",
                )
            )
            continue
        records.append(
            ManifestRecord(
                line=line_number,
                values={str(key): str(record_value) for key, record_value in value.items()},
            )
        )
    return records, issues


def _ordered_record(record: dict[str, str]) -> dict[str, str]:
    return {field: record.get(field, "") for field in REQUIRED_FIELDS}


def _review_contract_files(repo_root: Path | None) -> list[tuple[str, Path]]:
    files: dict[str, Path] = {}
    package_root = Path(__file__).resolve().parent
    for path in sorted(package_root.rglob("*.py")):
        files[f"package/{path.relative_to(package_root).as_posix()}"] = path

    if repo_root is not None:
        root = Path(repo_root).resolve()
        for path_value in CONTRACT_DOCUMENT_PATHS:
            path = root / path_value
            if path.is_file():
                files[f"repo/{path.relative_to(root).as_posix()}"] = path
        docs_root = root / "docs"
        if docs_root.is_dir():
            for path in sorted(docs_root.rglob("*.md")):
                files[f"repo/{path.relative_to(root).as_posix()}"] = path

    return sorted(files.items())

def _plain_value(text: str, field_name: str) -> str:
    match = re.search(rf"^{re.escape(field_name)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if match is None:
        return ""
    return match.group(1).strip()


def _version_is_older(recorded_version: str, current_version: str) -> bool:
    recorded_parts = _version_parts(recorded_version)
    current_parts = _version_parts(current_version)
    if recorded_parts is None or current_parts is None:
        return recorded_version != current_version
    max_length = max(len(recorded_parts), len(current_parts))
    recorded_parts = recorded_parts + (0,) * (max_length - len(recorded_parts))
    current_parts = current_parts + (0,) * (max_length - len(current_parts))
    return recorded_parts < current_parts


def _version_parts(value: str) -> tuple[int, ...] | None:
    parts = value.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _manifest_issue(path: Path, repo_root: Path, line: int, rule: str, message: str) -> LintIssue:
    return LintIssue(
        path=_relative_path(path, repo_root),
        test_name="<agent-review>",
        line=line,
        rule=rule,
        message=message,
    )


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return Path(path).resolve().relative_to(Path(repo_root).resolve())
    except ValueError:
        return Path(path)
