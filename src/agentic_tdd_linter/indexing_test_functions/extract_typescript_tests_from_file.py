"""Extract tests from one Node-style TypeScript file."""

from __future__ import annotations

import re
from pathlib import Path

from .extracted_test_record import ExtractedTestRecord


_TEST_CALL_PATTERN = re.compile(r"(?m)(?<![\w$.])test\s*\(")


def extract_typescript_tests_from_file(
    path: Path,
    repo_root: Path,
) -> list[ExtractedTestRecord]:
    """Return TypeScript tests extracted in source order."""

    absolute_path = Path(path).resolve()
    relative_path = _relative_path(absolute_path, repo_root)
    source = absolute_path.read_text(encoding="utf-8")
    file_docstring, file_docstring_end = _file_jsdoc(source)
    matches = list(_TEST_CALL_PATTERN.finditer(source))
    tests = []
    for index, match in enumerate(matches):
        call_start = match.start()
        docstring, source_start = _leading_jsdoc(
            source,
            call_start,
            file_docstring_end=file_docstring_end,
        )
        source_end = len(source)
        if index + 1 < len(matches):
            _, source_end = _leading_jsdoc(
                source,
                matches[index + 1].start(),
                file_docstring_end=file_docstring_end,
            )
        tests.append(
            ExtractedTestRecord(
                path=relative_path,
                name=_test_name(source[call_start:]),
                line=source.count("\n", 0, call_start) + 1,
                node=None,
                docstring=docstring,
                source=source[source_start:source_end].strip(),
                file_docstring=file_docstring,
            )
        )
    return tests


def _relative_path(path: Path, repo_root: Path) -> Path:
    try:
        return Path(path).resolve().relative_to(Path(repo_root).resolve())
    except ValueError:
        return Path(path)


def _file_jsdoc(source: str) -> tuple[str, int]:
    match = re.match(r"\A\s*/\*\*(.*?)\*/", source, flags=re.DOTALL)
    if match is None:
        return "", 0
    docstring = _clean_jsdoc(match.group(1))
    if not docstring.startswith("Tests in this file validate `"):
        return "", 0
    return docstring, match.end()


def _leading_jsdoc(
    source: str,
    call_start: int,
    *,
    file_docstring_end: int,
) -> tuple[str, int]:
    prefix = source[file_docstring_end:call_start].rstrip()
    jsdoc_start = prefix.rfind("/**")
    if jsdoc_start == -1:
        return "", call_start
    match = re.fullmatch(r"/\*\*(.*?)\*/", prefix[jsdoc_start:], flags=re.DOTALL)
    if match is None:
        return "", call_start
    absolute_start = file_docstring_end + jsdoc_start
    return _clean_jsdoc(match.group(1)), absolute_start


def _clean_jsdoc(comment: str) -> str:
    return "\n".join(
        line.strip().removeprefix("*").strip()
        for line in comment.splitlines()
    ).strip()


def _test_name(call_text: str) -> str:
    match = re.search(r'\(\s*"([^"]+)"', call_text)
    if match is None:
        return "<anonymous test>"
    return match.group(1)
