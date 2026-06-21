# GitHub Actions Review Proof

`agentic-tdd-linter` separates local agent review from CI verification.

The full review artifacts stay local. The committed proof is the compact JSONL manifest at `tests/agentic_review_manifest.jsonl`.

## Local Review

Run the linter on the developer machine:

```bash
agentic-tdd-linter check --all --reviewer codex:gpt-5.5
```

The linter checks `tests/agentic_review_manifest.jsonl` first. If the manifest is missing or stale, it writes review artifacts under `tests/agentic_review_artifacts`. Each artifact includes the agent review prompt, a copy of the test file being reviewed, the review `Status:`, review notes, and the test file SHA. The artifact files are intentionally ignored by git.

Review those artifacts with the local Claude or Codex session already being used for development. After review, the agent sets each artifact `Status:` to `pass` or `fail`.

Then rerun the same command:

```bash
agentic-tdd-linter check --all --reviewer codex:gpt-5.5
```

When the reviewed artifacts pass, the rerun writes or updates `tests/agentic_review_manifest.jsonl`. Commit that manifest with the code change.

## Manifest Contents

Each JSONL record proves one reviewed test file:

```json
{"path": "tests/test_example.py", "source_sha256": "...", "status": "pass", "linter_version": "0.1.0", "review_contract_sha256": "...", "reviewer": "codex:gpt-5.5"}
```

The fields mean:
- `path`: the reviewed test file.
- `source_sha256`: the exact contents of that test file at review time.
- `status`: the review result. CI accepts only `pass`.
- `linter_version`: the stable linter version value that wrote the attestation.
- `review_contract_sha256`: a hash of the linter source and repository documentation.
- `reviewer`: the model or agent identity used for review.

## GitHub Actions Verification

In CI, run the same command:

```bash
agentic-tdd-linter check --all --reviewer codex:gpt-5.5
```

GitHub Actions verifies the committed manifest against the committed repository state before falling back to artifact review:
1. The manifest must include a record for each checked test file.
2. Each `source_sha256` must match the committed test file contents.
3. Each record must have `status: pass`.
4. Each `linter_version` must match the linter version installed by the workflow.
5. Each `review_contract_sha256` must match the current linter source and documentation.

When those checks pass, CI does not need the full review artifacts. When the manifest is missing or stale, the command creates the full review artifact and fails until the review is completed locally and the refreshed manifest is committed.

## Token Cost

GitHub Actions does not need to call Claude, Codex, or another model. The model work happens locally before commit. CI only verifies cryptographic hashes and manifest fields.

That means teams can use their existing local Claude or Codex session for review and avoid paying for another model pass in CI.

## When To Refresh Proof

Run `agentic-tdd-linter check --all --reviewer ...` again when:
- a reviewed test file changes
- the linter version is bumped
- `README.md`, `pyproject.toml`, or files under `docs` change
- the manifest format changes
