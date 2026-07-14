"""Verify extracted-test records.

Terms:
- `ExtractedTestRecord`: ExtractedTestRecord is the shared data structure for one indexed test. For example, it stores a test's path, name, line, syntax node, documentation, and source without a language discriminator.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)


class ExtractedTestRecordTests(unittest.TestCase):
