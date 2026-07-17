"""Verify source-module API and test-file structure."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


class SourceModuleStructureTests(unittest.TestCase):
    def test_repository_modules_have_test_files(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Repository validation requires `test module` per `source module`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `_missing_test_paths` produces `[]`.
        Sources possess tests.

        Similar Coverage:
        - Lower Level Test: `test_source_module_structure.py::test_rejects_module_without_test_file`
          Justification: Diagnostic completeness — Lower test verifies missing-test assertion. This test verifies repository scan.
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

    def test_rejects_module_without_test_file(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Repository validation emits an error when an orphan `source module` lacks a `test module`.
        Specialized usage: For module coverage, the `source module` lacks a `test module` instead of having one.

        Verification Method: verify private function output

        Verification Detail:
        Validation propagates `AssertionError`.

        Similar Coverage:
        - Higher Level Test: `test_source_module_structure.py::test_repository_modules_have_test_files`
          Justification: Diagnostic completeness — This test verifies missing-test assertion. Higher test verifies repository scan.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_root = root / "src" / "agentic_tdd_linter"
            test_root = root / "tests"
            source = package_root / "agentic_linter" / "orphan.py"
            source.parent.mkdir(parents=True)
            source.write_text("VALUE = 1\n", encoding="utf-8")
            test_root.mkdir()

            with self.assertRaises(AssertionError):
                _assert_modules_have_matching_test_files(
                    package_root=package_root,
                    test_root=test_root,
                )

    def test_modules_have_source_or_support(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Mirrored unit-test modules match source modules.
        This rule applies to production responsibility folders under `tests`.

        Verification Method: verify public function output

        Verification Detail:
        Every `test_<module>.py` maps back to an existing source module.
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
        `_public_api_violations` produces `[]`.
        Checked modules provide `narrow API`s.

                continue
        Similar Coverage:
        - Lower Level Test: `test_determine_agent_md_status.py::test_exposes_one_public_function`
          Justification: Deeper coverage — Lower test alone verifies status function.
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_exposes_one_public_function`
          Justification: Deeper coverage — Lower test alone verifies manifest function.
        - Lower Level Test: `test_extract_tests_from_file.py::test_modules_expose_one_public_function`
          Justification: Deeper coverage — Lower test alone verifies extraction functions.
        - Lower Level Test: `test_linter_e2e_review.py::test_module_has_one_public_function`
          Justification: Deeper coverage — Lower test verifies the E2E harness module exposes exactly one named function; this policy permits two public functions.

        self.assertEqual([], violations)
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


def _matching_test_path(
    source: Path,
    *,
    package_root: Path,
    test_root: Path,
) -> Path:
    return test_root / relative_source.parent / f"test_{source.name}"


def _missing_test_paths(*, package_root: Path, test_root: Path) -> list[str]:
    return [
        str(
            _matching_test_path(
                source,
                package_root=package_root,
                test_root=test_root,
            ).relative_to(test_root)
        )
        for source in _source_modules(package_root)
            source,
            package_root=package_root,
            test_root=test_root,
        ).is_file()
    ]


def _assert_modules_have_matching_test_files(
    *,
    package_root: Path,
) -> None:
    missing_tests = _missing_test_paths(
        package_root=package_root,
        test_root=test_root,
    )
    if missing_tests:
        raise AssertionError(
            "source modules require matching test files: " + ", ".join(missing_tests)
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
