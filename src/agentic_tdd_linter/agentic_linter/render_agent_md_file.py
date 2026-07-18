"""Generate markdown prompts for agentic test-docstring review."""

from __future__ import annotations

import ast
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, StrictUndefined, Template

from .determine_agent_md_status import _source_sha256
from .map_test_function_to_agent_md_file import map_test_function_to_agent_md_file
from ..indexing_test_functions.extract_tests_from_file import extract_tests_from_file
from ..indexing_test_functions.extracted_test_record import ExtractedTestRecord

TEMPLATE_PATH = "agentic_linter/single_test_review.agent.md.j2"


def _render_agent_md_files_for_test_file(
    test_file_path: Path,
    repo_root: Path | None = None,
) -> list[tuple[ExtractedTestRecord, str]]:
    """Return one agent-review prompt for each test in a file."""

    absolute_path = Path(test_file_path).resolve()
    tests = extract_tests_from_file(
        absolute_path,
        repo_root if repo_root is not None else absolute_path.parent,
    )
    return [
        (test, _render_agent_md(test_file_path=absolute_path, test=test))
        for test in tests
    ]


def _render_agent_md(
    test_file_path: Path,
    test: ExtractedTestRecord,
) -> str:
    """Return an agent-review prompt for one test."""

    absolute_path = Path(test_file_path).resolve()
    return _agentic_review_template().render(
        file_docstring=_file_docstring(absolute_path),
        source_sha256=_source_sha256(absolute_path),
        test=test.source or "<missing test source>",
        scenario_type=_scenario_type(test),
    ).rstrip() + "\n"


def _scenario_type(test: ExtractedTestRecord) -> str:
    for line in test.docstring.splitlines():
        field, separator, value = line.strip().partition(":")
        if separator and field == "Test Path":
            scenario_type = value.strip()
            if scenario_type in {"happy path", "failure path"}:
                return scenario_type
            raise ValueError(
                "Test Path must be either 'happy path' or 'failure path' before rendering"
            )
    raise ValueError("Test Path is required before rendering")


def _file_docstring(test_file_path: Path) -> str:
    path = Path(test_file_path).resolve()
    if path.suffix != ".py":
        return ""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    return ast.get_docstring(tree) or ""


@lru_cache(maxsize=1)
def _agentic_review_template() -> Template:
    template_source = files("agentic_tdd_linter").joinpath(TEMPLATE_PATH).read_text(
        encoding="utf-8"
    )
    environment = Environment(
        autoescape=False,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    return environment.from_string(template_source)


def _write_agent_md_files_for_test_file(
    test_file_path: Path,
    repo_root: Path,
    artifact_root: Path | None = None,
) -> list[Path]:
    """Write one agent-review artifact for each test in a file."""

    artifacts = []
    for test, markdown in _render_agent_md_files_for_test_file(
        test_file_path, repo_root
    ):
        artifacts.append(
            _write_agent_md_file(
                test_file_path,
                test,
                markdown,
                repo_root,
                artifact_root,
            )
        )
    return artifacts


def render_agent_md_file(
    test_file_path: Path,
    test: ExtractedTestRecord,
    repo_root: Path,
    artifact_root: Path | None = None,
) -> Path:
    """Write the agent-review artifact for one test."""

    markdown = _render_agent_md(test_file_path=test_file_path, test=test)
    return _write_agent_md_file(
        test_file_path,
        test,
        markdown,
        repo_root,
        artifact_root,
    )


def _write_agent_md_file(
    test_file_path: Path,
    test: ExtractedTestRecord,
    markdown: str,
    repo_root: Path,
    artifact_root: Path | None,
) -> Path:
    artifact_path = map_test_function_to_agent_md_file(
        test_file_path,
        repo_root,
        artifact_root,
        test.name,
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(markdown, encoding="utf-8")
    return artifact_path
