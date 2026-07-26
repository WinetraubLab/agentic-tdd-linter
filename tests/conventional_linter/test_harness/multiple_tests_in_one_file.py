"""Build multi-test Python and TypeScript sources."""

from __future__ import annotations

from . import _lint_source


def _lint_multi_python_source(source: str) -> set[str]:
    return _lint_source(source)


def _lint_multi_typescript_source(source: str) -> set[str]:
    return _lint_source(source, "tests/localArtifactRoundTrip.test.ts")
