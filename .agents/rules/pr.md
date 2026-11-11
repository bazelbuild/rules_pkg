---
trigger: model_decision
description: Rules for commits, pull request descriptions, and PR comments
---

@patching.md

# Pull Request Conventions

Before drafting a pull request, follow `patching.md` above and
`developers.md`.

## Scope
* PRs that change or add behavior must be tied to an issue. Link it in the
  description (`Fixes #<issue>` or `Work towards #<issue>`).
* Significant changes need a design discussion in an issue first.
* Do not send PRs that only bump dependency versions.
* Split refactoring from behavior changes into separate PRs.

## Titles and Descriptions
* Title format: `<area>: <summary>` when the change is scoped to one rule or
  area (e.g. `pkg_rpm: add vendor and packager attributes`); otherwise a
  plain imperative summary.
* The description becomes the merge commit message. State *why* the change
  is made and *how* at a conceptual level. Wrap at 80 columns.
* Never include per-file change lists, test logs, checklists, or AI
  disclosure metadata in the description or commit messages.
* Preserve the author's wording unless asked to change it.
* If the title or description diverges from the branch's scope, tell the
  user and ask before updating GitHub.

## Commit Workflow
* Do not commit or push without explicit permission.
* Never amend or rebase. Once a PR exists, push new commits or merge commits
  so review threads stay intact.
* Push to your fork (`origin`) and open the PR against
  `bazelbuild/rules_pkg` `main`.

## Comments
* When creating a PR, post one comment explaining how comments will be
  handled (agent monitors and replies, human reviews agent replies, or human
  replies directly).
* End every posted comment with an italicized line:
  * `*This is an automatically generated agent comment.*` when the user did
    not approve the exact text.
  * `*This is an agent-generated comment reviewed and approved by the
    user.*` only when they did.
* Comment only when actionable: answer a question, ask one, or say `PTAL`
  once CI passes. Do not narrate CI runs, SHAs, or diff details.
