"""Extract Node-style TypeScript tests from `.test.ts` files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


TEST_CALL_PATTERN = re.compile(r"(?m)(?<![\w$.])test\s*\(")


@dataclass(frozen=True)
class TypeScriptTest:
    """A TypeScript test call with its nearest leading JSDoc comment."""

    name: str
    line: int
    docstring: str
    source: str


def is_typescript_test_file(path: Path) -> bool:
    """Return whether a path is a Node-style TypeScript test file."""

    return path.name.endswith(".test.ts")


def typescript_tests(source: str) -> list[TypeScriptTest]:
    """Return TypeScript test calls from source in file order."""

    matches = list(TEST_CALL_PATTERN.finditer(source))
    tests = []
    for index, match in enumerate(matches):
        call_start = match.start()
        docstring, source_start = _leading_jsdoc(source, call_start)
        source_end = len(source)
        if index + 1 < len(matches):
            _, source_end = _leading_jsdoc(source, matches[index + 1].start())
        tests.append(
            TypeScriptTest(
                name=_test_name(source[call_start:]),
                line=source.count("\n", 0, call_start) + 1,
                docstring=docstring,
                source=source[source_start:source_end].strip(),
            )
        )
    return tests


def _leading_jsdoc(source: str, call_start: int) -> tuple[str, int]:
    prefix = source[:call_start].rstrip()
    jsdoc_start = prefix.rfind("/**")
    if jsdoc_start == -1:
        return "", call_start
    match = re.fullmatch(r"/\*\*(.*?)\*/", prefix[jsdoc_start:], flags=re.DOTALL)
    if match is None:
        return "", call_start
    return _clean_jsdoc(match.group(1)), jsdoc_start


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
