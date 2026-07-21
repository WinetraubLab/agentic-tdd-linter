"""Verify test-file discovery.

Terms:
- `discovered file`: A discovered file is a test file selected for extraction and linting. For example, an all-mode search discovers `tests/test_example.py`.
- `discover_test_files`: This public function selects test files for extraction. For example, `discover_test_files` returns Python and TypeScript test paths.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_tdd_linter.indexing_test_functions.discover_test_files import (
    discover_test_files,
)


class TestFileDiscoveryTests(unittest.TestCase):
    def test_ignores_temporary_fixtures(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `discover_test_files` excludes temporary fixtures from repository discovery.
        Specialized usage: Discovery receives temporary location instead of maintained location.

        Verification Method: verify public function output

        Verification Detail:
        `discover_test_files` output excludes `tests/temporary_fixtures/test_generated.py`.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            tests_root = repo_root / "tests"
            fixture = tests_root / "temporary_fixtures" / "test_generated.py"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("def test_generated(): pass\n", encoding="utf-8")

            discovered = discover_test_files(
                repo_root,
                mode="all",
                test_root=tests_root,
            )

        self.assertEqual([], discovered)


if __name__ == "__main__":
    unittest.main()
