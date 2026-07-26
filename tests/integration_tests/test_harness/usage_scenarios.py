"""Provide repository and command setup for usage-scenario tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def run_cli(
    repo_root: Path,
    command: str,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH", "")
    source_root = str(PROJECT_ROOT / "src")
    environment["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else source_root + os.pathsep + existing_pythonpath
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_tdd_linter.cli.main",
            command,
            "--repo-root",
            str(repo_root),
            *arguments,
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def write_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def packet_paths(repo_root: Path) -> list[Path]:
    return sorted(
        (repo_root / "tests" / "agentic_review_artifacts").glob("*.agent.md")
    )


def complete_packets(repo_root: Path, *, status: str, evidence: str) -> None:
    for packet_path in packet_paths(repo_root):
        packet = packet_path.read_text(encoding="utf-8")
        if status == "pass":
            packet = packet.replace(
                "| pending | Replace with review evidence. |",
                f"| pass | {evidence}. |",
            )
        else:
            packet = packet.replace(
                "| pending | Replace with review evidence. |",
                f"| fail | {evidence}. |",
                1,
            ).replace(
                "| pending | Replace with review evidence. |",
                f"| pass | {evidence}. |",
            )
        packet_path.write_text(packet, encoding="utf-8")


def record_approved_manifest(
    repo_root: Path,
    *,
    reviewer: str,
    review_status: str,
    review_evidence: str,
) -> None:
    creation = run_cli(repo_root, "create-agent-md")
    if creation.returncode != 0:
        raise AssertionError(creation.stdout + creation.stderr)
    complete_packets(
        repo_root,
        status=review_status,
        evidence=review_evidence,
    )
    lint = run_cli(repo_root, "lint", "--reviewer", reviewer)
    if lint.returncode != 0:
        raise AssertionError(lint.stdout + lint.stderr)


def manifest_records(repo_root: Path) -> list[dict[str, str]]:
    manifest_path = repo_root / "tests" / "agentic_review_manifest.jsonl"
    return [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
    ]


def remove_packet_directory(repo_root: Path) -> None:
    artifact_root = repo_root / "tests" / "agentic_review_artifacts"
    for packet_path in artifact_root.glob("*.agent.md"):
        packet_path.unlink()
    if artifact_root.exists():
        artifact_root.rmdir()
