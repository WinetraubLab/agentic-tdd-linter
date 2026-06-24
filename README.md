# agentic-tdd-linter

`agentic-tdd-linter` is a linter for Python tests written during agent-assisted [test-driven development (TDD)](https://martinfowler.com/bliki/TestDrivenDevelopment.html).
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
   - The coding agent simplifies the implementation while keeping the approved tests passing.
   - A typical refactoring prompt is:

     ```text
     Simplify the implementation while preserving the behavior proven by the approved tests.
     Remove untested edge-case handling.
     ```

   - The refactored implementation is accepted based on the approved test suite.

For refactor-phase agent guidance, see [Refactor Workflow](docs/workflows/refactor.md).

You can also print the refactor prompt from the CLI:

```bash
agentic-tdd-linter --refactor-instructions
```

The key assumption is that generated implementation code may be too large or complex for humans to review line by line. Instead, human review should focus on the tests, because the tests define the intended behavior. If the tests are clear, complete, and correct, then the generated implementation can be judged by whether it satisfies those tests.

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

Paste this prompt into your coding agent, such as Claude or Codex:

```text
Add the following command as an additional check after the normal test suite:

uvx --from "git+https://github.com/WinetraubLab/agentic-tdd-linter" agentic-tdd-linter check --all --reviewer codex:gpt-5.5

Follow the repository's existing patterns for test scripts. Do not replace existing tests or linters.
```

The coding agent should add this command to the repository's standard testing workflow.
The linter should run after the normal test suite, so its findings are evaluated alongside test and coverage results.
It also writes missing agent review artifacts under `tests/agentic_review_artifacts`.

The first run may fail after creating pending review artifacts. Review those artifacts, update each `Status:` to `pass` or `fail`, then rerun the same command.

By default, `agentic-tdd-linter check` scans changed test files. Use `--all` to scan every project test file, or pass specific files or directories for focused work.

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
      - run: uvx --from "git+https://github.com/WinetraubLab/agentic-tdd-linter" agentic-tdd-linter check --all --reviewer codex:gpt-5.5
```

Before committing, run the same `uvx` command locally. If it creates `tests/agentic_review_artifacts`, review each generated `.agent.md` file, update each `Status:` to `pass` or `fail`, rerun the same command, and commit `tests/agentic_review_manifest.jsonl`.
````

Full proof flow: [GitHub Actions Review Proof](docs/workflows/github-actions.md).

## Test Docstring Contract

```text
Test naming:
Up to six words in test names: `test_` plus up to five descriptive words.

Test Path: <exactly one of: happy path | failure path>

Requirement Tested:
<1-2 sentences describing the behavior under test, up to 30 words.>

Verification Method: <exactly one of: verify public function output | verify private function output | visual inspection by user>

Verification Detail:
<optional sentence explaining what the test checks; mention any mocking here>

Inspection Instructions:
<required for visual inspection tests; tell the user exactly what to verify in the image>
```

Instructions:
- Use `happy path` when valid or supported inputs produce the expected successful result.
- Use `failure path` when invalid, unsafe, missing, or unsupported inputs are rejected with the expected error or guard behavior.
- Use `verify public function output` when the test calls a public function and asserts its returned output.
- Use `verify private function output` when the test calls a leading-underscore function and asserts its returned output, raised error, or state change.
- Use `visual inspection by user` when correctness is difficult to assert in code and the test writes a review artifact.
- Describe the specific behavior under test. Avoid generic wording such as `behaves as expected`.
- Keep the requirement, function inputs, and expected value close to the test body.
