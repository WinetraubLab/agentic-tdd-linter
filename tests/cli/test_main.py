"""Tests in this file validate `CLI` located at `src/agentic_tdd_linter/cli/main.py`.
`CLI` is responsible for providing the create-agent-md and lint command interface.

Terms:
- `CLI output`: CLI output is the text printed for a command result. For example, it reports lint issues or the number of recorded attestations.
- `.agent.md`: An .agent.md file contains one review scorecard that create-agent-md generates. For example, packet creation writes one file for each test.
- `reviewer identity`: A reviewer identity names the agent and model that completed a review. For example, `codex:gpt-5.5` is a reviewer identity.
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
        `CLI` emits `CLI output` with the generated `.agent.md` count when caller selects a nondefault test root.
        Specialized usage: For generated fixtures, CLI configures temporary_fixtures as the test root instead of the default root.

        Verification Method: verify public function output

        Verification Detail:
        `CLI output` contains the text `generated 2 agent review packets` for one single-test packet and one cross-test packet.

        Similar Coverage:
        - Higher Level Test: `test_load_all_formats.py::test_loads_python_tests`
          Justification: Deeper coverage — The current test proves packet-count reporting for a nondefault test root. The higher test proves complete Python packet loading.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_root = repo_root / "temporary_fixtures"
            test_root.mkdir()
            test_file = test_root / "pass_test.py"
            module_file = repo_root / "src" / "addition.py"
            module_file.parent.mkdir()
            module_file.write_text("def add(a, b): return a + b\n", encoding="utf-8")
            test_file.write_text(
                textwrap.dedent(
                    '''
                    """Tests in this file validate `addition` located at `src/addition.py`.
                    `addition` is responsible for calculating numeric sums.
                    """

                    def test_adds_positive_numbers() -> None:
                        """Test Path: happy path

                        Requirement Tested:
                        `addition` calculates sums.
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

        self.assertIn("generated 2 agent review packets", stdout.getvalue())


class ReviewProofFlowTests(unittest.TestCase):
    def test_lint_reports_only_selected_file(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `CLI` confines `CLI output` to the caller-selected test-file path.
        Specialized usage: Caller provides one test-file path instead of the full scope, so CLI confines `CLI output` to that file.

        Verification Method: verify public function output

        Verification Detail:
        Harness invokes lint with `test_first.py` as the selected path.
        `CLI output` contains the selected `test_first.py` file.
        `CLI output` omits the other `test_second.py` file.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tests = root / "tests"
            tests.mkdir()
            first = tests / "test_first.py"
            second = tests / "test_second.py"
            source = textwrap.dedent(
                '''
                """Tests in this file validate `examples` located at `src/examples.py`.
                `examples` is responsible for preserving boolean truth.
                """

                def test_example() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    `examples` preserves truth.
                    When expressions are true, examples preserve truth.

                    Verification Method: verify public function output

                    Verification Detail:
                    The expression equals `True`.
                    """

                    assert True
                '''
            ).strip() + "\n"
            module_file = root / "src" / "examples.py"
            module_file.parent.mkdir()
            module_file.write_text("VALUE = True\n", encoding="utf-8")
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

        self.assertIn("test_first.py", stdout.getvalue())
        self.assertNotIn("test_second", stdout.getvalue())

    def test_lint_requires_reviewer(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `CLI` emits missing_reviewer for completed `.agent.md` files when `reviewer identity` is absent.
        Specialized usage: Caller provides a completed `.agent.md` file without `reviewer identity`, so CLI emits missing_reviewer.

        Verification Method: verify public function output

        Verification Detail:
        Harness creates passing manifest proof.
        Harness creates a completed `.agent.md` file.
        Harness invokes lint without `--reviewer`.
        `CLI output` contains `missing_reviewer`.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Justification: Deeper coverage — The current test proves lint rejects completed reviews without reviewer identity. The higher test proves reviewer-authenticated lint records completed reviews through the full workflow.
        - Higher Level Test: `test_review_documentation.py::test_readme_includes_reviewer`
          Justification: Deeper coverage — The current test proves runtime enforcement when reviewer identity is absent. The higher test verifies that README supplies reviewer identity in the lint command.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reviewer = "codex:gpt-5.5"
            test_source = textwrap.dedent(
                '''
                def test_adds_values() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    `addition` calculates sums.
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

        self.assertIn("missing_reviewer", stdout.getvalue())

def _write_test_file(root: Path, source: str) -> Path:
    test_directory = root / "tests"
    test_directory.mkdir()
    module_file = root / "src" / "addition.py"
    module_file.parent.mkdir()
    module_file.write_text("def add(a, b): return a + b\n", encoding="utf-8")
    test_file = test_directory / "test_sample.py"
    test_file.write_text(_with_file_docstring(source), encoding="utf-8")
    return test_file


def _with_file_docstring(source: str) -> str:
    return textwrap.dedent(
        '''
        """Tests in this file validate `addition` located at `src/addition.py`.
        `addition` is responsible for calculating numeric sums.
        """
        '''
    ).strip() + "\n\n" + source


def _valid_test_function_source(name: str) -> str:
    return textwrap.dedent(
        f'''\
        def {name}() -> None:
            """Test Path: happy path

            Requirement Tested:
            `addition` calculates sums.
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
