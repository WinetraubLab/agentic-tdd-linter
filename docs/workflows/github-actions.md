# GitHub Actions Review Proof

`agentic-tdd-linter` separates local agent review from CI verification.

The full review artifacts stay local. The committed proof is the compact JSONL manifest at `tests/agentic_review_manifest.jsonl`.

## Local Review

Run the linter on the developer machine:

```bash
agentic-tdd-linter check --all
```

The first run writes review artifacts under `tests/agentic_review_artifacts`. These artifacts contain the review prompt, test source, status field, notes, and source SHA. They are intentionally ignored by git.

Review those artifacts with the local Claude or Codex session already being used for development. After review, the agent sets each artifact `Status:` to `pass` or `fail`.
