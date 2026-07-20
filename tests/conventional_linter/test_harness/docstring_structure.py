"""Build sources for structured-docstring tests."""

from __future__ import annotations

from . import _lint_source


def _lint_docstring_source(source: str) -> set[str]:
    return _lint_source(source)


def _lint_typescript_docstring_source(source: str) -> set[str]:
    return _lint_source(source, "tests/localArtifactRoundTrip.test.ts")
