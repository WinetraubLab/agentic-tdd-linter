from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.cli import main


DEFAULT_REQUIREMENT = "Adding two numbers must yield positive result."
DEFAULT_VERIFICATION_DETAIL = "by asserting result is positive."
DEFAULT_TEST_BODY = "assert 1 + 1 > 0"


@dataclass(frozen=True)
class LinterResult:
    exit_code: int
    output: str


def run_linter_with_review(
    *,
    status: str,
    note: str,
    requirement: str = DEFAULT_REQUIREMENT,
    verification_detail: str = DEFAULT_VERIFICATION_DETAIL,
    test_body: str = DEFAULT_TEST_BODY,
) -> LinterResult:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = _write_test_file(
            repo_root,
            requirement=requirement,
            verification_detail=verification_detail,
            test_body=test_body,
        )
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            first_exit_code = main(["check", str(test_file), "--repo-root", str(repo_root)])

        artifact_path = _single_review_artifact(repo_root)
        _complete_review_artifact(artifact_path, status=status, note=note)
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["check", str(test_file), "--repo-root", str(repo_root)])

        if first_exit_code != 1:
            raise AssertionError("first linter run should fail until the generated artifact is reviewed")

        return LinterResult(exit_code=exit_code, output=stdout.getvalue())


def _write_test_file(
    repo_root: Path,
    *,
    requirement: str,
    verification_detail: str,
    test_body: str,
) -> Path:
    test_directory = repo_root / "tests"
    test_directory.mkdir()
    test_file = test_directory / "test_sample.py"
    test_file.write_text(
        textwrap.dedent(
            f'''
            def test_adds_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                {requirement}

                Verification Method: verify public function output

                Verification Detail:
                {verification_detail}
                """

                {_indented_body(test_body)}
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return test_file


def _indented_body(test_body: str) -> str:
    body = textwrap.dedent(test_body).strip()
    if not body:
        body = "pass"
    return textwrap.indent(body, " " * 16).lstrip()


def _single_review_artifact(repo_root: Path) -> Path:
    artifact_root = repo_root / "tests" / "agentic_review_artifacts"
    artifacts = sorted(artifact_root.glob("*.agent.md"))
    if len(artifacts) != 1:
        raise AssertionError(f"expected one generated review artifact, found {len(artifacts)}")
    return artifacts[0]


def _complete_review_artifact(artifact_path: Path, *, status: str, note: str) -> Path:
    text = artifact_path.read_text(encoding="utf-8")
    text = text.replace("Status: pending", f"Status: {status}", 1)
    text = text.replace("- Replace this line with the agent review result.", f"- {note}", 1)
    artifact_path.write_text(text, encoding="utf-8")
    return artifact_path
