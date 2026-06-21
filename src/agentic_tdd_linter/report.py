"""Report formatting for linter findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .docstrings import LintIssue


def format_text(issues: Sequence[LintIssue], files: Sequence[Path]) -> str:
    """Return human-readable output for linter results."""

    if not files:
        return "agentic-tdd-linter: no test files to lint"

    if not issues:
        noun = "file" if len(files) == 1 else "files"
        return f"agentic-tdd-linter: no issues found in {len(files)} {noun}"

    lines: list[str] = []
    for issue in issues:
        lines.append(f"{issue.severity} {issue.path}:{issue.line} {issue.test_name}")
        lines.append(f"Rule: {issue.rule}")
        lines.append(issue.message)
        lines.append("")
    return "\n".join(lines).rstrip()


def format_json(issues: Sequence[LintIssue], files: Sequence[Path]) -> str:
    """Return JSON output for linter results."""

    payload = {
        "status": "FAIL" if issues else "PASS",
        "files_checked": len(files),
        "issues": [
            {
                "severity": issue.severity,
                "path": str(issue.path),
                "line": issue.line,
                "test": issue.test_name,
                "rule": issue.rule,
                "message": issue.message,
            }
            for issue in issues
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
