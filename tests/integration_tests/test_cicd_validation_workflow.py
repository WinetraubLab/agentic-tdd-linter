"""Tests in this file validate `CI/CD linter` located at `src/agentic_tdd_linter/cli/run_lint_pipeline.py`.
`CI/CD linter` is responsible for validating committed review proof without creating review packets.

Terms:
- `CI/CD linter`: CI/CD linter runs `agentic-tdd-linter lint` in an automated pipeline against committed manifest proof. For example, it validates current proof without generating `.agent.md` files.
- `.agent.md`: An .agent.md file contains a review scorecard that create-agent-md generates for a test. For example, CI validates committed manifest proof without recreating these files.
"""

from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.integration_tests.test_harness.usage_scenarios import (
    record_approved_manifest as _record_approved_manifest,
    remove_packet_directory as _remove_packet_directory,
    run_cli as _run_cli,
    write_source as _write_source,
)


class CicdValidationWorkflowTests(unittest.TestCase):
    def test_outdated_version_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `CI/CD linter` emits missing_required_agent_md when manifest proof records a linter version different from the installed linter version.
        Specialized usage: The manifest records a modified linter version instead of the installed linter version, so `CI/CD linter` emits missing_required_agent_md.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates a temporary repository containing one valid test.
        2. Harness completes its review.
        3. Harness persists passing manifest proof before invoking `CI/CD linter`.
        4. Harness appends `-outdated` to the manifest's installed linter version.
        5. Harness removes the existing '.agent.md' files to reproduce `CI/CD linter` input.
        6. Harness invokes `CI/CD linter` using `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:version-reviewer`.
        7. `CI/CD linter` output contains missing_required_agent_md.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `current review proof` located at `src/review_proof.py`.
            `current review proof` is responsible for recording the linter version that approved a test.
            """

            def test_version_sensitive_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                `current review proof` remains valid for the linter release that recorded it.
                Standard usage: The installed linter records the completed review.

                Verification Method: verify public function output

                Verification Detail:
                The reviewed expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(
                repo_root / "src" / "review_proof.py",
                "PROOF = 'current'\n",
            )
            _write_source(repo_root / "tests" / "test_version.py", test_source)
            reviewer = "integration:version-reviewer"
            _record_approved_manifest(
                repo_root,
                reviewer=reviewer,
                review_status="pass",
                review_evidence="approved version fixture",
            )
            manifest_path = repo_root / "tests" / "agentic_review_manifest.jsonl"
            record = json.loads(manifest_path.read_text(encoding="utf-8"))
            recorded_version = record["linter_version"]
            record["linter_version"] = f"{recorded_version}-outdated"
            manifest_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            _remove_packet_directory(repo_root)

            lint = _run_cli(repo_root, "lint", "--reviewer", reviewer)

        self.assertIn("missing_required_agent_md", lint.stdout)

