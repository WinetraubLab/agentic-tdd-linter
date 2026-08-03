"""Tests in this file validate `render_cross_test_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/render_cross_test_agent_md_file.py`.
`render_cross_test_agent_md_file` is responsible for creating an isolated cross-test `.agent.md` that documents test-coverage relationships.

Terms:
- `cross-test packet`: A cross-test packet contains review context for relationships among tests. For example, it lists test files and Similar Coverage instructions.
- `relationship fields`: Relationship fields encode higher references, lower references, and classified justifications. For example, one pair names both test levels and its coverage difference.
- `coverage reference formats`: Coverage reference formats are ``Higher Level Test: `<file.py>::<test_name>``` and ``Lower Level Test: `<file.py>::<test_name>```. For example, cross-test instructions display both formats.
- `Similar Coverage`: Similar Coverage is the test-docstring section that records cross-level relationships. For example, each related test names its counterpart and justifies the coverage difference.
- `pair classification`: A pair classification stores whether two Requirement Tested descriptions overlap. For example, identical wording for different modules is classified yes.
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

    def test_overlap_result_preserves_freshness(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` preserves a completed `pair classification` when deciding whether packet inputs are stale.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Harness renders a packet for two test files.
        Harness replaces the pending pair classification with yes, Module Difference, and review evidence.
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
        - Lower Level Test: `test_render_agent_md_file.py::test_includes_review_isolation_instructions`
          Justification: Deeper coverage — The lower test explicitly prohibits inspecting repository files, manifests, and outer unit tests. The current test limits cross-test review to its packet and listed test docstrings.
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
        The packet contains `Requirement Tested:` from the test docstring.
        The packet excludes the implementation marker `implementation is absent`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_alpha.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                'def test_example() -> None:\n'
                '    """Test Path: happy path\n\n'
                '    Requirement Tested:\n'
                '    The example returns a value.\n'
                '    Standard usage: The scenario demonstrates baseline behavior.\n\n'
                '    Verification Method: verify public function output\n\n'
                '    Verification Detail:\n'
                '    The returned value is present.\n'
                '    """\n\n'
                '    assert "implementation is absent"\n',
                encoding="utf-8",
            )

            artifact = render_cross_test_agent_md_file([test_file], root)
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertIn("tests/test_alpha.py::test_example", artifact_text)
        self.assertIn("Requirement Tested:", artifact_text)
        self.assertNotIn("implementation is absent", artifact_text)

    def test_uses_one_reviewer_per_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` uses the same fresh isolated reviewer for every pair classification in one `cross-test packet`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The `cross-test packet` contains `Use one fresh isolated reviewer for this Markdown packet.`
        The packet prohibits delegating listed tests or criteria to another reviewer.
        The packet assigns every criterion and listed test to that reviewer.

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_requires_fresh_reviewers`
          Justification: Deeper coverage — The lower test verifies one fresh reviewer for a single-test packet. The current test additionally verifies that the same reviewer covers every criterion for every listed test in a cross-test packet.
        - Lower Level Test: `test_render_agent_md_file.py::test_requires_complete_review`
          Justification: Deeper coverage — The lower test verifies complete criterion coverage for one single-test packet. The current test additionally verifies complete criterion coverage for every listed test in a cross-test packet.
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

    def test_separates_overlap_from_relationship(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` creates a `cross-test packet` that distinguishes requirement-description overlap from a cross-level behavioral relationship.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The packet classifies the same requirement wording for different modules as overlap.
        The packet states that description-level overlap does not establish the same behavioral contract.
        The packet requires materially overlapping behavior, conditions, and outcomes before identifying a cross-level pair.
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
            "Requirements with the same wording applied to different named "
            "modules or contract subjects still have overlap and shall be "
            "classified `yes`.",
            artifact_text,
        )
        self.assertIn(
            "This is a description-level classification, not a conclusion that "
            "the tests verify the same behavioral contract.",
            artifact_text,
        )
        self.assertIn(
            "A cross-level pair exists only when both docstrings declare materially "
            "overlapping behavior, conditions, and outcomes in `Requirement Tested` "
            "and `Verification Detail`.",
            artifact_text,
        )

    def test_requires_overlap_explanations(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` requires every test in each cross-level pair to justify the relationship in its `Similar Coverage` section.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Cross-test file contains the instruction that every cross-level-pair test shall justify its relationship.
        The instruction encloses `Similar Coverage` in inline-code delimiters.
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
            "Every test in a cross-level pair shall justify the relationship "
            "in `Similar Coverage`",
            artifact_text,
        )

    def test_requires_reciprocal_references(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `render_cross_test_agent_md_file` generates a `cross-test packet` stating that a higher-level/lower-level pair provides reciprocal references when the pair passes.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The `cross-test packet` contains the exact sentence `A passing pair provides reciprocal references`.
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
        Packet contains ``Happy/Failure Path Difference: `<file.py>::<test_name>```.
        Packet contains ``Scenario Difference: `<file.py>::<test_name>```.
        Packet contains ``Module Difference: `<file.py>::<test_name>```.
        Packet contains `Explanation: <specific difference between the two tests>`.
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
