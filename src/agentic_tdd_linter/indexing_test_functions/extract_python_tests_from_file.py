"""Extract test functions from one Python file."""

from __future__ import annotations

import ast
from pathlib import Path

from .extracted_test_record import ExtractedTestRecord


def extract_python_tests_from_file(
    path: Path,
    repo_root: Path,
) -> list[ExtractedTestRecord]:
    """Return Python test functions extracted in source order."""

    absolute_path = Path(path).resolve()
    relative_path = _relative_path(absolute_path, repo_root)
    source = absolute_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(absolute_path))
    tests = [
        ExtractedTestRecord(
            path=relative_path,
            name=node.name,
            line=node.lineno,
            node=node,
            docstring=ast.get_docstring(node) or "",
            source=ast.get_source_segment(source, node) or "",
        )
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    return sorted(tests, key=lambda test: test.line)


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return Path(path).resolve().relative_to(Path(repo_root).resolve())
    except ValueError:
        return Path(path)
