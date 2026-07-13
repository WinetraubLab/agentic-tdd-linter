"""Verify source-module API and test-file structure."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


class SourceModuleStructureTests(unittest.TestCase):
    def test_repository_modules_have_test_files(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `source modules` require tests.
        When modules contain logic, `source modules` require tests.

        Verification Method: verify private function output

        Verification Detail:
        `_missing_test_paths` produces `[]`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        package_root = repo_root / "src" / "agentic_tdd_linter"
        test_root = repo_root / "tests"
        self.assertEqual(
            [],
            _missing_test_paths(
                package_root=package_root,
                test_root=test_root,
            ),
        )


    def test_unit_modules_match_source_modules(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Mirrored unit-test modules match source modules.
        This rule applies to production responsibility folders under `tests`.

        Verification Method: verify public function output

        Verification Detail:
        Every `test_<module>.py` maps back to an existing source module.
        """

        unmatched_tests = [
            str(test_file.relative_to(REPO_ROOT))
            for folder in MIRRORED_TEST_FOLDERS
            for test_file in sorted((TEST_ROOT / folder).glob("test_*.py"))
            if not _matching_source_path(test_file).is_file()
        ]

        self.assertEqual([], unmatched_tests)

    def test_modules_expose_narrow_apis(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Implementation modules expose narrow APIs.
        This rule applies to callable modules under `src`.

        Verification Method: verify public function output

        Verification Detail:
        AST reports one or two public functions per callable module.
        """

        violations = []
        for source in _implementation_modules():
            relative_source = source.relative_to(PACKAGE_ROOT)
            if relative_source in DATA_ONLY_MODULES:
                continue
            public_functions = _public_function_names(source)
            if not 1 <= len(public_functions) <= 2:
                violations.append(
                    f"{relative_source}: expected 1-2 public functions, "
                    f"found {public_functions}"
                )

        self.assertEqual([], violations)


def _implementation_modules() -> list[Path]:
    return sorted(
        path
        for path in PACKAGE_ROOT.rglob("*.py")
        if path.name != "__init__.py"
    )


def _matching_test_path(source: Path) -> Path:
    relative_source = source.relative_to(PACKAGE_ROOT)
    return TEST_ROOT / relative_source.parent / f"test_{source.name}"


def _matching_source_path(test_file: Path) -> Path:
    relative_test = test_file.relative_to(TEST_ROOT)
    source_name = relative_test.name.removeprefix("test_")
    return PACKAGE_ROOT / relative_test.parent / source_name


def _public_function_names(source: Path) -> list[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]


def _initializer_is_minimal(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr) and isinstance(
        tree.body[0].value,
        ast.Constant,
    ) and isinstance(tree.body[0].value.value, str)


if __name__ == "__main__":
    unittest.main()
