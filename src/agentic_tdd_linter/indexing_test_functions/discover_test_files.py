"""Discover test files selected for linting."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal


_SKIPPED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".claude",
    ".codex",
    "node_modules",
    "fixtures",
    "helpers",
    "cli_fixtures",
    "temporary_fixtures",
}


def discover_test_files(
    repo_root: Path,
    *,
    mode: Literal["all", "requested"] = "all",
    test_root: Path | None = None,
    paths: Iterable[str] = (),
) -> list[Path]:
    """Return test files selected by an all or requested-file mode."""

    root = Path(repo_root).resolve()
    if mode == "requested":
        return _requested_test_files(paths, root)
    if mode == "all":
        search_root = Path(test_root).resolve() if test_root is not None else root
        return _all_test_files(root, search_root)
    raise ValueError(f"unsupported test discovery mode: {mode}")


def _all_test_files(repo_root: Path, search_root: Path) -> list[Path]:
    return sorted(
        path
        for path in _candidate_test_files(search_root)
        if _is_project_test_file(path, repo_root, skip_path_parts=True)
    )


def _requested_test_files(paths: Iterable[str], repo_root: Path) -> list[Path]:
    requested: list[Path] = []
    for path_value in paths:
        path = Path(path_value)
        if not path.is_absolute():
            path = repo_root / path
        path = path.resolve()

        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if not path.is_relative_to(repo_root):
            raise ValueError(f"path is outside repository: {path}")
        if path.is_dir():
            requested.extend(
                child
                for child in _candidate_test_files(path)
                if _is_project_test_file(child, repo_root, skip_path_parts=False)
            )
            continue
        if not _is_supported_test_file(path):
            raise ValueError(f"path is not a supported test file: {path}")
        requested.append(path)

    return sorted(set(requested))


def _candidate_test_files(search_root: Path) -> list[Path]:
    return sorted([*search_root.rglob("*.py"), *search_root.rglob("*.test.ts")])


def _is_supported_test_file(path: Path) -> bool:
    return path.suffix == ".py" or _is_typescript_test_file(path)


def _is_project_test_file(
    path: Path,
    repo_root: Path,
    *,
    skip_path_parts: bool,
) -> bool:
    try:
        relative_parts = path.resolve().relative_to(repo_root.resolve()).parts
    except ValueError:
        relative_parts = path.parts
    if skip_path_parts and any(part in _SKIPPED_PATH_PARTS for part in relative_parts):
        return False
    if path.suffix == ".py":
        return (
            path.name.startswith("test_")
            or path.name.endswith("_tests.py")
            or "tests" in relative_parts
        )
    return _is_typescript_test_file(path) and "tests" in relative_parts


def _is_typescript_test_file(path: Path) -> bool:
    return path.name.endswith(".test.ts")
