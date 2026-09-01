"""Tests in this file validate `test_review_documentation` located at `tests/repository_health/test_review_documentation.py`.
`test_review_documentation` is responsible for requiring README.md and docs/workflows/github-actions.md to document the supported pre-commit review and CI/CD validation workflows.

Terms:
- `.agent.md`: An .agent.md file contains one generated agent-review scorecard. For example, the pre-commit workflow creates and reviews .agent.md files before lint records proof.
- `reviewer identity`: A reviewer identity records the agent and model that completed a review. For example, `codex:gpt-5.5` is a reviewer identity.
- `$run-tdd-linter`: The $run-tdd-linter skill runs the repository's agentic TDD review workflow. For example, a coding agent invokes it after installation.
- `pre-commit review workflow`: The pre-commit review workflow orders three stages: run `agentic-tdd-linter create-agent-md` to create `.agent.md` files, complete their scorecards, and run reviewer-authenticated lint to persist proof.
- `CI/CD validation workflow`: The CI/CD validation workflow validates committed tests and manifest proof without creating scorecards. For example, GitHub Actions runs lint after changes are committed.
"""

from __future__ import annotations

import unittest
from pathlib import Path


class ReviewDocumentationTests(unittest.TestCase):
    def test_readme_names_pre_commit_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README.md to include a level-three `pre-commit review workflow` heading.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README.md contents contain `### Pre-commit review workflow`.

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
        `test_review_documentation` requires README.md to include a level-three `CI/CD validation workflow` heading.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README.md contents contain `### CI/CD validation workflow`.

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

    def test_readme_directs_tdd_linter_skill(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README.md installation guidance to instruct users to ask the coding agent to run the installed `$run-tdd-linter` skill.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README.md installation commands instruct users to ask the coding agent to run `$run-tdd-linter`.

        Similar Coverage:
        - Scenario Difference: `test_review_documentation.py::test_readme_shows_review_workflow`
          Explanation: The current test verifies the installation guidance delegates review to the installed skill. The named test verifies the reference documentation retains the ordered manual pre-commit workflow; both exercise README review guidance through materially different entry points.
        """

        repo_root = Path(__file__).resolve().parents[2]
        readme = (repo_root / "README.md").read_text(encoding="utf-8")
        installation_guide = readme.split("## Add It To Your Project", 1)[1].split(
            "## Install It On GitHub Actions On Your Project", 1
        )[0]

        expected_instruction = (
            "Then ask your coding agent:\\n\\n"
            "Run the \\`\\$run-tdd-linter\\` skill."
        )
        self.assertIn(expected_instruction, installation_guide)

    def test_readme_shows_review_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_review_documentation` requires README.md reference guidance to describe the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The Pre-commit review workflow section contains `agentic-tdd-linter create-agent-md` before `Complete every generated scorecard`.
        The section contains `Complete every generated scorecard` before `lint --reviewer <identity>`.

        Similar Coverage:
        - Module Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_review_documentation.py::test_readme_names_pre_commit_workflow`
          Explanation: The current test verifies `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint. The named test verifies `test_review_documentation` requires README to include a level-three `pre-commit review workflow` heading; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_review_documentation.py::test_readme_directs_tdd_linter_skill`
          Explanation: The current test verifies the reference guidance retains the ordered manual pre-commit workflow. The named test verifies the installation guidance delegates review to the installed skill; both use happy path, but exercise README review guidance through materially different entry points.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide = (repo_root / "README.md").read_text(encoding="utf-8")
        pre_commit_guide = guide.split("### Pre-commit review workflow", 1)[1].split(
            "### CI/CD validation workflow", 1
        )[0]
        step_markers = (
            "agentic-tdd-linter create-agent-md",
            "Complete every generated scorecard",
            "lint --reviewer <identity>",
        )
        step_positions = tuple(pre_commit_guide.index(marker) for marker in step_markers)

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

if __name__ == "__main__":
    unittest.main()
