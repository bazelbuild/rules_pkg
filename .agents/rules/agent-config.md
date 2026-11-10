---
trigger: glob
description: Prose style rules for agent configs, rules, and skills
globs: ".agents/**/*.md,AGENTS.md,CLAUDE.md,GEMINI.md"
---

# Agent Configuration Style

* Write in concise Strunk & White prose: omit needless words, use active voice,
  and state imperatives directly.
* Do not use mannered prose, filler phrases, or verbose explanations.
* Wrap lines at 80 columns.
* Keep `CLAUDE.md` and `GEMINI.md` as one-line `@./AGENTS.md` pointers. Put
  shared guidance in `AGENTS.md` or `.agents/rules/`.
