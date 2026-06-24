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
    artifact_path = _artifact_path(source_sha256)
    exit_code, output = _run_linter(source_sha256)
    if "agent_review_not_run" in output:
        raise RuntimeError(
            "did not run, agent should review "
            f"{_display_path(artifact_path)} and then run test again"
        )
    _record_artifact_review(source_sha256, artifact_path)
    return exit_code == 0, output


REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = REPO_ROOT / "temporary_fixtures"
ARTIFACT_ROOT = TEST_ROOT / "agentic_review_artifacts"
MANIFEST_PATH = TEST_ROOT / "agentic_review_manifest.jsonl"
REVIEWER = "e2e:review"

sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.agent_review_manifest import review_contract_sha256
from agentic_tdd_linter.cli import main
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
        exit_code = main(
            [
                "check",
                str(TEST_ROOT / f"{source_sha256}.py"),
                "--test-root",
                str(TEST_ROOT),
                "--review-proof",
                "artifact",
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
        if record.get("review_contract_sha256") != review_contract_sha256(REPO_ROOT):
            continue
        if _version_is_older(record.get("linter_version", ""), __version__):
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


def _record_artifact_review(source_sha256: str, artifact_path: Path) -> None:
    artifact_text = artifact_path.read_text(encoding="utf-8")
    status = _field_value(artifact_text, "Status").lower()
    if status not in {"pass", "fail"}:
        return

    record = {
        "path": _source_path(source_sha256).as_posix(),
        "source_sha256": source_sha256,
        "status": status,
        "linter_version": __version__,
        "review_contract_sha256": review_contract_sha256(REPO_ROOT),
        "reviewer": REVIEWER,
        "reason": _notes_value(artifact_text),
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


def _field_value(text: str, field_name: str) -> str:
    prefix = f"{field_name}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def _notes_value(text: str) -> str:
    notes_started = False
    notes: list[str] = []
    for line in text.splitlines():
        if line.strip() == "Notes:":
            notes_started = True
            continue
        if not notes_started:
            continue
        if line.startswith("- "):
            notes.append(line[2:].strip())
        elif notes and line.startswith("  "):
            notes[-1] = f"{notes[-1]} {line.strip()}"
    return " ".join(notes).strip()


def _version_is_older(recorded_version: str, current_version: str) -> bool:
    recorded_parts = _version_parts(recorded_version)
    current_parts = _version_parts(current_version)
    if recorded_parts is None or current_parts is None:
        return recorded_version != current_version
    max_length = max(len(recorded_parts), len(current_parts))
    recorded_parts = recorded_parts + (0,) * (max_length - len(recorded_parts))
    current_parts = current_parts + (0,) * (max_length - len(current_parts))
    return recorded_parts < current_parts


def _version_parts(value: str) -> tuple[int, ...] | None:
    parts = value.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _artifact_path(source_sha256: str) -> Path:
    return ARTIFACT_ROOT / f"{source_sha256}.agent.md"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
