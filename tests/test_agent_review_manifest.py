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


EXPECTED_ATTESTATION_LINTER_VERSION = "0.2.0"
REVIEWER = "codex:gpt-5.5"


class AgentReviewManifestTests(unittest.TestCase):
    def test_linter_version_recorded(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Attestation records use the linter version.

        Verification Method: verify public function output

        Verification Detail:
        Version constant equals the expected linter version.
        """

        self.assertEqual(EXPECTED_ATTESTATION_LINTER_VERSION, __version__)

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

        self.assertIn("stale_agent_review_attestation", rules)

