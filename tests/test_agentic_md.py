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
        Generated `.agent.md` files for agent review include numbered guidance before tests.
        Guidance tells agents how to evaluate each test requirement.

        Verification Method: verify public function output

        Verification Detail:
        Instruction section precedes listed tests.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        instruction_start = markdown.index("## Review Instructions")
        tests_start = markdown.index("## Tests")
        instruction_section = markdown[instruction_start:tests_start]
        numbered_lines = [
            line
            for line in instruction_section.splitlines()
            if line[:1].isdigit() and ". " in line
        ]

        self.assertLess(instruction_start, tests_start)
        self.assertGreaterEqual(len(numbered_lines), 3)

    def test_includes_python_test_names(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files for agent review contain Python test names.
        Python test names tell agents which requirements need review.

        Verification Method: verify public function output

        Verification Detail:
        Generated test names appear in `.agent.md` review file.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("`test_adds_values`", markdown)
        self.assertIn("`test_strips_value`", markdown)
        self.assertNotIn("helper_function", markdown)

    def test_includes_typescript_test_names(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files for agent review contain TypeScript test names.
        TypeScript test names tell agents which requirements need review.

        Verification Method: verify public function output

        Verification Detail:
        Generated test names appear in `.agent.md` review file.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = Path(directory) / "localArtifactRoundTrip.test.ts"
            test_file.write_text(_typescript_sample_source(), encoding="utf-8")
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("`local artifact round trip`", markdown)
        self.assertIn("`local artifact trims value`", markdown)

    def test_includes_python_test_source(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files for agent review include Python test source.
        Python source lets agents compare each requirement with assertions.

        Verification Method: verify public function output

        Verification Detail:
        Generated assertion appears in `.agent.md` source block.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("- Test Source:", markdown)
        self.assertIn("````python", markdown)
        self.assertIn("assert 1 + 1 == 2", markdown)

    def test_includes_typescript_test_source(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files for agent review include TypeScript test source.
        TypeScript source lets agents compare each requirement with assertions.

        Verification Method: verify public function output

        Verification Detail:
        TypeScript assertion appears in `.agent.md` source block.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = Path(directory) / "localArtifactRoundTrip.test.ts"
            test_file.write_text(_typescript_sample_source(), encoding="utf-8")
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("````typescript", markdown)
        self.assertIn("assert.equal(readLocalArtifact(), \"saved artifact\")", markdown)

    def test_includes_sentence_checks(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files for agent review include sentence checks.
        Checks tell agents how to inspect requirement wording.

        Verification Method: verify public function output

        Verification Detail:
        Sentence check names appear in `.agent.md` review file.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        self.assertIn("Sentence Structure Check (Pass/Fail)", markdown)
        self.assertIn("Subject -> Verb -> Object", markdown)
        self.assertIn("main verb", markdown)
        self.assertIn("read as a noun", markdown)
        self.assertIn("Condition Check (Pass/Fail)", markdown)
        self.assertIn("Relative Clause Check (Pass/Fail)", markdown)
        self.assertIn("referent information", markdown)
        self.assertIn("Concept Check (Pass/Fail)", markdown)

    def test_includes_requirement_example_instruction(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files tell agents to require a second requirement row.
        Second-row examples help agents reject generic requirements.

        Verification Method: verify public function output

        Verification Detail:
        Instruction section names `Requirement Tested`, scenario, and concrete example.
        """

        with tempfile.TemporaryDirectory() as directory:
            test_file = _write_test_file(Path(directory), _sample_source())
            markdown = agentic_md_for_test_file(test_file)

        instruction_start = markdown.index("## Review Instructions")
        tests_start = markdown.index("## Tests")
        instruction_section = markdown[instruction_start:tests_start]

        self.assertIn(
            "The first `Requirement Tested` row should state the use case or scenario.",
            instruction_section,
        )
        self.assertIn(
            "The second row should give a concrete example.",
            instruction_section,
        )

    def test_marks_missing_docstring(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Generated `.agent.md` files for agent review show missing-docstring markers.
        Markers tell agents which tests lack review text.

        Verification Method: verify public function output

        Verification Detail:
        Missing-docstring marker appears for undocumented test.
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
        Generated `.agent.md` files for agent review put `Source SHA256` on the final line.
        Source hash lets the linter detect changed tests after review.

        Verification Method: verify public function output

        Verification Detail:
        Final line contains test file SHA.
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
        `write_agentic_md_for_test_file` writes pending `.agent.md` files for agent review.
        Pending status tells agents the file still needs review.

        Verification Method: verify public function output

        Verification Detail:
        Generated `.agent.md` file has pending status.
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


def _typescript_sample_source() -> str:
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

        /**
         * Test Path: happy path
         *
         * Requirement Tested:
         * Local artifact trims surrounding whitespace.
         *
         * Verification Method: verify public function output
         *
         * Verification Detail:
         * Loaded artifact content equals trimmed artifact content.
         */
        test("local artifact trims value", () => {
          assert.equal(readLocalArtifact().trim(), "saved artifact");
        });
        """
    ).strip() + "\n"

if __name__ == "__main__":
    unittest.main()
