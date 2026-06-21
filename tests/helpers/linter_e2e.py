from __future__ import annotations

import contextlib
import io
import json
import shlex
import subprocess
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
        review_command = _write_reviewer_command(repo_root, status=status, note=note)

        with contextlib.redirect_stdout(stdout):
            first_exit_code = main(["check", str(test_file), "--repo-root", str(repo_root)])

        artifact_path = _single_review_artifact(repo_root)
        _assert_pending_review(first_exit_code, stdout.getvalue())
        _run_reviewer_command(review_command, artifact_path)
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "check",
                    str(test_file),
                    "--reviewer",
                    "codex:gpt-5.5",
                    "--repo-root",
                    str(repo_root),
                ]
            )

        return LinterResult(exit_code=exit_code, output=stdout.getvalue())


def run_linter_source_with_review(*, source: str, status: str, note: str) -> LinterResult:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = _write_source_file(repo_root, source)
        stdout = io.StringIO()
        review_command = _write_reviewer_command(repo_root, status=status, note=note)

        with contextlib.redirect_stdout(stdout):
            first_exit_code = main(["check", str(test_file), "--repo-root", str(repo_root)])

        artifact_path = _single_review_artifact(repo_root)
        _assert_pending_review(first_exit_code, stdout.getvalue())
        _run_reviewer_command(review_command, artifact_path)
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "check",
                    str(test_file),
                    "--reviewer",
                    "codex:gpt-5.5",
                    "--repo-root",
                    str(repo_root),
                ]
            )

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


def _write_source_file(repo_root: Path, source: str) -> Path:
    test_directory = repo_root / "tests"
    test_directory.mkdir()
    test_file = test_directory / "test_sample.py"
    test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
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


def _assert_pending_review(exit_code: int, output: str) -> None:
    if exit_code != 1:
        raise AssertionError("first linter run should fail until the generated artifact is reviewed")
    if "agent_review_not_run" not in output:
        raise AssertionError("first linter run should report pending agent review")


def _run_reviewer_command(review_command: str, artifact_path: Path) -> None:
    result = subprocess.run(
        shlex.split(review_command),
        env={"AGENTIC_TDD_LINTER_ARTIFACT": str(artifact_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        raise AssertionError(f"review command failed with exit code {result.returncode}: {output}")


def _write_reviewer_command(repo_root: Path, *, status: str, note: str) -> str:
    reviewer = repo_root / "review_agent.py"
    reviewer.write_text(
        textwrap.dedent(
            f"""
            from pathlib import Path
            import os


            status = {json.dumps(status)}
            note = {json.dumps(note)}
            artifact = Path(os.environ["AGENTIC_TDD_LINTER_ARTIFACT"])
            text = artifact.read_text(encoding="utf-8")
            text = text.replace("Status: pending", f"Status: {{status}}", 1)
            text = text.replace("- Replace this line with the agent review result.", f"- {{note}}", 1)
            artifact.write_text(text, encoding="utf-8")
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return shlex.join([sys.executable, str(reviewer)])
