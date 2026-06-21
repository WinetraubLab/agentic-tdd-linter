class GenericWordingTests(unittest.TestCase):
    def test_repeated_requirement_fails(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        Repeated requirements fail review.

        Verification Method: verify public function output

        Verification Detail:
        The output reports generic wording.
        """

        source = '''
            def test_normalizes_name() -> None:
                """Test Path: happy path

                Requirement Tested:
                Parser returns normalized value.

                Verification Method: verify public function output

                Verification Detail:
                The assertion compares a lowercase name.
                """

                assert normalize_name("Ada") == "ada"


            def test_normalizes_city() -> None:
                """Test Path: happy path

                Requirement Tested:
                Parser returns normalized value.

                Verification Method: verify public function output

                Verification Detail:
                The assertion compares a lowercase city.
                """

                assert normalize_city("Paris") == "paris"
        '''

        result = run_linter_source_with_review(
            source=source,
            status="fail",
            note=(
                "Notify Generic Requirement: Fail. The same requirement appears "
                "in multiple tests, so each requirement should name the specific "
                "behavior under review."
            ),
        )

        self.assertEqual(1, result.exit_code)
        self.assertIn("agent_review_failed", result.output)
        self.assertIn("Generic Requirement", result.output)
