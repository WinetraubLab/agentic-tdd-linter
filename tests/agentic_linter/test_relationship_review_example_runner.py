"""Tests in this file validate `test_relationship_review_example_runner` located at `tests/agentic_linter/test_harness/test_relationship_review_example_runner.py`.
`test_relationship_review_example_runner` is responsible for evaluating docstring-only test-relationship YAML examples.

Terms:
- `test-relationship YAML example`: A test-relationship YAML example contains two test identifiers, their docstrings, an expected pair classification, and expected relationship scorecards.
- `docstring-only packet`: A docstring-only packet evaluates Similar Coverage without embedding either test implementation.
- `pair classification`: A pair classification records `yes` or `no` for requirement-description overlap between two tests.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.agentic_linter.test_harness.test_relationship_review_example_runner import (
    run_test_relationship_review_examples,
)
from tests.agentic_linter.test_harness.test_relationship_review_yaml_fixture_contract import (
    EXAMPLES,
    lint_test_relationship_review_examples,
)


class TestRelationshipReviewExampleRunnerTests(unittest.TestCase):
    def test_demos_generate_pair_tables(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_relationship_review_example_runner` generates one `docstring-only packet` with a `pair classification` and a scorecard for each test in every `test-relationship YAML example`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The demo fixture passes schema validation.
        The first runner invocation identifies three pending packets.
        Each packet contains two test identifiers, `## Test Docstrings`, one pair-classification row, and two `## Review Scorecard` headings.
        Each packet states that test implementations are absent.
        """

        self.assertEqual(
            [],
            lint_test_relationship_review_examples(examples_path=EXAMPLES),
        )
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            artifact_root = temporary_root / "artifacts"
            report_path = temporary_root / "report.json"

            with self.assertRaisesRegex(RuntimeError, "examples are pending"):
                run_test_relationship_review_examples(
                    examples_path=EXAMPLES,
                    artifact_root=artifact_root,
                    report_path=report_path,
                )

            packets = tuple(sorted(artifact_root.glob("*.agent.md")))
            packet_texts = [
                packet.read_text(encoding="utf-8")
                for packet in packets
            ]
            combined_packet_text = "\n".join(packet_texts)

        self.assertEqual(3, len(packets))
        self.assertTrue(
            all("## Test Docstrings" in text for text in packet_texts)
        )
        self.assertTrue(
            all(
                "## Requirement Pair Classifications" in text
                for text in packet_texts
            )
        )
        self.assertIn(
            "tests/unit/test_invoice_total.py::test_calculates_invoice_total",
            combined_packet_text,
        )
        self.assertIn(
            "tests/integration/test_invoice_checkout.py::"
            "test_checkout_displays_invoice_total",
            combined_packet_text,
        )
        self.assertIn(
            "tests/unit/test_user_cache.py::test_removes_expired_entries",
            combined_packet_text,
        )
        self.assertIn(
            "tests/unit/test_session_cache.py::test_removes_expired_entries",
            combined_packet_text,
        )
        self.assertIn(
            "tests/unit/test_config_parser.py::test_rejects_malformed_syntax",
            combined_packet_text,
        )
        self.assertIn(
            "tests/integration/test_audit_archive.py::"
            "test_archives_completed_records",
            combined_packet_text,
        )
        self.assertTrue(
            all(
                text.count("\n## Review Scorecard\n") == 2
                for text in packet_texts
            )
        )
        self.assertTrue(
            all(
                "Do not require or infer test implementation that is absent"
                in text
                for text in packet_texts
            )
        )

    def test_completed_demo_matches_expectations(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `test_relationship_review_example_runner` compares each completed test scorecard with the corresponding expectations in a `test-relationship YAML example`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The harness applies mock.patch.dict to supply the reviewer identity while marking expected pair classifications and every scorecard row.
        The completed run returns three reviewed packets.
        The test-relationship report records three YAML cases, six docstrings, and twenty-seven successful checks.
        """

        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            artifact_root = temporary_root / "artifacts"
            report_path = temporary_root / "report.json"
            with self.assertRaises(RuntimeError):
                run_test_relationship_review_examples(
                    examples_path=EXAMPLES,
                    artifact_root=artifact_root,
                    report_path=report_path,
                )
            packet_paths = tuple(sorted(artifact_root.glob("*.agent.md")))
            for packet_path in packet_paths:
                packet_text = packet_path.read_text(encoding="utf-8")
                overlap = (
                    "no"
                    if packet_path.stem.startswith("similar_coverage_003_unrelated_requirements_case")
                    else "yes"
                )
                completed_text = packet_text.replace(
                    "| pending | Replace with overlap evidence. |",
                    f"| {overlap} | Pair classification matches the fixture. |",
                ).replace("| pending |", "| pass |")
                packet_path.write_text(completed_text, encoding="utf-8")

            with mock.patch.dict(
                "os.environ",
                {"AGENT_REVIEW_MODEL": "demo-reviewer medium"},
            ):
                result = run_test_relationship_review_examples(
                    examples_path=EXAMPLES,
                    artifact_root=artifact_root,
                    report_path=report_path,
                )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(packet_paths, result.agent_md_files)
        self.assertEqual("test-relationship", report["review_type"])
        self.assertEqual(
            ["cross-test", "relational", "Similar Coverage"],
            report["review_type_aliases"],
        )
        self.assertEqual(3, report["yaml_cases"])
        self.assertEqual(6, report["test_docstrings"])
        self.assertEqual("27/27 (100% pass)", report["total"]["success"])
        self.assertEqual("3/3 (100% pass)", report["criteria"]["10"]["success"])


if __name__ == "__main__":
    unittest.main()
