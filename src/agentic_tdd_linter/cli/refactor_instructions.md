# Refactor Workflow

Use this workflow after the approved tests are passing.

The goal of the refactor phase is to simplify the implementation while preserving the behavior proven by the approved tests.

## Agent Instructions

- Simplify code paths.
- Simplify helper functions in the codebase.
- Remove untested edge-case handling.
- Prefer direct, readable implementation.
- Keep public behavior unchanged.
- Run the full test suite after changes.
- Do not weaken, rewrite, or remove approved tests.
- Do not optimize for named examples from the tests.
- Generalize from the requirement, not from literal test cases.

## Prompt

```text
Simplify the implementation while preserving the behavior proven by the approved tests.

Simplify code paths and helper functions in the codebase.
Remove untested edge-case handling.
Keep public behavior unchanged.
Do not weaken, rewrite, or remove approved tests.
Do not optimize for named examples from the tests.
Generalize from the requirement, not from literal test cases.
Run the full test suite after changes.
```
