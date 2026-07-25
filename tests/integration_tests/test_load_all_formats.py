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
        `create-agent-md` creates a `packet set` from a discovered `.py` test file.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates `src/parser.py` and `tests/test_parser.py`.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>` as a subprocess.
        3. Command produces exit code `0`.
        4. Artifact directory contains one single-test packet.
        5. Artifact directory contains one cross-test packet.
        6. Single-test packet contains the Python file declaration, test name, requirement, and function source.
        7. Cross-test packet contains the Python test-file path and source.

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_creates_pending_packet`
          Justification: Deeper coverage — The lower test proves that one renderer output has exactly 25 pending rows. This test proves Python discovery, extraction, and complete packet content.
        """

        python_source = textwrap.dedent(
            '''\
            """Tests in this file validate `parser` located at `src/parser.py`.
            `parser` is responsible for returning stored text.
            """

            def test_returns_stored_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `parser` returns stored text.
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
            _write_source(repo_root / "src" / "parser.py", "def parse(): return 'stored text'\n")
            _write_source(test_file, python_source)

            creation = _run_cli(repo_root, "create-agent-md")
            packets = _packet_paths(repo_root)
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
        self.assertIn(
            "Tests in this file validate `parser` located at `src/parser.py`.",
            single_packet,
        )
        self.assertIn("`parser` is responsible for returning stored text.", single_packet)
        self.assertIn("`parser` returns stored text.", single_packet)
        self.assertIn("def test_returns_stored_text", single_packet)
        self.assertIn("tests/test_parser.py", cross_packet)
        self.assertIn("def test_returns_stored_text", cross_packet)

    def test_loads_typescript_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `create-agent-md` creates a `packet set` from a discovered `.test.ts` test file.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        1. Harness creates `src/parser.ts` and `tests/parser.test.ts`.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>` as a subprocess.
        3. Command produces exit code `0`.
        4. Artifact directory contains one single-test packet.
        5. Artifact directory contains one cross-test packet.
        6. Single-test packet contains the TypeScript file declaration, test label, JSDoc requirement, and test-call source.
        7. Cross-test packet contains the TypeScript test-file path and source.

        Similar Coverage:
        - Lower Level Test: `test_render_agent_md_file.py::test_creates_pending_packet`
          Justification: Deeper coverage — The lower test proves that one renderer output has exactly 25 pending rows. This test proves TypeScript discovery, extraction, and complete packet content.
        """

        typescript_source = textwrap.dedent(
            '''\
            /**
             * Tests in this file validate `parser` located at `src/parser.ts`.
             * `parser` is responsible for returning stored text.
             */

            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * `parser` returns stored text.
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
            _write_source(repo_root / "src" / "parser.ts", "export const parse = () => 'stored text';\n")
            _write_source(test_file, typescript_source)

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
