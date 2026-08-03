"""Tests in this file validate `pre-commit review workflow` located at `src/agentic_tdd_linter/cli/run_lint_pipeline.py`.
`pre-commit review workflow` is responsible for maintaining test-review evidence before commit.

Terms:
- `pre-commit review workflow`: The pre-commit review workflow completes the review lifecycle before changes are committed. For example, it refreshes stale scorecards before commit.
- `.agent.md`: An .agent.md file contains one generated agent-review scorecard. For example, create-agent-md regenerates the edited test's .agent.md file.
- `cross_test_review.agent.md`: The cross_test_review.agent.md file reviews relationships among the complete selected test set. For example, create-agent-md --fresh regenerates the cross-test review.
- `agent_review_failed`: The agent_review_failed issue identifies a completed review containing failed criteria. For example, lint emits this issue with correction instructions.
- `failed-review correction procedure`: A failed-review correction procedure tells editors to read the complete scorecard in every failed .agent.md, evaluate the test and docstring against every criterion including passing criteria, and regenerate the selected packets once. For example, agent_review_failed output provides this procedure.
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
        5. `_manifest_records` output provides the asserted manifest fields.
        6. Manifest contains path `tests/test_arithmetic.py`.
        7. Manifest contains test `test_adds_two_numbers`.
        8. Manifest contains status `pass`.
        9. Manifest contains reviewer `integration:nominal-reviewer`.

        Similar Coverage:
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_recording_keeps_current_proof`
          Justification: Deeper coverage — The lower test proves orphan cleanup preserves current `manifest proof`. The current test proves the complete `pre-commit review workflow`.
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_pending_review_is_not_recorded`
          Justification: Deeper coverage — The lower test proves pending scorecards leave manifest proof absent. The current test proves completed scorecards create proof through the full workflow.
        - Lower Level Test: `test_main.py::test_lint_requires_reviewer`
          Justification: Deeper coverage — The lower test proves completed reviews require reviewer identity. The current test proves reviewer-authenticated lint records completed reviews through the full workflow.
        - Higher Level Test: `test_review_documentation.py::test_readme_shows_review_workflow`
          Justification: Deeper coverage — The current test executes the review lifecycle. The higher test verifies that README documents the same ordered lifecycle.
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
                "reviewer": expected_reviewer,
            },
            {
                key: records[0][key]
                for key in ("path", "test", "status", "reviewer")
            },
        )

    def test_lint_before_packet_creation_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` instructs callers to create an `.agent.md` when lint detects an unreviewed valid test.
        Specialized usage: Caller invokes lint before create-agent-md, so `pre-commit review workflow` emits missing_required_agent_md guidance naming create-agent-md.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing one conventionally valid unreviewed test.
        2. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository>` before create-agent-md.
        3. `pre-commit review workflow` output contains missing_required_agent_md.
        4. `pre-commit review workflow` output contains `agentic-tdd-linter create-agent-md`.
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
        self.assertIn("agentic-tdd-linter create-agent-md", lint.stdout)

    def test_classic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` prevents `.agent.md` creation when conventional linter emits missing_requirement.
        Specialized usage: The test lacks Requirement Tested, so `pre-commit review workflow` creates zero `.agent.md` files.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing a test whose docstring lacks Requirement Tested.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `missing_requirement`.
        4. Packet list contains zero `.agent.md` paths.

        Similar Coverage:
        - Lower Level Test: `test_docstring_structure.py::test_reports_empty_requirement`
          Justification: Diagnostic completeness — The lower test proves the exact missing-requirement rule. The current test proves that the rule prevents packet creation through the `pre-commit review workflow`.
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

    def test_agentic_linter_errors_scenario(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` requires editors to consider every scorecard criterion, including passed criteria, before fixing a test with a failed `.agent.md` review.
        Specialized usage: One of two completed `.agent.md` reviews fails, so lint reports agent_review_failed and provides the full-scorecard correction steps.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing two tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness marks one generated `.agent.md` review as pass and the other as fail.
        4. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:failure-reviewer`.
        5. `_run_cli` output contains `agent_review_failed`.
        6. `_run_cli` output directs editors to the complete scorecard in each failed `.agent.md` packet.
        7. `_run_cli` output instructs editors to evaluate the proposed test and docstring against every criterion, including criteria that passed.
        8. `_run_cli` output contains `Regenerate the selected packets once`.

        Similar Coverage:
        - Lower Level Test: `test_determine_agent_md_status.py::test_derives_pass_status`
          Justification: Deeper coverage — The lower test proves pass-status derivation. The current test combines a passing review with a failed review through the `pre-commit review workflow`.
        - Lower Level Test: `test_determine_agent_md_status.py::test_derives_fail_status`
          Justification: Deeper coverage — The lower test proves fail-status precedence. The current test proves that a failed review produces the `pre-commit review workflow` diagnostic.
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
        self.assertIn(
            "read the complete scorecard in each failed `.agent.md` packet",
            lint.stdout,
        )
        self.assertIn(
            "evaluate the proposed test and docstring against every criterion",
            lint.stdout,
        )
        self.assertIn("including criteria that passed", lint.stdout)
        self.assertIn("Regenerate the selected packets once", lint.stdout)

    def test_stale_test_requires_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `pre-commit review workflow` requires a new review only for an edited test and its cross-test relationships.
        Specialized usage: Two tests in the same file have approved `.agent.md` files, but caller edits one test, so its `.agent.md` and `cross_test_review.agent.md` become pending while the unchanged test's `.agent.md` stays approved.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a temporary repository containing two tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Harness classifies every review as successful.
        4. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository> --reviewer integration:approved-reviewer` to persist passing proof.
        5. Harness modifies only the first test source outside the `pre-commit review workflow`.
        6. Harness invokes `agentic-tdd-linter lint --repo-root <temporary-repository>` again.
        7. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        8. Edited-test and cross-test '.agent.md' files contain `| pending | Replace with review evidence. |`.
        9. Unchanged-test '.agent.md' content retains `approved before source edit`.
        10. Cross-test '.agent.md' contains `tests/test_first.py` and excludes `tests/test_second.py`.

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_creates_pending_packet`
          Justification: Deeper coverage — The lower test proves that one renderer output has exactly 25 pending rows. The current test proves which packets regenerate after a source edit and which packet remains unchanged.
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_added_function_preserves_existing_proof`
          Justification: Deeper coverage — The lower test isolates proof preservation after adding a function. The current test proves selective packet regeneration after editing one function.
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_deleted_function_proof_removed`
          Justification: Deeper coverage — The lower test isolates proof cleanup after deleting a function. The current test proves selective packet regeneration after editing one function.
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
            second_packet = next(
                path for path in single_packets if "test_second_truth" in path.name
            )
            cross_packet = next(
                path
                for path in _packet_paths(repo_root)
                if path.name == "cross_test_review.agent.md"
            )

            _write_source(test_file, edited_source)
            _run_cli(repo_root, "lint")
            _run_cli(repo_root, "create-agent-md")
            contents_after = _packet_contents(repo_root)
            edited_packet_after = contents_after[first_packet]
            unchanged_packet_after = contents_after[second_packet]
            cross_packet_after = contents_after[cross_packet]

        self.assertIn(
            "| pending | Replace with review evidence. |",
            edited_packet_after,
        )
        self.assertNotIn("approved before source edit", edited_packet_after)
        self.assertIn("approved before source edit", unchanged_packet_after)
        self.assertNotIn(
            "| pending | Replace with review evidence. |",
            unchanged_packet_after,
        )
        self.assertIn(
            "| pending | Replace with review evidence. |",
            cross_packet_after,
        )
        self.assertNotIn("approved before source edit", cross_packet_after)
        self.assertIn("tests/test_truth.py", cross_packet_after)
    def test_removes_obsolete_single_test_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `pre-commit review workflow` removes an obsolete single-test `.agent.md` during ordinary generation.
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
        `pre-commit review workflow` replaces the complete `.agent.md` set with one pending single-test file per current test and one pending cross-test file when create-agent-md runs with unscoped --fresh.
        Specialized usage: For refresh of a populated folder instead of an empty folder, `pre-commit review workflow` removes completed and obsolete files before creating the pending current-test set.

        Verification Method: verify public function output

        Verification Detail:
        1. `_packet_paths` output contains two single-test `.agent.md` files and one cross-test `.agent.md` file.
        2. `_packet_contents` output gives every scorecard row status `pending`.
        3. `_packet_contents` output contains no prior completed evidence.
        4. `_packet_paths` output excludes the extra deleted-test file.

        Similar Coverage:
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_deleted_file_proof_removed`
          Justification: Deeper coverage — The lower test isolates manifest-proof removal after test-file deletion. The current test verifies that unscoped refresh rebuilds the complete `.agent.md` file set.
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
            refreshed_contents_by_path = _packet_contents(repo_root)
            refreshed_contents = list(refreshed_contents_by_path.values())
            refreshed_statuses = [
                [
                    cells[3]
                    for line in text.splitlines()
                    if len(cells := [cell.strip() for cell in line.split("|")]) >= 5
                    and cells[1].isdigit()
                ]
                for text in refreshed_contents
            ]
            cross_packet_after = refreshed_contents_by_path[cross_packet_path]

        self.assertEqual(3, len(refreshed_packets))
        self.assertTrue(
            all(statuses and set(statuses) == {"pending"} for statuses in refreshed_statuses)
        )
        self.assertNotEqual(cross_packet_before, cross_packet_after)
        self.assertTrue(all(reviewed_evidence not in text for text in refreshed_contents))
        self.assertNotIn(obsolete_packet_path, refreshed_packets)

if __name__ == "__main__":
    unittest.main()
