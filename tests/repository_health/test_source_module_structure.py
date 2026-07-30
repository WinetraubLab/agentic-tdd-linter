"""Tests in this file validate `test_source_module_structure` located at `tests/repository_health/test_source_module_structure.py`.
`test_source_module_structure` is responsible for enforcing repository source-module and test-module structure.

Terms:
- `source module`: A source module is a non-`__init__.py` Python file under src/agentic_tdd_linter. For example, tests/cli/test_main.py matches src/agentic_tdd_linter/cli/main.py.
- `test module`: A test module is a test_*.py file under tests. For example, tests/cli/test_main.py is a test module.
- `test-harness module`: A test-harness module is a same-basename non-test Python file beside a test module or inside its folder's test_harness package. For example, test_harness/mock_keyword_identification.py supports test_mock_keyword_identification.py.
- `data-only module`: A data-only module is indexing_test_functions/extracted_test_record.py or version.py. For example, version.py exposes version data instead of public functions.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path


class SourceModuleStructureTests(unittest.TestCase):
    def test_tests_have_source_or_harness(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_source_module_structure` requires every `test module` in agentic_linter, cli, conventional_linter, and indexing_test_functions to have a same-basename `source module` or `test-harness module`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `_unmatched_test_paths` produces `[]` for agentic_linter, cli, conventional_linter, and indexing_test_functions.

        Similar Coverage:
        - Lower Level Test: `test_load_all_formats.py::test_rejects_missing_module`
          Justification: Deeper coverage — The lower test isolates CLI rejection of one missing declared module path. The current test enforces counterpart coverage across repository test modules.
        """

        repo_root = Path(__file__).resolve().parents[2]
        package_root = repo_root / "src" / "agentic_tdd_linter"
        test_root = repo_root / "tests"
        mirrored_folders = (
            "agentic_linter",
            "cli",
            "conventional_linter",
            "indexing_test_functions",
        )
        self.assertEqual(
            [],
            _unmatched_test_paths(
                repo_root=repo_root,
                package_root=package_root,
                test_root=test_root,
                mirrored_folders=mirrored_folders,
            ),
        )

    def test_requires_one_or_two_public_functions(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `test_source_module_structure` reports a `source module` that exposes fewer than one or more than two public functions.
        Specialized usage: A source module exposes zero or three public functions instead of one or two, so `test_source_module_structure` reports it.

        Verification Method: verify private function output

        Verification Detail:
        `_public_api_violations` identifies controlled modules with zero or three public functions.
        `_public_api_violations` accepts a controlled module with two public functions.
        """

        with tempfile.TemporaryDirectory() as directory:
            controlled_root = Path(directory)
            (controlled_root / "empty.py").write_text("", encoding="utf-8")
            (controlled_root / "valid.py").write_text(
                "def first(): pass\ndef second(): pass\n",
                encoding="utf-8",
            )
            three_functions = (
                "def first(): pass\n"
                "def second(): pass\n"
                "def third(): pass\n"
            )
            (controlled_root / "excess.py").write_text(
                three_functions,
                encoding="utf-8",
            )

            controlled_violations = _public_api_violations(
                controlled_root,
                set(),
            )

        self.assertEqual(
            [
                "empty.py: expected 1-2 public functions, found []",
                "excess.py: expected 1-2 public functions, "
                "found ['first', 'second', 'third']",
            ],
            controlled_violations,
        )

    def test_exempts_data_only_modules_from_public_function_limit(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_source_module_structure` exempts every `data-only module` from the one-or-two-public-functions limit.
        Specialized usage: A declared `data-only module` exposes three public functions instead of at most two, so `test_source_module_structure` accepts it.

        Verification Method: verify private function output

        Verification Detail:
        `_public_api_violations` produces `[]` for the package root when the two `data-only module` paths are exempt.
        `_public_api_violations` accepts a controlled three-function `data-only module`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        package_root = repo_root / "src" / "agentic_tdd_linter"
        data_only_modules = {
            Path("indexing_test_functions/extracted_test_record.py"),
            Path("version.py"),
        }
        repository_violations = _public_api_violations(
            package_root,
            data_only_modules,
        )

        with tempfile.TemporaryDirectory() as directory:
            controlled_root = Path(directory)
            three_functions = (
                "def first(): pass\n"
                "def second(): pass\n"
                "def third(): pass\n"
            )
            (controlled_root / "data.py").write_text(
                three_functions,
                encoding="utf-8",
            )

            controlled_violations = _public_api_violations(
                controlled_root,
                {Path("data.py")},
            )

        self.assertEqual([], repository_violations)
        self.assertEqual([], controlled_violations)


def _source_modules(package_root: Path) -> list[Path]:
    return sorted(
        path
        for path in package_root.rglob("*.py")
        if path.name != "__init__.py"
    )


def _matching_source_path(
    test_file: Path,
    *,
    test_root: Path,
    package_root: Path,
) -> Path:
    relative_test = test_file.relative_to(test_root)
    source_name = relative_test.name.removeprefix("test_")
    return package_root / relative_test.parent / source_name


def _matching_test_support_paths(test_file: Path) -> tuple[Path, Path]:
    support_name = test_file.name.removeprefix("test_")
    return (
        test_file.with_name(support_name),
        test_file.parent / "test_harness" / support_name,
    )


def _unmatched_test_paths(
    *,
    repo_root: Path,
    package_root: Path,
    test_root: Path,
    mirrored_folders: tuple[str, ...],
) -> list[str]:
    return [
        str(test_file.relative_to(repo_root))
        for folder in mirrored_folders
        for test_file in sorted((test_root / folder).glob("test_*.py"))
        if not _matching_source_path(
            test_file,
            test_root=test_root,
            package_root=package_root,
        ).is_file()
        and not any(
            support_path.is_file()
            for support_path in _matching_test_support_paths(test_file)
        )
    ]


def _public_api_violations(
    package_root: Path,
    data_only_modules: set[Path],
) -> list[str]:
    violations = []
    for source in _source_modules(package_root):
        relative_source = source.relative_to(package_root)
        if relative_source in data_only_modules:
            continue
        public_functions = _public_function_names(source)
        if not 1 <= len(public_functions) <= 2:
            violations.append(
                f"{relative_source}: expected 1-2 public functions, "
                f"found {public_functions}"
            )
    return violations


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
