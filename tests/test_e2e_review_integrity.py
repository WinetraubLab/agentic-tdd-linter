from __future__ import annotations

import ast
import unittest
from pathlib import Path


E2E_MODULE = Path(__file__).resolve().parent / "helpers" / "linter_e2e.py"


class E2EReviewIntegrityTests(unittest.TestCase):
    def test_e2e_has_one_public_function(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` exposes one public function.

        Verification Method: verify file structure

        Verification Detail:
        AST lists one public function name.
        """

        tree = ast.parse(E2E_MODULE.read_text(encoding="utf-8"))
        public_functions = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and "_" not in node.name
        ]

        self.assertEqual(["review"], public_functions)


if __name__ == "__main__":
    unittest.main()
