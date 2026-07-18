"""Verify the public interface of the E2E review harness.

Terms:
- `public interface`: The public interface is the callable that integration tests use to run one generated scenario. For example, `linter_e2e_review` is the harness's public interface.
- `test_source_code`: This text parameter supplies one complete synthetic test file. For example, a caller passes Python source through test_source_code.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


class MainFunctionInterfaceVerificationTests(unittest.TestCase):
    def test_module_has_one_public_function(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The test-harness module provides one public interface: `linter_e2e_review`.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        `_public_functions` output contains only `linter_e2e_review`.

        Similar Coverage:
        - Higher Level Test: `test_source_module_structure.py::test_modules_expose_narrow_apis`
          Justification: Deeper coverage — This test verifies the exact singleton API of the E2E harness module; the repository policy permits two public functions.
        """

        function = _main_function()

        self.assertEqual("linter_e2e_review", function.name)

    def test_public_interface_accepts_test_source_as_text(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The `public interface` accepts only one input parameter; the parameter is called `test_source_code` and is text.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Keyword names contain only `["test_source_code"]`.
        `str` annotates `test_source_code`.
        """

        function = _main_function()
        parameter_names = [argument.arg for argument in function.args.kwonlyargs]
        annotation = next(
            _annotation_name(argument.annotation)
            for argument in function.args.kwonlyargs
            if argument.arg == "test_source_code"
        )

        self.assertEqual(["test_source_code"], parameter_names)
        self.assertEqual("str", annotation)

    def test_public_interface_is_keyword_only(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        The `public interface` accepts parameters only by keyword.
        Standard usage: The scenario demonstrates baseline behavior.

        Verification Method: verify private function output

        Verification Detail:
        Signature omits positional and variadic parameters.
        """

        function = _main_function()
        invalid_parameters = [
            argument.arg
            for argument in function.args.posonlyargs + function.args.args
        ]
        if function.args.vararg is not None:
            invalid_parameters.append(function.args.vararg.arg)
        if function.args.kwarg is not None:
            invalid_parameters.append(function.args.kwarg.arg)

        self.assertEqual([], invalid_parameters)


def _main_function() -> ast.FunctionDef:
    module_path = (
        Path(__file__).resolve().parent
        / "test_harness"
        / "linter_e2e_review.py"
    )
    public_functions = _public_functions(module_path)
    return next(
        function
        for function in public_functions
        if function.name == "linter_e2e_review"
    )


def _annotation_name(annotation: ast.expr | None) -> str:
    if isinstance(annotation, ast.Name):
        return annotation.id
    return ""


def _public_functions(path: Path) -> list[ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]


if __name__ == "__main__":
    unittest.main()
