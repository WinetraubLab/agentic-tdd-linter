    def test_dispatches_python_file(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        File extraction selects Python parsers.
        When paths end in `.py`, dispatch invokes Python extraction.

        Verification Method: verify public function output

        Verification Detail:
        The public function produces `test_alpha`.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "test_sample.py"
            test_file.write_text("def test_alpha():\n    assert True\n", encoding="utf-8")

            extracted_tests = extract_tests_from_file(test_file, repo_root)

        self.assertEqual("test_alpha", extracted_tests[0].name)

    def test_dispatches_typescript_file(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        File extraction selects TypeScript parsers.
        When paths end in `.test.ts`, dispatch invokes TypeScript extraction.

        Verification Method: verify public function output

        Verification Detail:
        The public function produces `alpha`.
        """

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            test_file = repo_root / "sample.test.ts"
            test_file.write_text('test("alpha", () => {});\n', encoding="utf-8")

            extracted_tests = extract_tests_from_file(test_file, repo_root)

        self.assertEqual("alpha", extracted_tests[0].name)


def _public_functions_in(module_path: Path) -> list[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    return [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]


if __name__ == "__main__":
    unittest.main()
