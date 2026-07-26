"""Build sources for classification tests."""

from __future__ import annotations

from . import _lint_source


def _lint_classification_source(source: str) -> set[str]:
    return _lint_source(source)
