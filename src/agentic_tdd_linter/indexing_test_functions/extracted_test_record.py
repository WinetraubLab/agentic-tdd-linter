"""Shared record for one extracted test."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractedTestRecord:
    """One extracted test and its structured documentation."""

    # Test-file path relative to the repository root when the file is inside it.
    path: Path
    # Python function name or TypeScript test label.
    name: str
    # One-based line where the test begins, excluding any leading TypeScript JSDoc.
    line: int
    # Python syntax-tree node; None for languages that are not parsed with ast.
    node: ast.FunctionDef | ast.AsyncFunctionDef | None
    # Python docstring or cleaned TypeScript JSDoc attached to the test.
    docstring: str
    # Complete source text for this test, including its structured documentation.
    source: str = ""
    # Python module docstring shared by the file's tests; None for other languages.
    file_docstring: str | None = None
