---
trigger: always_on
---

# Workspace Rules

Unless told otherwise, start new work from current upstream code:
* `upstream` is `bazelbuild/rules_pkg`; `origin` is the user's fork.
* Fetch first (`git fetch upstream main`) and base new branches on it
  (`git checkout -b <branch> upstream/main`).
* Push only to `origin`, and only with explicit permission.
* When syncing with `upstream/main`, commit or stash local changes first and
  conclude the merge in its own commit. Never `git stash` while `MERGE_HEAD`
  is active.
* Never pass `gh auth token` output or other credentials on a command line or
  in a URL. Use configured SSH keys or `gh` natively.
