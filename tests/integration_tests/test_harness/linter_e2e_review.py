"""Run generated test scenarios through the complete linter review workflow.

This test-harness module belongs under integration_tests because it exercises
the conventional linter, CLI, agent-review packet generation, external agent
handoff, and review manifest together. It is not production linter code: the
integration tests use it to write temporary scenarios, pause for agent review,
and obtain the final proof-backed lint result on a later run.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import textwrap
from pathlib import Path

def linter_e2e_review(
    *,
    test_source_code: str,
) -> tuple[bool, str]:
    normalized_source = _normalized_source(test_source_code)
    source_sha256 = _source_sha256(normalized_source)
    _write_test_source(source_sha256, normalized_source)
    manifest_record = _current_manifest_record(source_sha256)
    if manifest_record is not None:
        return _review_result_from_manifest(manifest_record)
    exit_code, output = _run_linter(source_sha256)
    artifact_paths = _artifact_paths(source_sha256)
    if "agent_review_not_run" in output:
        review_paths = ", ".join(_display_path(path) for path in artifact_paths)
        raise RuntimeError(
            "did not run, agent should review "
            f"{review_paths} and then run test again"
        )
    _record_artifact_review(source_sha256, artifact_paths)
    return exit_code == 0, output


REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = REPO_ROOT / "temporary_fixtures"
ARTIFACT_ROOT = TEST_ROOT / "agentic_review_artifacts"
MANIFEST_PATH = TEST_ROOT / "agentic_review_manifest.jsonl"
REVIEWER = "e2e:review"

sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.agentic_linter.build_manifest_from_agent_md_files import (
    _review_contract_sha256,
)
from agentic_tdd_linter.cli.main import main
from agentic_tdd_linter.version import __version__


def _normalized_source(test_source_code: str) -> str:
    return textwrap.dedent(test_source_code).strip() + "\n"


def _source_sha256(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _write_test_source(source_sha256: str, normalized_source: str) -> Path:
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    test_file = TEST_ROOT / f"{source_sha256}.py"
    test_file.write_text(normalized_source, encoding="utf-8")
    return test_file


def _run_linter(source_sha256: str) -> tuple[int, str]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        if not _artifact_paths(source_sha256):
            main(
                [
                    "create-agent-md",
                    str(TEST_ROOT / f"{source_sha256}.py"),
                    "--test-root",
                    str(TEST_ROOT),
                    "--manifest",
                    str(MANIFEST_PATH),
                ]
            )
        exit_code = main(
            [
                "lint",
                str(TEST_ROOT / f"{source_sha256}.py"),
                "--test-root",
                str(TEST_ROOT),
                "--manifest",
                str(MANIFEST_PATH),
                "--reviewer",
                REVIEWER,
            ]
        )
    return exit_code, stdout.getvalue()


def _current_manifest_record(source_sha256: str) -> dict[str, str] | None:
    if not MANIFEST_PATH.exists():
        return None

    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw_record = json.loads(line)
        except json.JSONDecodeError:
            return None
        record = {str(key): str(value) for key, value in raw_record.items()}
        if record.get("source_sha256") != source_sha256:
            continue
        if record.get("path") != _source_path(source_sha256).as_posix():
            continue
        if record.get("review_contract_sha256") != _review_contract_sha256(REPO_ROOT):
            continue
        if record.get("linter_version", "") != __version__:
            continue
        if record.get("status") not in {"pass", "fail"}:
            continue
        return record
    return None


def _review_result_from_manifest(record: dict[str, str]) -> tuple[bool, str]:
    status = record["status"]
    if status == "pass":
        return True, "agentic-tdd-linter: no issues found in 1 file\n"
    reason = record.get("reason", "agent review failed")
    return (
        False,
        (
            f"FAIL {record['path']}:1 <agent-review>\n"
            "Rule: agent_review_failed\n"
            f"{reason}\n"
        ),
    )


def _record_artifact_review(source_sha256: str, artifact_paths: list[Path]) -> None:
    artifact_texts = [path.read_text(encoding="utf-8") for path in artifact_paths]
    statuses = [_scorecard_status(text) for text in artifact_texts]
    if not statuses or any(status not in {"pass", "fail"} for status in statuses):
        return
    status = "fail" if "fail" in statuses else "pass"

    record = {
        "path": _source_path(source_sha256).as_posix(),
        "source_sha256": source_sha256,
        "status": status,
        "linter_version": __version__,
        "review_contract_sha256": _review_contract_sha256(REPO_ROOT),
        "reviewer": REVIEWER,
        "reason": " ".join(
            value for value in (_failed_scorecard_notes(text) for text in artifact_texts) if value
        ),
    }
    records = [
        existing_record
        for existing_record in _manifest_records()
        if existing_record.get("source_sha256") != source_sha256
    ]
    records.append(record)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        "".join(
            json.dumps(_ordered_manifest_record(existing_record), separators=(", ", ": "))
            + "\n"
            for existing_record in sorted(records, key=lambda value: value["path"])
        ),
        encoding="utf-8",
    )


def _manifest_records() -> list[dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return []
    records: list[dict[str, str]] = []
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append({str(key): str(value) for key, value in json.loads(line).items()})
    return records


def _ordered_manifest_record(record: dict[str, str]) -> dict[str, str]:
    return {
        "path": record.get("path", ""),
        "source_sha256": record.get("source_sha256", ""),
        "status": record.get("status", ""),
        "linter_version": record.get("linter_version", ""),
        "review_contract_sha256": record.get("review_contract_sha256", ""),
        "reviewer": record.get("reviewer", ""),
        "reason": record.get("reason", ""),
    }


def _source_path(source_sha256: str) -> Path:
    return Path("temporary_fixtures") / f"{source_sha256}.py"


def _artifact_paths(source_sha256: str) -> list[Path]:
    return sorted(ARTIFACT_ROOT.glob(f"{source_sha256}__*.agent.md"))


def _scorecard_status(text: str) -> str:
    results = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        results.append(cells[2].lower())
    if not results or any(result not in {"pass", "fail"} for result in results):
        return "pending"
    return "fail" if "fail" in results else "pass"


def _failed_scorecard_notes(text: str) -> str:
    notes = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 4 and cells[0].isdigit() and cells[2].lower() == "fail":
            notes.append(f"{cells[1]}: {cells[3]}")
    return "; ".join(notes)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
