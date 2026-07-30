---
name: run-all-yaml-reviews
description: Run every single-test agent-review YAML example from scratch, complete fresh isolated reviews, compare current mismatches with HEAD and five recent historical snapshots, and classify failures as new tests, flaky results, existing HEAD failures, or regressions. Use when the user says "run all YAMLs", "run all YAML examples", "review all YAML fixtures", asks for a fresh full YAML review, or requests YAML regression analysis.
---

# Run All YAML Reviews

Run the complete anonymous single-test YAML review and explain every mismatch against repository history.

## Announce the skill

Before taking any action, tell the user:

> Using `$run-all-yaml-reviews`: starting a fresh review of every YAML example.

Do not silently invoke this skill. Include the current skill step number in every progress update.

## Step 1: Remove previous reviews

Work from the repository root. Preserve YAML fixtures, criteria, source files, and unrelated changes.

Remove every `.agent.md` file under `temporary_fixtures/agent_review_examples/agentic_review_artifacts/`.
Remove `tests/agentic_linter/test_agent_review_example_runner.jsonl` so committed attestations cannot satisfy this fresh run.

## Step 2: Generate all YAML reviews

Run:

```bash
.venv/bin/python -m unittest \
  tests.agentic_linter.test_agent_review_example_runner.AgentReviewExampleRunnerTests.test_anonymous_agent_review_examples \
  -v
```

The invocation should stop with pending packets. Treat that result as packet generation, not as the final YAML assessment.

## Step 3: Review every generated file

Review every generated `.agent.md` file by following its instructions:

- Follow the review procedure embedded in each generated `.agent.md`.
- Continue until no generated packet contains a pending scorecard row.

## Step 4: Rerun all YAML tests

After reviewers complete every generated `.agent.md`, run the same unittest command again:

```bash
.venv/bin/python -m unittest \
  tests.agentic_linter.test_agent_review_example_runner.AgentReviewExampleRunnerTests.test_anonymous_agent_review_examples \
  -v
```

This invocation compares completed scorecards with YAML expectations and updates `tests/agentic_linter/test_agent_review_example_runner.json` and `tests/agentic_linter/test_agent_review_example_runner.jsonl`, even when comparison failures make the test exit nonzero. Do not edit YAML or criterion wording during this run.

## Step 5: Analyze history

Run:

```bash
.venv/bin/python \
  .agents/skills/run-all-yaml-reviews/scripts/analyze_yaml_review_history.py
```

The analyzer compares the completed working-tree sidecar and criterion template with:

- Git HEAD; and
- the five most recent repository snapshots that changed either `tests/agentic_linter/test_agent_review_example_runner.json` or `src/agentic_tdd_linter/agentic_linter/single_test_review.agent.md.j2`.

Assign every enforced `(YAML case, criterion)` pair to exactly one of seven categories in this priority order. Apply the categories to successful and failing comparisons alike.

1. **New test pass**: The YAML case, or its enforced criterion check, does not exist in HEAD, and the completed working-tree review matches the YAML expectation.
2. **New test fail**: The YAML case, or its enforced criterion check, does not exist in HEAD, and the completed working-tree review fails the YAML expectation.
3. **Flaky**: Comparable recorded runs contain both success and failure while the complete criterion wording is unchanged.
4. **Fails in HEAD**: HEAD records the same failure and comparable runs with the same criterion wording do not record a success.
5. **Regression**: HEAD records success consistently, but the completed working-tree review fails.
6. **Stable pass**: Both HEAD and the completed working-tree review match the YAML expectation.
7. **Fixed**: HEAD fails the YAML expectation, but the completed working-tree review matches it.

Criterion wording is unchanged only when the complete criterion heading and rule text are identical. Report whether each failing criterion changed across the inspected snapshots. A wording change does not hide a regression; mention the change in the result explanation.

## Step 6: Report

The analyzer produces the complete Markdown table. For the initial user-facing report, show only rows for criteria whose complete heading or rule text differs from Git HEAD. This is a presentation filter only: do not change the analyzer command, analysis, classifications, or generated table.

Use exactly these columns:

| Criterion # | One-line explanation | # Passing / # Total (%) | Result explanations |
|---:|---|---:|---|

In `Criterion #`, append ` (edited)` when the criterion's complete heading or rule text differs from Git HEAD.
Render unchanged criteria as the plain number. Preserve this marker when showing the full table.

In `Result explanations`, show counts and YAML case names for New test pass, New test fail, Flaky, Fails in HEAD, Regression, and Fixed.
Show the Stable pass count without listing every stable YAML case.
Put every category on a separate line inside the table cell by separating categories with the HTML line break `<br>`. 
The category counts for each criterion must equal that criterion's total enforced YAML checks.
Also state whether a criterion with a current failure changed in the inspected history.

After presenting the focused table, ask whether the user wants the full table containing unchanged criteria. If the user says yes, return every row from the analyzer output already produced. Do not rerun the analyzer, YAML reviews, or history collection.

After the table, report:

- final YAML runner status;
- YAML file, case, and enforced-check counts;
- whether any pending packet rows remain; and
- the path to the updated JSON sidecar.

At the end of every completed YAML review cycle, run:

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
```

Print the result as `Cycle completed at (local time): <timestamp>`. Use the
machine's local time from this command rather than inferring the time.

Do not fix fixtures or criteria unless the user asks after reviewing this report.
