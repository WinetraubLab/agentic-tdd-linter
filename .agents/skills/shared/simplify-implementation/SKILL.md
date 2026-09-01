---
name: simplify-implementation
description: Simplify implementation code only after the full test suite passes, while preserving tested behavior and removing unnecessary or untested complexity. Use when implementation is complete and tests are green, or when asked to simplify production or test-harness code without changing approved tests.
---

# Simplify Implementation

Simplify the complete implementation surface after all tests pass while keeping approved tests and public behavior unchanged.

## Workflow

1. Run the full test suite and continue only when every test passes. If any test fails, stop and report the failures instead of simplifying the implementation.
2. Inventory every implementation file under `src/` and every file inside any `test_harness/` directory.
3. Inspect every inventoried file, including files untouched by the current change. Do not limit the simplification to changed files, nearby modules, or named examples.
4. Apply relevant simplifications across the complete inventory:
   - simplify code paths and helpers;
   - remove untested edge-case handling;
   - prefer direct, readable implementations;
   - do not optimize for named examples from tests;
   - generalize from requirements rather than literal test values.
5. Preserve public behavior. Do not weaken, rewrite, or remove approved tests.
6. Run the full test suite after completing the consolidated simplification.

For each inventoried file, either make the relevant cleanup or deliberately determine that no cleanup is warranted. Do not skip a file because it was not recently modified.
