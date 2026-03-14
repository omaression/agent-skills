---
name: context-optimizer
description: Optimize OpenClaw context usage to reduce token cost, avoid context-window pressure, and keep long sessions responsive. Use when the user asks about reducing token usage or API costs, trimming context, context overflow/truncation errors, compacting or resetting stale sessions, lowering memory-retrieval overhead, shrinking tool output, reducing injected workspace/bootstrap size, or tuning openclaw.json for context efficiency.
---

# Context Optimizer

Diagnose first. Change one lever at a time. Re-measure after each change.

## 1) Inspect before editing

Prefer built-in observability first:

- `/status`
- `/context list`
- `/context detail`
- `/usage tokens` or `/usage full`
- `openclaw config file`
- `openclaw config validate`

Do not guess from old blog posts or legacy config examples.

## 2) Pick the smallest effective lever

### A. Bootstrap / system-prompt overhead

You usually cannot make OpenClaw’s total system prompt tiny, but you can reduce controllable overhead.

Check for:
- oversized `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `MEMORY.md`
- too many skills with long descriptions
- large screenshot/image payloads

Main knobs:
- `agents.defaults.bootstrapMaxChars`
- `agents.defaults.bootstrapTotalMaxChars`
- `agents.defaults.bootstrapPromptTruncationWarning`
- `agents.defaults.imageMaxDimensionPx`

Use this lever when `/context detail` shows injected files or image payloads dominating.

Rules:
- shorten bloated bootstrap files before raising limits
- keep skill descriptions compact; metadata is always injected
- lower `imageMaxDimensionPx` for screenshot-heavy workflows

### B. Long-session history growth

OpenClaw handles long sessions with **compaction** and **context pruning**.

Use chat controls first:
- `/compact` to keep the thread and summarize older history
- `/new` or `/reset` for topic changes or stale/broken sessions

Main knobs:
- `agents.defaults.compaction`
- `agents.defaults.contextPruning`

Use this lever when:
- long chats keep getting truncated
- old tool results make follow-up turns expensive
- cache writes spike after idle gaps

Rules:
- use compaction to preserve continuity
- use `/new` for hard topic changes
- use `contextPruning` to trim **old tool results**, not user/assistant turns
- do not invent keys like `maxHistoryMessages` or `summarizeAfter`

### C. Memory retrieval overhead

Memory search lives under `agents.defaults.memorySearch`, not a top-level `memorySearch` block.

Main knobs:
- `enabled`
- `sources`
- `extraPaths`
- `query.maxResults`
- `query.minScore`
- `query.hybrid.*`
- `chunking.tokens`
- `chunking.overlap`

Use this lever when:
- too many weak memory hits are injected
- results are repetitive or stale
- broad `extraPaths` made recall noisy

Rules:
- lower `query.maxResults` before disabling memory entirely
- raise `query.minScore` to cut weak matches
- keep `extraPaths` intentional; avoid indexing huge trees casually
- enable MMR when results are repetitive
- enable temporal decay when stale dated notes outrank recent ones
- do not hardcode embedding defaults unless you verified the live config

### D. Tool output size

Large tool results often cost more context than chat messages.

Main knobs:
- `tools.web.search.maxResults`
- `tools.web.fetch.maxCharsCap`
- `agents.defaults.contextPruning`

Use this lever when:
- search returns too many results
- fetched pages are too large
- repeated reads/searches/exec output bloat the transcript

Rules:
- request fewer search results
- fetch smaller excerpts
- read only relevant file sections
- rely on pruning for old tool output in long sessions

## 3) Recommended order

1. Inspect with `/context detail`
2. Cut oversized bootstrap files or image payloads
3. Reduce tool output size
4. Tune `contextPruning`
5. Tune memory retrieval
6. Use `/compact` or `/new` when the session itself is the problem

## 4) Safe starting defaults

Start here before doing anything exotic:

```json5
{
  agents: {
    defaults: {
      contextPruning: { mode: "cache-ttl", ttl: "1h" },
      memorySearch: { query: { maxResults: 3, minScore: 0.75 } }
    }
  },
  tools: {
    web: {
      search: { maxResults: 3 }
    }
  }
}
```

## 5) Validation loop

After edits:
1. Run `openclaw config validate`
2. Restart the gateway if your deployment requires it
3. Re-check `/status`, `/context list`, and `/context detail`
4. Confirm recall quality is still acceptable
5. Keep the smallest change that improves cost or latency without harming usefulness

## What not to do

- do not use undocumented keys copied from old examples
- do not hardcode config paths; use `openclaw config file`
- do not assume memory defaults, embedding models, or service names
- do not chase an arbitrary “tiny system prompt” target
- do not widen bootstrap limits as the first fix

## References

Read only if needed:
- `references/config-keys.md`
- `references/diagnostics-playbook.md`
