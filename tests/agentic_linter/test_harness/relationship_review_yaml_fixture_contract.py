"""Validate repository-owned test-relationship YAML fixture contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .yaml_case_name import yaml_case_name_errors


REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = (
    REPO_ROOT
    / "tests"
    / "agentic_linter"
    / "fixtures"
    / "test_relationship_review"
)
TEMPLATE_PATH = (
    REPO_ROOT
    / "src"
    / "agentic_tdd_linter"
    / "agentic_linter"
    / "test_relationship_review.agent.md.j2"
)
REQUIRED_FILE_DOCSTRING = "\n".join(
    (
        "# Test-relationship examples for agent review.",
        "# Each example contains two test identifiers and docstrings followed by one pair-level expected scorecard.",
        "# Test implementations are intentionally excluded because only docstring relationships are evaluated.",
        "# The expected scorecard contains requirement-description overlap set to `yes` or `no` with an explanation comment.",
        "# An overlapping result requires one supported difference kind with an explanation comment.",
        "# A non-overlapping result stops after requirement-description overlap and omits kind.",
    )
)
TEST_KEYS = ("test_1", "test_2")
DIFFERENCE_KINDS = (
    "Happy/Failure Path Difference",
    "Scenario Difference",
    "Module Difference",
)


@dataclass(frozen=True)
class TestRelationshipDocstring:
    key: str
    identifier: str
    docstring: str


@dataclass(frozen=True)
class TestRelationshipReviewExample:
    name: str
    tests: tuple[TestRelationshipDocstring, TestRelationshipDocstring]
    expected_requirement_overlap: str
    expected_difference_kind: str | None


def lint_test_relationship_review_examples(*, examples_path: Path) -> list[str]:
    """Return schema errors for every test-relationship example file."""

    errors: list[str] = []
    try:
        files = relationship_review_example_files(Path(examples_path))
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
        errors.extend(yaml_case_name_errors(path, text))
        try:
            read_test_relationship_review_examples(path)
        except ValueError as error:
            errors.append(str(error))
    return errors


def read_test_relationship_review_examples(
    path: Path,
    criterion_titles: dict[int, str] | None = None,
) -> list[TestRelationshipReviewExample]:
    """Parse validated test-relationship examples from one YAML fixture."""

    del criterion_titles
    lines = path.read_text(encoding="utf-8").splitlines()
    examples: list[TestRelationshipReviewExample] = []
    example_name = ""
    section = ""
    current_test = ""
    identifiers: dict[str, str] = {}
    docstring_lines: dict[str, list[str]] = {}
    expected_requirement_overlap = ""
    expected_difference_kind: str | None = None

    def finish_example() -> None:
        nonlocal example_name, section, current_test
        nonlocal identifiers, docstring_lines
        nonlocal expected_requirement_overlap, expected_difference_kind
        if not example_name:
            return
        missing_tests = [key for key in TEST_KEYS if key not in identifiers]
        if missing_tests:
            raise ValueError(
                f"{path}: {example_name} needs {', '.join(missing_tests)}"
            )
        if len(set(identifiers.values())) != len(TEST_KEYS):
            raise ValueError(f"{path}: {example_name} test identifiers must be unique")
        if expected_requirement_overlap not in {"yes", "no"}:
            raise ValueError(
                f"{path}: {example_name} expected_scorecards needs "
                "requirement_description_overlap result set to yes or no"
            )
        if (
            expected_requirement_overlap == "yes"
            and expected_difference_kind not in DIFFERENCE_KINDS
        ):
            raise ValueError(
                f"{path}: {example_name} overlapping expected_scorecards "
                "needs one supported kind"
            )
        if (
            expected_requirement_overlap == "no"
            and expected_difference_kind is not None
        ):
            raise ValueError(
                f"{path}: {example_name} non-overlapping expected_scorecards "
                "must omit kind"
            )
        parsed_tests: list[TestRelationshipDocstring] = []
        for key in TEST_KEYS:
            docstring = "\n".join(docstring_lines.get(key, [])).rstrip() + "\n"
            if not docstring.strip():
                raise ValueError(f"{path}: {example_name} {key} needs a docstring")
            parsed_tests.append(
                TestRelationshipDocstring(
                    key=key,
                    identifier=identifiers[key],
                    docstring=docstring,
                )
            )
        examples.append(
            TestRelationshipReviewExample(
                name=example_name,
                tests=(parsed_tests[0], parsed_tests[1]),
                expected_requirement_overlap=expected_requirement_overlap,
                expected_difference_kind=expected_difference_kind,
            )
        )
        example_name = ""
        section = ""
        current_test = ""
        identifiers = {}
        docstring_lines = {}
        expected_requirement_overlap = ""
        expected_difference_kind = None

    for line_number, line in enumerate(lines, start=1):
        if not line:
            if section == "docstring" and current_test:
                docstring_lines[current_test].append("")
            continue
        if line.lstrip().startswith("#") and section != "docstring":
            continue
        if not line.startswith(" ") and line.endswith(":"):
            finish_example()
            example_name = line[:-1]
            continue
        if not example_name:
            raise ValueError(f"unsupported YAML at {path}:{line_number}")
        test_match = re.fullmatch(r"  (test_1|test_2):", line)
        if test_match:
            if section in {"expected_scorecards", "expected_overlap"}:
                raise ValueError(
                    f"{path}:{line_number}: tests must precede expected_scorecards"
                )
            current_test = test_match.group(1)
            if current_test in identifiers or current_test in docstring_lines:
                raise ValueError(f"{path}: {example_name} duplicates {current_test}")
            section = "test"
            continue
        if line == "  expected_scorecards:":
            if any(key not in docstring_lines for key in TEST_KEYS):
                raise ValueError(
                    f"{path}:{line_number}: expected_scorecards must follow both tests"
                )
            if expected_requirement_overlap:
                raise ValueError(
                    f"{path}: {example_name} duplicates expected_scorecards"
                )
            section = "expected_scorecards"
            current_test = ""
            continue
        if (
            line == "    requirement_description_overlap:"
            and section == "expected_scorecards"
        ):
            section = "expected_overlap"
            continue
        overlap_match = re.fullmatch(
            r"      result:\s+(yes|no)\s+#\s+(.+\S|\S)",
            line,
            re.IGNORECASE,
        )
        if section == "expected_overlap" and overlap_match:
            if expected_requirement_overlap:
                raise ValueError(
                    f"{path}: {example_name} duplicates overlap result"
                )
            expected_requirement_overlap = overlap_match.group(1).lower()
            continue
        overlap_without_explanation = re.fullmatch(
            r"      result:\s+(yes|no)(?:\s+#\s*)?",
            line,
            re.IGNORECASE,
        )
        if section == "expected_overlap" and overlap_without_explanation:
            raise ValueError(
                f"{path}:{line_number}: overlap result needs an explanation comment"
            )
        kind_match = re.fullmatch(
            r"      kind:\s+(.+?)\s+#\s+(.+\S|\S)",
            line,
        )
        if section == "expected_overlap" and kind_match:
            if not expected_requirement_overlap:
                raise ValueError(
                    f"{path}:{line_number}: kind must follow overlap result"
                )
            if expected_difference_kind is not None:
                raise ValueError(f"{path}: {example_name} duplicates kind")
            kind = kind_match.group(1).strip()
            if kind not in DIFFERENCE_KINDS:
                raise ValueError(
                    f"{path}:{line_number}: kind must be one of "
                    + ", ".join(DIFFERENCE_KINDS)
                )
            expected_difference_kind = kind
            continue
        kind_without_explanation = re.fullmatch(
            r"      kind:\s+(.+?)(?:\s+#\s*)?",
            line,
        )
        if section == "expected_overlap" and kind_without_explanation:
            raise ValueError(
                f"{path}:{line_number}: kind needs an explanation comment"
            )
        identifier_match = re.fullmatch(r"    identifier:\s+`([^`]+)`", line)
        if section == "test" and current_test and identifier_match:
            if current_test in identifiers:
                raise ValueError(
                    f"{path}:{line_number}: {current_test} duplicates identifier"
                )
            identifiers[current_test] = identifier_match.group(1).strip()
            continue
        if line == "    docstring: |" and section == "test" and current_test:
            if current_test not in identifiers:
                raise ValueError(
                    f"{path}:{line_number}: docstring must follow identifier"
                )
            docstring_lines[current_test] = []
            section = "docstring"
            continue
        if section == "docstring" and current_test and line.startswith("      "):
            docstring_lines[current_test].append(line[6:])
            continue
        field_match = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):", line)
        if field_match:
            raise ValueError(
                f"{path}:{line_number}: unsupported field "
                f"`{field_match.group(1)}`"
            )
        raise ValueError(f"unsupported YAML at {path}:{line_number}")
    finish_example()
    return examples


def relationship_review_example_files(path: Path) -> list[Path]:
    """Return YAML files in the selected test-relationship fixture folder."""

    if path.is_file():
        path = path.parent
    if not path.is_dir():
        raise ValueError(
            f"test-relationship example path does not exist: {path}"
        )
    files = sorted(path.glob("*.yaml"))
    if not files:
        raise ValueError(
            f"test-relationship example folder contains no YAML files: {path}"
        )
    return files


def criterion_titles_from_template() -> dict[int, str]:
    """Return test-relationship criterion titles from the Jinja template."""

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
