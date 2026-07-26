"""Verify that agentic review artifacts match the current test file."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ..conventional_linter.run_conventional_linter import LintIssue
from .map_test_function_to_agent_md_file import map_test_function_to_agent_md_file


COMPLETED_REVIEW_STATUSES = {"pass", "fail"}
SCENARIO_NOTE_PREFIX = "Scenario or example:"
SCORECARD_ROW_PATTERN = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE,
)


def _source_sha256(path: Path) -> str:
    """Return the SHA256 digest for a file."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _agent_md_file_is_stale(test_file_path: Path, artifact_path: Path) -> bool:
    """Return whether an artifact was generated for an old test file."""

    try:
        artifact_text = Path(artifact_path).read_text(encoding="utf-8")
    except OSError:
        return False
    review_hash = _backtick_value(artifact_text, "Source SHA256")
    return not review_hash or review_hash != _source_sha256(test_file_path)


def determine_agent_md_status(artifact_text: str) -> str:
    """Return the overall status derived from one review scorecard."""

    rows = _scorecard_rows(artifact_text)
    if not rows:
        return _plain_value(artifact_text, "Status").lower()
    results = [row[2].lower() for row in rows]
    if any(result not in COMPLETED_REVIEW_STATUSES for result in results):
        return "pending"
    if any(result == "fail" for result in results):
        return "fail"
    return "pass"


def _lint_agent_md_file(
    test_file_path: Path,
    artifact_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    test_name: str | None = None,
) -> list[LintIssue]:
    """Return issues when one test's review artifact is missing or stale."""

    if repo_root is None:
        raise ValueError("repo_root is required")

    test_file = Path(test_file_path).resolve()
    artifact = (
        Path(artifact_path)
        if artifact_path is not None
        else map_test_function_to_agent_md_file(test_file, repo_root, artifact_root, test_name)
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
    expected_hash = _source_sha256(test_file)
    review_hash = _backtick_value(artifact_text, "Source SHA256")
    scorecard_rows = _scorecard_rows(artifact_text)
    status = determine_agent_md_status(artifact_text)

    if not review_hash or review_hash != expected_hash:
        issues.append(
            _issue(
                relative_artifact,
                "stale_agent_review_artifact",
                "agent review artifact must include the current source SHA256 value",
            )
        )

    scorecard_issue = _scorecard_issue_message(artifact_text, scorecard_rows)
    if scorecard_issue:
        issues.append(
            _issue(
                relative_artifact,
                "invalid_review_scorecard",
                scorecard_issue,
            )
        )

    if status not in COMPLETED_REVIEW_STATUSES:
        issues.append(
            _issue(
                relative_artifact,
                "agent_review_not_run",
                (
                    "every scorecard row must contain exactly one pass or fail result; "
                    "complete the scorecard, then rerun "
                    "`agentic-tdd-linter lint`"
                ),
            )
        )
    elif not scorecard_rows:
        missing_scenario_note = _missing_scenario_note_message(artifact_text)
        if missing_scenario_note:
            issues.append(
                _issue(
                    relative_artifact,
                    "missing_review_scenario",
                    (
                        "agent review notes must include "
                        "one `Scenario or example: ...` line for the reviewed test; "
                        f"{missing_scenario_note}"
                    ),
                )
            )

    if status == "fail":
        notes = _failed_scorecard_notes(scorecard_rows) or _notes_value(artifact_text)
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
    matches = re.findall(
        rf"^{re.escape(field_name)}:\s*`([^`]+)`\s*$",
        text,
        re.MULTILINE,
    )
    if not matches:
        return ""
    return matches[-1].strip()


def _plain_value(text: str, field_name: str) -> str:
    match = re.search(rf"^{re.escape(field_name)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if match is None:
        return ""
    return match.group(1).strip()


def _scorecard_rows(text: str) -> list[tuple[int, str, str, str]]:
    scorecard = _markdown_section(text, "Review Scorecard")
    return [
        (
            int(match.group(1)),
            match.group(2).strip(),
            match.group(3).strip(),
            match.group(4).strip(),
        )
        for match in SCORECARD_ROW_PATTERN.finditer(scorecard)
    ]


def _scorecard_issue_message(
    text: str,
    rows: list[tuple[int, str, str, str]],
) -> str:
    if not rows:
        return ""
    criteria_text = _markdown_section(text, "Review Criteria")
    criteria = [
        (int(number), name.strip())
        for number, name in re.findall(
            r"^(?:####\s+)?(\d+)\.\s+(.+?)\s*$",
            criteria_text,
            re.MULTILINE,
        )
    ]
    row_criteria = [(number, name) for number, name, _, _ in rows]
    if criteria != row_criteria:
        return "scorecard must contain exactly one row for each review criterion"
    invalid_results = [
        name
        for _, name, result, _ in rows
        if result.lower() not in COMPLETED_REVIEW_STATUSES and result.lower() != "pending"
    ]
    if invalid_results:
        return "scorecard results must be exactly pass or fail"
    missing_notes = [
        name
        for _, name, result, notes in rows
        if result.lower() == "fail"
        and (not notes or "replace with review evidence" in notes.lower())
    ]
    if missing_notes:
        return "failed scorecard rows require concrete notes"
    return ""


def _failed_scorecard_notes(rows: list[tuple[int, str, str, str]]) -> str:
    return "; ".join(
        f"{name}: {notes}"
        for _, name, result, notes in rows
        if result.lower() == "fail" and notes
    )


def _markdown_section(text: str, heading: str) -> str:
    matches = list(
        re.finditer(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    )
    if not matches:
        return ""
    match = matches[-1]
    section = text[match.end() :]
    next_heading = re.search(r"^##\s+", section, re.MULTILINE)
    if next_heading is not None:
        section = section[: next_heading.start()]
    return section


def _notes_value(text: str) -> str:
    return " ".join(_notes_lines(text))


def _notes_lines(text: str) -> list[str]:
    lines = text.splitlines()
    notes: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped == "Notes:":
            collecting = True
            continue
        if collecting and stripped.startswith("#"):
            break
        if collecting and stripped:
            notes.append(stripped.removeprefix("-").strip())
    return notes


def _missing_scenario_note_message(text: str) -> str:
    expected_count = 1
    actual_count = len(_scenario_notes(text))
    if actual_count >= expected_count:
        return ""
    return f"expected {expected_count}, found {actual_count}"


def _scenario_notes(text: str) -> list[str]:
    scenarios: list[str] = []
    for note in _notes_lines(text):
        if not note.startswith(SCENARIO_NOTE_PREFIX):
            continue
        value = note.removeprefix(SCENARIO_NOTE_PREFIX).strip()
        if not value or "replace this line" in value.lower():
            continue
        scenarios.append(value)
    return scenarios


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return path.relative_to(Path(repo_root).resolve())
    except ValueError:
        return path
