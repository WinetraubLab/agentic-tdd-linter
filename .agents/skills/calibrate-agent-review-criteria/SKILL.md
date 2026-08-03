---
name: calibrate-agent-review-criteria
description: Diagnose mismatches between single-test agent-review YAML expectations and anonymous scorecards, decide whether the fixture or criterion is wrong, and test generalized criterion wording through blind isolated packet experiments. Use when a YAML example expects pass or fail for a criterion but an agent review returns a different result.
---

# Calibrate Agent Review Criteria

Resolve scorecard mismatches without tailoring review rules to one fixture.

## Diagnose

1. Read the mismatched YAML example, its selected `expected_scorecard` rows, the corresponding generated packet, and the relevant criterion in `single_test_review.agent.md.j2`.
2. Classify each mismatch:
   - **Fixture defect:** obsolete syntax, an ambiguous example, or an expectation outside the criterion's scope.
   - **Criterion ambiguity:** the intended rule is valid but the criterion does not state it clearly enough.
   - **Reviewer variance:** the fixture and criterion align, but isolated reviews disagree.
3. Do not change YAML merely to force a passing comparison when it represents behavior the criterion should detect.

## Run Option A and audit contradictions

1. Collect every YAML example that enforces the selected criterion, not only the initially mismatched case.
2. Show **Option A**, consisting of the criterion's existing heading and complete wording unchanged.
3. Prepare Option A with `--current` for every collected example. Preserve every packet and run a fresh isolated review of only the selected criterion.
4. Compare every Option-A result with its YAML expectation.
5. Before creating Options B through D, group the examples by the exact content that the criterion evaluates. Use only the sections and fields named by the criterion; ignore content outside its scope. For criterion 44, for example, compare `File Docstring` content because criterion 44 evaluates only that section.
6. Treat opposite YAML expectations for identical criterion-scoped content as a contradiction. Similar content with a material scoped difference is not a contradiction.
7. If contradictions exist, stop before proposing or running Options B through D. Present every contradiction to the user in a table containing:
   - YAML file and case name;
   - expected result;
   - the identical criterion-scoped content or a precise summary and stable hash; and
   - why no criterion wording can produce both outcomes.
8. Do not edit the fixtures or choose an expectation. Ask the user to resolve the intended behavior, then restart Option A after the fixtures are aligned.
9. If no contradictions exist, report the complete Option-A result and continue to proposing Options B through D.

Example Option-A preparation:

```bash
.venv/bin/python \
  .agents/skills/calibrate-agent-review-criteria/scripts/criterion_experiment.py \
  prepare <case> <criterion> --current
```

## Propose fixes after the audit

- For a fixture defect, propose the smallest YAML change that demonstrates the same general rule clearly.
- For criterion ambiguity, propose exactly three reusable replacements labeled **Option B**, **Option C**, and **Option D** before editing Jinja.
- Keep candidates domain-neutral. Do not copy fixture paths, identifiers, constants, function names, or domain language into a criterion.
- Preserve the criterion's scope and avoid duplicating another criterion.
- Show Options A through D to the user before running the B-through-D experiment.

## Run the B-through-D blind experiment

1. Run this experiment only after the Option-A contradiction audit passes.
2. Preserve the complete Option-A packets and results as the unchanged baseline. Regenerate Option A only when a fixture or criterion changed after that baseline.
3. Prepare Options B, C, and D separately with the selected case, criterion number, candidate title, and rule lines. This regenerates only that anonymous packet and changes only the experimental criterion.
4. Preserve a separate packet for each option so experiments cannot overwrite or influence one another. Use option-labeled paths such as `a/`, `b/`, `c/`, and `d/`.
5. Do not edit the YAML or Jinja template during the experiment.
6. Start a fresh isolated reviewer with no conversation context for each option.
7. Give the reviewer only that option's generated Markdown packet. Do not expose the YAML case name, expected result, other options, earlier reviews, diagnosis, or repository files.
8. Ask the reviewer to evaluate only the experimental criterion, update only its scorecard row, and leave every other row unchanged.
9. Run `scripts/criterion_experiment.py compare` separately for the preserved Option-A baseline and every reviewed replacement.
10. Show the user a side-by-side result containing Options A through D, their wording, expected result, actual result, reviewer reasoning, and mismatch status.
11. Compare every replacement with Option A. Treat a replacement as an improvement only when it resolves a mismatch that Option A reproduces without regressing controls.

Example:

```bash
.venv/bin/python \
  .agents/skills/calibrate-agent-review-criteria/scripts/criterion_experiment.py \
  prepare assertion_quality_001_extra_assertion_proves 51 \
  --title "Assertions Prove the Stated Requirement" \
  --rule 'Every assertion shall prove the exact behavior stated in `Requirement Tested`.' \
  --rule 'Assertions that further validate related behavior require explicit descriptions in `Requirement Tested`.'
```

## Check generality

A candidate is promising only when:

- The isolated result matches the YAML expectation.
- The review note follows the general rule rather than fixture-specific clues.
- The wording applies to another domain with the same structural defect.
- An expected-pass example for the criterion remains valid.
- Another expected-fail example with different language is still detected when available.

Treat one successful run as evidence, not proof. Repeat blind reviews when variance is suspected.

## Apply an accepted criterion

After user approval:

1. Update the criterion heading and wording in `single_test_review.agent.md.j2`.
2. Update its scorecard-row title.
3. Update matching YAML criterion comments and focused render assertions.
4. Regenerate and review affected single-test packets.
5. Run focused YAML comparisons, then the complete single-test YAML suite.
6. Do not run cross-test review unless the user explicitly requests it.

Keep pending packets separate from expectation mismatches in the final report.
