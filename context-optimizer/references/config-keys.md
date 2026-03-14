# Config Keys That Matter for Context Optimization

Use `openclaw config file` to find the active config, and `openclaw config validate` after edits.

## Bootstrap / injected workspace

### `agents.defaults.bootstrapMaxChars`
Max characters per injected bootstrap file before truncation.

### `agents.defaults.bootstrapTotalMaxChars`
Max total injected characters across bootstrap files.

### `agents.defaults.bootstrapPromptTruncationWarning`
Controls whether the agent sees truncation warnings when bootstrap content is cut.

### `agents.defaults.imageMaxDimensionPx`
Reduce this for screenshot-heavy sessions to lower image payload and vision-token cost.

## Long-session controls

### `agents.defaults.compaction`
Controls how older session history is summarized and persisted.

Use when:
- sessions are long but continuity still matters
- you want summaries instead of a hard reset

### `agents.defaults.contextPruning`
Trims old **tool results** from in-memory context before LLM calls.

Important:
- does not rewrite session history on disk
- affects tool results, not user/assistant messages
- useful when old reads/searches/exec output dominate context

High-value fields:
- `mode`
- `ttl`
- `keepLastAssistants`
- `softTrimRatio`
- `hardClearRatio`
- `minPrunableToolChars`
- `softTrim.*`
- `hardClear.*`
- `tools.allow` / `tools.deny`

## Memory retrieval controls

### `agents.defaults.memorySearch.enabled`
Master switch for memory indexing + retrieval.

### `agents.defaults.memorySearch.sources`
Usually keep this to `["memory"]` unless transcript recall is needed.

### `agents.defaults.memorySearch.extraPaths`
Add extra Markdown sources intentionally. Avoid dumping entire repos here.

### `agents.defaults.memorySearch.query.maxResults`
Lower this to inject fewer memory hits.

### `agents.defaults.memorySearch.query.minScore`
Raise this to filter weak matches.

### `agents.defaults.memorySearch.query.hybrid.*`
Use for better recall quality, not just more recall.

High-value subfields:
- `enabled`
- `vectorWeight`
- `textWeight`
- `candidateMultiplier`
- `mmr.enabled`
- `mmr.lambda`
- `temporalDecay.enabled`
- `temporalDecay.halfLifeDays`

### `agents.defaults.memorySearch.chunking.tokens`
Chunk size used for indexing.

### `agents.defaults.memorySearch.chunking.overlap`
Overlap between adjacent chunks.

## Web tool output controls

### `tools.web.search.maxResults`
Lower this first when web search is bloating context.

### `tools.web.search.timeoutSeconds`
Useful operationally, though not a direct token knob.

### `tools.web.fetch.maxCharsCap`
Clamp fetch output size globally.

## Useful commands

```bash
openclaw config file
openclaw config validate
```

In chat:
- `/status`
- `/context list`
- `/context detail`
- `/usage tokens`
- `/compact`
- `/new`
- `/reset`
