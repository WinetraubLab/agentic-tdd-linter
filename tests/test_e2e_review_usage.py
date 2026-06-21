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

    def test_linter_e2e_review_calls_stay_in_test_functions(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test functions call `linter_e2e_review` directly without wrappers.

        Verification Method: verify public function output

        Verification Detail:
        AST reports calls that are not directly inside one `test_*` function.
        """

        invalid_calls: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            parents: dict[ast.AST, ast.AST] = {}
            for parent in ast.walk(tree):
                for child in ast.iter_child_nodes(parent):
                    parents[child] = parent

            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "linter_e2e_review"
                ):
                    continue
                function_ancestors: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
                parent = parents.get(node)
                while parent is not None:
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        function_ancestors.append(parent)
                    parent = parents.get(parent)
                if (
                    len(function_ancestors) != 1
                    or not function_ancestors[0].name.startswith("test_")
                ):
                    invalid_calls.append(
                        f"{test_file}:{node.lineno}: "
                        "do not wrap; call directly inside test function"
                    )

        self.assertEqual([], invalid_calls)


if __name__ == "__main__":
    unittest.main()
