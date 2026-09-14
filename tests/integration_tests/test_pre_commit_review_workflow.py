"""Tests in this file validate `pre-commit review workflow` located at `src/agentic_tdd_linter/cli/run_lint_pipeline.py`.
`pre-commit review workflow` is responsible for maintaining test-review evidence before commit.

Terms:
- `pre-commit review workflow`: The pre-commit review workflow completes the review lifecycle before changes are committed. For example, it refreshes stale scorecards before commit.
- `.agent.md`: An .agent.md file contains one generated agent-review scorecard. For example, create-agent-md regenerates the edited test's .agent.md file.
- `cross_test_review.agent.md`: The cross_test_review.agent.md file reviews relationships among the complete selected test set. For example, create-agent-md --fresh regenerates the cross-test review.
- `agent_review_failed`: The agent_review_failed issue identifies a completed review containing failed criteria. For example, lint emits this issue with skill-based correction guidance.
- `$run-tdd-linter`: The $run-tdd-linter skill coordinates correction of TDD lint failures. For example, failure output directs a coding agent to run this skill.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.integration_tests.test_harness.usage_scenarios import (
    complete_packets as _complete_packets,
    manifest_records as _manifest_records,
    packet_contents as _packet_contents,
    packet_paths as _packet_paths,
    run_cli as _run_cli,
    write_source as _write_source,
)


class PreCommitReviewWorkflowTests(unittest.TestCase):
    def _record_current_review(
        self,
        repo_root: Path,
        *,
        reviewer: str,
        evidence: str,
    ) -> Path:
        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `current review example` located at `src/current.py`.
            `current review example` is responsible for exposing a stable truth value.
            """

            def test_current_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                `current review example` exposes a true value.
                Standard usage: The source and its passing review remain unchanged.

                Verification Method: verify public function output

                Verification Detail:
                The exposed value equals true.
                """

                assert True
            '''
        )
        manifest_path = repo_root / "tests" / "agentic_review_manifest.jsonl"
        _write_source(repo_root / "src" / "current.py", "VALUE = True\n")
        _write_source(repo_root / "tests" / "test_current.py", test_source)
        _run_cli(repo_root, "create-agent-md")
        _complete_packets(repo_root, status="pass", evidence=evidence)
        recorded_lint = _run_cli(
            repo_root,
            "lint",
            "--reviewer",
            reviewer,
        )
        self.assertEqual(0, recorded_lint.returncode)
        return manifest_path

    def _make_review_packets_obsolete(
        self,
        repo_root: Path,
        *,
        completed_evidence: str,
        pending_marker: str,
    ) -> None:
        for packet_path in _packet_paths(repo_root):
            if packet_path.name == "cross_test_review.agent.md":
                packet_path.write_text(
                    f"obsolete relationship review\n{pending_marker}\n",
                    encoding="utf-8",
                )
                continue
            packet_path.write_text(
                packet_path.read_text(encoding="utf-8").replace(
                    f"| pass | {completed_evidence}. |",
                    f"{pending_marker} Replace with review evidence. |",
                ),
                encoding="utf-8",
            )

    def test_current_manifest_generates_zero_packets(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` generates zero review packets when every test has current passing manifest proof.
        Standard usage: The source and its passing proof remain unchanged after review.

        Verification Method: verify public function output

        Verification Detail:
        Create-agent-md succeeds and outputs `generated 0 agent review packets`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies generation creates no packets for unchanged passing proof. The named test verifies generation creates pending packets for one edited test; the current test is happy path, while the named test is failure path.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._record_current_review(
                repo_root,
                reviewer="integration:current-reviewer",
                evidence="current review passed",
            )
            creation = _run_cli(repo_root, "create-agent-md")

        self.assertEqual(0, creation.returncode)
        self.assertIn("generated 0 agent review packets", creation.stdout)

    def test_repeated_generation_preserves_manifest(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` preserves manifest bytes across repeated `create-agent-md` invocations when every test has current passing proof.
        Specialized usage: A pre-commit automation retries `create-agent-md` after losing the first command result, without changing tests or the manifest, so the retry must leave committed review proof byte-identical.

        Verification Method: verify public function output

        Verification Detail:
        Both create-agent-md invocations succeed.
        Manifest bytes after each invocation equal the bytes recorded before either invocation.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_incomplete_review_preserves_manifest`
          Explanation: The current test verifies repeated generation preserves current manifest bytes. The named test verifies incomplete replacement review preserves prior manifest bytes; the current test is happy path, while the named test is failure path.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            manifest_path = self._record_current_review(
                repo_root,
                reviewer="integration:idempotence-reviewer",
                evidence="idempotence review passed",
            )
            manifest_before = manifest_path.read_bytes()
            first_creation = _run_cli(repo_root, "create-agent-md")
            manifest_after_first = manifest_path.read_bytes()
            second_creation = _run_cli(repo_root, "create-agent-md")
            manifest_after_second = manifest_path.read_bytes()

        self.assertEqual(0, first_creation.returncode)
        self.assertEqual(0, second_creation.returncode)
        self.assertEqual(manifest_before, manifest_after_first)
        self.assertEqual(manifest_before, manifest_after_second)

    def test_lint_ignores_obsolete_pending_packets(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` accepts current passing manifest proof without evaluating pending rows in obsolete `.agent.md` and `cross_test_review.agent.md` files.
        Specialized usage: An abandoned review run leaves pending packet files on disk after the tests and manifest return to an already approved state, so ordinary lint must ignore those leftover files.

        Verification Method: verify public function output

        Verification Detail:
        `_packet_contents` identifies pending rows in `.agent.md` and `cross_test_review.agent.md`.
        The lint command produces exit code `0`.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            completed_evidence = "obsolete packet review passed"
            pending_marker = "| pending |"
            self._record_current_review(
                repo_root,
                reviewer="integration:obsolete-packet-reviewer",
                evidence=completed_evidence,
            )
            self._make_review_packets_obsolete(
                repo_root,
                completed_evidence=completed_evidence,
                pending_marker=pending_marker,
            )
            contents = _packet_contents(repo_root)
            individual_packets = [
                text
                for path, text in contents.items()
                if path.name != "cross_test_review.agent.md"
            ]
            cross_packet = next(
                text
                for path, text in contents.items()
                if path.name == "cross_test_review.agent.md"
            )

            lint = _run_cli(repo_root, "lint")

        self.assertTrue(any(pending_marker in text for text in individual_packets))
        self.assertIn(pending_marker, cross_packet)
        self.assertEqual(0, lint.returncode)

    def test_nominal_review_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing one test.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness classifies every generated `.agent.md` scorecard as pass.
        4. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:nominal-reviewer`.
        5. `_manifest_records` output provides the asserted manifest record.
        6. The manifest record contains path `tests/test_arithmetic.py`, test `test_adds_two_numbers`, and status `pass`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_excludes_added_function`
          Explanation: The current test verifies the pre-commit review workflow persists an approved test after its scorecard passes. The named test verifies `build_manifest_from_agent_md_files` omits a new test whose review is incomplete; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_pending_review_is_not_recorded`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies `build_manifest_from_agent_md_files` creates `manifest proof` only after the reviewer completes every scorecard row; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_recording_keeps_current_proof`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies `build_manifest_from_agent_md_files` retains passing `manifest proof` during `orphaned record` cleanup when its source SHA256 matches the current test content; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_main.py::test_lint_requires_reviewer`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies `CLI` emits missing_reviewer for completed `.agent.md` files when `reviewer identity` is absent; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_retains_supplied_reviewer`
          Explanation: The current test verifies `pre-commit review workflow` persists the approved test's path, name, and status. The named test verifies the workflow retains the reviewer supplied to lint in that test's manifest record; both use happy path, but exercise materially different record fields.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies a failed `.agent.md` scorecard directs callers to `$run-tdd-linter`; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_classic_linter_errors_scenario`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_classic_linter_guidance_scenario`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies conventional lint failure directs callers to `$run-tdd-linter`; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_lint_before_packet_creation_scenario`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies missing review proof replaces create-agent-md command guidance with `$run-tdd-linter` guidance; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; the current test is happy path, while the named test is failure path.
        - Module Difference: `test_review_documentation.py::test_readme_shows_review_workflow`
          Explanation: The current test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes. The named test verifies `test_review_documentation` requires README to list the `pre-commit review workflow` in this order: create `.agent.md` files, review them, then persist manifest proof through reviewer-authenticated lint; both exercise materially the same scenario through different named modules or contract subjects.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `addition` located at `src/arithmetic.py`.
            `addition` is responsible for combining numbers into their sum.

            Terms:
            - `addition`: Addition combines two numbers into their sum. For example, one plus one produces two.
            """

            def test_adds_two_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `addition` produces the sum of two numbers.
                Standard usage: The operands are positive integers.

                Verification Method: verify public function output

                Verification Detail:
                One plus one equals `2`.
                """

                assert 1 + 1 == 2
            '''
        )
        expected_test_path = "tests/test_arithmetic.py"
        expected_test_name = "test_adds_two_numbers"
        expected_reviewer = "integration:nominal-reviewer"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(
                repo_root / "src" / "arithmetic.py",
                "def add(a, b): return a + b\n",
            )
            _write_source(repo_root / expected_test_path, test_source)

            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence="nominal review passed")
            _run_cli(repo_root, "lint", "--reviewer", expected_reviewer)
            records = _manifest_records(repo_root)

        self.assertEqual(
            {
                "path": expected_test_path,
                "test": expected_test_name,
                "status": "pass",
            },
            {
                key: records[0][key]
                for key in ("path", "test", "status")
            },
        )

    def test_retains_supplied_reviewer(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` retains the reviewer supplied to lint in the approved test's manifest record.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        The manifest record's reviewer equals `integration:nominal-reviewer` supplied to lint.

        Similar Coverage:
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `pre-commit review workflow` retains the reviewer supplied to lint in the approved test's manifest record. The named test verifies the workflow persists the approved test's path, name, and status; both use happy path, but exercise materially different record fields.
        - Happy/Failure Path Difference: `test_main.py::test_lint_requires_reviewer`
          Explanation: The current test verifies `pre-commit review workflow` retains the reviewer supplied to lint. The named test verifies `CLI` rejects a completed scorecard when reviewer identity is absent; the current test is happy path, while the named test is failure path.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `addition` located at `src/arithmetic.py`.
            `addition` is responsible for combining numbers into their sum.

            Terms:
            - `addition`: Addition combines two numbers into their sum. For example, one plus one produces two.
            """

            def test_adds_two_numbers() -> None:
                """Test Path: happy path

                Requirement Tested:
                `addition` produces the sum of two numbers.
                Standard usage: The operands are positive integers.

                Verification Method: verify public function output

                Verification Detail:
                One plus one equals `2`.
                """

                assert 1 + 1 == 2
            '''
        )
        expected_reviewer = "integration:nominal-reviewer"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(
                repo_root / "src" / "arithmetic.py",
                "def add(a, b): return a + b\n",
            )
            _write_source(repo_root / "tests" / "test_arithmetic.py", test_source)

            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence="nominal review passed")
            _run_cli(repo_root, "lint", "--reviewer", expected_reviewer)
            records = _manifest_records(repo_root)

        self.assertEqual(expected_reviewer, records[0]["reviewer"])

    def test_lint_before_packet_creation_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance when lint detects an unreviewed valid test.
        Specialized usage: Caller invokes lint before review proof exists, so `pre-commit review workflow` emits missing_required_agent_md with skill-based guidance and no create-agent-md command.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing one conventionally valid unreviewed test.
        2. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository>` before create-agent-md.
        3. `pre-commit review workflow` output contains missing_required_agent_md.
        4. `pre-commit review workflow` output contains `Run the `$run-tdd-linter` skill.` and omits a create-agent-md command.

        Similar Coverage:
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_classic_linter_errors_scenario`
          Explanation: The current test verifies `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance for an unreviewed valid test. The named test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_classic_linter_guidance_scenario`
          Explanation: The current test verifies `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance for an unreviewed valid test. The named test verifies conventional lint failure output directs callers to `$run-tdd-linter`; both use failure path, but exercise materially different failure scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Explanation: The current test verifies `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance for an unreviewed valid test. The named test verifies a failed `.agent.md` scorecard directs callers to `$run-tdd-linter`; both use failure path, but exercise materially different failure scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance for an unreviewed valid test. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance for an unreviewed valid test. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_review_documentation.py::test_readme_directs_tdd_linter_skill`
          Explanation: The current test verifies failure output replaces create-agent-md command guidance with `$run-tdd-linter` guidance. The named test verifies README installation guidance asks the coding agent to run `$run-tdd-linter`; the current test is failure path, while the named test is happy path.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `unreviewed behavior` located at `src/unreviewed.py`.
            `unreviewed behavior` is responsible for evaluating boolean expressions.
            """

            def test_unreviewed_behavior() -> None:
                """Test Path: happy path

                Requirement Tested:
                `unreviewed behavior` evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "unreviewed.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_unreviewed.py", test_source)

            lint = _run_cli(repo_root, "lint")

        self.assertIn("missing_required_agent_md", lint.stdout)
        self.assertIn("Run the `$run-tdd-linter` skill.", lint.stdout)
        self.assertNotIn("agentic-tdd-linter create-agent-md", lint.stdout)

    def test_classic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` prevents `.agent.md` creation when conventional lint fails.
        Specialized usage: The test lacks Requirement Tested, so the workflow emits missing_requirement and creates zero `.agent.md` files.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing a test whose docstring lacks Requirement Tested.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `missing_requirement`.
        4. Packet list contains zero `.agent.md` paths.

        Similar Coverage:
        - Module Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement. The named test verifies `conventional_linter` emits missing_requirement when `Requirement Tested` contains nothing; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_lint_before_packet_creation_scenario`
          Explanation: The current test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement. The named test verifies failure output replaces create-agent-md command guidance with `$run-tdd-linter` guidance for an unreviewed valid test; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_classic_linter_guidance_scenario`
          Explanation: The current test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement. The named test verifies the same failure directs callers to `$run-tdd-linter`; both use failure path, but prove materially different outcomes.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_refresh_scenario`
          Explanation: The current test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement. The named test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh; the current test is failure path, while the named test is happy path.
        """

        invalid_test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `invalid fixture` located at `src/invalid.py`.
            `invalid fixture` is responsible for representing invalid documentation.
            """

            def test_invalid_documentation() -> None:
                """Test Path: failure path

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "invalid.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_invalid.py", invalid_test_source)

            creation = _run_cli(repo_root, "create-agent-md")
            packets = _packet_paths(repo_root)

        self.assertIn("missing_requirement", creation.stdout)
        self.assertEqual([], packets)

    def test_classic_linter_guidance_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` directs callers to `$run-tdd-linter` when conventional lint fails.
        Specialized usage: A test without Requirement Tested produces missing_requirement with skill-based guidance.

        Verification Method: verify public function output

        Verification Detail:
        Command output contains missing_requirement and `Run the `$run-tdd-linter` skill.`.

        Similar Coverage:
        - Module Difference: `test_docstring_structure.py::test_reports_empty_requirement`
          Explanation: The current test verifies conventional failure output directs callers to `$run-tdd-linter` when Requirement Tested is empty. The named test verifies `conventional_linter` emits missing_requirement for the empty field; both exercise materially the same scenario through different named modules or contract subjects.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_classic_linter_errors_scenario`
          Explanation: The current test verifies conventional lint failure directs callers to `$run-tdd-linter`. The named test verifies the same failure prevents `.agent.md` creation; both use failure path, but prove materially different outcomes.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_lint_before_packet_creation_scenario`
          Explanation: The current test verifies conventional lint failure directs callers to `$run-tdd-linter`. The named test verifies missing review proof replaces create-agent-md command guidance with `$run-tdd-linter` guidance; both use failure path, but exercise materially different failure scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Explanation: The current test verifies conventional lint failure directs callers to `$run-tdd-linter`. The named test verifies a failed `.agent.md` scorecard directs callers to `$run-tdd-linter`; both use failure path, but exercise materially different failure scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies conventional lint failure directs callers to `$run-tdd-linter`. The named test verifies `pre-commit review workflow` persists an approved test after review succeeds; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies conventional lint failure directs callers to `$run-tdd-linter`. The named test verifies `pre-commit review workflow` regenerates review packets after a test changes; both use failure path, but exercise materially different failure scenarios.
        - Happy/Failure Path Difference: `test_review_documentation.py::test_readme_directs_tdd_linter_skill`
          Explanation: The current test verifies conventional failure output directs callers to `$run-tdd-linter`. The named test verifies README installation guidance asks the coding agent to run `$run-tdd-linter`; the current test is failure path, while the named test is happy path.
        """

        invalid_test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `invalid fixture` located at `src/invalid.py`.
            `invalid fixture` is responsible for representing invalid documentation.
            """

            def test_invalid_documentation() -> None:
                """Test Path: failure path

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "invalid.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_invalid.py", invalid_test_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn("missing_requirement", creation.stdout)
        self.assertIn("Run the `$run-tdd-linter` skill.", creation.stdout)

    def test_agentic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` replaces create-agent-md command guidance with `$run-tdd-linter` guidance when a completed `.agent.md` review contains a failed criterion.
        Specialized usage: When a completed `.agent.md` review contains a failed criterion, the workflow emits agent_review_failed with skill-based guidance and no create-agent-md command.

        Verification Method: verify public function output

        Verification Detail:
        1. A completed `.agent.md` review contains a failed criterion.
        2. `_run_cli` output contains `agent_review_failed`.
        3. `_run_cli` output contains `Run the `$run-tdd-linter` skill.`.
        4. `_run_cli` output omits the create-agent-md command.

        Similar Coverage:
        - Scenario Difference: `test_determine_agent_md_status.py::test_derives_fail_status`
          Explanation: The current test verifies `pre-commit review workflow` directs callers to `$run-tdd-linter` after a failed `.agent.md` review. The named test verifies `determine_agent_md_status` derives fail status when any `.agent.md` row has fail status; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_determine_agent_md_status.py::test_derives_pass_status`
          Explanation: The current test verifies `pre-commit review workflow` directs callers to `$run-tdd-linter` after a failed `.agent.md` review. The named test verifies `determine_agent_md_status` derives pass status when every scorecard row succeeds; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `pre-commit review workflow` directs callers to `$run-tdd-linter` after a failed `.agent.md` review. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_lint_before_packet_creation_scenario`
          Explanation: The current test verifies a failed `.agent.md` scorecard directs callers to `$run-tdd-linter`. The named test verifies missing review proof replaces create-agent-md command guidance with `$run-tdd-linter` guidance; both use failure path, but exercise materially different failure scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_classic_linter_guidance_scenario`
          Explanation: The current test verifies a failed `.agent.md` scorecard directs callers to `$run-tdd-linter`. The named test verifies conventional lint failure directs callers to `$run-tdd-linter`; both use failure path, but exercise materially different failure scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `pre-commit review workflow` directs callers to `$run-tdd-linter` after a failed `.agent.md` review. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_review_documentation.py::test_readme_directs_tdd_linter_skill`
          Explanation: The current test verifies failed-scorecard output directs callers to `$run-tdd-linter`. The named test verifies README installation guidance asks the coding agent to run `$run-tdd-linter`; the current test is failure path, while the named test is happy path.
        """

        passing_source = textwrap.dedent(
            '''\
            """Tests in this file validate `passing review behavior` located at `src/passing.py`.
            `passing review behavior` is responsible for evaluating approved boolean expressions.
            """

            def test_passing_review() -> None:
                """Test Path: happy path

                Requirement Tested:
                `passing review behavior` evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )
        failing_source = textwrap.dedent(
            '''\
            """Tests in this file validate `failing review behavior` located at `src/failing.py`.
            `failing review behavior` is responsible for evaluating rejected boolean expressions.
            """

            def test_failing_review() -> None:
                """Test Path: happy path

                Requirement Tested:
                `failing review behavior` evaluates to true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The expression equals true.
                """

                assert True
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "passing.py", "VALUE = True\n")
            _write_source(repo_root / "src" / "failing.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_passing.py", passing_source)
            _write_source(repo_root / "tests" / "test_failing.py", failing_source)
            _run_cli(repo_root, "create-agent-md")

            _complete_packets(repo_root, status="pass", evidence="mixed review passed")
            failing_packet = next(
                path
                for path in _packet_paths(repo_root)
                if "test_failing" in path.name
            )
            failing_text = failing_packet.read_text(encoding="utf-8").replace(
                "| pass | mixed review passed. |",
                "| fail | requirement is too vague. |",
                1,
            )
            failing_packet.write_text(failing_text, encoding="utf-8")
            lint = _run_cli(repo_root, "lint", "--reviewer", "integration:failure-reviewer")

        self.assertIn("agent_review_failed", lint.stdout)
        self.assertIn("Run the `$run-tdd-linter` skill.", lint.stdout)
        self.assertNotIn("agentic-tdd-linter create-agent-md", lint.stdout)

    def test_stale_test_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` creates only an edited test's pending `.agent.md` and every pending relationship involving that test in `cross_test_review.agent.md` when unchanged tests have passing manifest proof.
        Standard usage: After every test passes review, a developer edits one test and reruns `create-agent-md`, which requests a new review only for the edited test and its relationships.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing three tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness classifies every review as successful.
        4. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:approved-reviewer` to persist passing proof.
        5. Harness modifies only the first test source outside the `pre-commit review workflow`.
        6. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        7. Edited-test `.agent.md` contains `| pending | Replace with review evidence. |`.
        8. `cross_test_review.agent.md` contains every pending relationship involving the edited test and excludes the unchanged-versus-unchanged relationship.
        9. Unchanged tests receive no individual `.agent.md` packets.

        Similar Coverage:
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_added_function_preserves_existing_proof`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies `build_manifest_from_agent_md_files` preserves `manifest proof` for an unchanged test when a new test function appears in its file; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_function_proof_removed`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies `build_manifest_from_agent_md_files` removes an `orphaned record` while preserving `manifest proof` for an unchanged test in the same file; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_render_agent_md_file.py::test_creates_pending_packet`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_agentic_linter_errors_scenario`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies `pre-commit review workflow` requires editors to consider every scorecard criterion, including passed criteria, before fixing a test with a failed `.agent.md` review; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_lint_before_packet_creation_scenario`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies missing review proof replaces create-agent-md command guidance with `$run-tdd-linter` guidance; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_classic_linter_guidance_scenario`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies conventional lint failure directs callers to `$run-tdd-linter`; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_nominal_review_scenario`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies `pre-commit review workflow` persists an approved test in the manifest when its `.agent.md` scorecard passes; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_refresh_scenario`
          Explanation: The current test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships. The named test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_current_manifest_generates_zero_packets`
          Explanation: The current test verifies generation creates only review work involving one edited test. The named test verifies repeated generation creates no review work when every test and proof remains unchanged; the current test is failure path, while the named test is happy path.
        """

        original_source = textwrap.dedent(
            '''\
            """Tests in this file validate `truth example` located at `src/truth.py`.
            `truth example` is responsible for evaluating documented boolean expressions.
            """

            def test_first_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                `truth example` evaluates the first expression as true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The first expression equals true.
                """

                assert True

            def test_second_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                `truth example` evaluates the second expression as true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The second expression equals true.
                """

                assert True

            def test_third_truth() -> None:
                """Test Path: happy path

                Requirement Tested:
                `truth example` evaluates the third expression as true.
                Standard usage: The expression is the boolean value true.

                Verification Method: verify public function output

                Verification Detail:
                The third expression equals true.
                """

                assert True
            '''
        )
        edited_source = original_source.replace(
            "`truth example` evaluates the first expression as true.",
            "`truth example` evaluates the documented first expression.",
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_truth.py"
            _write_source(repo_root / "src" / "truth.py", "VALUE = True\n")
            _write_source(test_file, original_source)
            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence="approved before source edit")

            _run_cli(
                repo_root,
                "lint",
                "--reviewer",
                "integration:approved-reviewer",
            )
            single_packets = [
                path
                for path in _packet_paths(repo_root)
                if path.name != "cross_test_review.agent.md"
            ]
            first_packet = next(
                path for path in single_packets if "test_first_truth" in path.name
            )
            cross_packet = next(
                path
                for path in _packet_paths(repo_root)
                if path.name == "cross_test_review.agent.md"
            )

            _write_source(test_file, edited_source)
            creation = _run_cli(repo_root, "create-agent-md")
            contents_after = _packet_contents(repo_root)
            edited_packet_after = contents_after[first_packet]
            cross_packet_after = contents_after[cross_packet]
            single_packets_after = [
                path
                for path in contents_after
                if path.name != "cross_test_review.agent.md"
            ]

        self.assertIn(
            "| pending | Replace with review evidence. |",
            edited_packet_after,
        )
        self.assertNotIn("approved before source edit", edited_packet_after)
        self.assertIn("generated 2 agent review packets", creation.stdout)
        self.assertEqual([first_packet], single_packets_after)
        self.assertIn(
            "| pending | pending | Replace with classification evidence. |",
            cross_packet_after,
        )
        self.assertNotIn("approved before source edit", cross_packet_after)
        self.assertIn(
            "tests/test_truth.py::test_first_truth",
            cross_packet_after,
        )
        self.assertIn(
            "tests/test_truth.py::test_second_truth",
            cross_packet_after,
        )
        self.assertIn(
            "tests/test_truth.py::test_third_truth",
            cross_packet_after,
        )
        self.assertNotIn(
            "| `tests/test_truth.py::test_second_truth` | "
            "`tests/test_truth.py::test_third_truth` |",
            cross_packet_after,
        )


    def test_removes_obsolete_single_test_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` removes an obsolete single-test `.agent.md` during ordinary generation.
        Specialized usage: A caller invokes packet generation a second time after renaming test_current to test_renamed. On the second invocation, `pre-commit review workflow` removes test_current's `.agent.md` because it is now obsolete.

        Verification Method: verify public function output

        Verification Detail:
        `_packet_paths` output initially contains the original function's packet.
        `_packet_paths` output excludes the obsolete packet after the test function is renamed.

        Similar Coverage:
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_refresh_scenario`
          Explanation: The current test verifies `pre-commit review workflow` removes an obsolete single-test `.agent.md` during ordinary generation. The named test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh; both use happy path, but exercise materially different scenarios.
        """

        initial_source = textwrap.dedent(
            '''\
            """Tests in this file validate `truth example` located at `src/truth.py`.
            `truth example` is responsible for evaluating documented boolean expressions.
            """

            def test_current() -> None:
                """Test Path: happy path

                Requirement Tested:
                `truth example` evaluates the current expression as true.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                The current expression equals true.
                """

                assert True

            '''
        )
        renamed_source = initial_source.replace("test_current", "test_renamed")

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_truth.py"
            _write_source(repo_root / "src" / "truth.py", "VALUE = True\n")
            _write_source(test_file, initial_source)
            _run_cli(repo_root, "create-agent-md", "--fresh")
            initial_packets = _packet_paths(repo_root)
            obsolete_packets = [
                path
                for path in initial_packets
                if path.name != "cross_test_review.agent.md"
            ]
            _write_source(test_file, renamed_source)
            _run_cli(repo_root, "create-agent-md")
            current_packets = _packet_paths(repo_root)
            current_names = {path.name for path in current_packets}

        self.assertEqual(
            ["test_truth__test_current.agent.md"],
            [path.name for path in obsolete_packets],
        )
        self.assertNotIn(
            "test_truth__test_current.agent.md",
            current_names,
        )

    def test_refresh_scenario(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and pending `cross_test_review.agent.md` when create-agent-md runs with unscoped --fresh.
        Specialized usage: When a populated folder contains completed and obsolete files instead of the pending current-test set, `pre-commit review workflow` produces the pending current-test set.

        Verification Method: verify public function output

        Verification Detail:
        1. `_packet_paths` output contains one named single-test `.agent.md` file for each current test and `cross_test_review.agent.md`.
        2. `_packet_contents` output gives every scorecard row status `pending`.
        3. `_packet_contents` output contains no prior completed evidence.
        4. `_packet_paths` output excludes the extra deleted-test file.
        5. Refreshed `cross_test_review.agent.md` content differs from its completed predecessor.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_build_manifest_from_agent_md_files.py::test_deleted_file_proof_removed`
          Explanation: The current test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh. The named test verifies `build_manifest_from_agent_md_files` eliminates every `orphaned record` whose reviewed file no longer exists; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_render_agent_md_file.py::test_creates_pending_packet`
          Explanation: The current test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh. The named test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_classic_linter_errors_scenario`
          Explanation: The current test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh. The named test verifies `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_removes_obsolete_single_test_packet`
          Explanation: The current test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh. The named test verifies `pre-commit review workflow` removes an obsolete single-test `.agent.md` during ordinary generation; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_pre_commit_review_workflow.py::test_stale_test_requires_review`
          Explanation: The current test verifies `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh. The named test verifies `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships; the current test is happy path, while the named test is failure path.
        - Scenario Difference: `test_pre_commit_review_workflow.py::test_current_manifest_generates_zero_packets`
          Explanation: The current test verifies explicit fresh generation recreates every packet despite current proof. The named test verifies repeated ordinary generation preserves current proof without creating packets; both use happy path, but exercise materially different scenarios.
        """

        first_source = textwrap.dedent(
            '''\
            """Tests in this file validate `first refresh expression` located at `src/first_refresh.py`.
            `first refresh expression` is responsible for evaluating the first refresh value.
            """

            def test_first_refresh() -> None:
                """Test Path: happy path

                Requirement Tested:
                `first refresh expression` evaluates to true.
                Standard usage: The expression is unchanged.

                Verification Method: verify public function output

                Verification Detail:
                The first expression equals true.
                """

                assert True
            '''
        )
        second_source = textwrap.dedent(
            '''\
            """Tests in this file validate `second refresh expression` located at `src/second_refresh.py`.
            `second refresh expression` is responsible for evaluating the second refresh value.
            """

            def test_second_refresh() -> None:
                """Test Path: happy path

                Requirement Tested:
                `second refresh expression` evaluates to true.
                Standard usage: The expression is unchanged.

                Verification Method: verify public function output

                Verification Detail:
                The second expression equals true.
                """

                assert True
            '''
        )
        reviewed_evidence = "completed before fresh review"

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "first_refresh.py", "VALUE = True\n")
            _write_source(repo_root / "src" / "second_refresh.py", "VALUE = True\n")
            _write_source(repo_root / "tests" / "test_first.py", first_source)
            _write_source(repo_root / "tests" / "test_second.py", second_source)
            _run_cli(repo_root, "create-agent-md")
            _complete_packets(repo_root, status="pass", evidence=reviewed_evidence)
            _run_cli(
                repo_root,
                "lint",
                "--reviewer",
                "integration:refresh-reviewer",
            )
            cross_packet_path = next(
                path
                for path in _packet_paths(repo_root)
                if path.name == "cross_test_review.agent.md"
            )
            cross_packet_before = _packet_contents(repo_root)[cross_packet_path]
            obsolete_packet_path = (
                repo_root
                / "tests"
                / "agentic_review_artifacts"
                / "test_deleted__test_deleted.agent.md"
            )
            obsolete_packet_path.write_text("obsolete packet\n", encoding="utf-8")

            _run_cli(repo_root, "create-agent-md", "--fresh")
            refreshed_packets = _packet_paths(repo_root)
            expected_single_packet_names = {
                "test_first__test_first_refresh.agent.md",
                "test_second__test_second_refresh.agent.md",
            }
            actual_single_packet_names = {
                path.name
                for path in refreshed_packets
                if path.name != "cross_test_review.agent.md"
            }
            refreshed_contents_by_path = _packet_contents(repo_root)
            refreshed_contents = list(refreshed_contents_by_path.values())
            refreshed_statuses = [
                [
                    cells[3]
                    for line in text.splitlines()
                    if len(cells := [cell.strip() for cell in line.split("|")]) >= 6
                    and (
                        cells[1].isdigit()
                        or cells[1].startswith("`tests/")
                    )
                ]
                for text in refreshed_contents
            ]
            cross_packet_after = refreshed_contents_by_path[cross_packet_path]

        self.assertEqual(3, len(refreshed_packets))
        self.assertEqual(
            expected_single_packet_names,
            actual_single_packet_names,
        )
        self.assertTrue(
            all(statuses and set(statuses) == {"pending"} for statuses in refreshed_statuses)
        )
        self.assertNotEqual(cross_packet_before, cross_packet_after)
        self.assertTrue(all(reviewed_evidence not in text for text in refreshed_contents))
        self.assertNotIn(obsolete_packet_path, refreshed_packets)

if __name__ == "__main__":
    unittest.main()
