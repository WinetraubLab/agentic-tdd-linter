from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.docstrings import all_test_files, requested_test_files


class TestFileDiscoveryTests(unittest.TestCase):
    def test_discovers_python_and_typescript(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test discovery includes Python tests.
        Test discovery includes TypeScript tests.

        Verification Method: verify public function output

        Verification Detail:
        Expected list contains both paths.
        Discovery calls produce expected list.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            tests_root = repo_root / "tests"
            python_test = tests_root / "test_example.py"
            typescript_test = (
                tests_root
                / "primitives"
                / "activity-plan-template-steps"
                / "localArtifactRoundTrip.test.ts"
            )
            ignored_typescript = tests_root / "primitives" / "helper.ts"
            python_test.parent.mkdir(parents=True)
            typescript_test.parent.mkdir(parents=True)
            python_test.write_text(_python_test_source(), encoding="utf-8")
            typescript_test.write_text(_typescript_test_source(), encoding="utf-8")
            ignored_typescript.write_text("export const helper = true;\n", encoding="utf-8")

            all_paths = _relative_paths(all_test_files(repo_root, tests_root), repo_root)
            requested_paths = _relative_paths(requested_test_files(["tests"], repo_root), repo_root)

        expected_paths = [
            Path("tests/primitives/activity-plan-template-steps/localArtifactRoundTrip.test.ts"),
            Path("tests/test_example.py"),
        ]
        self.assertEqual(expected_paths, all_paths)
        self.assertEqual(expected_paths, requested_paths)


def _relative_paths(paths: list[Path], repo_root: Path) -> list[Path]:
    root = repo_root.resolve()
    return [path.resolve().relative_to(root) for path in paths]


def _python_test_source() -> str:
    return textwrap.dedent(
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
    ).strip() + "\n"


def _typescript_test_source() -> str:
    return textwrap.dedent(
        """
        import test from "node:test";
        import assert from "node:assert/strict";

        /**
         * Test Path: happy path
         *
         * Requirement Tested:
         * Local artifact writes survive a primitive round trip.
         *
         * Verification Method: verify public function output
         *
         * Verification Detail:
         * Loaded artifact content equals written artifact content.
         */
        test("local artifact round trip", () => {
          assert.equal(readLocalArtifact(), "saved artifact");
        });
        """
    ).strip() + "\n"


if __name__ == "__main__":
    unittest.main()
