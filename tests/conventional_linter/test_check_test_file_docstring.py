    def test_reports_missing_file_docstring(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        The `check` requires file docstrings.

        Verification Method: verify public function output

        Verification Detail:
        The issue rule equals `missing_file_docstring`.
        The issue test name equals `<module>`.
        The issue line equals `1`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            test_file = root / "tests" / "test_sample.py"
            test_file.parent.mkdir()
            test_file.write_text(
                "def test_sample():\n    assert True\n",
                encoding="utf-8",
            )

            issues = check_test_file_docstring(test_file, root)

        self.assertEqual(["missing_file_docstring"], [issue.rule for issue in issues])
        self.assertEqual(["<module>"], [issue.test_name for issue in issues])
        self.assertEqual([1], [issue.line for issue in issues])
