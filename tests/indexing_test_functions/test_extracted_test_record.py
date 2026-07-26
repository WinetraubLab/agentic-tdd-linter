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
    def test_stores_required_fields(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `extracted_test_record` preserves `record fields` through `ExtractedTestRecord`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Record exposes path `tests/test_sample.py`. Record exposes name `test_sample`.
        Record exposes line `1`. Record exposes node `None`.
        Record exposes docstring `Sample documentation.`.
        Record exposes source `def test_sample(): pass`.
        Record exposes file-docstring `None`.

        Similar Coverage:
        - Higher Level Test: `test_load_all_formats.py::test_loads_python_tests`
          Justification: Shared foundation — The current test preserves language-neutral indexed fields reused by Python packet generation. The higher test loads those fields into complete Python packets.
        - Higher Level Test: `test_load_all_formats.py::test_loads_typescript_tests`
          Justification: Shared foundation — The current test preserves language-neutral indexed fields reused by TypeScript packet generation. The higher test loads those fields into complete TypeScript packets.
        """

        expected_fields = (
            Path("tests/test_sample.py"),
            "test_sample",
            1,
            None,
            "Sample documentation.",
            "def test_sample(): pass",
            None,
        )
        record = ExtractedTestRecord(
            path=expected_fields[0],
            name=expected_fields[1],
            line=expected_fields[2],
            node=expected_fields[3],
            docstring=expected_fields[4],
            source=expected_fields[5],
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

if __name__ == "__main__":
    unittest.main()
