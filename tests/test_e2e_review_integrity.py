from __future__ import annotations

import ast
import unittest
from pathlib import Path


E2E_MODULE = Path(__file__).resolve().parent / "helpers" / "linter_e2e.py"
TEST_ROOT = Path(__file__).resolve().parent


class E2EReviewIntegrityTests(unittest.TestCase):
    def test_e2e_has_one_public_function(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` exposes one public function.

        Verification Method: verify file structure

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

    def test_tests_import_e2e_public_function_only(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test files import `e2e` through its public function.

        Verification Method: verify file structure

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

    def test_e2e_public_function_requires_keyword_arguments(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` public parameters require keyword names.
        This will prevent hidden parameters.

        Verification Method: verify file structure

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

    def test_e2e_public_function_parameter_identities(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` public parameters use approved names.

        Verification Method: verify file structure

        Verification Detail:
        Signature names `command` and `passes_on_success`.
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

        self.assertEqual(["command", "passes_on_success"], parameter_names)

    def test_e2e_public_function_parameter_types(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `e2e` public parameters use approved types.

        Verification Method: verify file structure

        Verification Detail:
        Signature types are `str` and `bool`.
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
                [("command", "str"), ("passes_on_success", "bool")],
                allowed_parameters,
            )

        self.assertEqual([], invalid_parameters)


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
