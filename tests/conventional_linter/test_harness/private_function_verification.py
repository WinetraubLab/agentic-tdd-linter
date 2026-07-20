"""Build sources for private-function verification tests."""

from __future__ import annotations

from . import _lint_source


def _lint_private_verification_source(source: str) -> set[str]:
    return _lint_source(source)
