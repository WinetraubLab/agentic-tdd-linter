class CrossTestAgentMarkdownTests(unittest.TestCase):
    def test_writes_cross_test_packet(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The `renderer` generates cross-test packets.
        When paths repeat, renderer retains canonical path.

        Verification Method: verify public function output

        Verification Detail:
        `Artifact` equals `tests/agentic_review_artifacts/cross_test_review.agent.md`.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_example():\n    assert True\n"
            first = root / "tests" / "test_alpha.py"
            second = root / "tests" / "test_beta.py"
            first.parent.mkdir(parents=True)
            first.write_text(source, encoding="utf-8")
            second.write_text(source, encoding="utf-8")

            artifact = render_cross_test_agent_md_file(
                [first, second, first],
                root,
            )

        self.assertEqual(
            root.resolve()
            / "tests"
            / "agentic_review_artifacts"
            / "cross_test_review.agent.md",
            artifact,
        )

    def test_deduplicates_cross_test_paths(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The `renderer` deduplicates paths.
        When path lists repeat entries, the packet includes each path once.

        Verification Method: verify public function output

        Verification Detail:
        Alpha count equals one. Beta count equals one.
        """

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "def test_example():\n    assert True\n"
            first = root / "tests" / "test_alpha.py"
            second = root / "tests" / "test_beta.py"
            first.parent.mkdir(parents=True)
            first.write_text(source, encoding="utf-8")
            second.write_text(source, encoding="utf-8")

            artifact = render_cross_test_agent_md_file(
                [first, second, first],
                root,
            )
            artifact_text = artifact.read_text(encoding="utf-8")

        self.assertEqual(1, artifact_text.count("`tests/test_alpha.py`"))
        self.assertEqual(1, artifact_text.count("`tests/test_beta.py`"))
