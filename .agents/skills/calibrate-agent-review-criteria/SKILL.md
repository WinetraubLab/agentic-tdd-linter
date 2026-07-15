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

## Propose fixes

- For a fixture defect, propose the smallest YAML change that demonstrates the same general rule clearly.
- For criterion ambiguity, propose two or three reusable formulations before editing Jinja.
- Keep candidates domain-neutral. Do not copy fixture paths, identifiers, constants, function names, or domain language into a criterion.
- Preserve the criterion's scope and avoid duplicating another criterion.
- Show candidate wording to the user before running an experiment.

## Run a blind experiment

1. Run `scripts/criterion_experiment.py prepare` with the selected case, criterion number, candidate title, and rule lines. This regenerates only that anonymous packet and changes only the criterion inside the generated packet.
2. Do not edit the YAML or Jinja template during the experiment.
3. Start a fresh isolated reviewer with no conversation context.
4. Give the reviewer only the generated Markdown packet. Do not expose the YAML case name, expected result, earlier reviews, diagnosis, or repository files.
5. Ask the reviewer to evaluate only the experimental criterion, update only its scorecard row, and leave every other row unchanged.
6. Run `scripts/criterion_experiment.py compare` after review.
7. Report candidate wording, expected result, actual result, reviewer reasoning, and mismatch status.

Example:

```bash
.venv/bin/python \
  .agents/skills/calibrate-agent-review-criteria/scripts/criterion_experiment.py \
  prepare extra_assertion_proves_other_behavior 51 \
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
