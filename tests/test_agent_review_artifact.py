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
from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_ran_proof import (
    lint_agent_review_artifact,
    source_sha256,
)
from agentic_tdd_linter.agentic_md import write_agentic_md_for_test_file


class AgentReviewArtifactTests(unittest.TestCase):
    def test_accepts_reviewed_pass_artifact(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        When the SHA matches the test file, `Status: pass` is accepted.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the reviewed pass artifact returns an empty issue list.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact = _write_artifact(root, test_file, status="pass")

            issues = lint_agent_review_artifact(test_file, artifact, root)

        self.assertEqual([], issues)

    def test_accepts_default_artifact(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts a pass artifact from `tests/agentic_review_artifacts`.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the default pass artifact returns an empty issue list.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_artifact(
                root,
                test_file,
                status="pass",
                artifact_path=agent_review_artifact_path(test_file, root),
            )

            issues = lint_agent_review_artifact(test_file, repo_root=root)

        self.assertEqual([], issues)

    def test_reports_pending_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Pending artifact emits incomplete-review issue.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `agent_review_not_run` is reported for pending status.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact = _write_artifact(root, test_file, status="pending")

            rules = _issue_rules(lint_agent_review_artifact(test_file, artifact, root))

        self.assertIn("agent_review_not_run", rules)

    def test_reports_unreviewed_generated_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Untouched generated artifact emits incomplete-review issue.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `agent_review_not_run` is reported for the generated pending artifact.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            write_agentic_md_for_test_file(test_file, root)

            rules = _issue_rules(lint_agent_review_artifact(test_file, repo_root=root))

        self.assertIn("agent_review_not_run", rules)

    def test_reports_stale_signature(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Old source SHA emits stale review proof.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `stale_agent_review_artifact` is reported for a mismatched SHA.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact = _write_artifact(root, test_file, status="pass", source_hash="0" * 64)

            rules = _issue_rules(lint_agent_review_artifact(test_file, artifact, root))

        self.assertIn("stale_agent_review_artifact", rules)

    def test_reports_review_issue(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Fail artifact emits agent review issue.

        Verification Method: verify public function output

        Verification Detail:
        by asserting `agent_review_failed` is reported for failed review status.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact = _write_artifact(root, test_file, status="fail")

            rules = _issue_rules(lint_agent_review_artifact(test_file, artifact, root))

        self.assertIn("agent_review_failed", rules)

def _write_test_file(root: Path) -> Path:
    test_file = root / "test_sample.py"
    test_file.write_text(
        textwrap.dedent(
            """
            def test_adds_values() -> None:
                assert 1 + 1 == 2
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return test_file


def _write_artifact(
    root: Path,
    test_file: Path,
    *,
    status: str,
    source_hash: str | None = None,
    artifact_path: Path | None = None,
) -> Path:
    artifact = artifact_path if artifact_path is not None else root / "test_sample.agent.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    review_hash = source_hash if source_hash is not None else source_sha256(test_file)
    artifact.write_text(
        textwrap.dedent(
            f"""
            # Agentic Test Docstring Review

            Test file: `test_sample.py`
            Source SHA256: `{review_hash}`

            ## Agent Review Result

            Status: {status}
            Notes:
            - test_adds_values: requirement is specific.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return artifact


def _write_reviewed_project(root: Path) -> Path:
    test_file = root / "tests" / "test_sample.py"
    test_file.parent.mkdir()
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

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(["check", "--all", "--repo-root", str(root)])
    artifact_path = agent_review_artifact_path(test_file, root)
    artifact_text = artifact_path.read_text(encoding="utf-8")
    artifact_text = artifact_text.replace("Status: pending", "Status: pass", 1)
    artifact_text = artifact_text.replace(
        "- Replace this line with the agent review result.",
        "- test_adds_values passes review.",
        1,
    )
    artifact_path.write_text(artifact_text, encoding="utf-8")
    return test_file


def _replace_requirement(test_file: Path, requirement: str) -> None:
    text = test_file.read_text(encoding="utf-8")
    text = text.replace(
        "addition returns the expected sum for two positive integers.",
        requirement,
        1,
    )
    test_file.write_text(text, encoding="utf-8")


def _issue_rules(issues: list[object]) -> set[str]:
    return {issue.rule for issue in issues}


if __name__ == "__main__":
    unittest.main()
