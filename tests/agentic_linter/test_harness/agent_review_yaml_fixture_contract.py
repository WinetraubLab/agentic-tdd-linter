"""Validate repository-owned agent-review YAML fixture contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "fixtures"
    / "single_test_review"
)
TEMPLATE_PATH = (
    REPO_ROOT
    / "src"
    / "agentic_tdd_linter"
    / "agentic_linter"
    / "single_test_review.agent.md.j2"
)
REQUIRED_FILE_DOCSTRING = "\n".join(
    (
        "# Test-source examples for agent review.",
        "# Each example contains only `file_docstring`, `test`, and `expected_scorecard`.",
        "# Criteria omitted from `expected_scorecard` are ignored during comparison.",
        "# Criterion comments must match their titles in `single_test_review.agent.md.j2`.",
        "# Each outcome must be `pass` or `fail` followed by an explanation comment.",
    )
)


@dataclass(frozen=True)
class ExpectedResult:
    result: str


@dataclass(frozen=True)
class AgentReviewExample:
    name: str
    file_docstring: str
    test: str
    expected_scorecard: dict[int, ExpectedResult]


def lint_agent_review_examples(*, examples_path: Path) -> list[str]:
    """Return schema errors for every agent-review example file in one folder."""

    errors: list[str] = []
    criterion_titles = criterion_titles_from_template()
    try:
        files = agent_review_example_files(Path(examples_path))
    except ValueError as error:
        return [str(error)]
    for path in files:
        text = path.read_text(encoding="utf-8")
        if not text.startswith(REQUIRED_FILE_DOCSTRING + "\n\n"):
            errors.append(
                f"{path}: file must begin with the required documentation header "
                "followed by one blank line"
            )
        errors.extend(_example_spacing_errors(path, text))
        try:
            read_agent_review_examples(path, criterion_titles)
        except ValueError as error:
            errors.append(str(error))
    return errors


def read_agent_review_examples(
    path: Path,
    criterion_titles: dict[int, str] | None = None,
) -> list[AgentReviewExample]:
    """Parse validated agent-review examples from one YAML fixture."""

    criterion_titles = (
        criterion_titles
        if criterion_titles is not None
        else criterion_titles_from_template()
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    examples: list[AgentReviewExample] = []
    example_name = ""
    file_docstring_lines: list[str] = []
    test_lines: list[str] = []
    expected_scorecard: dict[int, dict[str, str]] = {}
    criterion: int | None = None
    section = ""

    def finish_example() -> None:
        nonlocal example_name, file_docstring_lines, test_lines
        nonlocal expected_scorecard, criterion, section
        if not example_name:
            return
        parsed_scorecard: dict[int, ExpectedResult] = {}
        for number, values in expected_scorecard.items():
            result = values.get("result", "").lower()
            if result not in {"pass", "fail"}:
                raise ValueError(
                    f"{path}: {example_name} criterion {number} needs pass or fail"
                )
            parsed_scorecard[number] = ExpectedResult(result=result)
        if not parsed_scorecard:
            raise ValueError(f"{path}: {example_name} needs an expected_scorecard")
        file_docstring = "\n".join(file_docstring_lines).rstrip() + "\n"
        if not file_docstring.strip():
            raise ValueError(f"{path}: {example_name} needs a file_docstring")
        test = "\n".join(test_lines).rstrip() + "\n"
        if not test.strip():
            raise ValueError(f"{path}: {example_name} needs test source")
        examples.append(
            AgentReviewExample(
                name=example_name,
                file_docstring=file_docstring,
                test=test,
                expected_scorecard=parsed_scorecard,
            )
        )
        example_name = ""
        file_docstring_lines = []
        test_lines = []
        expected_scorecard = {}
        criterion = None
        section = ""

    for line_number, line in enumerate(lines, start=1):
        if not line:
            if section == "file_docstring" and example_name:
                file_docstring_lines.append("")
            elif section == "test" and example_name:
                test_lines.append("")
            continue
        if line.lstrip().startswith("#"):
            if section == "file_docstring" and example_name and line.startswith("    "):
                file_docstring_lines.append(line[4:])
            elif section == "test" and example_name and line.startswith("    "):
                test_lines.append(line[4:])
            continue
        if not line.startswith(" ") and line.endswith(":"):
            finish_example()
            example_name = line[:-1]
            continue
        if not example_name:
            raise ValueError(f"unsupported YAML at {path}:{line_number}")
        if line == "  expected_scorecard:":
            if section != "test":
                raise ValueError(
                    f"{path}:{line_number}: expected_scorecard must follow test"
                )
            section = "expected_scorecard"
            continue
        if line == "  test: |":
            if section != "file_docstring":
                raise ValueError(
                    f"{path}:{line_number}: test must follow file_docstring"
                )
            section = "test"
            criterion = None
            continue
        if line == "  file_docstring: |":
            if section:
                raise ValueError(
                    f"{path}:{line_number}: file_docstring must be the first field"
                )
            section = "file_docstring"
            criterion = None
            continue
        field_match = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):", line)
        if field_match:
            raise ValueError(
                f"{path}:{line_number}: unsupported field `{field_match.group(1)}`; "
                "only `file_docstring`, `test`, and `expected_scorecard` are allowed"
            )
        criterion_match = re.fullmatch(r"    (\d+):\s+#\s+(.+)", line)
        if section == "expected_scorecard" and criterion_match:
            criterion = int(criterion_match.group(1))
            title = criterion_match.group(2).strip()
            expected_title = criterion_titles.get(criterion)
            if expected_title is None:
                raise ValueError(
                    f"{path}:{line_number}: criterion {criterion} does not exist in "
                    "single_test_review.agent.md.j2"
                )
            if title != expected_title:
                raise ValueError(
                    f"{path}:{line_number}: criterion {criterion} comment must be "
                    f"`{expected_title}`"
                )
            if criterion in expected_scorecard:
                raise ValueError(f"{path}: {example_name} duplicates criterion {criterion}")
            expected_scorecard[criterion] = {}
            continue
        value_match = re.fullmatch(
            r"      (pass|fail)\s+#\s+(.+\S|\S)", line, re.IGNORECASE
        )
        if section == "expected_scorecard" and criterion is not None and value_match:
            expected_scorecard[criterion]["result"] = value_match.group(1)
            continue
        outcome_without_explanation = re.fullmatch(
            r"      (pass|fail)(?:\s+#\s*)?", line, re.IGNORECASE
        )
        if (
            section == "expected_scorecard"
            and criterion is not None
            and outcome_without_explanation
        ):
            raise ValueError(
                f"{path}:{line_number}: {outcome_without_explanation.group(1).lower()} "
                "needs an explanation comment"
            )
        if section == "file_docstring" and line.startswith("    "):
            file_docstring_lines.append(line[4:])
            continue
        if section == "test" and line.startswith("    "):
            test_lines.append(line[4:])
            continue
        raise ValueError(f"unsupported YAML at {path}:{line_number}")
    finish_example()
    return examples


def agent_review_example_files(path: Path) -> list[Path]:
    """Return all YAML example files in the selected fixture folder."""

    if path.is_file():
        path = path.parent
    if not path.is_dir():
        raise ValueError(f"agent-review example path does not exist: {path}")
    files = sorted(path.glob("*.yaml"))
    if not files:
        raise ValueError(f"agent-review example folder contains no YAML files: {path}")
    return files


def criterion_titles_from_template() -> dict[int, str]:
    """Return scorecard criterion titles from the Jinja template."""

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return {
        int(number): title.strip()
        for number, title in re.findall(
            r"^####\s+(\d+)\.\s+(.+?)\s*$", template, re.MULTILINE
        )
    }


def _example_spacing_errors(path: Path, text: str) -> list[str]:
    lines = text.splitlines()
    errors: list[str] = []
    for index, line in enumerate(lines):
        if line.startswith(" ") or not line.endswith(":") or line.startswith("#"):
            continue
        if index == 0 or lines[index - 1] != "":
            errors.append(f"{path}:{index + 1}: example must have one blank line above it")
        elif index >= 2 and lines[index - 2] == "":
            errors.append(
                f"{path}:{index + 1}: example must have only one blank line above it"
            )
    return errors
