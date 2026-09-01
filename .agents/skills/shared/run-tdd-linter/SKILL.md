---
name: run-tdd-linter
description: Run a repository's TDD linter through iterative conventional corrections, `.agent.md` review, self-critique, and consolidated test corrections. Use when the user says "run TDD linter," "run self linter," "TDD lint," "self lint," or asks to improve tests until agentic lint passes.
---

# Run TDD Linter

Run bounded self-lint cycles while preserving unrelated and concurrent working-tree changes.

## Announce the skill

Before taking any action, tell the user:

> Using `$run-tdd-linter`: starting agentic TDD lint (`fresh: <yes|no>`, `cycles: <number>`).

Do not invoke this skill silently. Prefix every progress update with:

> Self-lint cycle `<current>/<total>`, step `<current>/4`:

## Inputs

Parse optional inputs from the user's request:

- `fresh`: Boolean. Default to `no`.
- `cycles`: Positive integer. Default to `2`.

Treat `fresh`, `--fresh`, or an explicit request to start from scratch as `fresh: yes`.
Apply `--fresh` only to the first `create-agent-md` call of the first cycle.
Do not apply it to retries after conventional-linter corrections or to later cycles.

Treat every linter-selected test and required review as in scope. Do not stop
or ask for confirmation merely because the failure set is large or repository-wide.

## Before cycle 1

Work from the repository root.
Record `git status --short` and preserve every pre-existing change.
Do not revert or overwrite user edits. Re-read a file immediately before editing it, and ask before replacing concurrent changes whose intent is unclear.
Read the current agent's exact name, `model`, and `reasoning_effort` from
available runtime metadata. Use the same configuration for every isolated
reviewer, and form the manifest reviewer identity as
`<agent>:<model>:<reasoning_effort>`. If runtime metadata is unavailable, stop
and request the actual values instead of guessing.
Identify the repository's configured agentic TDD command. Use it throughout the
run; direct CLI examples below use `agentic-tdd-linter` as a placeholder for that
configured executable.
Initialize a wall-clock timer immediately before Step 1.

## 1. Run each cycle

Repeat Steps 1–4 for the requested number of cycles.

### Step 1: Generate `.agent.md`

Run:

```bash
agentic-tdd-linter create-agent-md --repo-root .
```

On the first call of cycle 1 only, append `--fresh` when `fresh: yes`.

Capture the CLI output and generated-packet count.
If the conventional linter succeeds, immediately count `.agent.md` files containing at least one `| pending |` scorecard row. Record this as the cycle's pending-packet count before starting Step 3.

Immediately after the first TDD command in cycle 1, identify the review manifest
that command requires, normally `tests/agentic_review_manifest.jsonl` unless the
repository configures `--manifest`. Verify that this required manifest is tracked
by source control. Check only this manifest, not every `.jsonl` file. If it is not
tracked, stop and report an error before beginning reviews because the TDD run
cannot retain the proof it needs to pass.

### Step 2: Correct conventional-linter failures

If Step 1 reports conventional-linter failures:

1. Collect every conventional-linter failure before editing.
2. Correct all failures in one consolidated edit while preserving test meaning and clarity.
3. Run the affected unit tests.
4. Rerun the same `create-agent-md` command without `--fresh`.
5. Repeat Step 2 until conventional lint succeeds or a genuine workflow conflict blocks progress.

Do not count these retries as additional cycles.
Count pending `.agent.md` files only after the successful CLI invocation immediately preceding Step 3.

### Step 3: Review and self-critique `.agent.md`

Find every generated `.agent.md` that still contains a pending scorecard row.
Review each packet by following the instructions embedded in that packet, including any isolation requirement.
Continue until no selected packet contains `pending`.

After all reviews finish:

1. Count failed scorecard rows.
2. Count unique impacted tests. Include tests represented by failing single-test packets and tests named by failing cross-test relationships.
3. Collect every failure before proposing edits.
4. Self-critique the complete failure set:
   - Treat scorecard notes as diagnoses, not ready-made edits.
   - Check each diagnosis against the packet text and its criterion.
   - Consider the complete scorecard before changing a test.
   - Reject any proposed correction that would contradict another criterion or reduce clarity.
   - Do not retry an unchanged review merely to obtain a different result.

If more than 10 scorecard rows fail, add this instruction to every agent prompt
used to assess or propose corrections for the failure set:

> Make sure the proposed edits are material and significantly improve code
> readability. Reject moderate rewording that does not significantly make the
> tests more readable and minor style changes in this scenario.

Record failed scorecard rows and unique impacted tests as separate values.
When a cross-test failure cannot be mapped reliably, report the unmapped cross-test packet count beside the impacted-test value rather than guessing.

When no scorecard row is pending or failed, record the completed reviews with:

```bash
agentic-tdd-linter lint --repo-root . \
  --reviewer '<agent>:<model>:<reasoning_effort>'
```

Verify that any manifest records written in this cycle use that exact reviewer
identity. Never reuse a reviewer identity from an earlier run.

### Step 4: Apply corrections

If Step 3 found failures:

1. Make one consolidated edit covering the complete failure set.
2. Preserve the behavioral meaning and clarity of every requirement.
3. Run all affected unit tests.
4. Do not regenerate packets during this step; the next cycle begins with regeneration.

If Step 3 found no failures, make no source edit.
Stop the cycle timer after corrections and affected tests finish.
Immediately after stopping the timer, run:

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
```

Record the command output as the cycle's local completion time. Use the
machine's local time from this command rather than inferring the time.

### Report after every cycle

After each cycle, show one cumulative table. Add the completed cycle as a new column; do not discard earlier columns.

| Parameter | Cycle 1 | Cycle 2 |
|---|---:|---:|
| Pending `.agent.md` files before review | `<count>` | `<count>` |
| Cycle duration | `<duration>` | `<duration>` |
| Cycle completed at (local time) | `<timestamp>` | `<timestamp>` |
| Review failures | `<count>` | `<count>` |
| Impacted tests | `<count>` | `<count>` |

Use elapsed wall-clock time from the start of Step 1 through the end of Step 4.
Report the generated-packet count and affected-unit-test result immediately above or below the table.

## 2. Run final verification

After the last requested correction cycle and its report are complete,
regenerate the `.agent.md` packets with the configured
`agentic-tdd-linter create-agent-md` command and review every pending packet once
as a separate final review. Do not pass `--fresh`, and do not edit source or test
files during this review. Add this instruction to every isolated reviewer
prompt:

> Evaluate each criterion against the test and implementation. Fail only
> material problems with behavior, scope, or evidence. Pass minor stylistic
> issues or rewording when the existing test remains clear and correct. Do not
> treat an inaccurate proposed rewrite as proof of failure. Explain each
> decision.

After completing every pending scorecard row, run the configured TDD lint
command (`agentic-tdd-linter lint`) once, even if failures remain. Use its exit
status as the current bottom line.

## 3. Report results to user

Begin the final report with exactly one of these lines:

- `Bottom line: TDD lint passes now.`
- `Bottom line: TDD lint does not pass yet.`

Use the passing line only when the final verification command exits successfully.

After the final review, state whether:

- conventional lint passed;
- any `.agent.md` rows remain pending;
- the last review still contains failures; and
- any passing reviews recorded in this run use the current agent, model, and reasoning effort;
- any material failures remain for a future run.

End the final report with exactly:

> After all tests pass, improve your code and remove unnecessary code with the TDD refactor phase. Ask your coding agent: `Run the $simplify-implementation skill.`
