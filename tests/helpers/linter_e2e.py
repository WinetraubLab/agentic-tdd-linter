from __future__ import annotations

import contextlib
import io
import sys
import textwrap
from pathlib import Path

def linter_e2e_review(
    *,
    scenario_name: str,
    test_source_code: str,
) -> tuple[bool, str]:
    _write_test_source(scenario_name, test_source_code)
    artifact_path = _artifact_path(scenario_name)
    exit_code, output = _run_linter(scenario_name)
    if "agent_review_not_run" in output:
        raise RuntimeError(
            "did not run, agent should review "
            f"{_display_path(artifact_path)} and then run test again"
        )
    return exit_code == 0, output


REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = REPO_ROOT / "temporary_fixtures"
ARTIFACT_ROOT = TEST_ROOT / "agentic_review_artifacts"
REVIEWER = "e2e:review"

sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.cli import main


def _write_test_source(scenario_name: str, test_source_code: str) -> Path:
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    test_file = TEST_ROOT / f"{scenario_name}.py"
    test_file.write_text(textwrap.dedent(test_source_code).strip() + "\n", encoding="utf-8")
    return test_file


def _run_linter(scenario_name: str) -> tuple[int, str]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = main(
            [
                "check",
                str(TEST_ROOT / f"{scenario_name}.py"),
                "--test-root",
                str(TEST_ROOT),
                "--review-proof",
                "artifact",
                "--manifest",
                str(TEST_ROOT / "agentic_review_manifest.jsonl"),
                "--reviewer",
                REVIEWER,
            ]
        )
    return exit_code, stdout.getvalue()


def _artifact_path(scenario_name: str) -> Path:
    return ARTIFACT_ROOT / f"{scenario_name}.agent.md"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
