"""Tests in this file validate `test_review_documentation` located at `tests/repository_health/test_review_documentation.py`.
`test_review_documentation` is responsible for requiring README.md and docs/workflows/github-actions.md to document the supported pre-commit review and CI/CD validation workflows.

Terms:
- `reviewer identity`: A reviewer identity records the agent and model that completed a review. For example, `codex:gpt-5.5` is a reviewer identity.
- `lint arguments`: Lint arguments are exactly `lint`, `--reviewer`, and one reviewer identity in that order. For example, `lint --reviewer codex:gpt-5.5` supplies the lint arguments.
- `pre-commit review workflow`: The pre-commit review workflow orders three stages: run `agentic-tdd-linter create-agent-md` to create `.agent.md` files, complete their scorecards, and run reviewer-authenticated lint to persist proof.
- `CI/CD validation workflow`: The CI/CD validation workflow validates committed tests and manifest proof without creating scorecards. For example, GitHub Actions runs lint after changes are committed.
"""

from __future__ import annotations

import shlex
import unittest
from pathlib import Path


class ReviewDocumentationTests(unittest.TestCase):
    def test_readme_names_both_workflows(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README headings: `pre-commit review workflow` and `CI/CD validation workflow`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README contains heading `Pre-commit review workflow`.
        README contains heading `CI/CD validation workflow`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        readme = (repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("### Pre-commit review workflow", readme)
        self.assertIn("### CI/CD validation workflow", readme)

    def test_readme_includes_reviewer(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README to provide exact `lint arguments`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        README command contains exactly `lint`, `--reviewer`, and `codex:gpt-5.5` in that order.

        Similar Coverage:
        - Lower Level Test: `test_main.py::test_lint_requires_reviewer`
          Justification: Deeper coverage — The lower test proves runtime enforcement when reviewer identity is absent. The current test verifies that README supplies reviewer identity in the lint command.
        """

        repo_root = Path(__file__).resolve().parents[2]
        reviewer = "codex:gpt-5.5"
        expected_args = ["lint", "--reviewer", reviewer]
        self.assertEqual(_readme_review_command_args(repo_root), expected_args)

    def test_readme_shows_review_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then record them through reviewer-authenticated lint.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README contents list these markers in order:
        1. `agentic-tdd-linter create-agent-md`.
        2. `Review the generated files`.
        3. `agentic-tdd-linter lint --reviewer codex:gpt-5.5`.

        Similar Coverage:
        - Lower Level Test: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Justification: Deeper coverage — The lower test executes the review lifecycle. The current test verifies that README documents the same ordered lifecycle.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide = (repo_root / "README.md").read_text(encoding="utf-8")
        step_markers = (
            "agentic-tdd-linter create-agent-md",
            "Review the generated files",
            "agentic-tdd-linter lint --reviewer codex:gpt-5.5",
        )
        step_positions = tuple(guide.index(marker) for marker in step_markers)

        self.assertEqual(tuple(sorted(step_positions)), step_positions)

    def test_github_actions_shows_ci(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires `CI/CD validation workflow` guidance to prescribe 'agentic-tdd-linter lint' for committed manifest proof and repository tests.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The guide contains `agentic-tdd-linter lint`.
        The guide contains `GitHub Actions verifies committed agent-review proof`.
        The guide contains `committed tests and manifest proof`.

        Similar Coverage:
        - Lower Level Test: `test_cicd_validation_workflow.py::test_cicd_accepts_current_proof`
          Justification: Deeper coverage — The lower test executes CI lint against current proof. The current test verifies that GitHub Actions guidance documents that validation.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide = (
            repo_root / "docs" / "workflows" / "github-actions.md"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn("GitHub Actions verifies committed agent-review proof", guide)
        self.assertIn("agentic-tdd-linter lint", guide)
        self.assertIn("committed tests and manifest proof", guide)

    def test_github_actions_omits_packet_creation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the agentic-tdd-linter create-agent-md command.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The guide contains no `agentic-tdd-linter create-agent-md` command.

        Similar Coverage:
        - Lower Level Test: `test_cicd_validation_workflow.py::test_cicd_creates_no_packets`
          Justification: Deeper coverage — The lower test proves that CI lint creates no '.agent.md' files at runtime. The current test proves that the GitHub Actions guide describes the same constraint.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide = (
            repo_root / "docs" / "workflows" / "github-actions.md"
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn("agentic-tdd-linter create-agent-md", guide)


def _readme_review_command_args(repo_root: Path) -> list[str]:
    for line in (repo_root / "README.md").read_text(encoding="utf-8").splitlines():
        if "agentic-tdd-linter lint" not in line or "--reviewer" not in line:
            continue
        command_parts = shlex.split(line)
        command_index = next(
            index
            for index, part in enumerate(command_parts)
            if Path(part).name == "agentic-tdd-linter"
        )
        return command_parts[command_index + 1 :]
    raise AssertionError("README does not include the reviewer-explicit lint command")


if __name__ == "__main__":
    unittest.main()
