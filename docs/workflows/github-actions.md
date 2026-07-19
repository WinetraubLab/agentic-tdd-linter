# GitHub Actions Review Proof

GitHub Actions verifies committed agent-review proof. It does not perform reviews or create `.agent.md` files. The local review workflow is documented in the README.

The committed proof is the compact JSONL manifest at `tests/agentic_review_manifest.jsonl`.

## Manifest Contents

Each JSONL record proves one reviewed test:

```json
{"path": "tests/test_example.py", "test": "test_example", "source_sha256": "...", "status": "pass", "linter_version": "0.1.0", "review_contract_sha256": "...", "reviewer": "codex:gpt-5.5"}
```

The fields mean:
- `path`: the reviewed test file.
- `test`: the reviewed test name.
- `source_sha256`: the exact contents of that test file at review time.
- `status`: the review result. CI accepts only `pass`.
- `linter_version`: the linter version that wrote the attestation.
- `review_contract_sha256`: a hash of the linter source and repository documentation.
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
2. Each `source_sha256` must match the committed test file contents.
3. Each record must have `status: pass`.
4. Each `linter_version` must exactly match the linter version installed by the workflow.
5. Each `review_contract_sha256` must match the current linter source and documentation.

When those checks pass, CI succeeds without the local `.agent.md` files. When proof is missing or stale, `lint` exits with failure and tells the developer to complete the local review workflow. It never creates `.agent.md` files in CI.
