"""Verify focused command-line input and output behavior.

Terms:
- `main`: Main is the CLI entry function. For example, tests call main with command arguments and inspect its exit code.
- `main output`: Main output is the text printed for a command result. For example, it reports lint issues or the number of recorded attestations.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_tdd_linter.cli.main import main

from agentic_tdd_linter.agentic_linter.build_manifest_from_agent_md_files import (
    _agent_review_manifest_path,
    _review_contract_sha256,
)
from agentic_tdd_linter.agentic_linter.determine_agent_md_status import (
    _source_sha256,
)
from agentic_tdd_linter.agentic_linter.map_test_function_to_agent_md_file import (
    map_test_function_to_agent_md_file,
)
from agentic_tdd_linter.version import __version__


class CliTests(unittest.TestCase):
    def test_test_root_reports_generated_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `create-agent-md --test-root <directory>` processes tests outside the default `tests` directory and reports how many `.agent.md` files it generated.
        Specialized usage: For generated fixtures, CLI configures test root as temporary_fixtures (instead of tests).

        Verification Method: verify public function output

        Verification Detail:
        `main output` contains this text:
        `generated 1 agent review packets`
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_root = repo_root / "temporary_fixtures"
            test_root.mkdir()
            test_file = test_root / "pass_test.py"
            test_file.write_text(
                textwrap.dedent(
                    '''
                    """Document temporary addition tests."""

                    def test_adds_positive_numbers() -> None:
                        """Test Path: happy path

                        Requirement Tested:
                        Addition calculates sums.
                        When operands contain positive integers, addition calculates sums.

                        Verification Method: verify public function output

                        Verification Detail:
                        The expression produces `3`.
                        """

                        assert 1 + 2 == 3
                    '''
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "create-agent-md",
                        "--repo-root",
                        str(repo_root),
                        "--test-root",
                        str(test_root),
                        str(test_file),
                    ]
                )

        self.assertIn("generated 1 agent review packets", stdout.getvalue())


class ReviewProofFlowTests(unittest.TestCase):
    def test_lint_reports_only_selected_file(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        When lint is given one test-file path, it reports issues only for that selected file and ignores issues from unselected files.
        Specialized usage: The command names one test file while another test file in the repository also has lint issues.

        Verification Method: verify public function output

        Verification Detail:
        Run lint with `test_first.py` as the selected path.
        `main` produces `1` and reports its missing `.agent.md` file.
        `main output` does not mention the unselected `test_second.py` file.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tests = root / "tests"
            tests.mkdir()
            first = tests / "test_first.py"
            second = tests / "test_second.py"
            source = textwrap.dedent(
                '''
                """Document temporary CLI tests.

                A `CLI test` is source that exercises one command behavior.
                For example, an addition test exercises manifest processing.
                """

                def test_example() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Examples preserve truth.
                    When expressions are true, examples preserve truth.

                    Verification Method: verify public function output

                    Verification Detail:
                    The expression equals `True`.
                    """

                    assert True
                '''
            ).strip() + "\n"
            first.write_text(source, encoding="utf-8")
            second.write_text(source, encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "lint",
                        "--fresh",
                        "--repo-root",
                        str(root),
                        str(first),
                    ]
                )

        self.assertEqual(1, exit_code)
        self.assertIn("missing_required_agent_md", stdout.getvalue())
        self.assertNotIn("test_second", stdout.getvalue())

    def test_lint_requires_reviewer(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        When completed `.agent.md` files are ready to be recorded, lint fails with `missing_reviewer` if `--reviewer` is omitted.
        Specialized usage: The completed `.agent.md` file is present, but the `--reviewer` argument is omitted.

        Verification Method: verify public function output

        Verification Detail:
        Create passing manifest proof and a completed `.agent.md` file.
        Run lint without `--reviewer`.
        `main` produces `1` and reports `missing_reviewer` instead of recording review proof without an identity.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reviewer = "codex:gpt-5.5"
            test_source = textwrap.dedent(
                '''
                def test_adds_values() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Addition calculates sums.
                    When operands contain positive integers, addition calculates sums.

                    Verification Method: verify public function output

                    Verification Detail:
                    The expression produces `2`.
                    """

                    assert 1 + 1 == 2
                '''
            ).strip() + "\n"
            test_file = _write_test_file(root, test_source)
            _write_manifest(
                root,
                test_file,
                source_hash="0" * 64,
                status="pass",
                reviewer=reviewer,
            )
            _write_artifact(root, test_file, status="pass")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["lint", "--repo-root", str(root)])

        self.assertEqual(1, exit_code)
        self.assertIn("missing_reviewer", stdout.getvalue())

def _write_test_file(root: Path, source: str) -> Path:
    test_directory = root / "tests"
    test_directory.mkdir()
    test_file = test_directory / "test_sample.py"
    test_file.write_text(_with_file_docstring(source), encoding="utf-8")
    return test_file


def _with_file_docstring(source: str) -> str:
    return textwrap.dedent(
        '''
        """Document temporary CLI tests.

        A `CLI test` is source that exercises one command behavior.
        For example, an addition test exercises manifest processing.
        """
        '''
    ).strip() + "\n\n" + source


def _valid_test_function_source(name: str) -> str:
    return textwrap.dedent(
        f'''\
        def {name}() -> None:
            """Test Path: happy path

            Requirement Tested:
            Examples preserve truth.
            When expressions are true, examples preserve truth.

            Verification Method: verify public function output

            Verification Detail:
            The expression equals `True`.
            """

            assert True
        '''
    )


def _write_artifact(root: Path, test_file: Path, *, status: str) -> Path:
    artifact_path = map_test_function_to_agent_md_file(test_file, root, test_name="test_adds_values")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        textwrap.dedent(
            f"""
            # Agentic Test Docstring Review

            Test file: `tests/test_sample.py`
            Source SHA256: `{_source_sha256(test_file)}`

            ### `test_adds_values`

            ## Agent Review Result

            Status: {status}
            Notes:
            - Scenario or example: adding `1 + 1` should produce `2`.
            - Review result: Review passed.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return artifact_path


def _write_manifest(
    root: Path,
    test_file: Path,
    *,
    source_hash: str,
    status: str,
    reviewer: str,
    linter_version: str = __version__,
) -> Path:
    manifest_path = _agent_review_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "path": "tests/test_sample.py",
        "test": "test_adds_values",
        "source_sha256": source_hash,
        "status": status,
        "linter_version": linter_version,
        "review_contract_sha256": _review_contract_sha256(root),
        "reviewer": reviewer,
    }
    manifest_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return manifest_path


if __name__ == "__main__":
    unittest.main()
