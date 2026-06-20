# agentic-tdd-linter

`agentic-tdd-linter` is a linter for Python tests written during agent-assisted [test-driven development (TDD)](https://martinfowler.com/bliki/TestDrivenDevelopment.html).
It helps verify that tests written by coding agents are clear for human consumption in guiding implementation.

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
     Simplify the code and remove unnecessary edge-case handling as long as all tests continue to pass.
     ```

   - The refactored implementation is accepted based on the approved test suite.

The key assumption is that generated implementation code may be too large or complex for humans to review line by line. Instead, human review should focus on the tests, because the tests define the intended behavior. If the tests are clear, complete, and correct, then the generated implementation can be judged by whether it satisfies those tests.

## What It Checks

`agentic-tdd-linter` looks for tests that are:

- vague or hard to understand
- too broad for a single behavior
- missing meaningful assertions
- redundant with existing tests
- unrelated to the changed implementation
- unsupported by coverage information

The goal is to catch weak, vague, or bloated tests before they guide implementation.

### From your coding agent

Paste this prompt into your coding agent, such as Claude or Codex:

```text
Add the following command as an additional check after the normal test suite:

uvx --from "git+https://github.com/WinetraubLab/agentic-tdd-linter" agentic-tdd-linter check

Follow the repository’s existing patterns for test scripts. Do not replace existing tests or linters.
```

The coding agent should add this command to the repository’s standard testing workflow, such as a Makefile, justfile, CI workflow, or test script.
