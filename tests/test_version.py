"""Tests in this file validate `version` located at `src/agentic_tdd_linter/version.py`.
`version` is responsible for exposing package version metadata.

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
        `version` defines `__version__` equal to `project.version`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify public function output

        Verification Detail:
        Package metadata declares `project.version` equal to `__version__`.

        """

        repo_root = Path(__file__).resolve().parents[1]
        metadata = tomllib.loads(
            (repo_root / "pyproject.toml").read_text(encoding="utf-8")
        )
        project_version = metadata["project"]["version"]

        self.assertEqual(project_version, __version__)


if __name__ == "__main__":
    unittest.main()
