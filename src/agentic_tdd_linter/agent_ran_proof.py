"""Verify that agentic review artifacts match the current test file."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .docstrings import LintIssue
from .agent_review_artifacts import agent_review_artifact_path


COMPLETED_REVIEW_STATUSES = {"pass", "fail"}


def source_sha256(path: Path) -> str:
    """Return the SHA256 digest for a file."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def agent_review_artifact_is_stale(test_file_path: Path, artifact_path: Path) -> bool:
    """Return whether an artifact was generated for an old test file."""

    try:
        artifact_text = Path(artifact_path).read_text(encoding="utf-8")
    except OSError:
        return False
    review_hash = _backtick_value(artifact_text, "Source SHA256")
    return not review_hash or review_hash != source_sha256(test_file_path)


def lint_agent_review_artifact(
    test_file_path: Path,
    artifact_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> list[LintIssue]:
    """Return issues when an agentic review artifact is missing or stale."""

    if repo_root is None:
        raise ValueError("repo_root is required")

    test_file = Path(test_file_path).resolve()
    artifact = (
        Path(artifact_path)
        if artifact_path is not None
        else agent_review_artifact_path(test_file, repo_root, artifact_root)
    ).resolve()
    relative_artifact = _relative_path(artifact, repo_root)

    try:
        artifact_text = artifact.read_text(encoding="utf-8")
    except OSError as error:
        return [
            _issue(
                relative_artifact,
                "missing_agent_review_artifact",
                f"could not read agent review artifact: {error}",
            )
        ]

    issues: list[LintIssue] = []
    expected_hash = source_sha256(test_file)
    review_hash = _backtick_value(artifact_text, "Source SHA256")
    status = _plain_value(artifact_text, "Status").lower()

    if not review_hash or review_hash != expected_hash:
        issues.append(
            _issue(
                relative_artifact,
                "stale_agent_review_artifact",
                "agent review artifact must include the current test file SHA256",
            )
        )

    if status not in COMPLETED_REVIEW_STATUSES:
        issues.append(
            _issue(
                relative_artifact,
                "agent_review_not_run",
                (
                    "agent review artifact must have Status: pass or Status: fail; "
                    "review the artifact, update the status, then rerun "
                    "`agentic-tdd-linter check --all`"
                ),
            )
        )
    elif status == "fail":
        notes = _notes_value(artifact_text)
        message = "agent review artifact reported at least one review issue"
        if notes:
            message = f"{message}: {notes}"
        issues.append(
            _issue(
                relative_artifact,
                "agent_review_failed",
                message,
            )
        )

    return issues


def _issue(path: Path, rule: str, message: str) -> LintIssue:
    return LintIssue(
        path=path,
        test_name="<agent-review>",
        line=1,
        rule=rule,
        message=message,
    )


def _backtick_value(text: str, field_name: str) -> str:
    match = re.search(rf"^{re.escape(field_name)}:\s*`([^`]+)`\s*$", text, re.MULTILINE)
    if match is None:
        return ""
    return match.group(1).strip()


def _plain_value(text: str, field_name: str) -> str:
    match = re.search(rf"^{re.escape(field_name)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if match is None:
        return ""
    return match.group(1).strip()


def _notes_value(text: str) -> str:
    lines = text.splitlines()
    notes: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped == "Notes:":
            collecting = True
            continue
        if collecting and stripped.startswith("## "):
            break
        if collecting and stripped:
            notes.append(stripped.removeprefix("-").strip())
    return " ".join(notes)


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.relative_to(Path(repo_root).resolve())
    except ValueError:
        return path
