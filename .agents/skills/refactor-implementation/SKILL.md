---
description: Simplify implementation code while preserving approved behavior and remove untested edge-case handling. Use after approved tests pass or when asked to refactor, simplify helpers, remove defensive branches, or clean production and test-harness implementations.
---

# Refactor Implementation

Simplify the complete implementation surface while keeping approved tests and public behavior unchanged.

## Workflow

1. Confirm the approved tests pass before refactoring.
2. Inventory every implementation file under `src/` and every file inside any `test_harness/` directory.
3. Inspect every inventoried file, including files untouched by the current change. Do not limit the refactor to changed files, nearby modules, or named examples.
4. Apply relevant simplifications across the complete inventory:
   - simplify code paths and helpers;
   - remove untested edge-case handling;
   - prefer direct, readable implementations;
   - do not optimize for named examples from tests;
   - generalize from requirements rather than literal test values.
5. Preserve public behavior. Do not weaken, rewrite, or remove approved tests.
6. Run the full test suite after completing the consolidated refactor.

For each inventoried file, either make the relevant cleanup or deliberately determine that no cleanup is warranted. Do not skip a file because it was not recently modified.
