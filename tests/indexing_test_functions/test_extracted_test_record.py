"""Tests in this file validate `extracted_test_record` located at `src/agentic_tdd_linter/indexing_test_functions/extracted_test_record.py`.
`extracted_test_record` is responsible for representing language-neutral indexed test data.

Terms:
- `ExtractedTestRecord`: ExtractedTestRecord is the shared data structure for one indexed test. For example, it stores a test's path, name, line, syntax node, documentation, and source without a language discriminator.
- `record fields`: Record fields are path, name, line, syntax node, docstring, source, and a file docstring that defaults to None. For example, a caller supplies all seven fields to an extracted record.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)


class ExtractedTestRecordTests(unittest.TestCase):
    def test_stores_supplied_fields(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extracted_test_record` retains caller-supplied `record fields` in `ExtractedTestRecord`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        `ExtractedTestRecord` exposes path `tests/test_sample.py`.
        `ExtractedTestRecord` exposes name `test_sample`.
        `ExtractedTestRecord` exposes line `1`.
        `ExtractedTestRecord` exposes `None` as its syntax node.
        `ExtractedTestRecord` exposes docstring `Sample documentation.`.
        `ExtractedTestRecord` exposes source `def test_sample(): pass`.
        `ExtractedTestRecord` exposes `Sample file documentation.` as its file docstring.
        """

        expected_fields = (
            Path("tests/test_sample.py"),
            "test_sample",
            1,
            None,
            "Sample documentation.",
            "def test_sample(): pass",
            "Sample file documentation.",
        )
        record = ExtractedTestRecord(
            path=expected_fields[0],
            name=expected_fields[1],
            line=expected_fields[2],
            node=expected_fields[3],
            docstring=expected_fields[4],
            source=expected_fields[5],
            file_docstring=expected_fields[6],
        )
        actual_fields = (
            record.path,
            record.name,
            record.line,
            record.node,
            record.docstring,
            record.source,
            record.file_docstring,
        )

        self.assertEqual(expected_fields, actual_fields)

    def test_defaults_file_docstring(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extracted_test_record` defaults `ExtractedTestRecord` file_docstring to None when callers omit the field.
        Specialized usage: Callers omit file_docstring rather than supplying documentation.

        Verification Method: verify public function output

        Verification Detail:
        `ExtractedTestRecord.file_docstring` equals `None`.
        """

        record = ExtractedTestRecord(
            path=Path("tests/test_sample.py"),
            name="test_sample",
            line=1,
            node=None,
            docstring="Sample documentation.",
            source="def test_sample(): pass",
        )

        self.assertIsNone(record.file_docstring)


if __name__ == "__main__":
    unittest.main()
