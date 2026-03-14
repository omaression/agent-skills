# Diagnostics Playbook

## Symptom: "OpenClaw is getting expensive"

Check:
1. `/status`
2. `/context detail`
3. `/usage tokens`

Common fixes:
- shorten oversized bootstrap files
- reduce `tools.web.search.maxResults`
- reduce fetch output size
- enable or tune `agents.defaults.contextPruning`
- lower memory `query.maxResults`

## Symptom: "Context got truncated" or "context too large"

Use in this order:
1. `/compact`
2. `/new` or `/reset` if the topic changed or the session is stale
3. inspect `/context detail`
4. tune `agents.defaults.contextPruning`

Do not respond with undocumented history keys.

## Symptom: memory recall is noisy

Check:
- `agents.defaults.memorySearch.extraPaths`
- `agents.defaults.memorySearch.query.maxResults`
- `agents.defaults.memorySearch.query.minScore`

Common fixes:
- remove broad `extraPaths`
- lower `maxResults`
- raise `minScore`
- enable `query.hybrid.mmr`
- enable `query.hybrid.temporalDecay` if stale daily notes dominate

## Symptom: search/fetch tools dump too much text

Check:
- `tools.web.search.maxResults`
- `tools.web.fetch.maxCharsCap`
- whether the workflow is reading full pages/files unnecessarily

Common fixes:
- request fewer search results
- fetch smaller excerpts
- read only the relevant section of large files
- rely on pruning for old tool output in long sessions

## Symptom: screenshots are expensive

Check:
- how many screenshots/images are being sent
- `agents.defaults.imageMaxDimensionPx`

Common fixes:
- lower image dimension cap
- avoid repeated large screenshots when text or DOM tools are enough

## Rule of thumb

Make one small change at a time, validate it, and keep the cheapest fix that preserves behavior.
