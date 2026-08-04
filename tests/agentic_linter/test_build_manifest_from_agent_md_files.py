"""Tests in this file validate `build_manifest_from_agent_md_files` located at `src/agentic_tdd_linter/agentic_linter/build_manifest_from_agent_md_files.py`.
`build_manifest_from_agent_md_files` is responsible for converting completed `.agent.md` reviews into manifest proof and validating existing proof stored by default in `tests/agentic_review_manifest.jsonl`.
Changing one test invalidates only that test's proof.

Terms:
- `manifest proof`: Manifest proof records a completed review for a test. Proof becomes stale when it no longer matches test content or the review contract, and proof becomes orphaned when its test no longer exists.
- `review contract`: The review contract includes the linter criteria and repository review documentation. For example, changing README.md changes the contract.
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
        `build_manifest_from_agent_md_files` retains `manifest proof` for an unchanged test when a new test function appears in its file.
        Specialized usage: When a new test in the unchanged test's file lacks `manifest proof`, `build_manifest_from_agent_md_files` retains the unchanged test's `manifest proof`.

        Verification Method: verify public function output

        Verification Detail:
        The manifest contains the original `test_adds_values` record unchanged.

        Similar Coverage:
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_function_proof_removed`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains `manifest proof` for an unchanged test when a new test function appears in its file. The named test verifies `build_manifest_from_agent_md_files` removes proof for a missing test while preserving `manifest proof` for an unchanged test in the same file; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_recording_keeps_current_proof`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains `manifest proof` for an unchanged test when a new test function appears in its file. The named test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during missing-test cleanup when its source SHA256 matches the current test content; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` preserves `manifest proof` for an unchanged test when a new test function appears in its file. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; both use failure path, but exercise materially different scenarios.
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

        self.assertIn(original_record, records)

    def test_excludes_added_function(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `build_manifest_from_agent_md_files` records only completed `manifest proof`, so it omits a new unreviewed test until that test receives passing proof.
        Specialized usage: When a new test appears beside an unchanged reviewed test without completed proof, `build_manifest_from_agent_md_files` leaves the new test out of the manifest.

        Verification Method: verify private function output

        Verification Detail:
        The manifest contains no record for `test_subtracts_values`.
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

        self.assertNotIn(
            "test_subtracts_values",
            [record["test"] for record in records],
        )

    def test_review_contract_changes_with_documentation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `build_manifest_from_agent_md_files` derives the `review contract` from README.md and docs/workflow.md.
        Specialized usage: Caller modifies README.md or docs/workflow.md instead of preserving both files, so `build_manifest_from_agent_md_files` produces a new digest.

        Verification Method: verify private function output

        Verification Detail:
        README.md edit produces a new digest.
        docs/workflow.md edit produces a new digest.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_manifest_reports_old_review_contract`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` derives the `review contract` from README.md and docs/workflow.md. The named test verifies `build_manifest_from_agent_md_files` emits stale_review_contract_attestation when `manifest proof` contains an outdated `review contract`; the current test is happy path, while the named test is failure path.
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
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_review_contract_changes_with_documentation`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` emits stale_review_contract_attestation when `manifest proof` contains an outdated `review contract`. The named test verifies `build_manifest_from_agent_md_files` derives the `review contract` from README.md and docs/workflow.md; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_cicd_validation_workflow.py::test_outdated_version_requires_review`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` emits stale_review_contract_attestation when `manifest proof` contains an outdated `review contract`. The named test verifies `CI/CD linter` emits missing_required_agent_md when manifest proof contains a linter version different from the installed linter version; both use failure path, but exercise materially different scenarios.
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
        `build_manifest_from_agent_md_files` eliminates `manifest proof` whose reviewed file no longer exists.
        Specialized usage: When a deleted reviewed file leaves `manifest proof`, `build_manifest_from_agent_md_files` removes that proof.

        Verification Method: verify private function output

        Verification Detail:
        Manifest contains no records.

        Similar Coverage:
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_function_proof_removed`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists. The named test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_recording_keeps_current_proof`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists. The named test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_refresh_scenario`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists. The named test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh; the current test is failure path, while the named test is happy path.
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
        `build_manifest_from_agent_md_files` removes `manifest proof` for a missing test while preserving proof for an unchanged test in the same file.
        Specialized usage: When one reviewed test no longer exists while another test in its file remains unchanged, `build_manifest_from_agent_md_files` removes only the missing test's `manifest proof`.

        Verification Method: verify private function output

        Verification Detail:
        `manifest proof` contains only `test_adds_values`.
        `manifest proof` excludes `test_subtracts_values`.

        Similar Coverage:
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_added_function_preserves_existing_proof`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file. The named test verifies `build_manifest_from_agent_md_files` preserves `manifest proof` for an unchanged test when a new test function appears in its file; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_file_proof_removed`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file. The named test verifies `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_recording_keeps_current_proof`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file. The named test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; both use failure path, but exercise materially different scenarios.
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
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_added_function_preserves_existing_proof`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content. The named test verifies `build_manifest_from_agent_md_files` preserves `manifest proof` for an unchanged test when a new test function appears in its file; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_file_proof_removed`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content. The named test verifies `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_function_proof_removed`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content. The named test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_cicd_validation_workflow.py::test_cicd_accepts_current_proof`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content. The named test verifies `CI/CD linter` accepts current manifest proof; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; both use happy path, but exercise materially different scenarios.
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
        - Scenario Difference: `test_determine_agent_md_status.py::test_derives_pending_status`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` creates `manifest proof` only after the reviewer completes every scorecard row. The named test verifies `determine_agent_md_status` derives pending status when a scorecard contains a pending row and no failed rows; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `build_manifest_from_agent_md_files` creates `manifest proof` only after the reviewer completes every scorecard row. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; the current test is failure path, while the named test is happy path.
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
