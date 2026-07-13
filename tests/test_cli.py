from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import textwrap
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

    def test_test_root_sets_artifact(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `--test-root` stores review artifacts under that test root.

        Verification Method: verify public function output

        Verification Detail:
        Generated artifact appears under selected root.
        """

        fixture_file = FIXTURES / "pass_test.py"
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_root = repo_root / "temporary_fixtures"
            test_root.mkdir()
            test_file = test_root / fixture_file.name
            test_file.write_text(fixture_file.read_text(encoding="utf-8"), encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check",
                        "--repo-root",
                        str(repo_root),
                        "--test-root",
                        str(test_root),
                        str(test_file),
                    ]
                )

            expected_artifact = (
                test_root
                / "agentic_review_artifacts"
                / "pass_test__test_adds_positive_numbers.agent.md"
            )
            artifact_exists = expected_artifact.exists()

        self.assertEqual(1, exit_code)
        self.assertTrue(artifact_exists)
        self.assertIn("agent_review_not_run", stdout.getvalue())

    def test_all_discovers_python_files(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `check --all` selects Python test files.

        Verification Method: verify public function output

        Verification Detail:
        Output includes `agent_review_not_run`.
        Output excludes no-test message.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_example.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(_python_test_source(), encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(repo_root)])

            output = stdout.getvalue()

        self.assertEqual(1, exit_code)
        self.assertIn("agent_review_not_run", output)
        self.assertNotIn("no test files to lint", output)

    def test_all_discovers_typescript_files(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `check --all` selects TypeScript files.

        Verification Method: verify public function output

        Verification Detail:
        Output includes `agent_review_not_run`.
        Output excludes no-test message.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = (
                repo_root
                / "tests"
                / "primitives"
                / "activity-plan-template-steps"
                / "localArtifactRoundTrip.test.ts"
            )
            test_file.parent.mkdir(parents=True)
            test_file.write_text(_typescript_test_source(), encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(repo_root)])

            output = stdout.getvalue()

        self.assertEqual(1, exit_code)
        self.assertIn("agent_review_not_run", output)
        self.assertNotIn("no test files to lint", output)

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

    def test_all_skips_review_artifacts_for_files_without_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI review skips files without test functions.
        This applies when discovery finds a test-named helper module.

        Verification Method: verify public function output

        Verification Detail:
        CLI exits successfully and leaves the artifact directory absent.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_helpers.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def helper_function() -> None:\n    return None\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(repo_root)])

            artifact_root = repo_root / "tests" / "agentic_review_artifacts"
            artifact_exists = artifact_root.exists()

        self.assertEqual(0, exit_code)
        self.assertFalse(artifact_exists)


def _copy_fixture(fixture_file: Path, repo_root: Path) -> Path:
    test_file = repo_root / fixture_file.name
    test_file.write_text(fixture_file.read_text(encoding="utf-8"), encoding="utf-8")
    return test_file


def _mark_single_artifact_pass(repo_root: Path) -> None:
    artifacts = sorted((repo_root / "tests" / "agentic_review_artifacts").glob("*.agent.md"))
    if len(artifacts) != 1:
        raise AssertionError(f"expected one generated review artifact, found {len(artifacts)}")
    artifact_text = artifacts[0].read_text(encoding="utf-8")
    artifact_text = artifact_text.replace("| pending |", "| pass |")
    artifact_text = artifact_text.replace(
        "- Scenario or example: Fill this line with the scenario or example used for judgment.",
        "- Scenario or example: fixture source validates CLI artifact recording.",
        1,
    )
    artifact_text = artifact_text.replace(
        "- Review result: Replace this line with the agent review result.",
        "- Review result: fixture passes review.",
        1,
    )
    artifacts[0].write_text(artifact_text, encoding="utf-8")


def _python_test_source() -> str:
    return textwrap.dedent(
        """
        def test_adds_values() -> None:
            \"\"\"Test Path: happy path

            Requirement Tested:
            Addition returns the expected sum for two positive integers.

            Verification Method: verify public function output

            Verification Detail:
            Returned total equals expected sum.
            \"\"\"

            assert 1 + 1 == 2
        """
    ).strip() + "\n"


def _typescript_test_source() -> str:
    return textwrap.dedent(
        """
        import test from "node:test";
        import assert from "node:assert/strict";

        /**
         * Test Path: happy path
         *
         * Requirement Tested:
         * Local artifact writes survive a primitive round trip.
         *
         * Verification Method: verify public function output
         *
         * Verification Detail:
         * Loaded artifact content equals written artifact content.
         */
        test("local artifact round trip", () => {
          assert.equal(readLocalArtifact(), "saved artifact");
        });
        """
    ).strip() + "\n"


if __name__ == "__main__":
    unittest.main()
