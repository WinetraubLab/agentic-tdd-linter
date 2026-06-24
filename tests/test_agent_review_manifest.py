from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_review_manifest import (
    agent_review_manifest_path,
    lint_agent_review_manifest,
    record_agent_review_attestations,
    review_contract_sha256,
)
from agentic_tdd_linter.agent_ran_proof import source_sha256
from agentic_tdd_linter.cli import main
from agentic_tdd_linter.version import __version__


REVIEWER = "codex:gpt-5.5"


class AgentReviewManifestTests(unittest.TestCase):
    def test_package_metadata_matches_linter_version(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Package metadata uses the linter version.

        Verification Method: verify public function output

        Verification Detail:
        Pyproject version equals the runtime version constant.
        """

        pyproject = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual(__version__, pyproject["project"]["version"])

    def test_records_review_attestation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Attestation recording writes compact proof records.

        Verification Method: verify public function output

        Verification Detail:
        Manifest record includes path, source hash, status, reviewer, and contract hash.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_artifact(root, test_file, status="pass")

            manifest_path, count, issues = record_agent_review_attestations(
                [test_file],
                root,
                reviewer="codex:gpt-5",
            )

            record = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected_hash = source_sha256(test_file)
            expected_contract_hash = review_contract_sha256(root)

        self.assertEqual(1, count)
        self.assertEqual([], issues)
        self.assertEqual("tests/test_sample.py", record["path"])
        self.assertEqual(expected_hash, record["source_sha256"])
        self.assertEqual("pass", record["status"])
        self.assertEqual(__version__, record["linter_version"])
        self.assertEqual(expected_contract_hash, record["review_contract_sha256"])
        self.assertEqual("codex:gpt-5", record["reviewer"])

    def test_manifest_accepts_matching_pass_record(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Manifest review proof accepts current pass records.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint returns no issues for a matching source hash.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(root, test_file, source_hash=source_sha256(test_file), status="pass")

            issues = lint_agent_review_manifest([test_file], root)

        self.assertEqual([], issues)

    def test_review_contract_hash_includes_documentation(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Review contract hash changes when documentation changes.

        Verification Method: verify public function output

        Verification Detail:
        Contract digest differs after README content changes.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme = root / "README.md"
            readme.write_text("first contract\n", encoding="utf-8")
            first_hash = review_contract_sha256(root)
            readme.write_text("second contract\n", encoding="utf-8")
            second_hash = review_contract_sha256(root)

        self.assertNotEqual(first_hash, second_hash)

    def test_review_contract_hash_includes_docs(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Review contract hash changes when docs change.

        Verification Method: verify public function output

        Verification Detail:
        Contract digest differs after docs content changes.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs" / "workflow.md"
            docs.parent.mkdir()
            docs.write_text("first contract\n", encoding="utf-8")
            first_hash = review_contract_sha256(root)
            docs.write_text("second contract\n", encoding="utf-8")
            second_hash = review_contract_sha256(root)

        self.assertNotEqual(first_hash, second_hash)

    def test_manifest_reports_stale_record(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Manifest review proof rejects stale source hashes.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint reports stale attestation when the hash differs.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(root, test_file, source_hash="0" * 64, status="pass")

            rules = _issue_rules(lint_agent_review_manifest([test_file], root))

        self.assertIn("stale_agent_review_attestation", rules)

    def test_manifest_accepts_current_linter_version(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Manifest review proof accepts the current linter version.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint returns no issues when record version equals runtime version.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(
                root,
                test_file,
                source_hash=source_sha256(test_file),
                status="pass",
                linter_version=__version__,
            )

            issues = lint_agent_review_manifest([test_file], root)

        self.assertEqual([], issues)

    def test_manifest_accepts_newer_linter_version(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Manifest review proof accepts a newer linter version.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint returns no issues when record version is higher than runtime version.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(
                root,
                test_file,
                source_hash=source_sha256(test_file),
                status="pass",
                linter_version="999.0.0",
            )

            issues = lint_agent_review_manifest([test_file], root)

        self.assertEqual([], issues)

    def test_manifest_reports_old_review_contract(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Manifest review proof rejects stale review contracts.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint reports old contract attestation when hashes differ.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(
                root,
                test_file,
                source_hash=source_sha256(test_file),
                status="pass",
                review_contract_hash="0" * 64,
            )

            rules = _issue_rules(lint_agent_review_manifest([test_file], root))

        self.assertIn("stale_review_contract_attestation", rules)

    def test_manifest_reports_old_linter_version(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Manifest review proof rejects stale linter versions.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint reports old linter attestation when versions differ.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(
                root,
                test_file,
                source_hash=source_sha256(test_file),
                status="pass",
                linter_version="0.0.0",
            )

            rules = _issue_rules(lint_agent_review_manifest([test_file], root))

        self.assertIn("stale_linter_review_attestation", rules)

    def test_manifest_detects_changed_source(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Manifest rejects stale proof when reviewed source changes.

        Verification Method: verify public function output

        Verification Detail:
        Manifest lint reports stale rule after source edit.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_artifact(root, test_file, status="pass")
            _, count, issues = record_agent_review_attestations(
                [test_file],
                root,
                reviewer="codex:gpt-5",
            )
            test_file.write_text(
                test_file.read_text(encoding="utf-8").replace(
                    "assert 1 + 1 == 2",
                    "assert 2 + 2 == 4",
                    1,
                ),
                encoding="utf-8",
            )

            rules = _issue_rules(lint_agent_review_manifest([test_file], root))

        self.assertEqual(1, count)
        self.assertEqual([], issues)
        self.assertIn("stale_agent_review_attestation", rules)

    def test_recording_removes_deleted_records(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Manifest refresh removes records when test files disappear.

        Verification Method: verify public function output

        Verification Detail:
        Manifest output contains current path after refresh.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            manifest_path = _write_manifest(
                root,
                test_file,
                source_hash=source_sha256(test_file),
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

            _, count, issues = record_agent_review_attestations(
                [test_file],
                root,
                reviewer=REVIEWER,
            )
            records = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(1, count)
        self.assertEqual([], issues)
        self.assertEqual(["tests/test_sample.py"], [record["path"] for record in records])

    def test_manifest_recording_requires_pass_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Manifest recording rejects incomplete artifact reviews.

        Verification Method: verify public function output

        Verification Detail:
        Recorder returns pending-review issues before writing manifest records.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_artifact(root, test_file, status="pending")

            manifest_path, count, issues = record_agent_review_attestations(
                [test_file],
                root,
                reviewer="codex:gpt-5",
            )

        self.assertEqual(0, count)
        self.assertFalse(manifest_path.exists())
        self.assertIn("agent_review_not_run", _issue_rules(issues))

    def test_check_writes_manifest_after_review(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Local check writes manifest proof after review.
        Manifest record stores reviewer identity.
        Manifest record stores content hashes.

        Verification Method: verify public function output

        Verification Detail:
        Check output reports attestation count.
        Manifest record contains reviewer identity.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_artifact(root, test_file, status="pass")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "check",
                        "--all",
                        "--reviewer",
                        REVIEWER,
                        "--repo-root",
                        str(root),
                    ]
                )

            record = json.loads(agent_review_manifest_path(root).read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertIn("recorded 1 review attestations", stdout.getvalue())
        self.assertEqual("tests/test_sample.py", record["path"])
        self.assertEqual(REVIEWER, record["reviewer"])

def _write_test_file(root: Path) -> Path:
    test_directory = root / "tests"
    test_directory.mkdir()
    test_file = test_directory / "test_sample.py"
    test_file.write_text(
        textwrap.dedent(
            """
            def test_adds_values() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                addition returns the expected sum for two positive integers.

                Verification Method: verify public function output

                Verification Detail:
                Returned total equals the expected sum.
                \"\"\"

                assert 1 + 1 == 2
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return test_file


def _write_artifact(root: Path, test_file: Path, *, status: str) -> Path:
    artifact_path = agent_review_artifact_path(test_file, root)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        textwrap.dedent(
            f"""
            # Agentic Test Docstring Review

            Test file: `tests/test_sample.py`
            Source SHA256: `{source_sha256(test_file)}`

            ## Agent Review Result

            Status: {status}
            Notes:
            - test_adds_values passes review.
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
    extra_fields: dict[str, str] | None = None,
) -> Path:
    manifest_path = agent_review_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    record = _manifest_record(
        root,
        path="tests/test_sample.py",
        source_hash=source_hash,
        status=status,
        linter_version=linter_version,
        review_contract_hash=review_contract_hash,
    )
    if extra_fields:
        record.update(extra_fields)
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
        "source_sha256": source_hash,
        "status": status,
        "linter_version": linter_version,
        "review_contract_sha256": (
            review_contract_hash
            if review_contract_hash is not None
            else review_contract_sha256(root)
        ),
        "reviewer": REVIEWER,
    }


def _issue_rules(issues: list[object]) -> set[str]:
    return {issue.rule for issue in issues}


if __name__ == "__main__":
    unittest.main()
