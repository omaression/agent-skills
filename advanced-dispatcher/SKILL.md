---
name: advanced-dispatcher
description: Route mid-session work to the right spawned model without changing the fixed main session. Use for coding, architecture, math, algorithms, web development, brainstorming, research, long-context reading, quick scripts, formatting, multi-model tradeoff evaluation, or structured build pipelines triggered by buildq:, build:, or buildx:. Default to strict no-Claude routing; allow Claude only when the current prompt explicitly includes --force-claude.
---

# Advanced Dispatcher

Classify work, dispatch it to the best spawned model, return the result to the main session.

## Non-negotiable rules

- Never use Anthropic models unless the current prompt contains `--force-claude`.
- Reject `--use-claude`, `--force-opus`, `--no-opus`.
- `--force-claude` is prompt-scoped, not session-scoped.
- Deterministic routing over ad hoc judgment.
- `openai-codex/*` → `long` cache retention.
- `opencode-go/*` → `short` cache retention.
- Claude never appears in build pipelines; `--force-claude` is limited to tradeoff proposals.
- For coding work intended to merge, use Trunk-Based Development: one short-lived branch per feature/bug/fix/area.
- Every PR-ready build flow must run robust automated tests before calling the work ready.
- Keep git-visible diffs minimal, atomic, and limited to necessary files.

## Routing table

| Domain | Model |
|---|---|
| Code & architecture | `openai-codex/gpt-5.4` |
| Math & algorithms | `opencode-go/glm-5` |
| Web dev & brainstorming | `opencode-go/minimax-m2.5` |
| Research & long context | `opencode-go/kimi-k2.5` |
| Quick scripts & formatting | `openai-codex/gpt-5.3-codex-spark` |

Spanning categories → route by highest-risk deliverable: architecture > math > long-context > formatting.

## Tradeoff protocol

Trigger when the user compares approaches, evaluates tradeoffs, or asks "which is better."

Default proposals: `opencode-go/glm-5` + `openai-codex/gpt-5.3-codex`
With `--force-claude`: `anthropic/claude-sonnet-4-6` + `anthropic/claude-opus-4-6`
Judge (always): `openai-codex/gpt-5.4`

## Build pipelines

Trigger on `buildq:`, `build:`, or `buildx:` prefix.

Pre-step: create or verify one short-lived branch for the scoped work.

### buildq: (quick, 5 steps)
1. plan → `gpt-5.4`
2. implement → `gpt-5.4`
3. test → `glm-5`
4. simplify → `gpt-5.3-codex`
5. retest → `glm-5`

### build: (standard, 10 steps)
1. parallel-plan-a → `gpt-5.4`
2. parallel-plan-b → `glm-5`
3. judge-plan → `gpt-5.4`
4. boilerplate → `gpt-5.3-codex-spark`
5. implement → `gpt-5.4`
6. test → `glm-5`
7. simplify → `gpt-5.3-codex`
8. retest → `glm-5`
9. review-resolve → `gpt-5.4`
10. final-test → `glm-5`

### buildx: (strict, 12 steps)
1. parallel-plan-a → `gpt-5.4`
2. parallel-plan-b → `glm-5`
3. judge-plan → `gpt-5.4`
4. boilerplate → `gpt-5.3-codex-spark`
5. implement → `gpt-5.4`
6. test → `glm-5`
7. simplify → `gpt-5.3-codex`
8. retest → `glm-5`
9. review-resolve-a → `gpt-5.4`
10. test-a → `glm-5`
11. review-resolve-b → `kimi-k2.5`
12. final-test → `glm-5`

Exit rule: do not mark the branch PR-ready until automated tests pass and the diff stays atomic.

## Judge output contract
See `../shared/contracts.md` (base section).

## Simplify contract
See `../shared/contracts.md`.

## Implementation contract

`dispatcher.py` must produce deterministic `RoutePlan` objects, expose route choice + cache retention + rationale + pipeline steps, support tradeoff/buildq/build/buildx, reject empty prompts and legacy flags.

## Validation checklist

1. Run `test_dispatcher.py` — all pass.
2. Smoke test tradeoff, `buildq:`, `build:`, `buildx:`.
3. Confirm Claude unreachable without `--force-claude`.
4. Confirm Claude never in build pipelines.
5. Confirm cache retention correctness.
6. Confirm judge output includes branch plan and PR/CI test gates.
