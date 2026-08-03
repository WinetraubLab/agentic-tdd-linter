"""Tests in this file validate `render_cross_test_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/render_cross_test_agent_md_file.py`.
`render_cross_test_agent_md_file` is responsible for creating an isolated cross-test `.agent.md` that documents test-coverage relationships.

Terms:
- `renderer`: The renderer creates a cross-test review packet from selected paths. For example, it writes one packet for two test files.
- `cross-test packet`: A cross-test packet contains review context for relationships among tests. For example, it lists test files and Similar Coverage instructions.
- `relationship fields`: Relationship fields encode higher references, lower references, and classified justifications. For example, one pair names both test levels and its coverage difference.
- `coverage reference formats`: Coverage reference formats are ``Higher Level Test: `<file.py>::<test_name>```, ``Lower Level Test: `<file.py>::<test_name>```, and `Justification: <classification> — <specific coverage difference>`. For example, cross-test instructions display all three formats.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_tdd_linter.agentic_linter.render_cross_test_agent_md_file import (
    _build_cross_test_review_scope,
    render_cross_test_agent_md_file,
)


class CrossTestAgentMarkdownTests(unittest.TestCase):
    def test_deduplicates_cross_test_paths(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` creates `cross-test packet` containing every unique selected path exactly once.
        Specialized usage: Selected paths contain one duplicate path instead of only unique paths, so `render_cross_test_agent_md_file` emits the duplicated path once.

        Verification Method: verify public function output

        Verification Detail:
        `cross-test packet` contains path `tests/test_alpha.py` once.
        `cross-test packet` contains path `tests/test_beta.py` once.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_example():\n    assert True\n"
            first = root / "tests" / "test_alpha.py"
            second = root / "tests" / "test_beta.py"
            first.parent.mkdir(parents=True)
            first.write_text(source, encoding="utf-8")
            second.write_text(source, encoding="utf-8")

            artifact = render_cross_test_agent_md_file(
                [first, second, first],
                root,
            )
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertEqual(1, docstring_section.count("tests/test_alpha.py"))
        self.assertEqual(1, docstring_section.count("tests/test_beta.py"))

    def test_lists_each_pair_once(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` creates one `pair classification` row for every unordered test pair.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Harness supplies three test files containing one test each.
        The packet contains exactly three `Replace with overlap evidence.` rows.
        The packet contains the alpha-beta, alpha-gamma, and beta-gamma pairs.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_files = []
            for name in ("alpha", "beta", "gamma"):
                test_file = root / "tests" / f"test_{name}.py"
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text(
                    "def test_example():\n    assert True\n",
                    encoding="utf-8",
                )
                test_files.append(test_file)

            artifact = render_cross_test_agent_md_file(test_files, root)
            artifact_text = artifact.read_text(encoding="utf-8")
            pair_section = artifact_text.partition(
                "\n## Requirement Pair Classifications\n"
            )[2].partition("\n## Review Scorecard\n")[0]

        self.assertEqual(
            3,
            pair_section.count("Replace with overlap evidence."),
        )
        self.assertIn(
            "| `tests/test_alpha.py::test_example` | "
            "`tests/test_beta.py::test_example` |",
            pair_section,
        )
        self.assertIn(
            "| `tests/test_alpha.py::test_example` | "
            "`tests/test_gamma.py::test_example` |",
            pair_section,
        )
        self.assertIn(
            "| `tests/test_beta.py::test_example` | "
            "`tests/test_gamma.py::test_example` |",
            pair_section,
        )

    def test_overlap_result_preserves_freshness(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` preserves a completed `pair classification` when deciding whether packet inputs are stale.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Harness renders a packet for two test files.
        Harness replaces the pending pair classification with yes and review evidence.
        `cross_test_agent_md_file_is_stale` returns false.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_files = []
            for name in ("alpha", "beta"):
                test_file = root / "tests" / f"test_{name}.py"
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text(
                    "def test_example():\n    assert True\n",
                    encoding="utf-8",
                )
                test_files.append(test_file)

            artifact = render_cross_test_agent_md_file(test_files, root)
            completed_text = artifact.read_text(encoding="utf-8").replace(
                "| pending | Replace with overlap evidence. |",
                "| yes | Both requirements use the same formulation. |",
            )
            artifact.write_text(completed_text, encoding="utf-8")

            is_stale = cross_test_agent_md_file_is_stale(test_files, root)

        self.assertFalse(is_stale)

    def test_instructions_limit_review_to_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` constrains `cross-test packet` context to the packet and listed files.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `Review context is limited to this packet and the listed test files.`

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_includes_review_isolation_instructions`
          Justification: Comparable coverage — The lower test constrains single-test review context. The current test applies the same isolation policy to cross-test review context.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn(
            "Review context is limited to this packet and the listed test files.",
            artifact_text,
        )

    def test_requires_overlap_explanations(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` requires `relationship fields` to provide a coverage classification and a specific coverage-difference explanation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `Justification: <classification> — <specific coverage difference>`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn(
            "Justification: <classification> — <specific coverage difference>",
            artifact_text,
        )

    def test_requires_reciprocal_references(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` requires `relationship fields` in each higher-level/lower-level pair to make each test reference the other.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `A passing pair provides reciprocal references and justifications in both tests.`
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn(
            "A passing pair provides reciprocal references",
            artifact_text,
        )

    def test_instructions_show_similar_coverage_format(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` provides exact `coverage reference formats` in `relationship fields`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Packet contains ``Higher Level Test: `<file.py>::<test_name>```.
        Packet contains ``Lower Level Test: `<file.py>::<test_name>```.
        Packet contains `Justification: <classification> — <specific coverage difference>`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                "def test_example():\n    assert True\n",
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn("Higher Level Test: `<file.py>::<test_name>`", artifact_text)
        self.assertIn("Lower Level Test: `<file.py>::<test_name>`", artifact_text)
        self.assertIn(
            "Justification: <classification> — <specific coverage difference>",
            artifact_text,
        )


if __name__ == "__main__":
    unittest.main()
