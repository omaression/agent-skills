---
name: context-optimizer
description: Slash OpenClaw token costs and prevent context overflow. Use whenever the user mentions high API costs, expensive tokens, context truncation, context overflow, slow responses in long sessions, noisy memory recall, bloated bootstrap, or wants to tune openclaw.json for efficiency. Also trigger when the user says their agent "uses too many tokens" or tasks feel "wasteful." This skill is aggressive and opinionated — it gives concrete configs to paste, not menus of knobs.
---

# Context Optimizer

Goal: cut input tokens to the minimum that preserves task quality.

Principle: diagnose → apply the single highest-impact fix → re-measure → repeat.

## Step 1 — Diagnose

Run these three commands (or ask the user to run them) before changing anything:

```
/status
/context detail
/usage tokens
```

Read the output. Identify which category dominates token usage — bootstrap, tool output, memory, or session length. Then go straight to the matching fix below.

## Step 2 — Apply fixes in impact order

Work top-down. Stop as soon as usage is acceptable.

### Fix 1: Shrink bootstrap files (usually the #1 sink)

Bootstrap files (`AGENTS.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `MEMORY.md`, custom skill files) are injected into every single LLM call. Oversized bootstrap is the most expensive problem because it compounds on every turn.

Actions:
- Audit each file: `cat` it out, count characters. Anything over 2000 chars is suspect.
- Rewrite for brevity. Strip filler, examples the agent rarely needs, redundant phrasing.
- Move rarely-needed reference material into files the agent can `cat` on demand instead of injecting every turn.

Config:
```json
{
  "agents": {
    "defaults": {
      "bootstrapMaxChars": 3000,
      "bootstrapTotalMaxChars": 12000,
      "imageMaxDimensionPx": 768
    }
  }
}
```

`imageMaxDimensionPx` at 768 instead of the default (often 1024+) saves significant vision tokens in screenshot-heavy workflows. Drop to 512 if pixel precision is not needed.

### Fix 2: Throttle tool output

Web search and file reads dump large payloads into context. These compound in long sessions because old results linger.

Config:
```json
{
  "tools": {
    "web": {
      "search": { "maxResults": 3 },
      "fetch": { "maxCharsCap": 4000 }
    }
  }
}
```

Also change agent behavior: read only relevant file sections (line ranges), not entire files. Fetch excerpts, not full pages.

### Fix 3: Prune stale tool results

In long sessions, old tool output (file reads, search results, command output) stays in context even when it is no longer relevant. Context pruning trims these automatically.

Config:
```json
{
  "agents": {
    "defaults": {
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "30m",
        "keepLastAssistants": 3,
        "minPrunableToolChars": 500
      }
    }
  }
}
```

This keeps the last 3 assistant turns' tool results intact and prunes anything older than 30 minutes that exceeds 500 chars. Tighten `ttl` to `"15m"` for fast-paced sessions.

### Fix 4: Tighten memory retrieval

Memory search results are injected into context before each turn. Too many results or low-quality matches waste tokens.

Config:
```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "query": {
          "maxResults": 3,
          "minScore": 0.75,
          "hybrid": {
            "mmr": { "enabled": true, "lambda": 0.7 },
            "temporalDecay": { "enabled": true, "halfLifeDays": 14 }
          }
        }
      }
    }
  }
}
```

- `maxResults: 3` — inject at most 3 memory chunks (default is often 5–10).
- `minScore: 0.75` — drop weak matches.
- `mmr` — deduplicate similar chunks so you don't get three variations of the same note.
- `temporalDecay` — deprioritize stale daily notes and old logs.

If recall quality drops, lower `minScore` to 0.6 or raise `maxResults` to 5.

Also check `memorySearch.extraPaths` — if it points at broad directories or entire repos, remove or narrow those paths.

### Fix 5: Session hygiene

Long conversations accumulate context even with pruning. Use built-in session controls:

- `/compact` — summarizes older history, keeps the thread alive. Use mid-session.
- `/new` — fresh session. Use on hard topic changes.
- `/reset` — full reset. Use when the session is unsalvageable.

For sessions that tend to run long, configure automatic compaction:
```json
{
  "agents": {
    "defaults": {
      "compaction": { "enabled": true }
    }
  }
}
```

## Step 3 — Validate

After each change:

1. `openclaw config validate` — catch syntax errors.
2. Restart the gateway if prompted.
3. Re-run `/status` and `/usage tokens`.
4. Spot-check that the agent still recalls what it needs (run a representative task).
5. If recall broke, back off the last change by one notch.

## Quick-reference: symptom → fix

| Symptom | Go to |
|---|---|
| Every turn is expensive, even simple ones | Fix 1 (bootstrap) |
| Cost spikes after searches or file reads | Fix 2 (tool output) |
| Long sessions get slow/truncated | Fix 3 (pruning) + Fix 5 (session hygiene) |
| Memory results feel noisy or irrelevant | Fix 4 (memory retrieval) |
| Screenshots are costly | Fix 1, set `imageMaxDimensionPx: 512` |
| "Context too large" / truncation errors | Fix 5 (`/compact` or `/new`), then Fix 3 |

## Aggressive all-in-one config

If the user wants maximum savings and is willing to tune back up from there:

```json
{
  "agents": {
    "defaults": {
      "bootstrapMaxChars": 2500,
      "bootstrapTotalMaxChars": 10000,
      "imageMaxDimensionPx": 512,
      "compaction": { "enabled": true },
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "15m",
        "keepLastAssistants": 2,
        "minPrunableToolChars": 300
      },
      "memorySearch": {
        "query": {
          "maxResults": 2,
          "minScore": 0.8,
          "hybrid": {
            "mmr": { "enabled": true, "lambda": 0.7 },
            "temporalDecay": { "enabled": true, "halfLifeDays": 7 }
          }
        }
      }
    }
  },
  "tools": {
    "web": {
      "search": { "maxResults": 2 },
      "fetch": { "maxCharsCap": 3000 }
    }
  }
}
```

Start here, then loosen any knob where quality suffers.

## Commands cheat sheet

| Command | Purpose |
|---|---|
| `openclaw config file` | Show active config path |
| `openclaw config validate` | Validate config syntax |
| `/status` | Session overview |
| `/context list` | List context entries |
| `/context detail` | Show context with sizes |
| `/usage tokens` | Token usage breakdown |
| `/compact` | Summarize + trim session |
| `/new` | Fresh session |
| `/reset` | Hard reset |
