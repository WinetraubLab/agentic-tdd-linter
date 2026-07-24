"""Repository tests verify that review documentation matches its workflow.

Terms:
- `reviewer identity`: A reviewer identity records the agent and model that completed a review. For example, `codex:gpt-5.5` is a reviewer identity.
- `lint arguments`: Lint arguments are exactly `lint`, `--reviewer`, and one reviewer identity in that order. For example, `lint --reviewer codex:gpt-5.5` supplies the lint arguments.
"""

from __future__ import annotations

import shlex
import unittest
from pathlib import Path


class ReviewDocumentationTests(unittest.TestCase):
    def test_readme_includes_reviewer(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        README provides exact `lint arguments`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Parsed arguments equal `lint`, `--reviewer`, and `codex:gpt-5.5` in that order.
        """

        repo_root = Path(__file__).resolve().parents[2]
        reviewer = "codex:gpt-5.5"
        expected_args = ["lint", "--reviewer", reviewer]
        self.assertEqual(_readme_review_command_args(repo_root), expected_args)

    def test_readme_shows_review_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        README presents the local review workflow in this order: create .agent.md files, complete scorecards, and record proof with a reviewer identity.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        README presents these steps in order:
        1. `create-agent-md` creates the scorecards.
        2. Reviewers complete every scorecard.
        3. `lint --reviewer` persists the completed reviews in the manifest.
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
        The GitHub Actions guide instructs CI to validate committed manifest proof against repository tests with 'agentic-tdd-linter lint'.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The guide contains `agentic-tdd-linter lint`.
        The guide declares that GitHub Actions verifies committed proof.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide = (repo_root / "docs" / "workflows" / "github-actions.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("GitHub Actions verifies committed agent-review proof", guide)
        self.assertIn("agentic-tdd-linter lint", guide)

    def test_github_actions_omits_packet_creation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The GitHub Actions workflow omits '.agent.md' creation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The guide excludes `agentic-tdd-linter create-agent-md`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide = (repo_root / "docs" / "workflows" / "github-actions.md").read_text(
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
