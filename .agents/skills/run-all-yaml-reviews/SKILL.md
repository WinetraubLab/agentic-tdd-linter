---
name: run-all-yaml-reviews
description: Run agent-review YAML examples from scratch. Use single-test review by default, or test-relationship review for Similar Coverage and relationships among tests when the user explicitly requests "run the test-relationship YAMLs", "review Similar Coverage", cross-test, or relational review. Complete fresh isolated reviews and report expectation mismatches; single-test mode also compares results with HEAD and five recent historical snapshots. Use when the user says "run all YAMLs", "run all YAML examples", "review all YAML fixtures", asks for a fresh full YAML review, or requests YAML regression analysis.
---

# Run All YAML Reviews

Run the selected YAML review type and explain every mismatch.

## Announce the skill

Before taking any action, tell the user:

> Using `$run-all-yaml-reviews`: starting a fresh <single-test or test-relationship> review of YAML files under `<selected fixture catalog>`.

Do not silently invoke this skill. Include the current skill step number in every progress update.

## Step 1: Select the review type and remove previous reviews

Select exactly one review type:

- **Single-test** is the default. Use it whenever the user does not explicitly request a review type.
- **Test-relationship** applies only when the user explicitly requests
  `run the test-relationship YAMLs`, `review Similar Coverage`, cross-test,
  cross test, relational, or test-relationship review. Treat
  `test-relationship` as the canonical name; treat `cross-test` and
  `relational` as aliases.

Use the corresponding YAML catalog:

| Review type | YAML files that run |
|---|---|
| Single-test | `tests/agentic_linter/fixtures/single_test_review/*.yaml` |
| Test-relationship | `tests/agentic_linter/fixtures/test_relationship_review/*.yaml` |

State both the selected review type and exact fixture catalog before removing
files. Enumerate every selected YAML file by repository-relative path so the
user can see exactly which YAMLs will run. Do not combine the two fixture
catalogs in one run unless the user explicitly asks for both.

Work from the repository root. Preserve YAML fixtures, criteria, source files, and unrelated changes.

Remove the selected review type's previous artifacts:

- **Single-test:** Every `.agent.md` under `temporary_fixtures/agent_review_examples/agentic_review_artifacts/` and `tests/agentic_linter/test_agent_review_example_runner.jsonl`.
- **Test-relationship:** Every `.agent.md` under `temporary_fixtures/test_relationship_review_examples/agentic_review_artifacts/` and `tests/agentic_linter/test_relationship_review_example_runner.jsonl`.

## Step 2: Generate all YAML reviews

Use `node_repl` to read `nodeRepl.requestMeta["x-codex-turn-metadata"]`.
Record its exact `model` and `reasoning_effort` values as
`AGENT_REVIEW_MODEL="<model> <reasoning_effort>"`. Do not infer either value
from an earlier report. Use this same reviewer configuration for every
isolated reviewer in the cycle. If runtime metadata is unavailable, stop and
request the actual model and reasoning effort instead of guessing.

For **single-test** review, run:

```bash
AGENT_REVIEW_MODEL='<model> <reasoning_effort>' \
  .venv/bin/python -m unittest \
  tests.agentic_linter.test_agent_review_example_runner.AgentReviewExampleRunnerTests.test_anonymous_agent_review_examples \
  -v
```

The invocation should stop with pending packets. Treat that result as packet generation, not as the final YAML assessment.

For **test-relationship** review, run:

```bash
AGENT_REVIEW_MODEL='<model> <reasoning_effort>' \
  .venv/bin/python -m \
  tests.agentic_linter.test_harness.relationship_review_example_runner
```

The test-relationship invocation should also stop with pending packets. Each
packet contains two test docstrings and one scorecard for their unordered pair.
Treat that result as packet generation, not as the final YAML assessment.

## Step 3: Review every generated file

Review every generated `.agent.md` file by following its instructions:

- Follow the review procedure embedded in each generated `.agent.md`.
- Continue until no generated packet contains a pending scorecard row.
- For test-relationship review, classify every pair's overlap as `yes` or
  `no`. For `yes`, set kind to exactly `Happy/Failure Path Difference`,
  `Scenario Difference`, or `Module Difference`. For `no`, set kind to
  `Not Applicable` and stop.

## Step 4: Rerun all YAML tests

After reviewers complete every generated `.agent.md`, rerun the command for the selected review type.

For **single-test** review:

```bash
AGENT_REVIEW_MODEL='<model> <reasoning_effort>' \
  .venv/bin/python -m unittest \
  tests.agentic_linter.test_agent_review_example_runner.AgentReviewExampleRunnerTests.test_anonymous_agent_review_examples \
  -v
```

This invocation compares completed scorecards with YAML expectations and updates `tests/agentic_linter/test_agent_review_example_runner.json` and `tests/agentic_linter/test_agent_review_example_runner.jsonl`, even when comparison failures make the test exit nonzero. Do not edit YAML or criterion wording during this run.
Verify that the JSON report and every newly written JSONL attestation identify
the recorded `AGENT_REVIEW_MODEL`.

For **test-relationship** review:

```bash
AGENT_REVIEW_MODEL='<model> <reasoning_effort>' \
  .venv/bin/python -m \
  tests.agentic_linter.test_harness.relationship_review_example_runner
```

This invocation compares each pair's completed relationship scorecard with its
YAML expectations and updates
`tests/agentic_linter/test_relationship_review_example_runner.json` and
`tests/agentic_linter/test_relationship_review_example_runner.jsonl`, even when
comparison failures make the command exit nonzero. Verify that both outputs
identify the recorded `AGENT_REVIEW_MODEL`.

## Step 5: Analyze history

For **single-test** review, run:

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

For **test-relationship** review, do not run the single-test history analyzer.
Read `tests/agentic_linter/test_relationship_review_example_runner.json` and
report the current expectation match for every enforced relationship
criterion. Historical classifications are unavailable until test-relationship
snapshots exist; state this without assigning single-test history categories
to test-relationship checks.

## Step 6: Report

For **single-test** review, follow the historical-report procedure below.

The analyzer produces the complete Markdown table. When one or more criteria have a complete heading or rule text that differs from Git HEAD, show only those rows in the initial user-facing report. When no criteria differ from Git HEAD, show the complete analyzer table immediately, sorted by numeric pass percentage ascending and then by criterion number ascending. This is a presentation rule only: do not change the analyzer command, analysis, classifications, or generated table.

Use exactly these columns:

| Criterion # | One-line explanation | # Passing / # Total (%) | Result explanations |
|---:|---|---:|---|

In `Criterion #`, append ` (edited)` only when the criterion's complete
heading or rule text in the working copy differs from that criterion at Git
HEAD. Compare the working copy directly with Git HEAD; wording differences in
older inspected snapshots shall not produce the marker. Render criteria that
match Git HEAD as the plain number, even when `Criterion changed: yes` reports
a historical wording change. Preserve this marker when showing the full table.

In `Result explanations`, show counts and YAML case names for New test pass, New test fail, Fails in HEAD, Regression, and Fixed.
Show the Stable pass count without listing every stable YAML case.
Put every category on a separate line inside the table cell by separating categories with the HTML line break `<br>`. 
The category counts for each criterion must equal that criterion's total enforced YAML checks.
Also state whether a criterion with a current failure changed in the inspected history.

After presenting a focused table of edited criteria, ask whether the user wants the full table containing unchanged criteria. If the user says yes, return every row from the analyzer output already produced. Do not ask this question when the complete table was already shown because no criteria differ from Git HEAD. Sort every full table by the numeric pass percentage in `# Passing / # Total (%)` in ascending order. Break equal percentages by criterion number in ascending order. Do not rerun the analyzer, YAML reviews, or history collection.

For **test-relationship** review, show the full table for all enforced criteria
from the test-relationship JSON report. Use the same four columns, sort by
numeric pass percentage ascending, and break ties by criterion number
ascending. In `Result explanations`, list current failing test-relationship
YAML case/pair keys and summarize the count of passing checks. Do not label
test-relationship results as New test, Flaky, Fails in HEAD, Regression,
Stable pass, or Fixed.

After the table, report:

- final YAML runner status;
- selected review type;
- YAML file, case, test-docstring when test-relationship, and enforced-check counts;
- whether any pending packet rows remain; and
- the path to the selected review type's updated JSON report.

At the end of every completed YAML review cycle, run:

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
```

Print the result as `Cycle completed at (local time): <timestamp>`. Use the
machine's local time from this command rather than inferring the time.

Do not fix fixtures or criteria unless the user asks after reviewing this report.
