"""Generate markdown prompts for agentic test-docstring review."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .agent_ran_proof import source_sha256
from .agent_review_artifacts import agent_review_artifact_path


@dataclass(frozen=True)
class MarkdownTest:
    """A test function included in the agentic review markdown."""

    name: str
    line: int
    docstring: str
    source: str


REVIEW_INSTRUCTIONS = (
    (
        "Notify Generic Requirement",
        (
            "Review `Requirement Tested` for specificity. Fail it when it "
            "could describe several tests, appears repeatedly without narrower "
            "wording, or can be swapped onto another test with little change."
        ),
    ),
    (
        "Notify Convoluted Wording",
        (
            "Flag double negation, generic wording, self-reference, unexplained "
            "domain terms, and ambiguous data-flow words. Local terms should be "
            "defined or backticked. Words such as `input`, `output`, and "
            "`returns` need an explicit owner. Prefer concrete language."
        ),
    ),
    (
        "Focus on What is Being Verified, Not How",
        (
            "`Requirement Tested` should state the behavior rule. "
            "`Verification Detail` should state the evidence that proves it. "
            "Fail wording that only names mechanics, fixtures, constants, "
            "assertions, commands, tags, or test names without explaining the "
            "behavior they prove."
        ),
    ),
    (
        "Sentence Checks",
        (
            "Sentence Structure Check (Pass/Fail): Pass if each sentence follows "
            "Subject -> Verb -> Object. The subject and object must each be no "
            "longer than two words. Fail if the main verb can also read as a "
            "noun, even when the sentence is grammatically parseable. If the "
            "idea cannot fit, write a second sentence with a concrete example.\n"
            "Condition Check (Pass/Fail): Pass if all conditions are stated "
            "explicitly using words such as if, when, unless, or only if. "
            "Fail if conditions must be inferred.\n"
            "Relative Clause Check (Pass/Fail): Fail if a sentence ends with "
            "a relative clause that omits referent information or requires the "
            "reader to infer what a term refers to.\n"
            "Concept Check (Pass/Fail): Pass if the sentence communicates a "
            "single primary idea, requirement, or decision. Fail if it combines "
            "multiple independent concepts."
        ),
    ),
    (
        "Assertion Purpose Check",
        (
            "Review every assertion in the test body. Each assertion must either "
            "narrowly prove `Requirement Tested` or validate a test input. "
            "Input-validation assertions must include the exact `# Input check` "
            "comment. Fail assertions that prove a different requirement or "
            "validate inputs without that tag."
        ),
    ),
    (
        "Keep Assertions Self-Contained",
        (
            "Review whether the requirement, test inputs, and user-defined "
            "expected values are defined inside the test body. Fail when any "
            "of them comes from an external constant, fixture, helper, or "
            "shared setup."
        ),
    ),
    (
        "Test Level Redundancy Check",
        (
            "When tests verify overlapping behavior at different levels, each "
            "`Requirement Tested` must include `see also test_...` and state "
            "which level each related test covers."
        ),
    ),
)


def agentic_md_for_test_file(test_file_path: Path, repo_root: Path | None = None) -> str:
    """Return an agent-review markdown prompt for every test in one file."""

    absolute_path = Path(test_file_path).resolve()
    source = absolute_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(absolute_path))
    display_path = _display_path(absolute_path, repo_root)
    tests = _test_functions(tree, source)

    lines = [
        "# Agentic Test Docstring Review",
        "",
        f"Test file: `{display_path}`",
        "",
        "For each test below, review the structured test docstring and assertions.",
        "Return concrete notes for tests that need clearer wording or assertion scope.",
        "",
        "## Review Instructions",
        "",
    ]

    for index, (title, instruction) in enumerate(REVIEW_INSTRUCTIONS, start=1):
        lines.append(f"{index}. {title}")
        for instruction_line in instruction.splitlines():
            lines.append(f"   {instruction_line}")
        lines.append("")

    lines.append("## Tests")
    lines.append("")

    if not tests:
        lines.append("No test functions found.")
        lines.append("")
    else:
        for test in tests:
            docstring = test.docstring or "<missing docstring>"
            lines.append(f"### `{test.name}`")
            lines.append("")
            lines.append(f"- Line: {test.line}")
            lines.append("- Docstring:")
            lines.append("")
            lines.append("````text")
            lines.append(docstring)
            lines.append("````")
            lines.append("")
            lines.append("- Test Source:")
            lines.append("")
            lines.append("````python")
            lines.append(test.source or "<missing source>")
            lines.append("````")
            lines.append("")

    lines.append("## Agent Review Result")
    lines.append("")
    lines.append("Status: pending")
    lines.append("Notes:")
    lines.append("- Replace this line with the agent review result.")
    lines.append("")
    lines.append("## Agent Review Proof")
    lines.append("")
    lines.append("Do not update `Source SHA256` until every review step in this file is complete.")
    lines.append(f"Source SHA256: `{source_sha256(absolute_path)}`")

    return "\n".join(lines).rstrip() + "\n"


def write_agentic_md_for_test_file(
    test_file_path: Path,
    repo_root: Path,
    artifact_root: Path | None = None,
) -> Path:
    """Write the agent-review markdown artifact for one test file."""

    artifact_path = agent_review_artifact_path(test_file_path, repo_root, artifact_root)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        agentic_md_for_test_file(test_file_path, repo_root),
        encoding="utf-8",
    )
    return artifact_path


def _test_functions(tree: ast.AST, source: str) -> list[MarkdownTest]:
    tests = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        tests.append(
            MarkdownTest(
                name=node.name,
                line=node.lineno,
                docstring=ast.get_docstring(node) or "",
                source=ast.get_source_segment(source, node) or "",
            )
        )
    return sorted(tests, key=lambda test: test.line)


def _display_path(path: Path, repo_root: Path | None) -> str:
    if repo_root is None:
        return str(path)
    try:
        return str(path.relative_to(Path(repo_root).resolve()))
    except ValueError:
        return str(path)
