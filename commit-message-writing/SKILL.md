---
name: commit-message-writing
description: Strict Conventional Commits v1.0.0 and SemVer commit discipline for git work. Use when preparing a commit, staging changes, writing or revising a commit message, deciding whether to split changes into multiple commits, planning a commit sequence, summarizing changes for a commit, discussing changelogs or releases, or after finishing any meaningful implementation unit even if the user did not explicitly ask to commit.
---

# Commit Message Writing

Write every commit as a valid Conventional Commit and keep each commit atomic.

## Enforcement model

Use two layers together:

1. `/.githooks/commit-msg` hard-blocks invalid commit messages at commit time.
2. This skill provides planning discipline: split changes correctly, choose the right type, and explain SemVer impact.

If the hook is not active yet, run:

```bash
bash scripts/install-git-hooks.sh
```

This sets `core.hooksPath=.githooks` for the repository so the tracked hook is used automatically.

## Required workflow

1. Check `git status --short` and `git diff --stat`.
2. Decide whether the current changes are one logical unit.
3. If multiple concerns are mixed, split them before committing. Do not batch unrelated work.
4. Pick the most specific commit type.
5. Write the message in this exact shape:

```text
<type>[optional scope][!]: <imperative lowercase description>

[optional body]

[optional footer(s)]
```

6. Validate the message before commit, even though the hook will also enforce it.
7. State SemVer impact when the user asks for release or version advice.

## Hard rules

- Always include a lowercase type followed by `: `.
- Use `feat` for new features.
- Use `fix` for bug fixes.
- Keep the description imperative, lowercase, and without a trailing period.
- Keep the description at 72 characters or fewer.
- Start the body one blank line after the description.
- Start footers one blank line after the body, or one blank line after the description if there is no body.
- Use footer format `Token: value`.
- Use hyphens instead of spaces in footer tokens, except `BREAKING CHANGE`.
- Use `!` and/or a `BREAKING CHANGE:` footer for breaking changes.
- Never use `WIP`, `misc`, `update`, or vague summaries.

## Type selection

- `feat` — new user-visible feature → SemVer minor
- `fix` — bug fix → SemVer patch
- `refactor` — restructure without behavior change → no bump
- `perf` — performance improvement → no bump unless it fixes a bug, then patch
- `docs` — documentation only → no bump
- `test` — tests only → no bump
- `build` — build system or dependencies → no bump
- `ci` — CI/CD changes → no bump
- `chore` — maintenance or tooling not covered above → no bump
- `style` — formatting only → no bump
- `revert` — revert prior commit → depends on reverted change

## Scope guidance

- Use a consistent noun for the affected area when one area is clearly dominant.
- Good scopes: `auth`, `telegram`, `memory`, `resume`, `roadmap`, `notion`.
- Omit scope only when the change is truly cross-cutting.
- Do not invent multiple scopes in one commit line.

## Splitting rules

Split into separate commits when any of these are true:

- new feature plus bug fix
- code changes plus formatting-only cleanup
- dependency/build changes plus application logic
- refactor plus behavior change that can stand alone
- generated files plus source changes that are not tightly coupled

If you cannot describe the whole diff with one type and one intent, split it.

## Body and footer guidance

Add a body when the reason is not obvious from the subject line.

Good footer examples:

```text
Refs: #42
Reviewed-by: Omar Abdalla
BREAKING CHANGE: remove legacy webhook payload format
```

## Examples

Good:

```text
feat(memory): add semantic search over past conversations

fix(telegram): handle empty message payloads gracefully

Ollama can return an empty string when context overflows.
Guard against it to avoid a bot crash.

feat(api)!: replace rest endpoints with graphql

BREAKING CHANGE: remove all /v1/rest/* routes

chore(deps): upgrade pydantic to 2.11
```

Bad:

```text
fixed stuff
Update
WIP
misc changes
feat: added the thing
```

## Validation helper

Use `skills/commit-message-writing/scripts/validate_commit_message.py` to lint a message before commit.

Examples:

```bash
python3 skills/commit-message-writing/scripts/validate_commit_message.py --message "feat(auth): add otp fallback"
printf 'fix(api): handle nil payload\n\nGuard a crash path.' | python3 skills/commit-message-writing/scripts/validate_commit_message.py --stdin
```

If the validator fails, fix the message before running `git commit`.
