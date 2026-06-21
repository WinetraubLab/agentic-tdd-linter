from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.cli import main


FIXTURES = Path(__file__).resolve().parent / "cli_fixtures"


class CliTests(unittest.TestCase):
    def test_valid_fixture_exits_zero(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The check command exits successfully when requested tests have no issues.

        Verification Method: verify public function output

        Verification Detail:
        by running main with the valid fixture path and capturing text output.
        """

        fixture_file = FIXTURES / "pass_test.py"
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = _copy_fixture(fixture_file, repo_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                first_exit_code = main(["check", "--repo-root", str(repo_root), str(test_file)])

            _mark_single_artifact_pass(repo_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check",
                        "--reviewer",
                        "codex:gpt-5.5",
                        "--repo-root",
                        str(repo_root),
                        str(test_file),
                    ]
                )

        self.assertEqual(1, first_exit_code)
        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())

    def test_invalid_fixture_exits_one(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        The check command exits with failure when requested tests have issues.

        Verification Method: verify public function output

        Verification Detail:
        by running main with an invalid fixture path and capturing text output.
        """

        fixture_file = FIXTURES / "fail_test_due_to_missing_requirement.py"
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = _copy_fixture(fixture_file, repo_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--repo-root", str(repo_root), str(test_file)])

        self.assertEqual(1, exit_code)
        self.assertIn("missing_requirement", stdout.getvalue())

    def test_refactor_instructions_prints_prompt(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The refactor instructions flag prints the refactor workflow without running checks.

        Verification Method: verify public function output

        Verification Detail:
        by running the flag and asserting the output includes the refactor prompt.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--refactor-instructions"])

        self.assertEqual(0, exit_code)
        self.assertIn("Simplify helper functions in the codebase.", stdout.getvalue())


def _copy_fixture(fixture_file: Path, repo_root: Path) -> Path:
    test_file = repo_root / fixture_file.name
    test_file.write_text(fixture_file.read_text(encoding="utf-8"), encoding="utf-8")
    return test_file


def _mark_single_artifact_pass(repo_root: Path) -> None:
    artifacts = sorted((repo_root / "tests" / "agentic_review_artifacts").glob("*.agent.md"))
    if len(artifacts) != 1:
        raise AssertionError(f"expected one generated review artifact, found {len(artifacts)}")
    artifact_text = artifacts[0].read_text(encoding="utf-8")
    artifact_text = artifact_text.replace("Status: pending", "Status: pass", 1)
    artifact_text = artifact_text.replace(
        "- Replace this line with the agent review result.",
        "- fixture passes review.",
        1,
    )
    artifacts[0].write_text(artifact_text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
