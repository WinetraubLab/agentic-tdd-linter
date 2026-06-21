from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_tdd_linter.docstrings import (
    _is_allowed_test_path,
    _is_allowed_verification_method,
)


class ClassificationTests(unittest.TestCase):
    def test_r01_accepts_happy_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts happy path as a valid test path classification.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it accepts the value.
        """

        self.assertTrue(_is_allowed_test_path("happy path"))

    def test_r01_accepts_failure_path(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts failure path as a valid test path classification.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it accepts the value.
        """

        self.assertTrue(_is_allowed_test_path("failure path"))

    def test_r01_rejects_other_path(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects values outside the allowed test path classifications.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it rejects an unsupported value.
        """

        self.assertFalse(_is_allowed_test_path("edge path"))

    def test_r02_accepts_public_output(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts "public function output" as a valid verification method.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it accepts the value.
        """

        self.assertTrue(_is_allowed_verification_method("verify public function output"))

    def test_r02_accepts_private_output(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts "private function output" as a valid verification method.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it accepts the value.
        """

        self.assertTrue(_is_allowed_verification_method("verify private function output"))

    def test_r02_accepts_visual_inspection(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Linter accepts "visual inspection by user" as a valid verification method.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it accepts the value.
        """

        self.assertTrue(_is_allowed_verification_method("visual inspection by user"))

    def test_r02_rejects_other_method(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Linter rejects values outside the allowed verification method classifications.

        Verification Method: verify private function output

        Verification Detail:
        by calling the private classification helper and asserting it rejects an unsupported value.
        """

        self.assertFalse(_is_allowed_verification_method("verify database state"))


if __name__ == "__main__":
    unittest.main()
