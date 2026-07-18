"""Build a compact review manifest from completed ``.agent.md`` files."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .map_test_function_to_agent_md_file import map_test_function_to_agent_md_file
from .determine_agent_md_status import (
    _lint_agent_md_file,
    _source_sha256,
    determine_agent_md_status,
)
from ..conventional_linter.run_conventional_linter import LintIssue
from ..indexing_test_functions.extract_tests_from_file import extract_tests_from_file
from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord
from ..version import __version__


DEFAULT_AGENT_REVIEW_MANIFEST = Path("tests") / "agentic_review_manifest.jsonl"
CONTRACT_DOCUMENT_PATHS = ("README.md", "pyproject.toml")
REQUIRED_FIELDS = (
    "path",
    "test",
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


def _agent_review_manifest_path(repo_root: Path, manifest_path: Path | None = None) -> Path:
    """Return the default persisted review manifest path."""

    root = Path(repo_root).resolve()
    path = manifest_path if manifest_path is not None else DEFAULT_AGENT_REVIEW_MANIFEST
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    return path


def _review_contract_sha256(repo_root: Path | None = None) -> str:
    """Return a digest for the linter behavior and documentation contract."""

    digest = hashlib.sha256()
    for label, path in _review_contract_files(repo_root):
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_manifest_from_agent_md_files(
    files: Iterable[Path],
    repo_root: Path,
    reviewer: str,
    manifest_path: Path | None = None,
    artifact_root: Path | None = None,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]] | None = None,
    preserve_unselected_tests: bool = False,
) -> tuple[Path, int, list[LintIssue]]:
    """Build compact pass records from reviewed ``.agent.md`` files."""

    root = Path(repo_root).resolve()
    manifest = _agent_review_manifest_path(root, manifest_path)
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

    contract_hash = _review_contract_sha256(root)
    selected_files = sorted({Path(file).resolve() for file in files})
    selected_paths = {
        _relative_path(test_file, root).as_posix() for test_file in selected_files
    }
    selected_keys = {
        (_relative_path(test_file, root).as_posix(), test.name)
        for test_file in selected_files
        for test in _tests_for_file(test_file, root, tests_by_file)
    }
    records: list[dict[str, str]] = []
    issues: list[LintIssue] = []

    for test_file in selected_files:
        for test in _tests_for_file(test_file, root, tests_by_file):
            artifact_issues = _lint_agent_md_file(
                test_file,
                repo_root=root,
                artifact_root=artifact_root,
                test_name=test.name,
            )
            if artifact_issues:
                issues.extend(artifact_issues)
                continue

            artifact_text = map_test_function_to_agent_md_file(
                test_file,
                root,
                artifact_root,
                test.name,
            ).read_text(encoding="utf-8")
            status = determine_agent_md_status(artifact_text)
            records.append(
                {
                    "path": _relative_path(test_file, root).as_posix(),
                    "test": test.name,
                    "source_sha256": _source_sha256(test_file),
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

    records_by_test: dict[tuple[str, str], dict[str, str]] = {}
    for record in existing_records:
        path = record.values.get("path", "")
        test_name = record.values.get("test", "")
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
        if path in selected_paths and not preserve_unselected_tests:
            continue
        if preserve_unselected_tests and (path, test_name) in selected_keys:
            continue
        if not test_name:
            continue
        records_by_test[(path, test_name)] = record.values
    for record in records:
        records_by_test[(record["path"], record["test"])] = record

    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(
            json.dumps(_ordered_record(records_by_test[key]), separators=(", ", ": ")) + "\n"
            for key in sorted(records_by_test)
        ),
        encoding="utf-8",
    )
    return manifest, len(records), []


def _find_tests_requiring_agent_review(
    files: Iterable[Path],
    repo_root: Path,
    manifest_path: Path | None = None,
    *,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]] | None = None,
    force_all: bool = False,
) -> dict[Path, list[ExtractedTestRecord]]:
    """Return selected tests without current passing manifest proof."""

    root = Path(repo_root).resolve()
    selected_files = sorted({Path(file).resolve() for file in files})
    selected_tests = {
        test_file: list(_tests_for_file(test_file, root, tests_by_file))
        for test_file in selected_files
    }
    _lint_agent_review_manifest(
        selected_files,
        root,
        manifest_path,
        tests_by_file=tests_by_file,
    )
    if force_all:
        return selected_tests

    manifest = _agent_review_manifest_path(root, manifest_path)
    records, parse_issues = _read_manifest_records(manifest, root, missing_is_issue=False)
    if parse_issues:
        return selected_tests

    contract_hash = _review_contract_sha256(root)
    approved_keys: set[tuple[str, str]] = set()
    for record in records:
        values = record.values
        path = values.get("path", "")
        test_name = values.get("test", "")
        test_file = (root / path).resolve()
        if (
            set(values) == set(REQUIRED_FIELDS)
            and values.get("status") == "pass"
            and values.get("review_contract_sha256") == contract_hash
            and values.get("linter_version") == __version__
            and test_file.is_file()
            and values.get("source_sha256") == _source_sha256(test_file)
        ):
            approved_keys.add((path, test_name))

    return {
        test_file: [
            test
            for test in tests
            if (_relative_path(test_file, root).as_posix(), test.name) not in approved_keys
        ]
        for test_file, tests in selected_tests.items()
    }


def _lint_agent_review_manifest(
    files: Iterable[Path],
    repo_root: Path,
    manifest_path: Path | None = None,
    *,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]] | None = None,
) -> list[LintIssue]:
    """Return manifest issues and remove attestations for stale test sources."""
    root = Path(repo_root).resolve()
    manifest = _agent_review_manifest_path(root, manifest_path)
    records, issues = _read_manifest_records(manifest, root, missing_is_issue=True)
    if issues:
        return issues

    records_by_test: dict[tuple[str, str], ManifestRecord] = {}
    stale_record_lines: set[int] = set()
    current_contract_hash = _review_contract_sha256(root)
    for record in records:
        path = record.values.get("path", "")
        test_name = record.values.get("test", "")
        identity = f"{path}::{test_name}" if test_name else path
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
                    f"review attestation for {identity or '<missing test>'} must have status pass",
                )
            )
        linter_version = record.values.get("linter_version", "")
        if linter_version and linter_version != __version__:
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "stale_linter_review_attestation",
                    (
                        f"review attestation for {identity or '<missing test>'} was "
                        f"recorded by linter version {linter_version}; expected exactly {__version__}"
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
                        f"review attestation for {identity or '<missing test>'} was "
                        "recorded with an old review contract SHA256"
                    ),
                )
            )
        if path and not (root / path).exists():
            stale_record_lines.add(record.line)
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "orphaned_agent_review_attestation",
                    f"review attestation points to missing file {path}",
                )
            )
        key = (path, test_name)
        if key in records_by_test:
            issues.append(
                _manifest_issue(
                    manifest,
                    root,
                    record.line,
                    "duplicate_agent_review_attestation",
                    f"duplicate review attestation for {identity}",
                )
            )
            continue
        records_by_test[key] = record

    selected_paths: set[str] = set()
    expected_keys: set[tuple[str, str]] = set()
    for test_file in sorted({Path(file).resolve() for file in files}):
        relative_path = _relative_path(test_file, root).as_posix()
        selected_paths.add(relative_path)
        for test in _tests_for_file(test_file, root, tests_by_file):
            identity = f"{relative_path}::{test.name}"
            key = (relative_path, test.name)
            expected_keys.add(key)
            record = records_by_test.get(key)
            if record is None:
                issues.append(
                    _manifest_issue(
                        manifest,
                        root,
                        1,
                        "missing_agent_review_attestation",
                        f"missing review attestation for {identity}",
                    )
                )
                continue

            values = record.values
            expected_hash = _source_sha256(test_file)
            if values.get("source_sha256") != expected_hash:
                stale_record_lines.add(record.line)
                issues.append(
                    _manifest_issue(
                        manifest,
                        root,
                        record.line,
                        "stale_agent_review_attestation",
                        f"review attestation for {identity} must match the current test file SHA256",
                    )
                )

    for key, record in records_by_test.items():
        if key[0] not in selected_paths or key in expected_keys:
            continue
        stale_record_lines.add(record.line)
        issues.append(
            _manifest_issue(
                manifest,
                root,
                record.line,
                "orphaned_agent_review_attestation",
                f"review attestation points to missing test {key[0]}::{key[1]}",
            )
        )

    if stale_record_lines:
        _remove_manifest_record_lines(manifest, stale_record_lines)

    return issues


def _remove_manifest_record_lines(manifest: Path, lines: set[int]) -> None:
    manifest_lines = manifest.read_text(encoding="utf-8").splitlines(keepends=True)
    manifest.write_text(
        "".join(
            line
            for line_number, line in enumerate(manifest_lines, start=1)
            if line_number not in lines
        ),
        encoding="utf-8",
    )


def _tests_for_file(
    test_file: Path,
    repo_root: Path,
    tests_by_file: Mapping[Path, Sequence[ExtractedTestRecord]] | None,
) -> Sequence[ExtractedTestRecord]:
    if tests_by_file is not None:
        return tests_by_file[test_file.resolve()]
    return extract_tests_from_file(test_file, repo_root)


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
    package_root = Path(__file__).resolve().parents[1]
    contract_paths = (
        path
        for path in package_root.rglob("*")
        if path.suffix in {".py", ".j2"}
    )
    for path in sorted(contract_paths):
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
