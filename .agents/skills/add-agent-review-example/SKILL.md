---
name: add-agent-review-example
description: Add a discovered Python test to this repository's agent-review YAML examples. Use when the user says they found a test, test snippet, or test file that should become an agent-review example and wants Codex to choose the appropriate YAML file, create the example, assign expected scorecard results, and validate the fixture schema.
---

# Add Agent Review Example

Add one test example to `tests/agentic_linter/fixtures/single_test_review/` while keeping the
YAML schema and Jinja scorecard synchronized.

## Workflow

1. Locate the repository root and read:
   - `tests/agentic_linter/fixtures/single_test_review/*.yaml`
   - `src/agentic_tdd_linter/agentic_linter/single_test_review.agent.md.j2`
   - `tests/agentic_linter/agent_review_yaml_fixture_contract.py`
   - `tests/agentic_linter/test_agent_review_yaml_fixture_contract.py`
2. Obtain the complete Python test source from the path, test name, or snippet supplied by
   the user. Preserve the source exactly; add only YAML block indentation.
3. Choose the YAML file whose filename and existing content
   best match the behavior being demonstrated. Create a topical YAML file only when
   no existing file is a reasonable fit.
4. When creating a YAML file, copy the exact required documentation header from
   `REQUIRED_FILE_DOCSTRING` in `tests/agentic_linter/agent_review_yaml_fixture_contract.py` and leave
   exactly one blank line before the first example.
5. Add a uniquely named example in this order:

   ```yaml
   descriptive_example_name:
     test: |
       def test_example() -> None:
           ...
     expected_scorecard:
       11: # First Sentence Describes Behavior
         fail # Explain why this result is expected.
   ```

6. Include only criterion numbers whose outcomes the example is intended to verify.
   Omitted scorecard criteria are ignored by comparison, whether the reviewer marks
   them `pass` or `fail`.
7. Copy every criterion number and title exactly from the Jinja template. Set its
   outcome to only `pass` or `fail`, followed by a non-empty explanation comment.
8. Keep exactly one blank line between top-level examples.
9. Run the focused schema test:

   ```bash
   .venv/bin/python -m unittest \
     tests.agentic_linter.test_agent_review_yaml_fixture_contract.AgentReviewYamlFixtureContractTests.test_accepts_repository_fixtures \
     -q
   ```

10. Run `git diff --check` and report the selected YAML file, example name, declared
    scorecard outcomes, and validation result.

## Guardrails

- Do not place `expected_scorecard` data inside generated Markdown review packets.
- Do not add fields other than `test` and `expected_scorecard` to an example.
- Do not alter the discovered test to make an expected result easier to obtain.
- Do not invent criterion numbers or paraphrase criterion-title comments.
- Do not run
  `tests.integration_tests.test_agent_review_examples.AgentReviewExampleTests.test_anonymous_agent_review_examples`
  unless the user asks to begin agent evaluation; that test intentionally creates
  pending review packets.
- Preserve unrelated repository changes.
