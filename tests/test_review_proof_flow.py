from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.agent_review_artifacts import agent_review_artifact_path
from agentic_tdd_linter.agent_review_manifest import (
    agent_review_manifest_path,
    review_contract_sha256,
)
from agentic_tdd_linter.agent_ran_proof import source_sha256
from agentic_tdd_linter.cli import main
from agentic_tdd_linter.version import __version__


REVIEWER = "codex:gpt-5.5"


class ReviewProofFlowTests(unittest.TestCase):
    def test_check_accepts_current_manifest(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Manifest proof satisfies attestation checks. Linter skips artifacts.

        Verification Method: verify public function output

        Verification Detail:
        Run automatic proof mode with a matching manifest and assert no artifact is created.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact_path = agent_review_artifact_path(test_file, root)
            _write_manifest(root, test_file, source_hash=source_sha256(test_file))
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            artifact_exists = artifact_path.exists()

        self.assertEqual(0, exit_code)
        self.assertFalse(artifact_exists)
        self.assertIn("no issues found", stdout.getvalue())

    def test_check_creates_missing_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Missing `review manifest` causes linter to create artifacts.

        Verification Method: verify public function output

        Verification Detail:
        Run check without a manifest and assert pending artifact is created.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            artifact_path = agent_review_artifact_path(test_file, root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            artifact_exists = artifact_path.is_file()

        self.assertEqual(1, exit_code)
        self.assertTrue(artifact_exists)
        self.assertIn("agent_review_not_run", stdout.getvalue())

    def test_check_creates_stale_artifact(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Stale review manifest causes automatic proof mode to create artifacts.

        Verification Method: verify public function output

        Verification Detail:
        Run check with an old source hash and assert pending artifact is created.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            expected_hash = source_sha256(test_file)
            artifact_path = agent_review_artifact_path(test_file, root)
            _write_manifest(root, test_file, source_hash="0" * 64)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            artifact_text = artifact_path.read_text(encoding="utf-8")

        self.assertEqual(1, exit_code)
        self.assertIn(f"Source SHA256: `{expected_hash}`", artifact_text)
        self.assertIn("agent_review_not_run", stdout.getvalue())

    def test_check_refreshes_manifest(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Reviewed artifact refreshes stale manifest with explicit reviewer.

        Verification Method: verify public function output

        Verification Detail:
        Run check with reviewer and assert manifest hash and reviewer are updated.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            expected_hash = source_sha256(test_file)
            _write_manifest(root, test_file, source_hash="0" * 64)
            _write_artifact(root, test_file)
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
        self.assertEqual(expected_hash, record["source_sha256"])
        self.assertEqual(REVIEWER, record["reviewer"])
        self.assertIn("recorded 1 review attestations", stdout.getvalue())

    def test_check_requires_reviewer(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Manifest refresh requires explicit reviewer identity.

        Verification Method: verify public function output

        Verification Detail:
        Run check without reviewer and assert missing reviewer is reported.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = _write_test_file(root)
            _write_manifest(root, test_file, source_hash="0" * 64)
            _write_artifact(root, test_file)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            record = json.loads(agent_review_manifest_path(root).read_text(encoding="utf-8"))

        self.assertEqual(1, exit_code)
        self.assertEqual("0" * 64, record["source_sha256"])
        self.assertIn("missing_reviewer", stdout.getvalue())


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


def _write_artifact(root: Path, test_file: Path) -> Path:
    artifact_path = agent_review_artifact_path(test_file, root)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        textwrap.dedent(
            f"""
            # Agentic Test Docstring Review

            Test file: `tests/test_sample.py`
            Source SHA256: `{source_sha256(test_file)}`

            ## Agent Review Result

            Status: pass
            Notes:
            - test_adds_values passes review.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return artifact_path


def _write_manifest(root: Path, test_file: Path, *, source_hash: str) -> Path:
    manifest_path = agent_review_manifest_path(root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "path": "tests/test_sample.py",
        "source_sha256": source_hash,
        "status": "pass",
        "linter_version": __version__,
        "review_contract_sha256": review_contract_sha256(root),
        "reviewer": REVIEWER,
    }
    manifest_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return manifest_path


if __name__ == "__main__":
    unittest.main()
