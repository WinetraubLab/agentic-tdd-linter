from __future__ import annotations

import contextlib
import io
import json
import shlex
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.cli import main


REVIEWER = "codex:gpt-5.5"
DOGFOOD_CHECK_ARGS = ["check", "--all", "--reviewer", REVIEWER]
LOCAL_REVIEW_CHECK_ARGS = ["check", "--all", "--reviewer", REVIEWER]


class SelfLintTests(unittest.TestCase):
    def test_dogfood_validates_repository_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Dogfood validates repository tests with committed review attestations.

        Verification Method: verify public function output

        Verification Detail:
        Command output includes success.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([*DOGFOOD_CHECK_ARGS, "--repo-root", str(REPO_ROOT)])

        self.assertEqual(0, exit_code)
        self.assertIn("no issues found", stdout.getvalue())

    def test_dogfood_matches_manifest_statuses(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Dogfood manifest records pass statuses for reviewed test files.

        Verification Method: verify public function output

        Verification Detail:
        Parser compares manifest statuses.
        """

        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([*DOGFOOD_CHECK_ARGS, "--repo-root", str(REPO_ROOT)])

        statuses = _agent_review_manifest_statuses()

        self.assertTrue(statuses)
        self.assertTrue(all(status == "pass" for status in statuses.values()))
        self.assertEqual(0, exit_code)

    def test_review_manifest_is_tracked(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Review manifest stays in source control.
        Fresh checkouts need committed proof records for CI verification.

        Verification Method: verify public function output

        Verification Detail:
        Git index includes `tests/agentic_review_manifest.jsonl`.
        """

        manifest_path = Path("tests") / "agentic_review_manifest.jsonl"
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(manifest_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr or result.stdout)

    def test_dogfood_matches_readme(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Dogfood uses README CI arguments.

        Verification Method: verify public function output

        Verification Detail:
        Parser compares README arguments.
        """

        self.assertEqual(_readme_ci_check_args(), DOGFOOD_CHECK_ARGS)

    def test_health_workflow_runs_unit_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Health workflow runs repository unit tests.
        Self-lint tests cover linter health inside that suite.

        Verification Method: verify public function output

        Verification Detail:
        Workflow runs unit tests and omits redundant direct linter command.
        """

        workflow = (REPO_ROOT / ".github" / "workflows" / "health.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("python -m unittest discover -s tests", workflow)
        self.assertNotIn("agentic-tdd-linter check --all --reviewer codex:gpt-5.5", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("push:", workflow)
        self.assertNotIn("branches:", workflow)
        self.assertNotIn("--review-proof manifest", workflow)

    def test_docs_use_two_run_review(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        README and GitHub Actions docs use the local review command.
        Documentation tells agents to rerun the same check command.
        `--reviewer` supplies the manifest reviewer identity when proof refreshes.

        Verification Method: verify public function output

        Verification Detail:
        Documentation includes reviewer-explicit check and omits standalone attest command.
        """

        documentation = "\n".join(
            [
                (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "docs" / "workflows" / "github-actions.md").read_text(
                    encoding="utf-8"
                ),
            ]
        )

        self.assertIn("agentic-tdd-linter check --all --reviewer codex:gpt-5.5", documentation)
        self.assertIn("Then rerun the same command", documentation)
        self.assertNotIn("agentic-tdd-linter attest", documentation)
        self.assertNotIn("--review-proof manifest", documentation)

    def test_readme_execution_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Local review command starts clean dogfood review. Second run passes after review.

        Verification Method: verify public function output

        Verification Detail:
        First report includes `agent_review_not_run`. Second report includes success.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = _write_test_file(repo_root)
            stdout = io.StringIO()

            _delete_agent_review_artifacts(repo_root)

            with contextlib.redirect_stdout(stdout):
                first_exit_code = main([*LOCAL_REVIEW_CHECK_ARGS, "--repo-root", str(repo_root)])

            artifact_path = agent_review_artifact_path(test_file, repo_root)
            artifact_exists = artifact_path.is_file()
            first_output = stdout.getvalue()
            _mark_agent_review_artifacts_pass(repo_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                second_exit_code = main([*LOCAL_REVIEW_CHECK_ARGS, "--repo-root", str(repo_root)])

            manifest_exists = (repo_root / "tests" / "agentic_review_manifest.jsonl").is_file()
            manifest_record = json.loads(
                (repo_root / "tests" / "agentic_review_manifest.jsonl").read_text(
                    encoding="utf-8"
                )
            )
            second_output = stdout.getvalue()

        self.assertEqual(1, first_exit_code)
        self.assertTrue(artifact_exists)
        self.assertIn("agent_review_not_run", first_output)
        self.assertIn("agentic-tdd-linter check --all", first_output)
        self.assertEqual(0, second_exit_code)
        self.assertTrue(manifest_exists)
        self.assertEqual(REVIEWER, manifest_record["reviewer"])
        self.assertIn("no issues found", second_output)
        self.assertIn("recorded 1 review attestations", second_output)


def _readme_ci_check_args() -> list[str]:
    for line in (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        if "agentic-tdd-linter check" not in line or "--reviewer" not in line:
            continue
        command_parts = shlex.split(line)
        command_index = command_parts.index("agentic-tdd-linter")
        return command_parts[command_index + 1 :]
    raise AssertionError("README does not include the reviewer-explicit check command")


def _agent_review_manifest_statuses() -> dict[Path, str]:
    manifest_path = REPO_ROOT / "tests" / "agentic_review_manifest.jsonl"
    statuses = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        statuses[Path(record["path"])] = record.get("status", "")
    return statuses


def _delete_agent_review_artifacts(repo_root: Path) -> None:
    artifact_root = repo_root / "tests" / "agentic_review_artifacts"
    if not artifact_root.exists():
        return
    for artifact_path in artifact_root.glob("*.agent.md"):
        artifact_path.unlink()


def _mark_agent_review_artifacts_pass(repo_root: Path) -> None:
    artifact_root = repo_root / "tests" / "agentic_review_artifacts"
    artifacts = sorted(artifact_root.glob("*.agent.md"))
    if not artifacts:
        raise AssertionError("expected generated agent review artifacts")
    for artifact_path in artifacts:
        artifact_text = artifact_path.read_text(encoding="utf-8")
        artifact_text = artifact_text.replace("Status: pending", "Status: pass", 1)
        artifact_text = artifact_text.replace(
            "- Replace this line with the agent review result.",
            "- Clean dogfood review passed.",
            1,
        )
        artifact_path.write_text(artifact_text, encoding="utf-8")


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
