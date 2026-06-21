"""Paths for persisted agent review artifacts."""

from __future__ import annotations

from pathlib import Path


DEFAULT_AGENT_REVIEW_ARTIFACT_DIR = Path("tests") / "agentic_review_artifacts"


def agent_review_artifact_path(
    test_file_path: Path,
    repo_root: Path,
    artifact_root: Path | None = None,
) -> Path:
    """Return the default persisted review artifact path for a test file."""

    root = Path(repo_root).resolve()
    test_file = Path(test_file_path).resolve()
    review_root = Path(artifact_root) if artifact_root is not None else DEFAULT_AGENT_REVIEW_ARTIFACT_DIR
    if not review_root.is_absolute():
        review_root = root / review_root

    return review_root / f"{test_file.stem}.agent.md"
