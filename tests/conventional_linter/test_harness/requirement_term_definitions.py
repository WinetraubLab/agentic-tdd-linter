"""Build sources for requirement-term definition tests."""

from __future__ import annotations

import textwrap

from . import _lint_source


def _lint_requirement_term_source(*, file_docstring: str, requirement: str) -> set[str]:
    normalized_file_docstring = textwrap.dedent(file_docstring).strip()
    normalized_requirement = textwrap.dedent(requirement).strip()
    function_docstring = textwrap.indent(
        "\n".join(
            (
                '"""Test Path: happy path',
                "",
                "Requirement Tested:",
                normalized_requirement,
                "",
                "Verification Method: verify public function output",
                "",
                "Verification Detail:",
                "The manifest contains one review.",
                '"""',
            )
        ),
        "    ",
    )
    return _lint_source(
        f'"""{normalized_file_docstring}"""\n\n'
        "def test_manifest() -> None:\n"
        f"{function_docstring}\n\n"
        "    assert True\n"
    )
