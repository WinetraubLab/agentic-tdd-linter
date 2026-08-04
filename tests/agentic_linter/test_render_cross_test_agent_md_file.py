"""Tests in this file validate `render_cross_test_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/render_cross_test_agent_md_file.py`.
`render_cross_test_agent_md_file` is responsible for creating an isolated cross-test `.agent.md` and determining whether that packet remains valid.

Terms:
- `cross-test packet`: A docstring-only review of relationships among tests.
- `pair classification`: An unordered pair's requirement overlap and, when applicable, difference kind.
- `Similar Coverage`: Docstring entries naming an overlapping test, difference kind, and explanation.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_tdd_linter.agentic_linter.render_cross_test_agent_md_file import (
    _build_cross_test_review_scope,
    cross_test_agent_md_file_is_stale,
    render_cross_test_agent_md_file,
)


class CrossTestAgentMarkdownTests(unittest.TestCase):
    def test_deduplicates_cross_test_paths(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` creates `cross-test packet` containing one docstring entry for every unique selected path.
        Specialized usage: Selected paths contain one duplicate path instead of only unique paths, so `render_cross_test_agent_md_file` emits one docstring entry for the duplicated path.

        Verification Method: verify public function output

        Verification Detail:
        The packet's `## Test Docstrings` section contains path `tests/test_alpha.py` once.
        The packet's `## Test Docstrings` section contains path `tests/test_beta.py` once.

        Similar Coverage:
        - Scenario Difference: `test_render_agent_md_file.py::test_creates_pending_packet`
          Explanation: The current test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing one docstring entry for every unique selected path. The named test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_embeds_docstrings_without_test_implementation`
          Explanation: The current test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing one docstring entry for every unique selected path. The named test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing each test identifier and docstring without its implementation; both use happy path, but exercise materially different scenarios.
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
            docstring_section = artifact_text.partition(
                "\n## Test Docstrings\n"
            )[2]
            docstring_section = docstring_section.partition(
                "\n## Requirement Pair Classifications\n"
            )[0]

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
        The packet contains exactly three `Replace with classification evidence.` rows.
        The packet contains the alpha-beta, alpha-gamma, and beta-gamma pairs.

        Similar Coverage:
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_completed_classification_remains_valid`
          Explanation: The current test verifies `render_cross_test_agent_md_file` creates one `pair classification` row for every unordered test pair. The named test verifies `render_cross_test_agent_md_file` treats a completed `pair classification` as still valid when selected test files remain unchanged; both use happy path, but exercise materially different scenarios.
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
            )[2]

        self.assertEqual(
            3,
            pair_section.count("Replace with classification evidence."),
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

    def test_completed_classification_remains_fresh(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` doesn't regenerate a completed `cross-test packet` when reviewed test files are unchanged.
        Specialized usage: When the `cross-test packet` contains a completed `pair classification` and none of the reviewed test files changed, `render_cross_test_agent_md_file` keeps the existing packet instead of replacing it with a pending review.

        Verification Method: verify public function output

        Verification Detail:
        The `cross-test packet` contains a completed `pair classification`.
        `cross_test_agent_md_file_is_stale` returns false for unchanged selected test files.

        Similar Coverage:
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_lists_each_pair_once`
          Explanation: The current test verifies `render_cross_test_agent_md_file` accepts a completed `pair classification` as fresh when selected test files remain unchanged. The named test verifies `render_cross_test_agent_md_file` creates one `pair classification` row for every unordered test pair; both use happy path, but exercise materially different scenarios.
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
                "| pending | pending | Replace with classification evidence. |",
                (
                    "| yes | Module Difference | Both requirements use the "
                    "same formulation for different modules. |"
                ),
            )
            artifact.write_text(completed_text, encoding="utf-8")

            is_stale = cross_test_agent_md_file_is_stale(test_files, root)

        self.assertFalse(is_stale)

    def test_instructions_limit_review_to_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` constrains `cross-test packet` context to the packet and listed test docstrings.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains `Review context is limited to this packet and the listed test docstrings.`

        Similar Coverage:
        - Module Difference: `test_render_agent_md_file.py::test_includes_review_isolation_instructions`
          Explanation: The current test verifies `render_cross_test_agent_md_file` constrains `cross-test packet` context to the packet and listed test docstrings. The named test verifies `render_agent_md_file` constrains `single-test packet` review context to the packet itself; both exercise materially the same scenario through different named modules or contract subjects.
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
            "Review context is limited to this packet and the listed test docstrings.",
            artifact_text,
        )

    def test_embeds_docstrings_without_test_implementation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` creates `cross-test packet` containing each test identifier and docstring without its implementation.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The packet contains `tests/test_alpha.py::test_example`.
        The packet contains the complete selected test docstring.
        The packet excludes the implementation marker `implementation is absent`.

        Similar Coverage:
        - Module Difference: `test_render_agent_md_file.py::test_creates_pending_packet`
          Explanation: The current test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing each test identifier and docstring without its implementation. The named test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_deduplicates_cross_test_paths`
          Explanation: The current test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing each test identifier and docstring without its implementation. The named test verifies `render_cross_test_agent_md_file` creates `cross-test packet` containing one docstring entry for every unique selected path; both use happy path, but exercise materially different scenarios.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            expected_docstring = (
                "Test Path: happy path\n\n"
                "Requirement Tested:\n"
                "The example returns a value.\n"
                "Standard usage: The scenario demonstrates baseline behavior.\n\n"
                "Verification Method: verify public function output\n\n"
                "Verification Detail:\n"
                "The returned value is present."
            )
            test_file.write_text(
                'def test_example() -> None:\n'
                '    """'
                + expected_docstring.replace("\n", "\n    ")
                + '\n'
                '    """\n\n'
                '    assert "implementation is absent"\n',
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn("tests/test_alpha.py::test_example", artifact_text)
        self.assertIn(expected_docstring, artifact_text)
        self.assertNotIn("implementation is absent", artifact_text)

    def test_uses_one_reviewer_per_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` requires one fresh isolated reviewer to complete every `pair classification` in a `cross-test packet`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The `cross-test packet` contains `Use one fresh isolated reviewer for this Markdown packet.`
        The `cross-test packet` prohibits delegating any listed pair or classification.
        The `cross-test packet` assigns every pair's overlap and kind to that reviewer.

        Similar Coverage:
        - Scenario Difference: `test_render_agent_md_file.py::test_requires_complete_review`
          Explanation: The current test verifies `render_cross_test_agent_md_file` uses the same fresh isolated reviewer for every pair classification in one `cross-test packet`. The named test verifies `render_agent_md_file` requires the reviewer to evaluate every criterion in each `single-test packet`; both use happy path, but exercise materially different scenarios.
        - Module Difference: `test_render_agent_md_file.py::test_requires_fresh_reviewers`
          Explanation: The current test verifies `render_cross_test_agent_md_file` uses the same fresh isolated reviewer for every pair classification in one `cross-test packet`. The named test verifies `render_agent_md_file` requires one fresh isolated reviewer for each `single-test packet`; both exercise materially the same scenario through different named modules or contract subjects.
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
            "Use one fresh isolated reviewer for this Markdown packet.",
            artifact_text,
        )
        self.assertIn(
            "Do not delegate any listed pair or classification to another reviewer.",
            artifact_text,
        )
        self.assertIn(
            "That reviewer shall classify every pair's overlap and kind.",
            artifact_text,
        )

    def test_requires_reciprocal_references(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` generates a `cross-test packet` stating that an overlapping pair provides reciprocal `Similar Coverage` entries with the same `pair classification`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The `cross-test packet` contains the exact sentence `A correctly documented pair provides reciprocal entries with the same classification.`

        Similar Coverage:
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_instructions_show_similar_coverage_format`
          Explanation: The current test verifies `render_cross_test_agent_md_file` generates a `cross-test packet` stating that an overlapping pair provides reciprocal entries with the same difference classification. The named test verifies `render_cross_test_agent_md_file` shows the exact `Similar Coverage` format for every supported difference kind; both use happy path, but exercise materially different scenarios.
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
            "A correctly documented pair provides reciprocal entries with the same "
            "classification.",
            artifact_text,
        )

    def test_instructions_show_similar_coverage_format(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` provides exact `Similar Coverage` formats for Happy/Failure Path Difference, Scenario Difference, and Module Difference with an Explanation placeholder.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The `cross-test packet` contains ``Happy/Failure Path Difference: `<file.py>::<test_name>```.
        The `cross-test packet` contains ``Scenario Difference: `<file.py>::<test_name>```.
        The `cross-test packet` contains ``Module Difference: `<file.py>::<test_name>```.
        The `cross-test packet` contains `Explanation: <specific difference between the two tests>`.

        Similar Coverage:
        - Scenario Difference: `test_render_cross_test_agent_md_file.py::test_requires_reciprocal_references`
          Explanation: The current test verifies `render_cross_test_agent_md_file` shows the exact `Similar Coverage` format for every supported difference kind. The named test verifies `render_cross_test_agent_md_file` generates a `cross-test packet` stating that an overlapping pair provides reciprocal entries with the same difference classification; both use happy path, but exercise materially different scenarios.
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
            "Happy/Failure Path Difference: `<file.py>::<test_name>`",
            artifact_text,
        )
        self.assertIn(
            "Scenario Difference: `<file.py>::<test_name>`",
            artifact_text,
        )
        self.assertIn(
            "Module Difference: `<file.py>::<test_name>`",
            artifact_text,
        )
        self.assertIn(
            "Explanation: <specific difference between the two tests>",
            artifact_text,
        )

if __name__ == "__main__":
    unittest.main()
