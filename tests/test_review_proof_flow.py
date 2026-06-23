            test_file = _write_test_file(root)
            artifact_path = agent_review_artifact_path(test_file, root)
            _write_manifest(root, test_file, source_hash=source_sha256(test_file))
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["check", "--all", "--repo-root", str(root)])

            artifact_exists = artifact_path.exists()

        self.assertEqual(0, exit_code)
        self.assertFalse(artifact_exists)
        self.assertIn("no issues found", stdout.getvalue())

