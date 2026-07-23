"""Repository tests verify source-module API policy.

Repository tests verify test-file structure.

Terms:
- `source module`: A source module is a non-`__init__.py` Python file under src/agentic_tdd_linter. For example, tests/cli/test_main.py matches src/agentic_tdd_linter/cli/main.py.
- `test module`: A test module is a test_*.py file under tests. For example, tests/cli/test_main.py is a test module.
- `test-harness module`: A test-harness module is a same-basename non-test Python file beside a test module or inside its folder's test_harness package. For example, test_harness/mock_keyword_identification.py supports test_mock_keyword_identification.py.
- `narrow API`: A narrow API provides one or two public functions. For example, main.py provides main.
- `data-only module`: A data-only module is indexing_test_functions/extracted_test_record.py or version.py. For example, version.py exposes version data instead of public functions.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


class SourceModuleStructureTests(unittest.TestCase):
    def test_tests_have_source_or_harness(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Repository requires every `test module` to have a same-basename `source module` or `test-harness module`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Each checked `test module` has one permitted module counterpart.
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

    def test_modules_expose_narrow_apis(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `narrow API` restricts `source module`s to ≤2 functions unless they are `data-only module`s.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Each checked non-data module provides a `narrow API`.
        """

        repo_root = Path(__file__).resolve().parents[2]
        package_root = repo_root / "src" / "agentic_tdd_linter"
        data_only_modules = {
            Path("indexing_test_functions/extracted_test_record.py"),
            Path("version.py"),
        }
        self.assertEqual(
            [],
            _public_api_violations(package_root, data_only_modules),
        )


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
