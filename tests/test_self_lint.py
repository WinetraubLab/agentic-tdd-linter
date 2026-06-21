from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.cli import main


FISHFOOD_CHECK_ARGS = ["check", "--all"]


class SelfLintTests(unittest.TestCase):
    def test_fishfood_validates_repository_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Fishfood validates repository tests.

        Verification Method: verify public function output

        Verification Detail:
        Command output includes success.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([*FISHFOOD_CHECK_ARGS, "--repo-root", str(REPO_ROOT)])

        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())

    def test_fishfood_matches_artifact_statuses(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Fishfood returns `1` when any `agent_review_artifact` has fail status. It returns `0` otherwise.

        Verification Method: verify public function output

        Verification Detail:
        Parser compares expected code.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([*FISHFOOD_CHECK_ARGS, "--repo-root", str(REPO_ROOT)])

        statuses = _agent_review_statuses()
        expected_exit_code = 1 if "fail" in statuses.values() else 0

        self.assertTrue(statuses)
        self.assertTrue(all(status in {"pass", "fail"} for status in statuses.values()))
        self.assertEqual(expected_exit_code, exit_code)

    def test_fishfood_matches_readme(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Fishfood uses README arguments.

        Verification Method: verify public function output

        Verification Detail:
        Parser compares README arguments.
        """

        self.assertEqual(_readme_check_args(), FISHFOOD_CHECK_ARGS)

    def test_readme_execution_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        README command creates `agent_review_artifact` files. Files start pending.

        Verification Method: verify public function output

        Verification Detail:
        Output includes `agent_review_not_run`.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = _write_test_file(repo_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main([*_readme_check_args(), "--repo-root", str(repo_root)])

            artifact_path = agent_review_artifact_path(test_file, repo_root)
            artifact_exists = artifact_path.is_file()
            output = stdout.getvalue()

        self.assertEqual(1, exit_code)
        self.assertTrue(artifact_exists)
        self.assertIn("agent_review_not_run", output)
        self.assertIn("agentic-tdd-linter check --all", output)


def _readme_check_args() -> list[str]:
    for line in (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        if "agentic-tdd-linter check" not in line:
            continue
        command_parts = shlex.split(line)
        command_index = command_parts.index("agentic-tdd-linter")
        return command_parts[command_index + 1 :]
    raise AssertionError("README does not include the agentic-tdd-linter check command")


def _agent_review_statuses() -> dict[Path, str]:
    artifact_root = REPO_ROOT / "tests" / "agentic_review_artifacts"
    statuses = {}
    for artifact_path in sorted(artifact_root.rglob("*.agent.md")):
        statuses[artifact_path] = _status_value(artifact_path.read_text(encoding="utf-8"))
    return statuses


def _status_value(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Status:"):
            return line.removeprefix("Status:").strip().lower()
    return ""


def _write_test_file(repo_root: Path) -> Path:
    test_directory = repo_root / "tests"
    test_directory.mkdir()
    test_file = test_directory / "test_sample.py"
    test_file.write_text(
        textwrap.dedent(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                by asserting the returned numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return test_file


if __name__ == "__main__":
    unittest.main()
