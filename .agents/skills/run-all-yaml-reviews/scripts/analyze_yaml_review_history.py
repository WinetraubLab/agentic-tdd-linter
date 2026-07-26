#!/usr/bin/env python3
"""Classify current agent-review YAML results against recent Git history."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


SIDECAR = Path("tests/agentic_linter/test_agent_review_example_runner.json")
HISTORICAL_SIDECARS = (
    SIDECAR,
    Path("tests/integration_tests/test_agent_review_examples.json"),
)
TEMPLATE = Path(
    "src/agentic_tdd_linter/agentic_linter/single_test_review.agent.md.j2"
)
FIXTURE_ROOT = Path("tests/agentic_linter/fixtures/single_test_review")
CRITERION_HEADING = re.compile(r"^####\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
TOP_LEVEL_CASE = re.compile(r"^([A-Za-z0-9_-]+):\s*$")
EXPECTED_CRITERION = re.compile(r"^    (\d+):\s+#")


@dataclass(frozen=True)
class Snapshot:
    revision: str
    sidecar: dict[str, object]
    criteria: dict[int, tuple[str, str]]
    cases: dict[str, set[int]]


def _git(repo_root: Path, *arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def _git_file(repo_root: Path, revision: str, path: Path) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path.as_posix()}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def _criteria(template: str) -> dict[int, tuple[str, str]]:
    matches = list(CRITERION_HEADING.finditer(template))
    criteria: dict[int, tuple[str, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(template)
        body = template[match.end() : end].strip()
        body = re.split(r"^###\s", body, maxsplit=1, flags=re.MULTILINE)[0].strip()
        criteria[int(match.group(1))] = (match.group(2).strip(), body)
    return criteria


def _fixture_cases(text: str) -> dict[str, set[int]]:
    cases: dict[str, set[int]] = {}
    current = ""
    for line in text.splitlines():
        match = TOP_LEVEL_CASE.match(line)
        if match:
            current = match.group(1)
            cases[current] = set()
            continue
        criterion = EXPECTED_CRITERION.match(line)
        if current and criterion:
            cases[current].add(int(criterion.group(1)))
    return cases


def _cases_at(repo_root: Path, revision: str) -> dict[str, set[int]]:
    paths = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        revision,
        "--",
        FIXTURE_ROOT.as_posix(),
        check=False,
    ).splitlines()
    cases: dict[str, set[int]] = {}
    for value in paths:
        path = Path(value)
        if path.suffix not in {".yaml", ".yml"}:
            continue
        text = _git_file(repo_root, revision, path)
        if text is not None:
            cases.update(_fixture_cases(text))
    return cases


def _working_tree_cases(repo_root: Path) -> dict[str, set[int]]:
    cases: dict[str, set[int]] = {}
    for path in sorted((repo_root / FIXTURE_ROOT).glob("*.yaml")):
        cases.update(_fixture_cases(path.read_text(encoding="utf-8")))
    return cases


def _snapshot(repo_root: Path, revision: str) -> Snapshot | None:
    sidecar_text = next(
        (
            text
            for path in HISTORICAL_SIDECARS
            if (text := _git_file(repo_root, revision, path)) is not None
        ),
        None,
    )
    template_text = _git_file(repo_root, revision, TEMPLATE)
    if sidecar_text is None or template_text is None:
        return None
    return Snapshot(
        revision=revision,
        sidecar=json.loads(sidecar_text),
        criteria=_criteria(template_text),
        cases=_cases_at(repo_root, revision),
    )


def _historical_snapshots(repo_root: Path) -> list[Snapshot]:
    head = _git(repo_root, "rev-parse", "HEAD").strip()
    changes = _git(
        repo_root,
        "log",
        "-n",
        "5",
        "--format=%H",
        "--",
        SIDECAR.as_posix(),
        TEMPLATE.as_posix(),
    ).splitlines()
    revisions = list(dict.fromkeys([head, *changes]))
    return [snapshot for revision in revisions if (snapshot := _snapshot(repo_root, revision))]


def _outcome(snapshot: Snapshot, criterion: int, case: str) -> str | None:
    if criterion not in snapshot.cases.get(case, set()):
        return None
    row = snapshot.sidecar.get("criteria", {}).get(str(criterion))
    if not isinstance(row, dict):
        return None
    failures = row.get("failing_yaml_cases", [])
    return "fail" if case in failures else "pass"


def _criterion_text(criteria: dict[int, tuple[str, str]], criterion: int) -> str:
    title, body = criteria.get(criterion, ("Unknown criterion", ""))
    return f"{title}\n{body}".strip()


def _classification(
    *,
    criterion: int,
    case: str,
    current_outcome: str,
    snapshots: list[Snapshot],
) -> str:
    if not snapshots:
        return "New test fail" if current_outcome == "fail" else "New test pass"
    head = snapshots[0]
    if case not in head.cases or criterion not in head.cases[case]:
        return "New test fail" if current_outcome == "fail" else "New test pass"

    observations_by_wording: dict[str, set[str]] = {}
    for snapshot in snapshots:
        outcome = _outcome(snapshot, criterion, case)
        if outcome is None:
            continue
        wording = _criterion_text(snapshot.criteria, criterion)
        observations_by_wording.setdefault(wording, set()).add(outcome)
    if any(values == {"pass", "fail"} for values in observations_by_wording.values()):
        return "Flaky"

    head_outcome = _outcome(head, criterion, case)
    if current_outcome == "fail" and head_outcome == "fail":
        return "Fails in HEAD"
    if current_outcome == "fail":
        return "Regression"
    if head_outcome == "fail":
        return "Fixed"
    return "Stable pass"


def _criterion_changed(
    criterion: int,
    current_criteria: dict[int, tuple[str, str]],
    snapshots: list[Snapshot],
) -> bool:
    wordings = {_criterion_text(current_criteria, criterion)}
    wordings.update(_criterion_text(snapshot.criteria, criterion) for snapshot in snapshots)
    return len(wordings) > 1


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _first_sentence(body: str) -> str:
    without_jinja = re.sub(r"{%.*?%}", "", body, flags=re.DOTALL)
    compact = " ".join(without_jinja.split())
    match = re.match(r"(.+?[.!?])(?:\s|$)", compact)
    return match.group(1) if match else compact


def _render_table(
    sidecar: dict[str, object],
    current_criteria: dict[int, tuple[str, str]],
    current_cases: dict[str, set[int]],
    snapshots: list[Snapshot],
) -> str:
    lines = [
        "| Criterion # | One-line explanation | # Passing / # Total (%) | Result explanations |",
        "|---:|---|---:|---|",
    ]
    rows = sidecar.get("criteria", {})
    for criterion_text, row in rows.items():
        criterion = int(criterion_text)
        title, body = current_criteria.get(criterion, ("Unknown criterion", ""))
        explanation = f"{title}: {_first_sentence(body)}" if body else title
        failures = set(row.get("failing_yaml_cases", []))
        checked_cases = sorted(
            case for case, criteria in current_cases.items() if criterion in criteria
        )
        grouped: dict[str, list[str]] = {}
        for case in checked_cases:
            category = _classification(
                criterion=criterion,
                case=case,
                current_outcome="fail" if case in failures else "pass",
                snapshots=snapshots,
            )
            grouped.setdefault(category, []).append(case)
        classified_count = sum(len(cases) for cases in grouped.values())
        enforced_checks = row.get("enforced_checks")
        if classified_count != len(checked_cases):
            raise ValueError(
                f"criterion {criterion} classified {classified_count} of "
                f"{len(checked_cases)} YAML checks"
            )
        if classified_count != enforced_checks:
            raise ValueError(
                f"criterion {criterion} classified {classified_count} checks, "
                f"but the sidecar enforces {enforced_checks}"
            )
        order = (
            "New test pass",
            "New test fail",
            "Flaky",
            "Fails in HEAD",
            "Regression",
            "Stable pass",
            "Fixed",
        )
        parts: list[str] = []
        for category in order:
            cases = grouped.get(category, [])
            if not cases:
                continue
            if category == "Stable pass":
                parts.append(f"Stable pass ({len(cases)})")
                continue
            parts.append(
                f"{category} ({len(cases)}): "
                + ", ".join(f"`{case}`" for case in sorted(cases))
            )
        if failures:
            changed = "yes" if _criterion_changed(criterion, current_criteria, snapshots) else "no"
            parts.append(f"Criterion changed: {changed}")
        result_text = "<br>".join(parts) if parts else "—"
        lines.append(
            f"| {criterion} | {_escape(explanation)} | {row['success']} | {result_text} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    arguments = parser.parse_args()
    repo_root = (
        arguments.repo_root.resolve()
        if arguments.repo_root
        else Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
    )
    sidecar = json.loads((repo_root / SIDECAR).read_text(encoding="utf-8"))
    current_criteria = _criteria((repo_root / TEMPLATE).read_text(encoding="utf-8"))
    current_cases = _working_tree_cases(repo_root)
    snapshots = _historical_snapshots(repo_root)
    hashes = ", ".join(snapshot.revision[:8] for snapshot in snapshots)
    print(f"History snapshots: {hashes}")
    print()
    print(_render_table(sidecar, current_criteria, current_cases, snapshots))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
