# GitHub Actions Review Proof

This repository has two separate workflows:

- The **pre-commit review workflow** creates `.agent.md` scorecards, completes their reviews, and records proof in the manifest before changes are committed.
- The **CI/CD validation workflow** runs `agentic-tdd-linter lint` against the committed tests and manifest proof.

GitHub Actions verifies committed agent-review proof. It performs only the CI/CD validation workflow. It does not perform reviews, create `.agent.md` files, or record new manifest proof. The pre-commit review workflow is documented in the README.

The committed proof is the compact JSONL manifest at `tests/agentic_review_manifest.jsonl`.

## Manifest Contents

Each JSONL record proves one reviewed test:

```json
{"path": "tests/test_example.py", "test": "test_example", "source_sha256": "...", "status": "pass", "linter_version": "0.1.0", "review_contract_sha256": "...", "reviewer": "codex:gpt-5.5"}
```

The fields mean:
- `path`: the reviewed test file.
- `test`: the reviewed test name.
- `source_sha256`: the exact extracted content of that test function at review time.
- `status`: the review result. CI accepts only `pass`.
- `linter_version`: historical metadata identifying the linter version that wrote the attestation.
- `review_contract_sha256`: a hash of the linter's Python and Jinja source files,
  `README.md`, `pyproject.toml`, and Markdown files under `docs/` at review time. It
  does not hash the reviewed test or the completed review response.
- `reviewer`: the model or agent identity used for review.

## Workflow Verification

In CI, verify the manifest:

```bash
agentic-tdd-linter lint
```

You can run that command directly as a workflow step, or call it from dogfood tests that are already part of the normal unit suite. This repository uses the dogfood test path, so the unit test workflow only needs:

```bash
python -m unittest discover -s tests
```

The workflow verifies the committed manifest against the committed repository state:
1. The manifest must include a record for each checked test.
2. Each `source_sha256` must match the committed test function's extracted content.
3. Each record must have `status: pass`.

The recorded `linter_version` and `review_contract_sha256` identify the linter and
review policy used for the original review. Changes to the linter or review policy do
not require a new review. A new review is required only when `source_sha256` no longer
matches the current test content.

When those checks pass, CI succeeds without the local `.agent.md` files. When proof is missing or stale, `lint` exits with failure and tells the coding agent to run the `$run-tdd-linter` skill. It never creates `.agent.md` files in CI.
