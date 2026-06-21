"""Validate how repository tests use the E2E review runner.

This file scans `test_*.py` imports to keep tests on the public
`linter_e2e_review` entry point. Runner contract and behavior checks live in
`test_e2e_review_runner.py`.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent


class E2EReviewUsageTests(unittest.TestCase):
    def test_tests_import_review_only(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test files import `e2e` through its public function.

        Verification Method: verify public function output

        Verification Detail:
        Import list contains `linter_e2e_review` only and not any private functions.
        """

        invalid_imports: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in {"linter_e2e", "helpers.linter_e2e"}:
                            invalid_imports.append(f"{test_file}:{node.lineno}")
                if not isinstance(node, ast.ImportFrom):
                    continue
                module = node.module or ""
                imported_names = [alias.name for alias in node.names]
                if module == "helpers" and "linter_e2e" in imported_names:
                    invalid_imports.append(f"{test_file}:{node.lineno}")
                if (
                    module == "helpers.linter_e2e"
                    and imported_names != ["linter_e2e_review"]
                ):
                    invalid_imports.append(f"{test_file}:{node.lineno}")

        self.assertEqual([], invalid_imports)


if __name__ == "__main__":
    unittest.main()
