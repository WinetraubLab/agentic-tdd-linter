"""Verify that contributor guides contain required review commands in workflow order.

Terms:
- `reviewer identity`: A reviewer identity records the agent and model that completed a review. For example, `codex:gpt-5.5` is a reviewer identity.
"""

from __future__ import annotations

import shlex
import unittest
from pathlib import Path


class ReviewDocumentationTests(unittest.TestCase):
    def test_readme_lint_example_includes_reviewer_argument(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        README provides a lint example showcasing the `--reviewer` argument and `reviewer identity`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Parsed arguments equal `lint`, `--reviewer`, and `codex:gpt-5.5` in that order.
        """

        repo_root = Path(__file__).resolve().parents[2]
        reviewer = "codex:gpt-5.5"
        expected_args = ["lint", "--reviewer", reviewer]
        self.assertEqual(_readme_review_command_args(repo_root), expected_args)

    def test_guides_show_complete_review_workflow(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        README and the GitHub Actions guide show this workflow: `create-agent-md` creates scorecards, reviewers complete scorecards, and `lint --reviewer` records review proof.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify filesystem state

        Verification Detail:
        README presents these steps in order:
        1. Scorecard creation uses `create-agent-md`.
        2. Review completion updates every scorecard.
        3. Proof recording uses `lint --reviewer`.
        The GitHub Actions guide presents the same ordered steps.
        """

        repo_root = Path(__file__).resolve().parents[2]
        guide_steps = {
            Path("README.md"): (
                "agentic-tdd-linter create-agent-md",
                "Review the generated files",
                "agentic-tdd-linter lint --reviewer codex:gpt-5.5",
            ),
            Path("docs/workflows/github-actions.md"): (
                "agentic-tdd-linter create-agent-md",
                "Review those artifacts",
                "agentic-tdd-linter lint --reviewer codex:gpt-5.5",
            ),
        }
        for guide_path, step_markers in guide_steps.items():
            with self.subTest(guide_path=guide_path):
                guide = (repo_root / guide_path).read_text(encoding="utf-8")
                step_positions = tuple(guide.index(marker) for marker in step_markers)
                self.assertEqual(
                    tuple(sorted(step_positions)),
                    step_positions,
                    f"{guide_path} must document creation, review, and proof recording in order",
                )


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
