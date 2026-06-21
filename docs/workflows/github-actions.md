# GitHub Actions Review Proof

`agentic-tdd-linter` separates local agent review from CI verification.

The full review artifacts stay local. The committed proof is the compact JSONL manifest at `tests/agentic_review_manifest.jsonl`.

## Local Review

Run the linter on the developer machine:

```bash
agentic-tdd-linter check --all
```

The linter checks `tests/agentic_review_manifest.jsonl` first. If the manifest is missing or stale, it writes review artifacts under `tests/agentic_review_artifacts`. Each artifact includes the agent review prompt, a copy of the test file being reviewed, the review `Status:`, review notes, and the test file SHA. The artifact files are intentionally ignored by git.

Review those artifacts with the local Claude or Codex session already being used for development. After review, the agent sets each artifact `Status:` to `pass` or `fail`.
## Manifest Contents

Each JSONL record proves one reviewed test file:

```json
{"path": "tests/test_example.py", "source_sha256": "...", "status": "pass", "linter_version": "0.3.0", "review_contract_sha256": "...", "reviewer": "codex:gpt-5"}
```

The fields mean:
- `path`: the reviewed test file.
- `source_sha256`: the exact contents of that test file at review time.
- `status`: the review result. CI accepts only `pass`.
- `review_contract_sha256`: a hash of the linter source and repository documentation.
- `reviewer`: the model or agent identity used for review.

