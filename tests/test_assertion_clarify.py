from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.linter_e2e import run_linter_with_review


class AssertionClarifyTests(unittest.TestCase):
    def test_extra_assertion_fails_review(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Agentic review rejects assertions beyond a narrow interpretation of the requirement.

        Verification Method: verify public function output

        Verification Detail:
        by asserting failed review output names the assertion purpose check.
        """
