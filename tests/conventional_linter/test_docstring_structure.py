"""Verify structured test-docstring rules.

Terms:
- `Test Path`: Test Path is the structured field naming a test's scenario category. For example, Test Path can contain happy path.
- `Requirement Tested`: Requirement Tested is the structured field stating behavior and scenario. For example, it says that a parser accepts valid text.
- `Verification Method`: Verification Method is the structured field naming the observation approach. For example, it can say verify public function output.
- `Verification Detail`: Verification Detail is the structured field stating exact evidence. For example, it says that the result equals three.
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
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)

from tests.conventional_linter.docstring_structure import (
    _lint_docstring_source,
    _lint_typescript_docstring_source,
)


class DocstringStructureTests(unittest.TestCase):
    def test_reports_missing_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        When tests omit docstrings, the linter emits issues.
        Specialized usage: For omission validation, docstring input becomes absent (instead of present).

        Verification Method: verify private function output

        Verification Detail:
        When tests have no docstrings, _lint_docstring_source includes `missing_docstring`.
        """

        rules = _lint_docstring_source(
            """
            def test_adds_values() -> None:
                assert 1 + 1 == 2
            """
        )

        self.assertIn("missing_docstring", rules)
