from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_ROOT))

from helpers.linter_e2e import review


E2E_MODULE = TEST_ROOT / "helpers" / "linter_e2e.py"


class E2EReviewIntegrityTests(unittest.TestCase):
    def test_e2e_has_one_public_function(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` exposes one public function.

        Verification Method: verify public function output

        Verification Detail:
        AST lists one public function name.
        """

        tree = ast.parse(E2E_MODULE.read_text(encoding="utf-8"))
        public_functions = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and "_" not in node.name
        ]

        self.assertEqual(["review"], public_functions)

    def test_tests_import_review_only(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test files import `e2e` through its public function.

        Verification Method: verify public function output

        Verification Detail:
        Import list contains `review` only.
        """

        invalid_imports: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in {"linter_e2e", "helpers.linter_e2e"}:
                            invalid_imports.append(f"{test_file}:{node.lineno}")
                if not isinstance(node, ast.ImportFrom):
                    continue
                module = node.module or ""
                imported_names = [alias.name for alias in node.names]
                if module == "helpers" and "linter_e2e" in imported_names:
                    invalid_imports.append(f"{test_file}:{node.lineno}")
                if module == "helpers.linter_e2e" and imported_names != ["review"]:
                    invalid_imports.append(f"{test_file}:{node.lineno}")

        self.assertEqual([], invalid_imports)

    def test_review_requires_keywords(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` public parameters require keyword names.
        Keyword-only arguments prevent hidden parameters.

        Verification Method: verify public function output

        Verification Detail:
        Function signature begins with `*`.
        """

        tree = ast.parse(E2E_MODULE.read_text(encoding="utf-8"))
        public_functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and "_" not in node.name
        ]
        self.assertEqual(1, len(public_functions))
        function = public_functions[0]
        signature_text = _signature_text(E2E_MODULE, function)

        self.assertTrue(signature_text.lstrip().startswith("*,"), signature_text)

    def test_review_parameter_names(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` public parameters use approved names.

        Verification Method: verify public function output

        Verification Detail:
        Signature names `scenario_name` and `test_source_code`.
        """

        tree = ast.parse(E2E_MODULE.read_text(encoding="utf-8"))
        public_functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and "_" not in node.name
        ]
        self.assertEqual(1, len(public_functions))
        function = public_functions[0]
        parameter_names = [argument.arg for argument in function.args.kwonlyargs]

        self.assertEqual(["scenario_name", "test_source_code"], parameter_names)

    def test_review_parameter_types(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` public parameters use approved types.

        Verification Method: verify public function output

        Verification Detail:
        Signature types are `str`.
        """

        tree = ast.parse(E2E_MODULE.read_text(encoding="utf-8"))
        public_functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and "_" not in node.name
        ]
        self.assertEqual(1, len(public_functions))
        invalid_parameters: list[str] = []

        for function in public_functions:
            invalid_parameters.extend(
                f"{function.name}.{argument.arg}"
                for argument in function.args.posonlyargs + function.args.args
            )
            if function.args.vararg is not None:
                invalid_parameters.append(f"{function.name}.{function.args.vararg.arg}")
            if function.args.kwarg is not None:
                invalid_parameters.append(f"{function.name}.{function.args.kwarg.arg}")
            allowed_parameters = [
                (argument.arg, _annotation_name(argument.annotation))
                for argument in function.args.kwonlyargs
            ]
            self.assertEqual(
                [("scenario_name", "str"), ("test_source_code", "str")],
                allowed_parameters,
            )

        self.assertEqual([], invalid_parameters)

    def test_review_pending_raises(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        New scenario without `review artifact` raises error.

        Verification Method: verify public function output

        Verification Detail:
        Remove previous `.agent.md` file when it exists.
        Run `e2e`; it creates the `.agent.md` file and raises an error
        so the agent can review it before running `e2e` again.
        """

        scenario_name = "test_new_case"
        _delete_scenario(scenario_name)
        artifact_path = (
            TEST_ROOT.parent
            / "temporary_fixtures"
            / "agentic_review_artifacts"
            / f"{scenario_name}.agent.md"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            (
                "did not run, agent should review "
                "temporary_fixtures/agentic_review_artifacts/test_new_case.agent.md "
                "and then run test again"
            ),
        ):
            review(
                scenario_name=scenario_name,
                test_source_code="""
                    def test_new_case() -> None:
                        \"\"\"Test Path: happy path

                        Requirement Tested:
                        Addition returns a positive sum.

                        Verification Method: verify public function output

                        Verification Detail:
                        Result value is positive.
                        \"\"\"

                        assert 1 + 1 > 0
                """,
            )

        self.assertTrue(artifact_path.exists())

        """Test Path: happy path

        Requirement Tested:
        `e2e` command result returns pass status.

        Verification Method: verify public function output

        Verification Detail:
        Return tuple starts with true.
        """

        passed, reason = review(
            command="this command passes"
        )

        self.assertIs(True, passed)

    def test_e2e_review_returns_fail_with_reason(self) -> None:
        """Test Path: failure path

        Requirement Tested:
        `e2e` command result returns fail status.

        Verification Method: verify public function output

        Verification Detail:
        Return reason contains `want`.
        """

        passed, reason = review(command="this command fails because it wants to")

        self.assertIs(False, passed)
        self.assertIn("want", reason)


def _annotation_name(annotation: ast.expr | None) -> str:
    if isinstance(annotation, ast.Name):
        return annotation.id
    return ""


def _signature_text(path: Path, function: ast.FunctionDef) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    signature_lines = lines[function.lineno - 1 : function.body[0].lineno - 1]
    return "\n".join(signature_lines).split("(", 1)[1]


if __name__ == "__main__":
    unittest.main()
