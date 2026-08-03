"""Tests in this file validate `test_review_documentation` located at `tests/repository_health/test_review_documentation.py`.
`test_review_documentation` is responsible for requiring README.md and docs/workflows/github-actions.md to document the supported pre-commit review and CI/CD validation workflows.

Terms:
- `.agent.md`: An .agent.md file contains one generated agent-review scorecard. For example, the pre-commit workflow creates and reviews .agent.md files before lint records proof.
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
    def test_readme_names_pre_commit_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README to include a level-three `pre-commit review workflow` heading.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README contents contain `### Pre-commit review workflow`.

        Similar Coverage:
        - Module Difference: `test_review_documentation.py::test_readme_names_cicd_workflow`
          Explanation: The current test verifies `test_review_documentation` requires README to include a level-three `pre-commit review workflow` heading. The named test verifies `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_review_documentation.py::test_readme_shows_review_workflow`
          Explanation: The current test verifies `test_review_documentation` requires README to include a level-three `pre-commit review workflow` heading. The named test verifies `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint; both use happy path, but exercise materially different scenarios.
        """

        repo_root = Path(__file__).resolve().parents[2]
        readme = (repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("### Pre-commit review workflow", readme)

    def test_readme_names_cicd_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README contents contain `### CI/CD validation workflow`.

        Similar Coverage:
        - Scenario Difference: `test_review_documentation.py::test_github_actions_omits_packet_creation`
          Explanation: The current test verifies `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading. The named test verifies `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the create-agent-md command; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_review_documentation.py::test_github_actions_shows_ci`
          Explanation: The current test verifies `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading. The named test verifies `test_review_documentation` requires GitHub Actions guidance to describe the `CI/CD validation workflow` as linting committed tests and manifest proof; both use happy path, but exercise materially different scenarios.
        - Module Difference: `test_review_documentation.py::test_readme_names_pre_commit_workflow`
          Explanation: The current test verifies `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading. The named test verifies `test_review_documentation` requires README to include a level-three `pre-commit review workflow` heading; both exercise materially the same scenario through different named modules or contract subjects.
        """

        repo_root = Path(__file__).resolve().parents[2]
        readme = (repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("### CI/CD validation workflow", readme)

    def test_readme_includes_reviewer(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README to provide exact `lint arguments`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `_readme_review_command_args` output provides the README command arguments.
        README command contains exactly `lint`, `--reviewer`, and `codex:gpt-5.5` in that order.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_main.py::test_lint_requires_reviewer`
          Explanation: The current test verifies `test_review_documentation` requires README to provide exact `lint arguments`. The named test verifies `CLI` emits missing_reviewer for completed `.agent.md` files when `reviewer identity` is absent; the current test is happy path, while the named test is failure path.
        """

        repo_root = Path(__file__).resolve().parents[2]
        reviewer = "codex:gpt-5.5"
        expected_args = ["lint", "--reviewer", reviewer]
        self.assertEqual(_readme_review_command_args(repo_root), expected_args)

    def test_readme_shows_review_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README contents contain `agentic-tdd-linter create-agent-md` before `Review the generated files`.
        README contents contain `Review the generated files` before `agentic-tdd-linter lint --reviewer codex:gpt-5.5`.

        Similar Coverage:
        - Module Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_review_documentation.py::test_readme_names_pre_commit_workflow`
          Explanation: The current test verifies `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint. The named test verifies `test_review_documentation` requires README to include a level-three `pre-commit review workflow` heading; both use happy path, but exercise materially different scenarios.
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
        `test_review_documentation` requires GitHub Actions guidance to describe the `CI/CD validation workflow` as linting committed tests and manifest proof.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        GitHub Actions guide contents contain `agentic-tdd-linter lint`.
        GitHub Actions guide contents contain `GitHub Actions verifies committed agent-review proof`.
        GitHub Actions guide contents contain `committed tests and manifest proof`.

        Similar Coverage:
        - Module Difference: `test_cicd_validation_workflow.py::test_cicd_accepts_current_proof`
          Explanation: The current test verifies `test_review_documentation` requires GitHub Actions guidance to describe the `CI/CD validation workflow` as linting committed tests and manifest proof. The named test verifies `CI/CD linter` accepts current manifest proof; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_review_documentation.py::test_github_actions_omits_packet_creation`
          Explanation: The current test verifies `test_review_documentation` requires GitHub Actions guidance to describe the `CI/CD validation workflow` as linting committed tests and manifest proof. The named test verifies `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the create-agent-md command; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_review_documentation.py::test_readme_names_cicd_workflow`
          Explanation: The current test verifies `test_review_documentation` requires GitHub Actions guidance to describe the `CI/CD validation workflow` as linting committed tests and manifest proof. The named test verifies `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading; both use happy path, but exercise materially different scenarios.
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
        `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the create-agent-md command.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        GitHub Actions guide contents contain no `agentic-tdd-linter create-agent-md` command.

        Similar Coverage:
        - Module Difference: `test_cicd_validation_workflow.py::test_cicd_creates_no_packets`
          Explanation: The current test verifies `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the create-agent-md command. The named test verifies `CI/CD linter` creates no `.agent.md` files when current manifest proof exists; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_review_documentation.py::test_github_actions_shows_ci`
          Explanation: The current test verifies `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the create-agent-md command. The named test verifies `test_review_documentation` requires GitHub Actions guidance to describe the `CI/CD validation workflow` as linting committed tests and manifest proof; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_review_documentation.py::test_readme_names_cicd_workflow`
          Explanation: The current test verifies `test_review_documentation` requires `CI/CD validation workflow` guidance to exclude the create-agent-md command. The named test verifies `test_review_documentation` requires README to include a level-three `CI/CD validation workflow` heading; both use happy path, but exercise materially different scenarios.
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
