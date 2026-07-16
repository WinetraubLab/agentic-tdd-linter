"""Verify Python test extraction.

Terms:
- `extracted Python test`: An extracted Python test is one Python test function represented as source data. For example, extraction represents `test_example` as one extracted Python test.
- `extract_python_tests_from_file`: This public function extracts test records from one Python file. For example, it returns separate records for `test_alpha` and `test_beta`.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentic_tdd_linter.indexing_test_functions.extract_python_tests_from_file import (
    extract_python_tests_from_file,
)


class PythonTestExtractionTests(unittest.TestCase):
    def test_extracts_python_test_names(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extract_python_tests_from_file` retains test names.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Names include `test_alpha` and `test_beta`.
        """

        python_source = textwrap.dedent(
            '''
            """Verify sample extraction.

            Terms:
            - `sample test`: A function selected by the Python extractor.
            """

            def test_alpha() -> None:
                """Alpha documentation."""
                assert True


            def test_beta() -> None:
                """Beta documentation."""
                assert True
            '''
        ).strip() + "\n"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_sample.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(python_source, encoding="utf-8")
            extracted_tests = extract_python_tests_from_file(test_file, repo_root)

        self.assertEqual(["test_alpha", "test_beta"], [test.name for test in extracted_tests])

    def test_extracts_python_test_source(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extract_python_tests_from_file` retains source text.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Source one contains `def test_alpha`.
        Source two contains `def test_beta`.
        """

        python_source = textwrap.dedent(
            '''
            """Verify sample extraction.

            Terms:
            - `sample test`: A function selected by the Python extractor.
            """

            def test_alpha() -> None:
                """Alpha documentation."""
                assert True


            def test_beta() -> None:
                """Beta documentation."""
                assert True
            '''
        ).strip() + "\n"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_sample.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(python_source, encoding="utf-8")
            extracted_tests = extract_python_tests_from_file(test_file, repo_root)

        self.assertIn("def test_alpha", extracted_tests[0].source)
        self.assertIn("def test_beta", extracted_tests[1].source)

    def test_extracts_python_file_glossary(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extract_python_tests_from_file` retains file glossaries.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Docstring contains `Terms:\n- `sample test`:`.
        """

        python_source = textwrap.dedent(
            '''
            """Verify sample extraction.

            Terms:
            - `sample test`: A function selected by the Python extractor.
            """

            def test_alpha() -> None:
                """Alpha documentation."""
                assert True


            def test_beta() -> None:
                """Beta documentation."""
                assert True
            '''
        ).strip() + "\n"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_sample.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(python_source, encoding="utf-8")
            extracted_tests = extract_python_tests_from_file(test_file, repo_root)

        self.assertIn("Terms:\n- `sample test`:", extracted_tests[0].file_docstring)

    def test_shares_python_file_docstring(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extract_python_tests_from_file` attaches file docstrings when tests share files.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Comparison confirms equality between records.
        """

        python_source = textwrap.dedent(
            '''
            """Verify sample extraction.

            Terms:
            - `sample test`: A function selected by the Python extractor.
            """

            def test_alpha() -> None:
                """Alpha documentation."""
                assert True


            def test_beta() -> None:
                """Beta documentation."""
                assert True
            '''
        ).strip() + "\n"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_sample.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(python_source, encoding="utf-8")
            extracted_tests = extract_python_tests_from_file(test_file, repo_root)

        self.assertEqual(
            extracted_tests[0].file_docstring,
            extracted_tests[1].file_docstring,
        )

if __name__ == "__main__":
    unittest.main()
