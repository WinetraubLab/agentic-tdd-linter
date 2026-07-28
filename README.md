# agentic-tdd-linter

`agentic-tdd-linter` is a linter for Python and TypeScript tests written during agent-assisted [test-driven development (TDD)](https://martinfowler.com/bliki/TestDrivenDevelopment.html).
It helps verify that tests written by coding agents are clear enough for humans to use when guiding implementation.

## Design Philosophy

Coding agents can generate implementation faster than humans can review it line by line. In agentic TDD, tests become the main review boundary: they define the intended behavior and constrain the generated code.
`agentic-tdd-linter` helps improve those tests before they become the specification. It does not replace human judgment, `pytest`, coverage tools, or code review.

## Development Pattern

`agentic-tdd-linter` is designed for an agentic TDD workflow built around the classic loop:

```text
Red -> Green -> Refactor
```

Follow this flow:

1. A human asks a coding agent to develop or modify a feature.
2. Red: test development, **with human review**.
   - The coding agent writes tests for the intended behavior.
   - `agentic-tdd-linter` checks whether the tests are understandable, focused, meaningful, connected to the change, and non-redundant.
   - The coding agent iterates on the tests until they are clear enough for human review.
   - The human reviews the tests as the primary specification of the intended behavior.
   - If the tests accurately capture the desired behavior, the human approves them.
3. Green: feature implementation, **without human review**.
   - The coding agent implements the feature until the approved tests pass.
   - The generated implementation is accepted based on the approved test suite, rather than line-by-line human review.
4. Refactor: implementation cleanup, **without human review**.
   - The coding agent uses the repository's refactor skill to simplify the complete implementation while keeping the approved tests passing.
   - The refactored implementation is accepted based on the approved test suite.

For the complete refactor-phase instructions, see [Refactor Implementation Skill](.agents/skills/refactor-implementation/SKILL.md).

The key assumption is that generated implementation code may be too large or complex for humans to review line by line. Instead, human review should focus on the tests, because the tests define the intended behavior. If the tests are clear, complete, and correct, then the generated implementation can be judged by whether it satisfies those tests.

## Repository Structure

Production code is grouped by responsibility:

```text
src/agentic_tdd_linter/
    indexing_test_functions/ # Shared test-file discovery and function indexing
    conventional_linter/  # Deterministic lint rules
    agentic_linter/       # Agent-review generation and proof
    cli/                  # Command-line behavior and reporting
```

Tests use the same boundaries and add two test-only groups:

```text
tests/
    indexing_test_functions/ # Tests for discovery and function indexing
    conventional_linter/  # Tests for deterministic lint rules
    agentic_linter/       # Tests for the agent-review subsystem
    cli/                  # Tests for CLI behavior
    integration_tests/    # End-to-end and dogfood tests
    repository_health/    # Fixture, manifest, workflow, and documentation health
```

`integration_tests` and `repository_health` have no production-code counterparts:
they verify interactions and the repository itself rather than implement linter behavior.

## What It Checks

`agentic-tdd-linter` looks for tests that are:
- vague or hard to understand
- missing meaningful assertions
- missing required structured docstring fields
- using unsupported test path or verification method classifications
- mislabeled as private verification without calling a private function
- missing required visual inspection instructions or artifacts

The goal is to catch weak, vague, or bloated tests before they guide implementation.

## Add It To Your Project

From the root of a new project, copy and run this entire block:

```bash
bash -c '
set -e

python3 -m venv .venv
./.venv/bin/pip install git+https://github.com/WinetraubLab/agentic-tdd-linter
./.venv/bin/agentic-tdd-linter create-agent-md

printf "\nReview the generated files and change every scorecard result from pending to pass or fail.\nPress Enter when the reviews are complete.\n"
read -r

./.venv/bin/agentic-tdd-linter lint --reviewer codex:gpt-5.5
'
```

The block pauses after generating `.agent.md` files because an agent must complete every scorecard before lint can record review proof. Replace `codex:gpt-5.5` when a different agent or model performs the review.

After the first successful run, add `./.venv/bin/agentic-tdd-linter lint` after the project's normal test suite. This preserves existing tests and linters while checking agent-authored tests alongside test and coverage results.

Each generated `.agent.md` file reviews one Python `test_...` function or TypeScript `test(...)` call. A source file with multiple tests produces one independent review artifact per test.

By default, both commands scan the test suite but process only tests without current passing manifest proof. Pass files or directories to limit the scope. Use `--fresh` to ignore previous review proof. For `create-agent-md`, this regenerates every packet in the selected scope, including the cross-test packet:

```bash
agentic-tdd-linter create-agent-md --fresh tests/test_example.py
agentic-tdd-linter lint --fresh tests/test_example.py --reviewer codex:gpt-5.5
```

Without a path, `--fresh` applies to the complete test root. With a path, it refreshes
every test in that file or directory and rebuilds the cross-test packet from that
selected scope while leaving unrelated single-test packets alone. Without `--fresh`,
packet creation preserves current proof, writes only missing or stale single-test
packets, and includes only files with added, deleted, or edited test content in the
cross-test packet.

Each single-test packet records the SHA256 of its extracted test content. Editing one
test therefore regenerates only that test's packet while preserving reviews for other
tests in the same file. Manifest proof records the linter version and review contract
so lint rejects reviews produced under an older policy.

## Install It On GitHub Actions On Your Project

Paste this prompt into your coding agent:

````text
Add `.github/workflows/agentic-tdd-linter.yml` to this project.

Use this workflow:

```yaml
name: Agentic TDD Linter

on:
  pull_request:
  push:

jobs:
  lint-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uvx --from "git+https://github.com/WinetraubLab/agentic-tdd-linter" agentic-tdd-linter lint
```

Before committing, run `agentic-tdd-linter create-agent-md`, review any generated packets, and run `agentic-tdd-linter lint --reviewer codex:gpt-5.5`. Commit the refreshed `tests/agentic_review_manifest.jsonl` with the test changes.
````

Full proof flow: [GitHub Actions Review Proof](docs/workflows/github-actions.md).

## Two Review Workflows

This project separates review creation from automated validation:

### Pre-commit review workflow

Contributors run this workflow before committing test changes:

1. Run `agentic-tdd-linter create-agent-md` to create `.agent.md` scorecards.
2. Complete every generated scorecard.
3. Run `lint --reviewer <identity>` to record completed reviews in `tests/agentic_review_manifest.jsonl`.
4. Commit the updated tests and manifest.

This workflow creates `.agent.md` files and updates manifest proof.

### CI/CD validation workflow

CI/CD runs `agentic-tdd-linter lint` after the changes are committed. It validates
the committed tests and `tests/agentic_review_manifest.jsonl`. CI/CD does not create
`.agent.md` files, perform reviews, or record new manifest proof. Missing, stale,
failed, or version-incompatible proof causes CI/CD to fail and directs the contributor
back to the pre-commit review workflow.

## Test Docstring Contract

```text
Test naming:
Use at most five descriptive words. The Python `test_` prefix is not counted.

File docstring:
"""Tests in this file validate `parser` located at `src/parser.py`.
`parser` is responsible for converting text into structured values.

Terms:
- `manifest proof`: A stored agent-review result for one test source hash.
"""

Test Path: <exactly one of: happy path | failure path>

Requirement Tested:
<First sentence: state the general behavioral rule.>
<Second sentence: describe one concrete use case or scenario where the rule applies. Maximum 30 words across both sentences.>

Verification Method: <exactly one of: verify public function output | verify private function output | visual inspection by user>

Verification Detail:
<optional sentence explaining what the test checks; mention any mocking here>

Similar Coverage:
<optional list of related tests at higher or lower levels; put lower-level justification here>

Inspection Instructions:
<required for visual inspection tests; tell the user exactly what to verify in the image>
```

Instructions:
- Begin every test-file docstring with the exact module declaration and responsibility sentences shown above.
- Use a repository-relative path that identifies an existing module.
- Begin every first `Requirement Tested` sentence with the exact backticked module name declared by the file.
- Split tests into separate files when their requirements validate different modules.
- Put the corresponding file-level JSDoc before imports in a TypeScript `.test.ts` file.
- Use `happy path` when valid or supported inputs produce the expected successful result.
- Use `failure path` when invalid, unsafe, missing, or unsupported inputs are rejected with the expected error or guard behavior.
- Use `verify public function output` when the test calls a public function and asserts its returned output.
- Use `verify private function output` when the test calls a leading-underscore function and asserts its returned output, raised error, or state change.
- Use `visual inspection by user` when correctness is difficult to assert in code and the test writes a review artifact.
- Use the first `Requirement Tested` sentence to state what the system must do. Avoid generic wording such as `behaves as expected`.
- Use the second `Requirement Tested` sentence to state when, where, or for whom the rule applies.
- Define every backticked value used in `Requirement Tested` under the file docstring's `Terms:` section. Match the backticked spelling exactly.
- Use `Verification Detail` for the exact expected result or evidence.
- Use a separate `Similar Coverage` section for reciprocal higher/lower-level test references and lower-level justification.
- Keep the requirement, function inputs, and expected value close to the test body.
