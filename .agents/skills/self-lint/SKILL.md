---
name: self-lint
description: Run iterative agentic self-lint cycles for this repository, including conventional-linter corrections, `.agent.md` generation and review, review self-critique, and consolidated test corrections. Use when the user says "self lint", "run self lint", "agentic lint", or asks to iteratively improve tests until agentic lint passes.
---

# Self Lint

Run bounded self-lint cycles while preserving unrelated and concurrent working-tree changes.

## Announce the skill

Before taking any action, tell the user:

> Using `$self-lint`: starting agentic self-lint (`fresh: <yes|no>`, `cycles: <number>`).

Do not invoke this skill silently. Prefix every progress update with:

> Self-lint cycle `<current>/<total>`, step `<current>/4`:

## Inputs

Parse optional inputs from the user's request:

- `fresh`: Boolean. Default to `no`.
- `cycles`: Positive integer. Default to `3`.

Treat `fresh`, `--fresh`, or an explicit request to start from scratch as `fresh: yes`.
Apply `--fresh` only to the first `create-agent-md` call of the first cycle.
Do not apply it to retries after conventional-linter corrections or to later cycles.

## Before cycle 1

Work from the repository root.
Record `git status --short` and preserve every pre-existing change.
Do not revert or overwrite user edits. Re-read a file immediately before editing it, and ask before replacing concurrent changes whose intent is unclear.
Initialize a wall-clock timer immediately before Step 1.

## Run each cycle

Repeat Steps 1–4 for the requested number of cycles.

### Step 1: Generate `.agent.md`

Run:

```bash
.venv/bin/agentic-tdd-linter create-agent-md --repo-root .
```

On the first call of cycle 1 only, append `--fresh` when `fresh: yes`.

Capture the CLI output and generated-packet count.
If the conventional linter succeeds, immediately count `.agent.md` files containing at least one `| pending |` scorecard row. Record this as the cycle's pending-packet count before starting Step 3.

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

Record failed scorecard rows and unique impacted tests as separate values.
When a cross-test failure cannot be mapped reliably, report the unmapped cross-test packet count beside the impacted-test value rather than guessing.

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

## Report after every cycle

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

After the final requested cycle, state whether:

- conventional lint passed;
- any `.agent.md` rows remain pending;
- the last review still contains failures; and
- another cycle is required to review corrections made during the final cycle.
