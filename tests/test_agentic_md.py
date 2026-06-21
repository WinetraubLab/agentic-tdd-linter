from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_ran_proof import source_sha256
from agentic_tdd_linter.agentic_md import agentic_md_for_test_file, write_agentic_md_for_test_file


class AgenticMarkdownTests(unittest.TestCase):
    def test_includes_review_instructions(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` includes generic requirement, jargon, assertion, and level checks.

        Verification Method: verify public function output

        Verification Detail:
        Markdown includes each checked heading.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("Notify Generic Requirement", markdown)
        self.assertIn("Notify Convoluted Wording", markdown)
        self.assertIn("test-specific jargon", markdown)
        self.assertIn("backticked", markdown)
        self.assertIn("Review markdown", markdown)
        self.assertIn("agent_review_artifact", markdown)
        self.assertIn("Focus on What is Being Verified, Not How", markdown)
        self.assertIn("behavior level", markdown)
        self.assertIn("exact sample assertions", markdown)
        self.assertIn("behavior-level evidence", markdown)
        self.assertIn("Assertion Purpose Check", markdown)
        self.assertIn("Keep Assertions Self-Contained", markdown)
        self.assertIn("requirement=", markdown)
        self.assertIn("Test Level Redundancy Check", markdown)

    def test_includes_each_test(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` contains test names from requested file.

        Verification Method: verify public function output

        Verification Detail:
        by asserting both generated test names appear in the markdown.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("`test_adds_values`", markdown)
        self.assertIn("`test_strips_value`", markdown)
        self.assertNotIn("helper_function", markdown)

    def test_includes_test_source(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` includes test source.

        Verification Method: verify public function output

        Verification Detail:
        by asserting a generated assertion appears in the markdown source block.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("- Test Source:", markdown)
        self.assertIn("assert 1 + 1 == 2", markdown)

    def test_includes_sentence_checks(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` includes sentence checklist.

        Verification Method: verify public function output

        Verification Detail:
        by asserting each sentence check name appears in the markdown.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("Sentence Structure Check (Pass/Fail)", markdown)
        self.assertIn("Subject -> Verb -> Object", markdown)
        self.assertIn("commonly used as a noun", markdown)
        self.assertIn("reports", markdown)
        self.assertIn("Condition Check (Pass/Fail)", markdown)
        self.assertIn("Relative Clause Check (Pass/Fail)", markdown)
        self.assertIn("whose SHA no longer matches", markdown)
        self.assertIn("Concept Check (Pass/Fail)", markdown)

    def test_marks_missing_docstring(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` includes missing-docstring marker.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the missing-docstring marker appears for an undocumented test.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(
                Path(directory),
                """
                def test_adds_values() -> None:
                    assert 1 + 1 == 2
                """,
            )
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("<missing docstring>", markdown)

    def test_places_signature_at_end(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `Review markdown` stores source SHA at final line.

        Verification Method: verify public function output

        Verification Detail:
        by asserting the final line contains the test file SHA.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            expected_signature = source_sha256(test_file)
            markdown = agentic_md_for_test_file(test_file)

        final_line = markdown.strip().splitlines()[-1]

        self.assertIn(
            "Do not update `Source SHA256` until every review step in this file is complete.",
            markdown,
        )
        self.assertEqual(f"Source SHA256: `{expected_signature}`", final_line)

    def test_writes_default_artifact(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `write_agentic_md_for_test_file` creates pending `agent_review_artifact`.

        Verification Method: verify public function output

        Verification Detail:
        Artifact file has pending status.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_directory = root / "tests"
            test_directory.mkdir()
            test_file = _write_test_file(test_directory, _sample_source())

            artifact_path = write_agentic_md_for_test_file(test_file, root)

            self.assertEqual(agent_review_artifact_path(test_file, root), artifact_path)
            self.assertTrue(artifact_path.is_file())
            self.assertIn("Status: pending", artifact_path.read_text(encoding="utf-8"))


def _write_test_file(directory: Path, source: str) -> Path:
    test_file = directory / "test_sample.py"
    test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
    return test_file


def _sample_source() -> str:
    return """
        def helper_function() -> None:
            return None


        def test_adds_values() -> None:
            \"\"\"Test Path: happy path

            Requirement Tested:
            addition returns the expected sum for two positive integers.

            Verification Method: verify public function output

            Verification Detail:
            by asserting the returned numeric total.
            \"\"\"

            assert 1 + 1 == 2


        def test_strips_value() -> None:
            \"\"\"Test Path: happy path

            Requirement Tested:
            stripping removes surrounding whitespace from text.

            Verification Method: verify public function output

            Verification Detail:
            by asserting the returned stripped string.
            \"\"\"

            assert " value ".strip() == "value"
    """

if __name__ == "__main__":
    unittest.main()
