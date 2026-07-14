"""Tests for mapping test functions to agent Markdown files.

Terms:
- `path mapper`: The path mapper converts between a test identity and its agent-packet path. For example, reversing a mapped path restores the original test name.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from agentic_tdd_linter.agentic_linter.map_test_function_to_agent_md_file import (
    map_agent_md_file_to_test_function,
    map_test_function_to_agent_md_file,
)


class AgentMarkdownFileMappingTests(unittest.TestCase):
    def test_round_trip_preserves_test_identity(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The `path mapper` retains identity.
        When callers reverse a path, it restores the test.

        Verification Method: verify public function output

        Verification Detail:
        Restored path equals expected path. Restored name equals expected name.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "tests" / "test_math.py"
            expected_path = Path("tests/test_math.py")
            expected_name = "test_adds_numbers"
            test_file.parent.mkdir(parents=True)
            test_file.write_text(
                textwrap.dedent(
                    '''
                    def test_adds_numbers() -> None:
                        """A test docstring."""
                        assert 1 + 1 == 2
                    '''
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            agent_md_file = map_test_function_to_agent_md_file(
                test_file,
                repo_root,
                test_name=expected_name,
            )

            restored = map_agent_md_file_to_test_function(agent_md_file, repo_root)

        self.assertEqual(expected_path, restored.path)
        self.assertEqual(expected_name, restored.name)


if __name__ == "__main__":
    unittest.main()
