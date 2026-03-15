---
name: context-optimizer
description: Optimize OpenClaw context usage to reduce token cost, avoid context-window pressure, and keep long sessions responsive. Use when the user asks about reducing token usage or API costs, trimming context, context overflow/truncation errors, compacting or resetting stale sessions, lowering memory-retrieval overhead, shrinking tool output, reducing injected workspace/bootstrap size, or tuning openclaw.json for context efficiency.
---

# Context Optimizer

Diagnose first. Change one lever at a time. Re-measure after each change.

## Inspection commands

- `/status`, `/context list`, `/context detail`
- `/usage tokens` or `/usage full`
- `openclaw config file`, `openclaw config validate`

Do not guess from old examples or blog posts.

## Optimization order

Work through this checklist in order:

1. **Cut oversized bootstrap files** — shorten bloated `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `MEMORY.md`. Keep skill descriptions compact. Lower `imageMaxDimensionPx` for screenshot-heavy workflows.
   - Knobs: `bootstrapMaxChars`, `bootstrapTotalMaxChars`, `imageMaxDimensionPx`

2. **Reduce tool output** — fewer search results, smaller page fetches, read only relevant file sections.
   - Knobs: `tools.web.search.maxResults`, `tools.web.fetch.maxCharsCap`

3. **Tune context pruning** — trim old tool results in long sessions.
   - Knobs: `agents.defaults.contextPruning` (mode: `cache-ttl`, ttl: `1h`)

4. **Tune memory retrieval** — lower `maxResults`, raise `minScore`, enable MMR for dedup, enable temporal decay for stale notes.
   - Knobs: under `agents.defaults.memorySearch.query.*`

5. **Session hygiene** — `/compact` to keep thread and summarize older history. `/new` or `/reset` for hard topic changes.
   - Knobs: `agents.defaults.compaction`

## Safe starting config

```json5
{
  agents: {
    defaults: {
      contextPruning: { mode: "cache-ttl", ttl: "1h" },
      memorySearch: { query: { maxResults: 3, minScore: 0.75 } }
    }
  },
  tools: { web: { search: { maxResults: 3 } } }
}
```

## Validation loop

1. `openclaw config validate`
2. Restart gateway if needed
3. Re-check `/status`, `/context list`, `/context detail`
4. Confirm recall quality is acceptable
5. Keep the smallest change that improves cost without harming usefulness

## References

Read only if needed:
- `references/config-keys.md`
- `references/diagnostics-playbook.md`
