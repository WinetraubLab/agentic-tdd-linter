"""Tests in this file validate `conventional_linter` located at `src/agentic_tdd_linter/conventional_linter/check_test_module_contract.py`.
`conventional_linter` is responsible for validating repository-relative test module declarations."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_tdd_linter.conventional_linter.check_test_module_contract import (
    check_test_module_contract,
)
from agentic_tdd_linter.indexing_test_functions.extracted_test_record import (
    ExtractedTestRecord,
)


class TestModuleContractTests(unittest.TestCase):
    def test_accepts_existing_repository_relative_file(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts a module declaration identifying an existing repository-relative file.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The issue list is empty when the declared source file exists.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            source_path = repo_root / "src" / "parser.py"
            source_path.parent.mkdir()
            source_path.touch()

            issues = check_test_module_contract(
                [_test_record("src/parser.py")],
                repo_root,
            )

        self.assertEqual([], issues)

    def test_accepts_existing_repository_relative_directory(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `conventional_linter` accepts a module declaration identifying an existing repository-relative directory.
        Specialized usage: The declared module is owned by a directory rather than one source file.

        Verification Method: verify public function output

        Verification Detail:
        The issue list is empty when the declared directory exists.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            (repo_root / "yaml-templates").mkdir()

            issues = check_test_module_contract(
                [_test_record("yaml-templates/")],
                repo_root,
            )

        self.assertEqual([], issues)

    def test_rejects_missing_repository_relative_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_test_module when a declared repository-relative path does not exist.
        Specialized usage: Neither a file nor a directory exists at the declared path.

        Verification Method: verify public function output

        Verification Detail:
        The issue uses missing_test_module and describes the accepted file-or-directory contract.
        """

        with tempfile.TemporaryDirectory() as directory:
            issues = check_test_module_contract(
                [_test_record("missing-module")],
                Path(directory),
            )

        self.assertEqual(["missing_test_module"], [issue.rule for issue in issues])
        self.assertIn(
            "repository-relative file or directory",
            issues[0].message,
        )

    def test_rejects_existing_absolute_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_test_module when a module declaration uses an absolute path.
        Specialized usage: The absolute path identifies an existing file within the repository.

        Verification Method: verify public function output

        Verification Detail:
        The issue list contains missing_test_module even though the absolute file exists.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            source_path = repo_root / "parser.py"
            source_path.touch()

            issues = check_test_module_contract(
                [_test_record(str(source_path))],
                repo_root,
            )

        self.assertEqual(["missing_test_module"], [issue.rule for issue in issues])

    def test_rejects_traversal_outside_repository(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `conventional_linter` emits missing_test_module when a module declaration traverses outside the repository.
        Specialized usage: The traversal path identifies an existing file beside the repository.

        Verification Method: verify public function output

        Verification Detail:
        The issue list contains missing_test_module for an existing file reached through parent traversal.
        """

        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            repo_root = temporary_root / "repository"
            repo_root.mkdir()
            (temporary_root / "outside.py").touch()

            issues = check_test_module_contract(
                [_test_record("../outside.py")],
                repo_root,
            )

        self.assertEqual(["missing_test_module"], [issue.rule for issue in issues])


def _test_record(declared_path: str) -> ExtractedTestRecord:
    return ExtractedTestRecord(
        path=Path("tests/test_parser.py"),
        name="test_parser",
        line=1,
        node=None,
        docstring="""Requirement Tested:
`conventional_linter` validates a module declaration.""",
        file_docstring=(
            "Tests in this file validate `conventional_linter` located at "
            f"`{declared_path}`.\n"
            "`conventional_linter` is responsible for validating module declarations."
        ),
    )


if __name__ == "__main__":
    unittest.main()
