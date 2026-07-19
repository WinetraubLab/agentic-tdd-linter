"""Verify manifest freshness capabilities not covered by CLI integration scenarios.

Manifest proof is scoped to the complete test file. Adding or deleting a test
function invalidates every record for that changed file. Proof is also invalidated
when repository review documentation changes. Records for deleted tests are removed,
and incomplete reviews are never recorded.

Terms:
- `manifest proof`: Manifest proof records a completed review for a test. For example, current passing proof allows lint to accept that test without another review.
- `review contract`: The review contract includes the linter criteria and repository review documentation. For example, changing README.md changes the contract.
- `stale record`: A stale record no longer matches its complete test file or review contract. For example, adding another test function makes the file's existing records stale.
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
    _source_sha256,
)
from agentic_tdd_linter.version import __version__


REVIEWER = "codex:gpt-5.5"


class AgentReviewManifestTests(unittest.TestCase):
    def test_added_function_invalidates_manifest_proof(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Adding a test function invalidates all manifest proof for its changed file and requires review evidence for the new function.
        Specialized usage: A reviewed test file gains another test function.

        Verification Method: verify private function output

        Verification Detail:
        Lint reports stale proof for the changed file and missing proof for `test_subtracts_values`.
        The stale manifest record is removed.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n"
            test_file = _write_test_file(root, source)
            _write_manifest(
                root,
                test_file,
                source_hash=_source_sha256(test_file),
                status="pass",
            )
            test_file.write_text(
                test_file.read_text(encoding="utf-8")
                + "\ndef test_subtracts_values() -> None:\n    assert 2 - 1 == 1\n",
                encoding="utf-8",
            )

            issues = _lint_agent_review_manifest([test_file], root)
            missing_issues = [
                issue for issue in issues if issue.rule == "missing_agent_review_attestation"
            ]
            rules = _issue_rules(issues)
            manifest_text = _agent_review_manifest_path(root).read_text(
                encoding="utf-8"
            )

        self.assertEqual(1, len(missing_issues))
        self.assertIn("test_subtracts_values", missing_issues[0].message)
        self.assertIn("stale_agent_review_attestation", rules)
        self.assertEqual("", manifest_text)

    def test_review_contract_changes_with_documentation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The review contract changes when repository review instructions change in README.md or documentation under docs.
        Standard usage: Repository documentation defines part of the review contract.

        Verification Method: verify private function output

        Verification Detail:
        Changing README.md changes the digest.
        Changing docs/workflow.md changes the digest.
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
        Agentic linter rejects manifest proof created under a different review contract.
        Specialized usage: The recorded review contract differs from the current contract.

        Verification Method: verify private function output

        Verification Detail:
        Issue rule is `stale_review_contract_attestation`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n"
            test_file = _write_test_file(root, source)
            _write_manifest(
                root,
                test_file,
                source_hash=_source_sha256(test_file),
                status="pass",
                review_contract_hash="0" * 64,
            )

            rules = _issue_rules(_lint_agent_review_manifest([test_file], root))

        self.assertIn("stale_review_contract_attestation", rules)

    def test_deleted_file_proof_is_reported_and_removed(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic linter reports and removes manifest proof when its reviewed test file has been deleted.
        Specialized usage: The reviewed source file no longer exists.

        Verification Method: verify private function output

        Verification Detail:
        Rules contain `orphaned_agent_review_attestation`.
        The manifest contains no records.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_adds_values() -> None:\n    assert 1 + 1 == 2\n"
            test_file = _write_test_file(root, source)
            _write_manifest(
                root,
                test_file,
                source_hash=_source_sha256(test_file),
                status="pass",
            )
            test_file.unlink()

            rules = _issue_rules(_lint_agent_review_manifest([], root))
            manifest_text = _agent_review_manifest_path(root).read_text(
                encoding="utf-8"
            )

        self.assertIn("orphaned_agent_review_attestation", rules)
        self.assertEqual("", manifest_text)

    def test_deleted_function_proof_is_reported_and_removed(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic linter identifies a deleted test function and removes every stale manifest record for its changed file.
        Specialized usage: One reviewed test function is deleted while another remains in the file.

        Verification Method: verify private function output

        Verification Detail:
        Exactly one orphaned-proof issue identifies `test_subtracts_values`.
        The manifest contains no records for the changed file.
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
                source_hash=_source_sha256(test_file),
                status="pass",
            )
            deleted_record = _manifest_record(
                root,
                path="tests/test_sample.py",
                source_hash=_source_sha256(test_file),
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

            issues = _lint_agent_review_manifest([test_file], root)
            orphan_issues = [
                issue for issue in issues if issue.rule == "orphaned_agent_review_attestation"
            ]
            manifest_text = manifest_path.read_text(encoding="utf-8")

        self.assertEqual(1, len(orphan_issues))
        self.assertIn("test_subtracts_values", orphan_issues[0].message)
        self.assertEqual("", manifest_text)

    def test_recording_replaces_orphans_with_current_proof(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Recording a completed review removes proof for deleted files while preserving proof for current tests.
        Specialized usage: The existing manifest contains one current record and one orphaned record.

        Verification Method: verify public function output

        Verification Detail:
        Refreshed paths contain only `tests/test_sample.py`.
        Manifest construction reports no issues.
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
            test_file = _write_test_file(root, source)
            manifest_path = _write_manifest(
                root,
                test_file,
                source_hash=_source_sha256(test_file),
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

            result_path, count, issues = build_manifest_from_agent_md_files(
                [test_file],
                root,
                reviewer=reviewer,
            )
            records = [
                json.loads(line)
                for line in result_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(1, count)
        self.assertEqual([], issues)
        self.assertEqual(
            ["tests/test_sample.py"],
            [record["path"] for record in records],
        )

    def test_pending_review_is_not_recorded(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic linter reports an incomplete `.agent.md` and records no manifest proof for it.
        Specialized usage: The review remains pending instead of containing completed results.

        Verification Method: verify private function output

        Verification Detail:
        Rules contain `agent_review_not_run`.
        The recorded-attestation count is zero and no manifest is created.
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

            manifest_path, count, issues = build_manifest_from_agent_md_files(
                [test_file],
                root,
                reviewer="codex:gpt-5",
            )

        self.assertIn("agent_review_not_run", _issue_rules(issues))
        self.assertEqual(0, count)
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
            Source SHA256: `{_source_sha256(test_file)}`

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
