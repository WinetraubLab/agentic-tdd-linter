"""Validate filename-based YAML case names."""

from __future__ import annotations

import re
from pathlib import Path


def yaml_case_name_errors(path: Path, text: str) -> list[str]:
    """Return errors for top-level cases outside the filename-number sequence."""

    errors: list[str] = []
    case_number = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        if (
            not line
            or line.startswith(" ")
            or line.startswith("#")
            or not line.endswith(":")
        ):
            continue
        case_number += 1
        actual_name = line[:-1]
        expected_prefix = f"{path.stem}_{case_number:03d}"
        optional_note = r"(?:_[a-z0-9]+_[a-z0-9]+_[a-z0-9]+)?"
        if not re.fullmatch(re.escape(expected_prefix) + optional_note, actual_name):
            errors.append(
                f"{path}:{line_number}: YAML case {case_number} must be named "
                f"`{expected_prefix}` or `{expected_prefix}_<three_word_note>`, "
                f"found `{actual_name}`"
            )
    return errors
