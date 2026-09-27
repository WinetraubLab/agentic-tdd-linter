---
name: update-agentic-tdd-linter
description: Use in a repository that depends on an older agentic TDD linter after a new version is published, so that repository's local checks and CI use the new version.
---

# Update Agentic TDD Linter

## Announce the skill

Before taking action, tell the user:

> Using `$update-agentic-tdd-linter`: checking the shared linter pin and installed executable.

Do not invoke this skill silently.

## Update procedure

1. Record the parent repository status. Identify its linter declaration,
   `.agents/skills/shared` submodule if present, configured command, and existing
   virtual-environment installation.
2. Preserve unrelated parent changes. Stop before replacing a dirty submodule
   whose edits are not part of the request.
3. Fetch the submodule's configured remote branch and resolve its exact commit.
   Move the submodule to that fetched commit. Do not assume `git pull` in the
   parent updates the submodule.
4. Reinstall the linter into an existing virtual environment from the updated
   local submodule. For the standard layout, run:

   ```bash
   .venv/bin/python -m pip install --no-deps --force-reinstall \
     ./.agents/skills/shared
   ```

5. If no submodule exists, update the repository's declared dependency or
   install the exact fetched commit while preserving its dependency-management
   convention.
6. Verify the submodule HEAD equals the fetched commit. Verify the installed
   distribution points to the updated source, and run the configured linter
   command.
7. Report linter failures separately from update failures. A linter may be
   current even when repository tests or review packets fail.
8. Tell the user to commit and push the parent repository's updated linter
   reference so other clones and CI receive the update. Do not stage or commit
   unless asked.

When updating multiple repositories, perform the same checks independently and
report the selected commit and verification result for each repository.
