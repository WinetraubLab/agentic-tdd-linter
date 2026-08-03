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
        "# Each example contains two test identifiers and docstrings, one expected pair classification, and expected scorecards.",
        "# Test implementations are intentionally excluded because only docstring relationships are evaluated.",
        "# Requirement-description overlap must be `yes` or `no` followed by an explanation comment.",
        "# Criteria omitted from an expected scorecard are ignored during comparison.",
        "# Criterion comments must match their titles in `test_relationship_review.agent.md.j2`.",
        "# Each scorecard outcome must be `pass` or `fail` followed by an explanation comment.",
    )
)
TEST_KEYS = ("test_1", "test_2")


@dataclass(frozen=True)
class ExpectedResult:
    result: str


@dataclass(frozen=True)
class TestRelationshipDocstring:
    key: str
    identifier: str
    docstring: str
    expected_scorecard: dict[int, ExpectedResult]


@dataclass(frozen=True)
class TestRelationshipReviewExample:
    name: str
    tests: tuple[TestRelationshipDocstring, TestRelationshipDocstring]
    expected_requirement_overlap: str


def lint_test_relationship_review_examples(*, examples_path: Path) -> list[str]:
    """Return schema errors for every test-relationship example file."""

    errors: list[str] = []
    criterion_titles = criterion_titles_from_template()
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
            read_test_relationship_review_examples(path, criterion_titles)
        except ValueError as error:
            errors.append(str(error))
    return errors


def read_test_relationship_review_examples(
    path: Path,
    criterion_titles: dict[int, str] | None = None,
) -> list[TestRelationshipReviewExample]:
    """Parse validated test-relationship examples from one YAML fixture."""

    criterion_titles = (
        criterion_titles
        if criterion_titles is not None
        else criterion_titles_from_template()
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    examples: list[TestRelationshipReviewExample] = []
    example_name = ""
    section = ""
    current_test = ""
    current_scorecard_test = ""
    identifiers: dict[str, str] = {}
    docstring_lines: dict[str, list[str]] = {}
    expected_requirement_overlap = ""
    expected_scorecards: dict[str, dict[int, dict[str, str]]] = {}
    criterion: int | None = None

    def finish_example() -> None:
        nonlocal example_name, section, current_test, current_scorecard_test
        nonlocal identifiers, docstring_lines, expected_requirement_overlap
        nonlocal expected_scorecards, criterion
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
                f"{path}: {example_name} expected_pair needs "
                "requirement_description_overlap set to yes or no"
            )
        parsed_tests: list[TestRelationshipDocstring] = []
        for key in TEST_KEYS:
            docstring = "\n".join(docstring_lines.get(key, [])).rstrip() + "\n"
            if not docstring.strip():
                raise ValueError(f"{path}: {example_name} {key} needs a docstring")
            scorecard_values = expected_scorecards.get(key, {})
            if not scorecard_values:
                raise ValueError(
                    f"{path}: {example_name} {key} needs an expected scorecard"
                )
            parsed_scorecard: dict[int, ExpectedResult] = {}
            for number, values in scorecard_values.items():
                result = values.get("result", "").lower()
                if result not in {"pass", "fail"}:
                    raise ValueError(
                        f"{path}: {example_name} {key} criterion {number} "
                        "needs pass or fail"
                    )
                parsed_scorecard[number] = ExpectedResult(result=result)
            parsed_tests.append(
                TestRelationshipDocstring(
                    key=key,
                    identifier=identifiers[key],
                    docstring=docstring,
                    expected_scorecard=parsed_scorecard,
                )
            )
        examples.append(
            TestRelationshipReviewExample(
                name=example_name,
                tests=(parsed_tests[0], parsed_tests[1]),
                expected_requirement_overlap=expected_requirement_overlap,
            )
        )
        example_name = ""
        section = ""
        current_test = ""
        current_scorecard_test = ""
        identifiers = {}
        docstring_lines = {}
        expected_requirement_overlap = ""
        expected_scorecards = {}
        criterion = None

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
            if section in {
                "expected_pair",
                "pair_overlap",
                "expected_scorecards",
                "scorecard",
            }:
                raise ValueError(
                    f"{path}:{line_number}: tests must precede expected_pair"
                )
            current_test = test_match.group(1)
            if current_test in identifiers or current_test in docstring_lines:
                raise ValueError(f"{path}: {example_name} duplicates {current_test}")
            section = "test"
            criterion = None
            continue
        if line == "  expected_pair:":
            if any(key not in docstring_lines for key in TEST_KEYS):
                raise ValueError(
                    f"{path}:{line_number}: expected_pair must follow both tests"
                )
            if expected_requirement_overlap:
                raise ValueError(f"{path}: {example_name} duplicates expected_pair")
            section = "expected_pair"
            current_test = ""
            criterion = None
            continue
        if (
            line == "    requirement_description_overlap:"
            and section == "expected_pair"
        ):
            section = "pair_overlap"
            continue
        pair_overlap_match = re.fullmatch(
            r"      (yes|no)\s+#\s+(.+\S|\S)",
            line,
            re.IGNORECASE,
        )
        if section == "pair_overlap" and pair_overlap_match:
            expected_requirement_overlap = pair_overlap_match.group(1).lower()
            continue
        pair_overlap_without_explanation = re.fullmatch(
            r"      (yes|no)(?:\s+#\s*)?",
            line,
            re.IGNORECASE,
        )
        if section == "pair_overlap" and pair_overlap_without_explanation:
            raise ValueError(
                f"{path}:{line_number}: "
                f"{pair_overlap_without_explanation.group(1).lower()} needs an "
                "explanation comment"
            )
        if line == "  expected_scorecards:":
            if any(key not in docstring_lines for key in TEST_KEYS):
                raise ValueError(
                    f"{path}:{line_number}: expected_scorecards must follow both tests"
                )
            if expected_requirement_overlap not in {"yes", "no"}:
                raise ValueError(
                    f"{path}:{line_number}: expected_scorecards must follow "
                    "expected_pair"
                )
            section = "expected_scorecards"
            current_test = ""
            current_scorecard_test = ""
            criterion = None
            continue
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
        scorecard_test_match = re.fullmatch(r"    (test_1|test_2):", line)
        if section in {"expected_scorecards", "scorecard"} and scorecard_test_match:
            current_scorecard_test = scorecard_test_match.group(1)
            if current_scorecard_test in expected_scorecards:
                raise ValueError(
                    f"{path}: {example_name} duplicates "
                    f"{current_scorecard_test} expected scorecard"
                )
            expected_scorecards[current_scorecard_test] = {}
            section = "scorecard"
            criterion = None
            continue
        criterion_match = re.fullmatch(r"      (\d+):\s+#\s+(.+)", line)
        if section == "scorecard" and current_scorecard_test and criterion_match:
            criterion = int(criterion_match.group(1))
            title = criterion_match.group(2).strip()
            expected_title = criterion_titles.get(criterion)
            if expected_title is None:
                raise ValueError(
                    f"{path}:{line_number}: criterion {criterion} does not exist in "
                    "test_relationship_review.agent.md.j2"
                )
            if title != expected_title:
                raise ValueError(
                    f"{path}:{line_number}: criterion {criterion} comment must be "
                    f"`{expected_title}`"
                )
            scorecard = expected_scorecards[current_scorecard_test]
            if criterion in scorecard:
                raise ValueError(
                    f"{path}: {example_name} {current_scorecard_test} duplicates "
                    f"criterion {criterion}"
                )
            scorecard[criterion] = {}
            continue
        value_match = re.fullmatch(
            r"        (pass|fail)\s+#\s+(.+\S|\S)", line, re.IGNORECASE
        )
        if (
            section == "scorecard"
            and current_scorecard_test
            and criterion is not None
            and value_match
        ):
            expected_scorecards[current_scorecard_test][criterion]["result"] = (
                value_match.group(1)
            )
            continue
        outcome_without_explanation = re.fullmatch(
            r"        (pass|fail)(?:\s+#\s*)?", line, re.IGNORECASE
        )
        if (
            section == "scorecard"
            and current_scorecard_test
            and criterion is not None
            and outcome_without_explanation
        ):
            raise ValueError(
                f"{path}:{line_number}: "
                f"{outcome_without_explanation.group(1).lower()} needs an "
                "explanation comment"
            )
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
