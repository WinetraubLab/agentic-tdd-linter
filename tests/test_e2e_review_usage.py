"""Validate how repository tests use the E2E review runner.

This file scans `test_*.py` imports to keep tests on the public
`linter_e2e_review` entry point. Runner contract and behavior checks live in
`test_e2e_review_runner.py`.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parent
TESTING_EXCEPTION_TAG = "#" + " testing exception"
REVIEW_CONTROL_FLOW_NODES = (ast.With, ast.AsyncWith, ast.Try) + (
    (ast.TryStar,) if hasattr(ast, "TryStar") else ()
)
SIMULATED_AGENT_REVIEW_MESSAGE = (
    "E2E should not simulate the agent reviewing. The expected behavour is "
    "that linter_e2e_review will fail upon first execution, this will give "
    "agent a chance to review .agent.md file and then on the second run we "
    "should pass. Simulating the agent response is not what we want"
)


class E2EReviewUsageTests(unittest.TestCase):
    def test_tests_import_review_only(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test files import `e2e` through its public function.

        Verification Method: verify public function output

        Verification Detail:
        Import list contains `linter_e2e_review` only and not any private functions.
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
                if (
                    module == "helpers.linter_e2e"
                    and imported_names != ["linter_e2e_review"]
                ):
                    invalid_imports.append(f"{test_file}:{node.lineno}")

        self.assertEqual([], invalid_imports)

    def test_review_calls_are_direct(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        Test functions call `linter_e2e_review` directly without wrappers.

        Verification Method: verify public function output

        Verification Detail:
        AST reports calls that are not directly inside one `test_*` function.
        """

        invalid_calls: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            parents: dict[ast.AST, ast.AST] = {}
            for parent in ast.walk(tree):
                for child in ast.iter_child_nodes(parent):
                    parents[child] = parent

            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "linter_e2e_review"
                ):
                    continue
                function_ancestors: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
                parent = parents.get(node)
                while parent is not None:
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        function_ancestors.append(parent)
                    parent = parents.get(parent)
                if (
                    len(function_ancestors) != 1
                    or not function_ancestors[0].name.startswith("test_")
                ):
                    invalid_calls.append(
                        f"{test_file}:{node.lineno}: "
                        "do not wrap; call directly inside test function"
                    )

        self.assertEqual([], invalid_calls)

    def test_review_calls_use_source_only(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `linter_e2e_review` accepts test source only.

        Verification Method: verify public function output

        Verification Detail:
        Parser compares call keywords.
        """

        invalid_calls: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not _calls_linter_e2e_review(node):
                    continue
                keyword_names = [keyword.arg for keyword in node.keywords]
                if node.args or keyword_names != ["test_source_code"]:
                    invalid_calls.append(
                        f"{test_file}:{node.lineno}: "
                        "call linter_e2e_review with test_source_code only"
                    )

        self.assertEqual([], invalid_calls)

    def test_wrappers_require_tag(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `with` and `try` statements wrap `linter_e2e_review` only with approval.

        Verification Method: verify public function output

        Verification Detail:
        AST reports `with` or `try` calls without the testing exception tag.
        Repo contains at most one testing exception tag.
        """

        invalid_calls: list[str] = []
        tag_locations: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            lines = test_file.read_text(encoding="utf-8").splitlines()
            tag_locations.extend(
                f"{test_file}:{line_number}"
                for line_number, line in enumerate(lines, start=1)
                if TESTING_EXCEPTION_TAG in line
            )
            tree = ast.parse("\n".join(lines) + "\n")
            parents: dict[ast.AST, ast.AST] = {}
            for parent in ast.walk(tree):
                for child in ast.iter_child_nodes(parent):
                    parents[child] = parent

            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "linter_e2e_review"
                ):
                    continue
                control_flow_ancestors: list[ast.AST] = []
                parent = parents.get(node)
                while parent is not None:
                    if isinstance(parent, REVIEW_CONTROL_FLOW_NODES):
                        control_flow_ancestors.append(parent)
                    parent = parents.get(parent)
                if control_flow_ancestors and not any(
                    _control_flow_has_testing_exception_tag(control_flow_node, lines)
                    for control_flow_node in control_flow_ancestors
                ):
                    invalid_calls.append(
                        f"{test_file}:{node.lineno}: "
                        "with or try statement requires testing exception tag"
                    )

        if len(tag_locations) > 1:
            invalid_calls.extend(
                f"{location}: only one testing exception tag is allowed"
                for location in tag_locations
            )

        self.assertEqual([], invalid_calls)

    def test_tests_do_not_simulate(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        E2E tests do not simulate agent review.

        Verification Method: verify public function output

        Verification Detail:
        AST reports status replacement, placeholder replacement, and `.agent.md`
        writes in files that import `linter_e2e_review`.
        """

        invalid_simulations: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            source = test_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            if not _imports_linter_e2e_review(tree):
                continue

            for node in ast.walk(tree):
                if _replaces_agent_review_status(node):
                    invalid_simulations.append(
                        f"{test_file}:{node.lineno}: {SIMULATED_AGENT_REVIEW_MESSAGE}"
                    )
                if _replaces_agent_review_placeholder(node):
                    invalid_simulations.append(
                        f"{test_file}:{node.lineno}: {SIMULATED_AGENT_REVIEW_MESSAGE}"
                    )
                if _writes_agent_md_path(node):
                    invalid_simulations.append(
                        f"{test_file}:{node.lineno}: {SIMULATED_AGENT_REVIEW_MESSAGE}"
                    )

        self.assertEqual([], invalid_simulations)

    def test_status_assertion_follows(self) -> None:
        """Test Path: happy path

        Requirement Tested:
        `linter_e2e_review` status is asserted on the next line.

        Verification Method: verify public function output

        Verification Detail:
        AST reports calls not followed by `self.assertIs(True, status)` or
        `self.assertIs(False, status)`.
        """

        invalid_calls: list[str] = []
        for test_file in sorted(TEST_ROOT.glob("test_*.py")):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            for function in [
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            ]:
                for index, statement in enumerate(function.body):
                    if not _assigns_linter_e2e_review(statement):
                        continue
                    if not _assigns_linter_e2e_review_to_status_reason(statement):
                        invalid_calls.append(
                            f"{test_file}:{statement.lineno}: "
                            "assign linter_e2e_review to status, reason"
                        )
                        continue
                    next_statement = (
                        function.body[index + 1]
                        if index + 1 < len(function.body)
                        else None
                    )
                    if not _asserts_status(next_statement):
                        invalid_calls.append(
                            f"{test_file}:{statement.lineno}: "
                            "assert status on the following line"
                        )

        self.assertEqual([], invalid_calls)


def _assigns_linter_e2e_review(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Assign)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "linter_e2e_review"
    )


def _calls_linter_e2e_review(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "linter_e2e_review"
    )


def _imports_linter_e2e_review(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.ImportFrom)
            and node.module == "helpers.linter_e2e"
        ):
            continue
        if any(alias.name == "linter_e2e_review" for alias in node.names):
            return True
    return False


def _replaces_agent_review_status(node: ast.AST) -> bool:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "replace"
        and len(node.args) >= 2
    ):
        return False
    values = [_string_value(argument) for argument in node.args[:2]]
    return values[0] == "Status: pending" and values[1] in {
        "Status: pass",
        "Status: fail",
    }


def _replaces_agent_review_placeholder(node: ast.AST) -> bool:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "replace"
        and node.args
    ):
        return False
    return (
        _string_value(node.args[0])
        == "- Replace this line with the agent review result."
    )


def _writes_agent_md_path(node: ast.AST) -> bool:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
    ):
        return False
    return ".agent.md" in _source_text(node.func.value)


def _string_value(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def _source_text(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(_source_text(value) for value in node.values)
    if isinstance(node, ast.FormattedValue):
        return _source_text(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_source_text(node.value)}.{node.attr}"
    if isinstance(node, ast.BinOp):
        return f"{_source_text(node.left)} {_source_text(node.right)}"
    if isinstance(node, ast.Call):
        return _source_text(node.func)
    return ""


def _control_flow_has_testing_exception_tag(
    control_flow_node: ast.AST,
    lines: list[str],
) -> bool:
    start_line = max(1, control_flow_node.lineno - 1)
    return any(
        TESTING_EXCEPTION_TAG in lines[line_number - 1]
        for line_number in range(start_line, control_flow_node.lineno + 1)
    )


def _assigns_linter_e2e_review_to_status_reason(statement: ast.stmt) -> bool:
    if not (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Tuple)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "linter_e2e_review"
    ):
        return False
    target_names = [
        element.id for element in statement.targets[0].elts if isinstance(element, ast.Name)
    ]
    return target_names == ["status", "reason"]


def _asserts_status(statement: ast.stmt | None) -> bool:
    if not (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and statement.value.func.attr == "assertIs"
        and len(statement.value.args) >= 2
    ):
        return False
    expected, actual = statement.value.args[:2]
    return (
        isinstance(expected, ast.Constant)
        and expected.value in {True, False}
        and isinstance(actual, ast.Name)
        and actual.id == "status"
    )


if __name__ == "__main__":
    unittest.main()
