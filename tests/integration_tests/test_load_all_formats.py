"""Tests in this file validate `create-agent-md` located at `src/agentic_tdd_linter/cli/run_lint_pipeline.py`.
`create-agent-md` is responsible for loading and validating Python and TypeScript tests before creating their review scorecards.

Terms:
- `.py`: This suffix identifies a Python test file. For example, `test_parser.py` contains Python tests discovered by the CLI.
- `.test.ts`: This suffix identifies a TypeScript test file. For example, `parser.test.ts` contains TypeScript tests discovered by the CLI.
- `packet set`: A packet set contains one single-test `.agent.md` file populated with a discovered test's documentation and source and one cross-test `.agent.md` file populated with test identifiers and docstrings.
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

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates `src/parser.py` and `tests/test_parser.py`.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository> --fresh` as a subprocess.
        3. Command produces exit code `0`.
        4. Artifact directory contains one single-test packet.
        5. Artifact directory contains one cross-test packet.
        6. Single-test packet contains `test_returns_stored_text`.
        7. Single-test packet contains `Tests in this file validate `parser` located at `src/parser.py`.`.
        8. Single-test packet contains `` `parser` is responsible for returning stored text.``.
        9. Single-test packet contains `` `parser` provides stored text.``.
        10. Single-test packet contains `def test_returns_stored_text`.
        11. Cross-test packet contains `tests/test_parser.py::test_returns_stored_text`.
        12. Cross-test packet contains `## Test Docstrings`.
        13. Cross-test packet contains `` `parser` provides stored text.``.
        14. Cross-test packet excludes `def test_returns_stored_text`.

        Similar Coverage:
        - Scenario Difference: `test_render_agent_md_file.py::test_creates_pending_packet`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file. The named test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_main.py::test_test_root_reports_generated_packet`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file. The named test verifies `CLI` emits `CLI output` with the generated `.agent.md` count when caller selects a nondefault test root; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_load_all_formats.py::test_loads_typescript_tests`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file. The named test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_rejects_python_without_file_docstring`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file. The named test verifies `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_rejects_typescript_without_file_docstring`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file. The named test verifies `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation; the current test is happy path, while the named test is failure path.
        """

        python_source = textwrap.dedent(
            '''\
            """Tests in this file validate `parser` located at `src/parser.py`.
            `parser` is responsible for returning stored text.
            """

            def test_returns_stored_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `parser` provides stored text.
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

            creation = _run_cli(repo_root, "create-agent-md", "--fresh")
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
        self.assertIn("`parser` provides stored text.", single_packet)
        self.assertIn("def test_returns_stored_text", single_packet)
        self.assertIn(
            "tests/test_parser.py::test_returns_stored_text",
            cross_packet,
        )
        self.assertIn("## Test Docstrings", cross_packet)
        self.assertIn("`parser` provides stored text.", cross_packet)
        self.assertNotIn("def test_returns_stored_text", cross_packet)

    def test_loads_typescript_tests(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates `src/parser.ts` and `tests/parser.test.ts`.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository> --fresh` as a subprocess.
        3. Command produces exit code `0`.
        4. Artifact directory contains one single-test packet.
        5. Artifact directory contains one cross-test packet.
        6. Single-test packet contains `returns stored text`.
        7. Single-test packet contains `Tests in this file validate `parser` located at `src/parser.ts`.`.
        8. Single-test packet contains `` `parser` is responsible for returning stored text.``.
        9. Single-test packet contains `` `parser` provides stored text.``.
        10. Single-test packet contains `test("returns stored text"`.
        11. Cross-test packet contains `tests/parser.test.ts::returns stored text`.
        12. Cross-test packet contains `## Test Docstrings`.
        13. Cross-test packet contains `` `parser` provides stored text.``.
        14. Cross-test packet excludes `test("returns stored text"`.

        Similar Coverage:
        - Scenario Difference: `test_render_agent_md_file.py::test_creates_pending_packet`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file. The named test verifies `render_agent_md_file` creates `single-test packet` containing its supplied test source exactly once and exactly 26 pending scorecard rows; both use happy path, but exercise materially different scenarios.
        - Scenario Difference: `test_load_all_formats.py::test_loads_python_tests`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file. The named test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file; both use happy path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_rejects_python_without_file_docstring`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file. The named test verifies `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation; the current test is happy path, while the named test is failure path.
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_rejects_typescript_without_file_docstring`
          Explanation: The current test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file. The named test verifies `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation; the current test is happy path, while the named test is failure path.
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
             * `parser` provides stored text.
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

            creation = _run_cli(repo_root, "create-agent-md", "--fresh")
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
        self.assertIn("returns stored text", single_packet)
        self.assertIn(
            "Tests in this file validate `parser` located at `src/parser.ts`.",
            single_packet,
        )
        self.assertIn("`parser` is responsible for returning stored text.", single_packet)
        self.assertIn("`parser` provides stored text.", single_packet)
        self.assertIn('test("returns stored text"', single_packet)
        self.assertIn(
            "tests/parser.test.ts::returns stored text",
            cross_packet,
        )
        self.assertIn("## Test Docstrings", cross_packet)
        self.assertIn("`parser` provides stored text.", cross_packet)
        self.assertNotIn('test("returns stored text"', cross_packet)

    def test_rejects_python_without_file_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation.
        Specialized usage: The `.py` file contains a documented test but omits its file docstring, so `create-agent-md` emits missing_file_docstring.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a `.py` file containing one fully documented test and no file docstring.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `missing_file_docstring`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_loads_python_tests`
          Explanation: The current test verifies `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation. The named test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_loads_typescript_tests`
          Explanation: The current test verifies `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation. The named test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_load_all_formats.py::test_rejects_typescript_without_file_docstring`
          Explanation: The current test verifies `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation. The named test verifies `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation; both use failure path, but exercise materially different scenarios.
        """

        python_source = textwrap.dedent(
            '''\
            def test_returns_stored_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `parser` provides stored text.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                Parser output equals `stored text`.
                """

                assert parse() == "stored text"
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "test_parser.py", python_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn("missing_file_docstring", creation.stdout)

    def test_rejects_typescript_without_file_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation.
        Specialized usage: The `.test.ts` file contains documented test JSDoc but omits file-level JSDoc, so `create-agent-md` emits missing_file_docstring.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a `.test.ts` file containing one fully documented test and no file-level JSDoc.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `missing_file_docstring`.

        Similar Coverage:
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_loads_python_tests`
          Explanation: The current test verifies `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation. The named test verifies `create-agent-md` creates a `packet set` from a discovered `.py` test file; the current test is failure path, while the named test is happy path.
        - Happy/Failure Path Difference: `test_load_all_formats.py::test_loads_typescript_tests`
          Explanation: The current test verifies `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation. The named test verifies `create-agent-md` creates a `packet set` when it discovers a `.test.ts` test file; the current test is failure path, while the named test is happy path.
        - Scenario Difference: `test_load_all_formats.py::test_rejects_python_without_file_docstring`
          Explanation: The current test verifies `create-agent-md` emits missing_file_docstring when a `.test.ts` file omits file-level documentation. The named test verifies `create-agent-md` emits missing_file_docstring when a `.py` test file omits file-level documentation; both use failure path, but exercise materially different scenarios.
        """

        typescript_source = textwrap.dedent(
            '''\
            import test from "node:test";
            import assert from "node:assert/strict";

            /**
             * Test Path: happy path
             *
             * Requirement Tested:
             * `parser` provides stored text.
             * Standard usage: The scenario demonstrates baseline behavior.
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
            _write_source(repo_root / "tests" / "parser.test.ts", typescript_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn("missing_file_docstring", creation.stdout)

    def test_rejects_requirement_without_declared_module(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `create-agent-md` requires every test requirement to identify the module declared by its test file.
        Specialized usage: The file declares parser, but one test requirement does not identify parser, so `create-agent-md` emits a multiple_modules_in_test_file issue.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates one file declaring `parser` and containing a requirement that does not identify parser.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `multiple_modules_in_test_file`.

        Similar Coverage:
        - Scenario Difference: `test_load_all_formats.py::test_instructs_split_for_multiple_modules`
          Explanation: The current test verifies `create-agent-md` requires every test requirement to identify the module declared by its test file. The named test verifies `create-agent-md` instructs the caller to create one test file per declared module when a test file contains tests that declare multiple modules; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_load_all_formats.py::test_rejects_missing_module`
          Explanation: The current test verifies `create-agent-md` requires every test requirement to identify the module declared by its test file. The named test verifies `create-agent-md` emits missing_test_module when a test file declares a module path that does not exist; both use failure path, but exercise materially different scenarios.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `parser` located at `src/parser.py`.
            `parser` is responsible for returning stored text.
            """

            def test_parses_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `parser` returns stored text.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                Parser output equals `stored text`.
                """

                assert parse() == "stored text"

            def test_formats_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                Formatting text returns formatted text.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                Formatter output equals `formatted text`.
                """

                assert format_text() == "formatted text"
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "parser.py", "def parse(): return 'stored text'\n")
            _write_source(repo_root / "tests" / "test_parser.py", test_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn("multiple_modules_in_test_file", creation.stdout)

    def test_instructs_split_for_multiple_modules(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `create-agent-md` instructs the caller to create one test file per declared module when a test file contains tests that declare multiple modules.
        Specialized usage: One test requirement identifies formatter instead of the declared parser, so `create-agent-md` prescribes one module per test file.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates one file declaring `parser` and containing parser and formatter tests.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `split this test file so each file validates one module`.

        Similar Coverage:
        - Scenario Difference: `test_load_all_formats.py::test_rejects_missing_module`
          Explanation: The current test verifies `create-agent-md` instructs the caller to create one test file per declared module when a test file contains tests that declare multiple modules. The named test verifies `create-agent-md` emits missing_test_module when a test file declares a module path that does not exist; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_load_all_formats.py::test_rejects_requirement_without_declared_module`
          Explanation: The current test verifies `create-agent-md` instructs the caller to create one test file per declared module when a test file contains tests that declare multiple modules. The named test verifies `create-agent-md` requires every test requirement to identify the module declared by its test file; both use failure path, but exercise materially different scenarios.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `parser` located at `src/parser.py`.
            `parser` is responsible for returning stored text.
            """

            def test_parses_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `parser` returns stored text.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                Parser output equals `stored text`.
                """

                assert parse() == "stored text"

            def test_formats_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `formatter` returns formatted text.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                Formatter output equals `formatted text`.
                """

                assert format_text() == "formatted text"
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "src" / "parser.py", "def parse(): return 'stored text'\n")
            _write_source(repo_root / "tests" / "test_parser.py", test_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn(
            "split this test file so each file validates one module",
            creation.stdout,
        )

    def test_rejects_missing_module(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `create-agent-md` emits missing_test_module when a test file declares a module path that does not exist.
        Specialized usage: The declaration identifies src/parser.py, but that file does not exist, so `create-agent-md` emits missing_test_module.

        Verification Method: verify public function output

        Verification Detail:
        1. Harness creates a test file declaring `src/parser.py` without creating that module.
        2. Harness invokes `agentic-tdd-linter create-agent-md --repo-root <temporary-repository>`.
        3. Command output contains `missing_test_module`.

        Similar Coverage:
        - Scenario Difference: `test_load_all_formats.py::test_instructs_split_for_multiple_modules`
          Explanation: The current test verifies `create-agent-md` emits missing_test_module when a test file declares a module path that does not exist. The named test verifies `create-agent-md` instructs the caller to create one test file per declared module when a test file contains tests that declare multiple modules; both use failure path, but exercise materially different scenarios.
        - Scenario Difference: `test_load_all_formats.py::test_rejects_requirement_without_declared_module`
          Explanation: The current test verifies `create-agent-md` emits missing_test_module when a test file declares a module path that does not exist. The named test verifies `create-agent-md` requires every test requirement to identify the module declared by its test file; both use failure path, but exercise materially different scenarios.
        - Happy/Failure Path Difference: `test_source_module_structure.py::test_tests_have_source_or_harness`
          Explanation: The current test verifies `create-agent-md` emits missing_test_module when a test file declares a module path that does not exist. The named test verifies `test_source_module_structure` requires every `test module` in agentic_linter, cli, conventional_linter, and indexing_test_functions to have a same-basename `source module` or `test-harness module`; the current test is failure path, while the named test is happy path.
        """

        test_source = textwrap.dedent(
            '''\
            """Tests in this file validate `parser` located at `src/parser.py`.
            `parser` is responsible for returning stored text.
            """

            def test_returns_stored_text() -> None:
                """Test Path: happy path

                Requirement Tested:
                `parser` returns stored text.
                Standard usage: The scenario demonstrates baseline behavior.

                Verification Method: verify public function output

                Verification Detail:
                Parser output equals `stored text`.
                """

                assert parse() == "stored text"
            '''
        )

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            _write_source(repo_root / "tests" / "test_parser.py", test_source)

            creation = _run_cli(repo_root, "create-agent-md")

        self.assertIn("missing_test_module", creation.stdout)


if __name__ == "__main__":
    unittest.main()
