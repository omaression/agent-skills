---
name: portfolio-dispatcher
description: Build and route work for Omar's portfolio project sequence across Finance, Healthcare, and Sustainability. Use when the user asks to plan, compare, architect, implement, review, or continue any of the three flagship portfolio projects, including references to "portfolio project," "finance project," "healthcare project," "sustainability project," "track project," or the 3-project employability portfolio sequence.
---

# Portfolio Dispatcher

Route portfolio project work through buildx pipelines (full or lite) with custom model assignments. Sits alongside `advanced-dispatcher` without modifying it.

## Non-negotiable rules

- Every prompt routes through `buildx`, `buildx-lite`, or tradeoff. No `buildq:`, `build:`, or standard single-model routes.
- Reject all flags: `--force-claude`, `--use-claude`, `--force-opus`, `--no-opus`.
- Escalation is per-step, not global.
- `portfolio_dispatcher.py` is the routing source of truth.
- Follow Trunk-Based Development: one short-lived branch per feature/bug/fix/area.
- Every PR-ready build flow must run robust automated tests first.
- Keep git diffs minimal, atomic, necessary files only.

## Routing classification

| Route | When | Opus? |
|---|---|---|
| **tradeoff** | Comparing approaches, "X vs Y", pros/cons | **No** |
| **buildx** (12-step) | Greenfield, major features, end-to-end builds | Yes (planning + judge) |
| **buildx-lite** (7-step) | Bugfixes, refactors, scoped changes, tests, cleanup | **No** |

### Scoped-work triggers (→ buildx-lite)

`fix`, `patch`, `bugfix`, `hotfix`, `refactor`, `tweak`, `adjust`, `rename`, `add test(s)`, `small/minor/quick change/fix/update`, `update test/doc/readme/config`, `cleanup`, `lint fix`.

### Tradeoff triggers

`evaluate tradeoffs`, `compare approaches/options/designs`, `choose between`, `which is better`, `pros and cons`, `should I use X or Y`, `advantages and disadvantages`, `X vs Y`, `weigh the options`.

## Model assignments

| Role | Base model | Escalation |
|---|---|---|
| Planning & architecture (full) | `opencode-go/kimi-k2.5` | — |
| Implementation & simplify | `openai-codex/gpt-5.4` | — |
| Code review | `anthropic/claude-sonnet-4-6` | — |
| Boilerplate | `openai-codex/gpt-5.3-codex-spark` | → `claude-sonnet-4-6` |
| Testing / adversarial | `opencode-go/glm-5` | → `claude-sonnet-4-6` |
| Research & wide-context | `opencode-go/kimi-k2.5` | → `openai-codex/gpt-5.4` |

Cache: `openai-codex/*` → `long`, `opencode-go/*` → `short`, `anthropic/*` → `short`.

Opus only in: full buildx judge. Never in buildx-lite or tradeoff proposals. Planning uses kimi-k2.5 for long-context architecture work. Research escalates to gpt-5.4.

## Buildx pipeline (full, 12 steps)

Pre-step: create or verify one short-lived branch.

1. **parallel-plan-a** → `kimi-k2.5`
2. **parallel-plan-b** → `gpt-5.4`
3. **judge-plan** → `claude-opus-4-6`
4. **boilerplate** → `gpt-5.3-codex-spark`
5. **implement** → `gpt-5.4`
6. **test** → `glm-5`
7. **simplify** → `gpt-5.4`
8. **retest** → `glm-5`
9. **review-resolve-a** → `claude-sonnet-4-6`
10. **test-a** → `glm-5`
11. **review-resolve-b** → `kimi-k2.5`
12. **final-test** → `glm-5`

Steps 4, 6, 8, 10, 11, 12 support escalation when marked `COMPLEX`.

Exit rule: PR not ready until tests pass and diff is atomic.

## Buildx-lite pipeline (7 steps)

Pre-step: create or verify one short-lived branch.

1. **plan** → `gpt-5.4`
2. **implement** → `gpt-5.4`
3. **test** → `glm-5`
4. **simplify** → `gpt-5.4`
5. **retest** → `glm-5`
6. **review** → `claude-sonnet-4-6`
7. **final-test** → `glm-5`

Steps 3, 5, 7 support escalation when marked `COMPLEX`.

Exit rule: PR not ready until tests pass and diff is minimal.

## Tradeoff protocol

Proposals: `gpt-5.3-codex` + `glm-5`. Judge: `gpt-5.4`.

## Judge output contract

Judge-plan must emit:
1. Selected architecture
2. Why it won
3. Project/file structure
4. Implementation order
5. Branch plan (name, scope boundary)
6. Test plan
7. PR/CI test gates
8. Simplification targets
9. Done criteria

For `buildx:`, also include:
1. Risk list
2. Likely failure modes
3. Review checklist

## Simplify contract

Must:
- Remove dead code
- Remove speculative abstractions
- Remove duplication
- Remove over-engineered interfaces
- Prefer fewer files when clarity is preserved

Must not:
- Rewrite architecture
- Add abstractions
- Expand scope

## Validation checklist

1. Run `tests/test_portfolio_dispatcher.py` — all pass.
2. Confirm model assignments match table.
3. Confirm escalation paths resolve correctly.
4. Confirm tradeoff uses gpt-5.3-codex + glm-5, judged by gpt-5.4.
5. Confirm cache retention matches table.
6. Confirm no legacy flags accepted.
7. Confirm scoped work → buildx-lite (no Opus).
8. Confirm greenfield → full buildx.
9. Confirm judge output includes branch plan and PR/CI test gates.
