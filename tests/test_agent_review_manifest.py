    def test_package_metadata_matches_linter_version(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Package metadata uses the linter version.

        Verification Method: verify public function output

        Verification Detail:
        Pyproject version equals the runtime version constant.
        """

        pyproject = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual(__version__, pyproject["project"]["version"])
        self.assertIn("stale_agent_review_attestation", rules)

