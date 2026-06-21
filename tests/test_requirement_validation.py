from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.docstrings import lint_test_files


class RequirementValidationTests(unittest.TestCase):
    def test_mock_call_without_detail_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Mock calls require mock detail.

        Verification Method: verify private function output

        Verification Detail:
        Rule set includes `mocking_detail_missing` for a Mock call.
        """

        rules = _lint_source(
            """
            from unittest.mock import Mock


            def test_fetches_value() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                service produces normalized text.

                Verification Method: verify public function output

                Verification Detail:
                Normalized text equals `ok`.
                \"\"\"

                dependency = Mock(return_value="ok")
                assert dependency() == "ok"
            """
        )

        self.assertIn("mocking_detail_missing", rules)

    def test_patch_decorator_without_detail_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Patch decorators require mock detail.

        Verification Method: verify private function output

        Verification Detail:
        Rule set includes `mocking_detail_missing` for a patch decorator.
        """

        rules = _lint_source(
            """
            from unittest.mock import patch


            @patch("test_sample.lookup")
            def test_reads_lookup(patched_lookup) -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                lookup produces normalized text.

                Verification Method: verify public function output

                Verification Detail:
                Normalized text equals `ok`.
                \"\"\"

                patched_lookup.return_value = "ok"
                assert patched_lookup() == "ok"
            """
        )

        self.assertIn("mocking_detail_missing", rules)

    def test_mock_detail_passes(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Mock detail permits mocked dependencies.

        Verification Method: verify private function output

        Verification Detail:
        Rule set excludes `mocking_detail_missing` when detail names mocking.
        """

        rules = _lint_source(
            """
            from unittest.mock import Mock


            def test_fetches_value() -> None:
                \"\"\"Test Path: happy path

                Requirement Tested:
                service produces normalized text.

                Verification Method: verify public function output

                Verification Detail:
                Mocked dependency produces normalized text.
                \"\"\"

                dependency = Mock(return_value="ok")
                assert dependency() == "ok"
            """
        )

        self.assertNotIn("mocking_detail_missing", rules)


def _lint_source(source: str) -> set[str]:
    with tempfile.TemporaryDirectory() as directory:
        repo_root = Path(directory)
        test_file = repo_root / "test_sample.py"
        test_file.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")

        return {issue.rule for issue in lint_test_files([test_file], repo_root)}


if __name__ == "__main__":
    unittest.main()
