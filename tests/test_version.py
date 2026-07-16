"""Tests for package version metadata.

Terms:
- `__version__`: This package attribute exposes the installed linter version. For example, it equals the version declared in pyproject.toml.
- `project.version`: This metadata field declares the package version in pyproject.toml. For example, a release updates project.version before packaging.
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from agentic_tdd_linter.version import __version__


class VersionTests(unittest.TestCase):
    def test_matches_package_metadata(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `project.version` corresponds to `__version__`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `_project_version` parses `project.version`.
        `_project_version` result equals `__version__`.

        Similar Coverage:
        - Lower Level Test: `test_build_manifest_from_agent_md_files.py::test_package_version_matches_manifest_contract`
          Justification: Deeper coverage — Lower test verifies manifest-version equality, which this metadata test omits.
        """

        repo_root = Path(__file__).resolve().parents[1]
        project_version = _project_version(repo_root / "pyproject.toml")

        self.assertEqual(project_version, __version__)


def _project_version(metadata_path: Path) -> str:
    metadata = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
    return metadata["project"]["version"]


if __name__ == "__main__":
    unittest.main()
