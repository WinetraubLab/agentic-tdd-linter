"""Validate filename-based YAML case names."""

from __future__ import annotations

import re
from pathlib import Path


def yaml_case_name_errors(path: Path, text: str) -> list[str]:
    """Return errors for top-level cases outside the filename-number format."""

    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if (
            not line
            or line.startswith(" ")
            or line.startswith("#")
            or not line.endswith(":")
        ):
            continue
        actual_name = line[:-1]
        expected_name = f"{path.stem}_<three_digit_number>"
        case_name = (
            re.escape(path.stem)
            + r"_[0-9]{3}(?:_[a-z0-9]+_[a-z0-9]+_[a-z0-9]+)?"
        )
        if not re.fullmatch(case_name, actual_name):
            errors.append(
                f"{path}:{line_number}: YAML case must be named "
                f"`{expected_name}` or `{expected_name}_<three_word_note>`, "
                f"found `{actual_name}`"
            )
    return errors
