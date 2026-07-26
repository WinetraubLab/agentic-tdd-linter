"""Tests in this file validate `map_test_function_to_agent_md_file` located at `src/agentic_tdd_linter/agentic_linter/map_test_function_to_agent_md_file.py`.
`map_test_function_to_agent_md_file` is responsible for mapping test identities to `.agent.md` paths and recovering test identities from those paths.

Terms:
- `path mapper`: The path mapper converts between a test identity and its agent-packet path. For example, reversing a mapped path returns the original test name.
- `test identity`: Test identity combines a repository-relative path and function name. For example, tests/test_math.py and test_adds_numbers identify one test.
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
        `map_test_function_to_agent_md_file` round trip recovers both repository-relative path and function name of `test identity`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        `path mapper` restores `test identity` with path `tests/test_math.py`.
        `path mapper` restores `test identity` with name `test_adds_numbers`.

        Similar Coverage:
        - Higher Level Test: `test_load_all_formats.py::test_loads_python_tests`
          Justification: Deeper coverage — The current test directly verifies round-trip recovery of the test path and function name. The higher test uses the mapping during complete Python packet loading without isolating its reverse mapping.
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
