"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/run_conventional_linter.py`.
`conventional_linter` is responsible for enforcing test documentation, naming, and visual-inspection conventions.

Terms:
- `Test Path`: Test Path is the structured field naming a test's scenario category. For example, Test Path can contain happy path.
- `Requirement Tested`: Requirement Tested is the structured field stating behavior and scenario. For example, it says that a parser accepts valid text.
- `Verification Method`: Verification Method is the structured field naming the observation approach. For example, it can say verify public function output.
- `Verification Detail`: Verification Detail is the structured field stating exact evidence. For example, it says that `_add_values` output equals three.
- `Inspection Instructions`: Inspection Instructions is the structured field that authorizes source inspection when linter issues cannot describe visual evidence. For example, it can name a specific module to inspect.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentic_tdd_linter.conventional_linter.run_conventional_linter import (
    run_conventional_linter,
)
from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)

from tests.conventional_linter.test_harness.docstring_structure import (
    _lint_docstring_source,
    _lint_typescript_docstring_source,
)


class DocstringStructureTests(unittest.TestCase):
    def test_reports_missing_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_docstring when a test lacks a test docstring.
        Specialized usage: The extracted record contains an empty test docstring instead of a populated docstring, so conventional linter emits missing_docstring.

        Verification Method: verify public function output

        Verification Detail:
        `conventional_linter` output contains `missing_docstring`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_method`
          Explanation: The current test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring. The named test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_test_path`
          Explanation: The current test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring. The named test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        """

        test = ExtractedTestRecord(
            path=Path("tests/test_sample.py"),
            name="test_sample",
            line=1,
            node=None,
            docstring="",
            source="def test_sample(): pass",
        )
        rules = {issue.rule for issue in run_conventional_linter(test)}

        self.assertIn("missing_docstring", rules)

    def test_reports_missing_test_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`.
        Specialized usage: When a test docstring omits `Test Path`, `conventional_linter` emits missing_test_path.

        Verification Method: verify private function output

        Verification Detail:
        The `_lint_docstring_source` rules contain `missing_test_path`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_failure_path`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` accepts `failure path`; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_happy_path`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` accepts `happy path` when parser input succeeds; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_docstring`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_method`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"
                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_test_path", rules)

    def test_reports_empty_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing.
        Specialized usage: When a docstring contains empty `Requirement Tested`, `conventional_linter` emits missing_requirement.

        Verification Method: verify private function output

        Verification Detail:
        When `Requirement Tested` contains nothing, `_lint_docstring_source` output contains `missing_requirement`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_docstring`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_method`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_test_path`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_requirement`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Module Difference: `test_pre_commit_review_workflow.py::test_classic_linter_errors_scenario`
          Explanation: The current test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing. The named test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement; both exercise materially the same scenario through different named modules or contract subjects.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_requirement", rules)

    def test_reports_missing_method(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`.
        Specialized usage: Docstring omits `Verification Method` instead of providing it, so `conventional_linter` emits missing_verification_method.

        Verification Method: verify private function output

        Verification Detail:
        When docstrings omit `Verification Method`, _lint_docstring_source contains `missing_verification_method`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_private_output`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` includes private function output in `supported methods`; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_public_output`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` accepts public function output among `supported methods`; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_visual_inspection`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` accepts a `visual inspection contract`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_classification.py::test_rejects_unsupported_verification_method`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` accepts only `supported methods` as Verification Method values; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_docstring`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_test_path`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_verification_method", rules)

    def test_reports_empty_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing.
        Specialized usage: When a docstring has an empty `Verification Detail`, `conventional_linter` emits missing_verification_detail.

        Verification Method: verify private function output

        Verification Detail:
        When `Verification Detail` contains nothing, `_lint_docstring_source` output contains `missing_verification_detail`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_docstring`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_method`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_test_path`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_verification_detail", rules)

    def test_reports_missing_inspection_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection.
        Specialized usage: When `Verification Detail` lacks an image path for visual inspection, `conventional_linter` emits missing_visual_inspection_artifact.

        Verification Method: verify private function output

        Verification Detail:
        `_lint_docstring_source` output contains `missing_visual_inspection_artifact`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_visual_inspection`
          Explanation: The current test verifies `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection. The named test verifies `conventional_linter` accepts a `visual inspection contract`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection. The named test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_visual_helper`
          Explanation: The current test verifies `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection. The named test verifies `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes an image for review.

                Inspection Instructions:
                Confirm the image shows the expected addition result.
                \"\"\"

                write_visual_inspection_artifact()
            """
        )

        self.assertIn("missing_visual_inspection_artifact", rules)

    def test_reports_missing_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`.
        Specialized usage: The fixture docstring declares visual inspection by user in its `Verification Method` but omits `Inspection Instructions`, so `conventional_linter` emits missing_inspection_instructions.

        Verification Method: verify private function output

        Verification Detail:
        When the fixture docstring declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`, `_lint_docstring_source` output contains `missing_inspection_instructions`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_visual_inspection`
          Explanation: The current test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`. The named test verifies `conventional_linter` accepts a `visual inspection contract`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_inspection_artifact`
          Explanation: The current test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`. The named test verifies `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_visual_helper`
          Explanation: The current test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`. The named test verifies `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`. The named test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes tests/artifacts/addition.png.
                \"\"\"

                write_visual_inspection_artifact()
            """
        )

        self.assertIn("missing_inspection_instructions", rules)

    def test_reports_missing_visual_helper(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact.
        Specialized usage: When a test declares visual inspection by user but lacks a write_visual_inspection_artifact call, `conventional_linter` emits missing_visual_inspection_helper.

        Verification Method: verify private function output

        Verification Detail:
        When a test declares visual inspection by user but omits a `write_visual_inspection_artifact` call, `_lint_docstring_source` output contains `missing_visual_inspection_helper`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_classification.py::test_accepts_visual_inspection`
          Explanation: The current test verifies `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact. The named test verifies `conventional_linter` accepts a `visual inspection contract`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_inspection_artifact`
          Explanation: The current test verifies `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact. The named test verifies `conventional_linter` emits missing_visual_inspection_artifact when `Verification Detail` lacks an image path for visual inspection; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` requires tests whose `Verification Method` is visual inspection by user to invoke write_visual_inspection_artifact. The named test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes tests/artifacts/addition.png.

                Inspection Instructions:
                Confirm the image shows the expected addition result.
                \"\"\"

                pass
            """
        )

        self.assertIn("missing_visual_inspection_helper", rules)

    def test_reports_long_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` prohibits test names longer than five words in every supported language.
        Specialized usage: For Python naming, a test name exceeds five words instead of staying within five, so `conventional_linter` emits test_name_too_long.

        Verification Method: verify private function output

        Verification Detail:
        The synthetic Python test name contains seven words.
        `_lint_docstring_source` output contains `test_name_too_long`.

        Similar Coverage:
        - Scenario Difference: `test_docstring_structure.py::test_reports_long_typescript_test_name`
          Explanation: The current test verifies `conventional_linter` prohibits test names longer than five words in every supported language. The named test verifies `conventional_linter` prohibits TypeScript labels when they exceed five words; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_two_positive_integer_values_correctly() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("test_name_too_long", rules)

    def test_reports_long_typescript_test_name(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` prohibits TypeScript labels when they exceed five words.
        Specialized usage: When a TypeScript label contains six or more words, `conventional_linter` emits test_name_too_long.

        Verification Method: verify private function output

        Verification Detail:
        `_lint_typescript_docstring_source` output contains `test_name_too_long` for a six-word TypeScript label.

        Similar Coverage:
        - Scenario Difference: `test_docstring_structure.py::test_reports_long_test_name`
          Explanation: The current test verifies `conventional_linter` prohibits TypeScript labels when they exceed five words. The named test verifies `conventional_linter` prohibits test names longer than five words in every supported language; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_typescript_docstring_source(
            """
            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * Addition returns the expected sum.
             * This rule applies to positive integers.
             *
             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Addition output equals two.
             */
            test("adds two positive integer values correctly", () => {
              assert.equal(1 + 1, 2);
            });
            """
        )

        self.assertIn("test_name_too_long", rules)

    def test_reports_same_line_requirement(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline.
        Specialized usage: Docstring locates `Requirement Tested` inline instead of on a separate line, so conventional linter emits invalid_requirement_format.

        Verification Method: verify private function output

        Verification Detail:
        When requirement text remains inline, _lint_docstring_source contains `invalid_requirement_format`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline. The named test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline. The named test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_typescript_fields_need_blank_lines`
          Explanation: The current test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline. The named test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested: addition returns the expected sum.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_requirement_format", rules)

    def test_reports_same_line_verification_detail(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline.
        Specialized usage: Docstring locates `Verification Detail` inline instead of on a separate line, so conventional linter emits invalid_verification_detail_format.

        Verification Method: verify private function output

        Verification Detail:
        When detail text remains inline, _lint_docstring_source contains `invalid_verification_detail_format`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline. The named test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_requirement`
          Explanation: The current test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline. The named test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_docstring_structure.py::test_typescript_fields_need_blank_lines`
          Explanation: The current test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline. The named test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail: Addition output equals expected numeric total.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertIn("invalid_verification_detail_format", rules)

    def test_reports_same_line_inspection_instructions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline.
        Specialized usage: Docstring locates `Inspection Instructions` inline instead of on a separate line, so conventional linter emits invalid_inspection_instructions_format.

        Verification Method: verify private function output

        Verification Detail:
        When instructions stay inline, _lint_docstring_source contains `invalid_inspection_instructions_format`.

        Similar Coverage:
        - Scenario Difference: `test_docstring_structure.py::test_reports_missing_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline. The named test verifies `conventional_linter` emits missing_inspection_instructions when a test declares visual inspection by user in its `Verification Method` and omits `Inspection Instructions`; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_requirement`
          Explanation: The current test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline. The named test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline. The named test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_typescript_fields_need_blank_lines`
          Explanation: The current test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline. The named test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent; both use failure path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def write_visual_inspection_artifact() -> None:
                return None


            def test_draws_result_image() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                The renderer writes images.

                Verification Method: visual inspection by user

                Verification Detail:
                The renderer writes tests/artifacts/addition.png.

                Inspection Instructions: Confirm the image shows the expected addition result.
                \"\"\"

                write_visual_inspection_artifact()
            """
        )

        self.assertIn("invalid_inspection_instructions_format", rules)

    def test_typescript_fields_need_blank_lines(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits invalid_field_spacing when a TypeScript test doc comment omits blank-line separators between structured documentation fields.
        Specialized usage: When a TypeScript test doc comment places structured documentation fields next to each other without blank-line separators, `conventional_linter` emits invalid_field_spacing.

        Verification Method: verify private function output

        Verification Detail:
        The `conventional_linter` rule set contains `invalid_field_spacing`.

        Similar Coverage:
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_inspection_instructions`
          Explanation: The current test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent. The named test verifies `conventional_linter` emits invalid_inspection_instructions_format when docstrings locate `Inspection Instructions` inline; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_requirement`
          Explanation: The current test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent. The named test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_docstring_structure.py::test_reports_same_line_verification_detail`
          Explanation: The current test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent. The named test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; the current test is failure path, while the named test is happy path.
        """

        rules = _lint_typescript_docstring_source(
            """
            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             * Requirement Tested:
             * Local artifact writes survive a primitive round trip.
             * Verification Method: verify public function output
             * Verification Detail:
             * Loaded artifact content equals written artifact content.
             */
            test("local artifact round trip", () => {
              assert.equal(readLocalArtifact(), "saved artifact");
            });
            """
        )

        self.assertIn("invalid_field_spacing", rules)

    def test_python_docstring_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The docstring contains four fields.
        The test contains `Test Path`.
        The test contains `Requirement Tested`.
        The test contains `Verification Method`.
        The test contains `Verification Detail`.
        The `_lint_docstring_source` output rules contain zero issues.

        Similar Coverage:
        - Scenario Difference: `test_classification.py::test_accepts_happy_path`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts `happy path` when parser input succeeds; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_classification.py::test_accepts_public_output`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts public function output among `supported methods`; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_classification.py::test_rejects_unsupported_verification_method`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts only `supported methods` as Verification Method values; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_missing_docstring`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_missing_method`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_missing_test_path`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_same_line_requirement`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_same_line_verification_detail`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_docstring_structure.py::test_typescript_doc_comment_passes`
          Explanation: The current test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; both use happy path, but exercise materially different scenarios.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                Addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Addition output equals expected sum.
                \"\"\"

                assert 1 + 1 == 2
            """
        )

        self.assertEqual(set(), rules)

    def test_typescript_doc_comment_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts TypeScript test docstrings when `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail` contain values and blank lines separate the fields.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        The TypeScript test docstring contains `Test Path`.
        The TypeScript test docstring contains `Requirement Tested`.
        The TypeScript test docstring contains `Verification Method`.
        The TypeScript test docstring contains `Verification Detail`.
        Every TypeScript test docstring field contains a value.
        Blank lines separate the TypeScript test docstring fields.
        `conventional_linter` issues are empty.

        Similar Coverage:
        - Scenario Difference: `test_classification.py::test_accepts_happy_path`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts `happy path` when parser input succeeds; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_classification.py::test_accepts_public_output`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts public function output among `supported methods`; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_classification.py::test_rejects_unsupported_verification_method`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts only `supported methods` as Verification Method values; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_docstring_structure.py::test_python_docstring_passes`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` accepts Python test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_empty_verification_detail`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_verification_detail when `Verification Detail` contains nothing; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_missing_docstring`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_docstring when a test lacks a test docstring; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_missing_method`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_verification_method when docstrings omit `Verification Method`; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_missing_test_path`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits missing_test_path for each test docstring that omits `Test Path`; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_same_line_requirement`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits invalid_requirement_format when docstrings locate `Requirement Tested` inline; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_reports_same_line_verification_detail`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits invalid_verification_detail_format when docstrings locate `Verification Detail` inline; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_docstring_structure.py::test_typescript_fields_need_blank_lines`
          Explanation: The current test verifies `conventional_linter` accepts TypeScript test docstrings when they contain `Test Path`, `Requirement Tested`, `Verification Method`, and `Verification Detail`. The named test verifies `conventional_linter` emits invalid_field_spacing when TypeScript fields are adjacent; the current test is happy path, while the named test is failure path.
        """

        rules = _lint_typescript_docstring_source(
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
            """
        )

        self.assertEqual(set(), rules)


if __name__ == "__main__":
    unittest.main()
