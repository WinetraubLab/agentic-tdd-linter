"""Tests in this file validate `build_manifest_from_agent_md_files` located at `src/agentic_tdd_linter/agentic_linter/build_manifest_from_agent_md_files.py`.
`build_manifest_from_agent_md_files` is responsible for converting completed `.agent.md` reviews into manifest proof stored by default in `tests/agentic_review_manifest.jsonl`, so unchanged test content can skip another agent review.
Changing one test invalidates only that test's proof.

Terms:
- `manifest proof`: Manifest proof records a completed review for a test. For example, current passing proof allows lint to accept that test without another review.
- `review contract`: The review contract includes the linter criteria and repository review documentation. For example, changing README.md changes the contract.
- `stale record`: A stale record no longer matches its test content or review contract. For example, editing a reviewed test function makes its record stale.
- `orphaned record`: An orphaned record identifies a test file or function that no longer exists. For example, deleting a reviewed function leaves an orphaned record for cleanup.
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_tdd_linter.agentic_linter.map_test_function_to_agent_md_file import (
    map_test_function_to_agent_md_file,
)
from agentic_tdd_linter.agentic_linter.build_manifest_from_agent_md_files import (
    _agent_review_manifest_path,
    _lint_agent_review_manifest,
    _review_contract_sha256,
    build_manifest_from_agent_md_files,
)
from agentic_tdd_linter.agentic_linter.determine_agent_md_status import (
    _test_content_sha256,
)
from agentic_tdd_linter.indexing_test_functions.extract_tests_from_file import (
    extract_tests_from_file,
)
from agentic_tdd_linter.version import __version__


REVIEWER = "codex:gpt-5.5"


class AgentReviewManifestTests(unittest.TestCase):
    def test_added_function_preserves_existing_proof(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `build_manifest_from_agent_md_files` preserves `manifest proof` for an unchanged test when a new test function appears in its file.
        Specialized usage: When a new test lacks `manifest proof`, `build_manifest_from_agent_md_files` retains the unchanged test's `manifest proof`.
        The new test remains excluded from the manifest.

        Verification Method: verify private function output

        Verification Detail:
        The manifest file contains only the `test_adds_values` record.
        The surviving record preserves its original proof fields.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Justification: Deeper coverage — The current test isolates manifest preservation after adding a function. The higher test verifies selective packet regeneration after caller modifies one existing function.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n"
            test_file = _write_test_file(root, source)
            _write_manifest(
                root,
                test_file,
                source_hash=_test_hash(test_file, root),
                status="pass",
            )
            original_record = json.loads(
                _agent_review_manifest_path(root)
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            test_file.write_text(
                test_file.read_text(encoding="utf-8")
                + "\ndef test_subtracts_values() -> None:\n    assert 2 - 1 == 1\n",
                encoding="utf-8",
            )

            _lint_agent_review_manifest([test_file], root)
            records = [
                json.loads(line)
                for line in _agent_review_manifest_path(root)
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual([original_record], records)

    def test_review_contract_changes_with_documentation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `build_manifest_from_agent_md_files` derives the `review contract` from README.md and docs/workflow.md.
        Specialized usage: Caller modifies README.md or docs/workflow.md instead of preserving both files, so `build_manifest_from_agent_md_files` produces a new digest.

        Verification Method: verify private function output

        Verification Detail:
        README.md edit produces a new digest.
        docs/workflow.md edit produces a new digest.
        """

        for relative_path in (Path("README.md"), Path("docs/workflow.md")):
            with (
                self.subTest(path=relative_path),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                document = root / relative_path
                document.parent.mkdir(parents=True, exist_ok=True)
                document.write_text("first contract\n", encoding="utf-8")
                first_hash = _review_contract_sha256(root)
                document.write_text("second contract\n", encoding="utf-8")
                second_hash = _review_contract_sha256(root)

                self.assertNotEqual(first_hash, second_hash)

    def test_manifest_reports_old_review_contract(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `build_manifest_from_agent_md_files` emits stale_review_contract_attestation when `manifest proof` contains an outdated `review contract`.
        Specialized usage: Manifest proof contains a mismatched `review contract` instead of the current `review contract`, so agentic linter emits stale_review_contract_attestation.

        Verification Method: verify private function output

        Verification Detail:
        Issue list contains `stale_review_contract_attestation`.

        Similar Coverage:
        - Higher Level Test: `test_cicd_validation_workflow.py::test_outdated_version_requires_review`
          Justification: Diagnostic completeness — The current test isolates the stale review-contract rule. The higher test exercises rejection of proof carrying outdated linter metadata through CI lint.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n"
            test_file = _write_test_file(root, source)
            _write_manifest(
                root,
                test_file,
                source_hash=_test_hash(test_file, root),
                status="pass",
                review_contract_hash="0" * 64,
            )

            rules = _issue_rules(_lint_agent_review_manifest([test_file], root))

        self.assertIn("stale_review_contract_attestation", rules)

    def test_deleted_file_proof_removed(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists.
        Specialized usage: When a deleted reviewed file leaves one `orphaned record`, `build_manifest_from_agent_md_files` removes that record.

        Verification Method: verify private function output

        Verification Detail:
        Manifest contains no records.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_refresh_removes_obsolete_packet`
          Justification: Comparable coverage — The current test removes manifest proof for a deleted test file. The higher test removes an obsolete `.agent.md` file through the CLI refresh workflow.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n"
            test_file = _write_test_file(root, source)
            _write_manifest(
                root,
                test_file,
                source_hash=_test_hash(test_file, root),
                status="pass",
            )
            test_file.unlink()

            _lint_agent_review_manifest([], root)
            manifest_text = _agent_review_manifest_path(root).read_text(
                encoding="utf-8"
            )

        self.assertEqual("", manifest_text)

    def test_deleted_function_proof_removed(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `build_manifest_from_agent_md_files` removes `manifest proof` when a reviewed test is deleted while preserving `manifest proof` for an unchanged test in the same file.
        Specialized usage: When caller erases one reviewed function, `build_manifest_from_agent_md_files` removes only that function's `manifest proof`.

        Verification Method: verify private function output

        Verification Detail:
        Manifest records contain only `test_adds_values`.
        Manifest records exclude `test_subtracts_values`.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Justification: Deeper coverage — The current test isolates manifest cleanup after function deletion. The higher test proves selective packet regeneration after an approved test is edited.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_source = (
                "def test_adds_values() -> None:\n"
                "    assert 1 + 1 == 2\n\n"
                "def test_subtracts_values() -> None:\n"
                "    assert 2 - 1 == 1\n"
            )
            test_file = _write_test_file(root, original_source)
            manifest_path = _write_manifest(
                root,
                test_file,
                source_hash=_test_hash(test_file, root),
                status="pass",
            )
            deleted_record = _manifest_record(
                root,
                path="tests/test_sample.py",
                source_hash=_test_hash(
                    test_file,
                    root,
                    test_name="test_subtracts_values",
                ),
                status="pass",
            )
            deleted_record["test"] = "test_subtracts_values"
            manifest_path.write_text(
                manifest_path.read_text(encoding="utf-8")
                + json.dumps(deleted_record)
                + "\n",
                encoding="utf-8",
            )
            test_file.write_text(
                "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n",
                encoding="utf-8",
            )

            _lint_agent_review_manifest([test_file], root)
            records = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(["test_adds_values"], [record["test"] for record in records])

    def test_recording_keeps_current_proof(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content.
        Specialized usage: The manifest contains one `orphaned record` alongside current `manifest proof` instead of containing only current `manifest proof`.

        Verification Method: verify public function output

        Verification Detail:
        `build_manifest_from_agent_md_files` output contains only `tests/test_sample.py`.
        Retained `manifest proof` has status `pass`.
        Retained source SHA256 equals the current `test_adds_values` content SHA256.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Justification: Deeper coverage — The current test proves orphan cleanup preserves current `manifest proof`. The higher test proves the complete CLI review lifecycle.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reviewer = "codex:gpt-5.5"
            source = textwrap.dedent(
                '''
                def test_adds_values() -> None:
                    """Test Path: happy path

                    Requirement Tested:
                    Addition computes the expected sum.
                    When operands are positive, addition computes two.

                    Verification Method: verify public function output

                    Verification Detail:
                    The sum is two.
                    """

                    assert 1 + 1 == 2
                '''
            ).strip() + "\n"
            test_file = _write_test_file(
                root,
                source,
                relative_path="tests/test_sample.py",
            )
            manifest_path = _write_manifest(
                root,
                test_file,
                source_hash=_test_hash(test_file, root),
                status="pass",
            )
            orphan_record = _manifest_record(
                root,
                path="tests/test_deleted.py",
                source_hash="0" * 64,
                status="pass",
            )
            manifest_path.write_text(
                manifest_path.read_text(encoding="utf-8")
                + json.dumps(orphan_record)
                + "\n",
                encoding="utf-8",
            )
            _write_artifact(root, test_file, status="pass")

            result_path, _, _ = build_manifest_from_agent_md_files(
                [test_file],
                root,
                reviewer=reviewer,
            )
            records = [
                json.loads(line)
                for line in result_path.read_text(encoding="utf-8").splitlines()
            ]
            expected_source_hash = _test_hash(test_file, root)

        self.assertEqual(
            ["tests/test_sample.py"],
            [record["path"] for record in records],
        )
        self.assertEqual(["pass"], [record["status"] for record in records])
        self.assertEqual(
            [expected_source_hash],
            [record["source_sha256"] for record in records],
        )

    def test_pending_review_is_not_recorded(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `build_manifest_from_agent_md_files` creates `manifest proof` only after the reviewer completes every scorecard row.
        Specialized usage: The scorecard contains pending rows instead of completed results, so the manifest file stays absent.

        Verification Method: verify public function output

        Verification Detail:
        Filesystem contains no manifest file.

        Similar Coverage:
        - Higher Level Test: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Justification: Deeper coverage — The current test proves pending scorecards leave manifest proof absent. The higher test proves completed scorecards create proof through the full workflow.
        - Lower Level Test: `test_determine_agent_md_status.py::test_derives_pending_status`
          Justification: Deeper coverage — The lower test isolates pending-status derivation. The current test applies pending status to manifest-recording policy.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = textwrap.dedent(
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
            test_file = _write_test_file(root, source)
            _write_artifact(root, test_file, status="pending")

            manifest_path, _, _ = build_manifest_from_agent_md_files(
                [test_file],
                root,
                reviewer="codex:gpt-5",
            )

        self.assertFalse(manifest_path.exists())


def _write_test_file(
    root: Path,
    source: str,
    *,
    relative_path: str = "tests/test_sample.py",
) -> Path:
    test_file = root / relative_path
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(_with_file_docstring(source), encoding="utf-8")
    return test_file


def _with_file_docstring(source: str) -> str:
    return textwrap.dedent(
        '''
        """Document temporary lint scenarios.

        A `temporary scenario` is source created to exercise one linter behavior.
        For example, a missing requirement scenario exercises requirement validation.
        """
        '''
    ).strip() + "\n\n" + source


def _test_hash(
    test_file: Path,
    root: Path,
    *,
    test_name: str = "test_adds_values",
) -> str:
    test = next(
        test
        for test in extract_tests_from_file(test_file, root)
        if test.name == test_name
    )
    return _test_content_sha256(test.source)


def _write_artifact(
    root: Path,
    test_file: Path,
    *,
    status: str,
    test_name: str = "test_adds_values",
) -> Path:
    artifact_path = map_test_function_to_agent_md_file(test_file, root, test_name=test_name)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        textwrap.dedent(
            f"""
            # Agentic Test Docstring Review

            Test file: `tests/test_sample.py`
            Test Content SHA256: `{_test_hash(test_file, root, test_name=test_name)}`

            ### `{test_name}`

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
    linter_version: str = __version__,
    review_contract_hash: str | None = None,
) -> Path:
    manifest_path = _agent_review_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    record = _manifest_record(
        root,
        path="tests/test_sample.py",
        source_hash=source_hash,
        status=status,
        linter_version=linter_version,
        review_contract_hash=review_contract_hash,
    )
    manifest_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return manifest_path


def _manifest_record(
    root: Path,
    *,
    path: str,
    source_hash: str,
    status: str,
    linter_version: str = __version__,
    review_contract_hash: str | None = None,
) -> dict[str, str]:
    return {
        "path": path,
        "test": "test_adds_values",
        "source_sha256": source_hash,
        "status": status,
        "linter_version": linter_version,
        "review_contract_sha256": (
            review_contract_hash
            if review_contract_hash is not None
            else _review_contract_sha256(root)
        ),
        "reviewer": REVIEWER,
    }


def _issue_rules(issues: list[object]) -> set[str]:
    return {issue.rule for issue in issues}


if __name__ == "__main__":
    unittest.main()
