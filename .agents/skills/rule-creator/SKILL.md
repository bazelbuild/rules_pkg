---
name: rule-creator
description: Create and format agent rules with proper front matter in the
  workspace
---

Use this skill when you need to create a new rule for the agent in the
workspace.

### Rule File Location

Create each workspace rule as its own Markdown file:
```
.agents/rules/<rule-name>.md
```

### Rule Format

Every rule file starts with a YAML front matter block defining the trigger
condition, followed by the rule content in Markdown.

```yaml
---
trigger: <trigger-condition>
---

# <Rule Title>

<Rule description and directives...>
```

#### Trigger Conditions
*   `always_on`: The rule applies to all tasks.
*   `model_decision`: The agent loads the rule based on its `description`
    when relevant. Prefer it for conceptual or cross-cutting rules (e.g.,
    `pr.md`, `rules_pkg.md`, `testing.md`).
*   `glob`: The rule activates when matching files (`globs:`) are accessed.
    Use it for syntax and formatting rules tied to file types. `globs` must
    be a quoted, comma-separated string (e.g., `globs: "*.bzl,BUILD"`),
    never a YAML list.

### Domain Separation
*   Keep language and tool rule files (`starlark.md`, `python.md`,
    `shell.md`, `docs.md`) general to those domains.
*   Put rules_pkg-specific API and distribution invariants in
    `.agents/rules/rules_pkg.md`.
*   Put shared guidance in `AGENTS.md`. Keep `CLAUDE.md` and `GEMINI.md` as
    `@./AGENTS.md` pointers.

### Formatting Guidelines
*   Wrap all text to 80 columns.
*   Omit needless words. State directives directly in active voice.
