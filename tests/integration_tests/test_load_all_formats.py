"""Tests in this file validate `create-agent-md` located at `src/agentic_tdd_linter/cli/run_lint_pipeline.py`.
`create-agent-md` is responsible for loading and validating Python and TypeScript tests before creating their review scorecards.

Terms:
- `.py`: This suffix identifies a Python test file. For example, `test_parser.py` contains Python tests discovered by the CLI.
- `.test.ts`: This suffix identifies a TypeScript test file. For example, `parser.test.ts` contains TypeScript tests discovered by the CLI.
- `packet set`: A packet set contains one single-test and one cross-test `.agent.md` file populated with a discovered test's documentation and source.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.integration_tests.test_harness.usage_scenarios import (
    packet_paths as _packet_paths,
    run_cli as _run_cli,
    write_source as _write_source,
)


class LoadAllFormatsTests(unittest.TestCase):
    def test_loads_python_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI creates populated single-test and cross-test '.agent.md' files for a discovered Python test file.
        Standard usage: The repository contains one documented `.py` test file.

        Verification Method: verify public function output

        Verification Detail:
        1. Create a temporary repository containing `tests/test_parser.py`.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>` as a subprocess.
        3. Read every generated '.agent.md' file.
        4. Verify that the command succeeds and creates one single-test packet plus one cross-test packet.
        5. Verify that the single-test packet contains the Python test name, requirement, and function source.
        6. Verify that the cross-test packet contains the Python test-file path and source.
        """

        python_source = textwrap.dedent(
            '''\
            """Verify Python parser behavior."""

            def test_returns_stored_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                Parser returns stored text.
                Standard usage: The parser receives stored text.

                Verification Method: verify public function output

                Verification Detail:
                Parser output equals `stored text`.
                """

                assert parse() == "stored text"
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_parser.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(python_source, encoding="utf-8")
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH", "")
            source_root = str(PROJECT_ROOT / "src")
            environment["PYTHONPATH"] = (
                source_root
                if not existing_pythonpath
                else source_root + os.pathsep + existing_pythonpath
            )

            creation = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_tdd_linter.cli.main",
                    "create-agent-md",
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=PROJECT_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            packets = sorted(
                (repo_root / "tests" / "agentic_review_artifacts").glob(
                    "*.agent.md"
                )
            )
            cross_packet_path = next(
                path
                for path in packets
                if path.name == "cross_test_review.agent.md"
            )
            single_packet_path = next(
                path
                for path in packets
                if path.name != "cross_test_review.agent.md"
            )
            single_packet = single_packet_path.read_text(encoding="utf-8")
            cross_packet = cross_packet_path.read_text(encoding="utf-8")

        self.assertEqual(0, creation.returncode, creation.stdout + creation.stderr)
        self.assertEqual(2, len(packets), packets)
        self.assertIn("test_returns_stored_text", single_packet)
        self.assertIn("Parser returns stored text.", single_packet)
        self.assertIn("def test_returns_stored_text", single_packet)
        self.assertIn("tests/test_parser.py", cross_packet)
        self.assertIn("def test_returns_stored_text", cross_packet)

    def test_loads_typescript_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        CLI creates populated single-test and cross-test '.agent.md' files for a discovered TypeScript test file.
        Standard usage: The repository contains one documented `.test.ts` file.

        Verification Method: verify public function output

        Verification Detail:
        1. Create a temporary repository containing `tests/parser.test.ts`.
        2. Run `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>` as a subprocess.
        3. Read every generated '.agent.md' file.
        4. Verify that the command succeeds and creates one single-test packet plus one cross-test packet.
        5. Verify that the single-test packet contains the TypeScript test label, JSDoc requirement, and test-call source.
        6. Verify that the cross-test packet contains the TypeScript test-file path and source.
        """

        typescript_source = textwrap.dedent(
            '''\
            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * Parser returns stored text.
             * Standard usage: The parser receives stored text.
             *
             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Parser output equals `stored text`.
             */
            test("returns stored text", () => {
              assert.equal(parse(), "stored text");
            });
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "parser.test.ts"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(typescript_source, encoding="utf-8")
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH", "")
            source_root = str(PROJECT_ROOT / "src")
            environment["PYTHONPATH"] = (
                source_root
                if not existing_pythonpath
                else source_root + os.pathsep + existing_pythonpath
            )

            creation = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_tdd_linter.cli.main",
                    "create-agent-md",
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=PROJECT_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            packets = sorted(
                (repo_root / "tests" / "agentic_review_artifacts").glob(
                    "*.agent.md"
                )
            )
            cross_packet_path = next(
                path
                for path in packets
                if path.name == "cross_test_review.agent.md"
            )
            single_packet_path = next(
                path
                for path in packets
                if path.name != "cross_test_review.agent.md"
            )
            single_packet = single_packet_path.read_text(encoding="utf-8")
            cross_packet = cross_packet_path.read_text(encoding="utf-8")

        self.assertEqual(0, creation.returncode, creation.stdout + creation.stderr)
        self.assertEqual(2, len(packets), packets)
        self.assertIn("returns stored text", single_packet)
        self.assertIn("Parser returns stored text.", single_packet)
        self.assertIn('test("returns stored text"', single_packet)
        self.assertIn("tests/parser.test.ts", cross_packet)
        self.assertIn('test("returns stored text"', cross_packet)

             * Verification Method: verify public function output
             *
             * Verification Detail:
             * Parser output equals `stored text`.
             */
            test("returns stored text", () => {
              assert.equal(parse(), "stored text");
            });
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "parser.test.ts", typescript_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn("missing_file_docstring", creation.stdout)


if __name__ == "__main__":
    unittest.main()
