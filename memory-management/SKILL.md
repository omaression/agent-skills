---
name: memory-management
description: Recall and write workspace memory for OpenClaw agents using MEMORY.md, memory/YYYY-MM-DD.md, memory_search, and memory_get. Use when the user asks about prior work, decisions, dates, people, preferences, todos, or says to remember something; also use when you need to store durable notes or explain how OpenClaw memory works.
---

# Memory Management

Use Markdown files as the source of truth. Retrieve first, then write only what should persist.

## Core model

OpenClaw memory has two layers:

- `MEMORY.md` — curated long-term memory
- `memory/YYYY-MM-DD.md` — daily notes and running context

`memory_search` finds likely snippets.
`memory_get` reads the exact lines you need.

## Retrieval workflow

Use this when the user asks about:
- prior work
- previous decisions
- dates or timelines
- people or preferences
- remembered todos
- “what do you remember about …”

Steps:
1. Run `memory_search` with a tight query.
2. If results are relevant, run `memory_get` only for the needed file/line range.
3. Answer from the retrieved text, not from guesswork.
4. If results are weak or empty, say you checked.

## Write workflow

Write memory when the user says or clearly implies:
- “remember this”
- this preference should stick
- this decision will matter later
- this is durable personal/project context

Write destination:
- `MEMORY.md` for durable facts, preferences, recurring workflows, and important long-term context
- `memory/YYYY-MM-DD.md` for day-to-day notes, short-term progress, one-off events, and running context

Rules:
- write the smallest useful note
- prefer concrete facts over commentary
- do not store secrets casually
- do not promise to remember something unless you wrote it down

## When not to use memory tools

Do not use memory retrieval when:
- the answer is fully contained in the current message or attached files
- the task is only about the current chat turn
- the user wants live repo state rather than remembered state

Do not write memory when:
- the fact is trivial or disposable
- the note belongs in project docs instead of personal memory
- the user is asking for temporary scratch work only

## Query guidance

Good search queries are short and specific.

Prefer:
- `omar internship goal fall 2026`
- `notion workspace page id`
- `advanced dispatcher model policy`
- `remembered preference python 3.12`

Avoid:
- whole paragraphs
- vague queries like `memory` or `what happened`

## Answering rules

- cite the retrieved file path/line when useful
- separate memory facts from current inference
- if memory seems stale, say so
- if a user asks for recall and memory is unavailable, say memory retrieval is unavailable instead of pretending

## Maintenance guidance

If memory is noisy or weak:
- keep `MEMORY.md` curated
- avoid stuffing random documents into memory paths
- store durable facts in stable wording
- use project docs for implementation detail that should not live in personal memory

## Minimal examples

### Recall
- search: `job application workflow notion`
- get: matching lines from `MEMORY.md`
- answer with the retrieved workflow

### Write
- user: `remember that I want Python 3.12 everywhere`
- write durable preference to `MEMORY.md`

### Daily note
- user: `remember that I finished the first draft tonight`
- write to today’s `memory/YYYY-MM-DD.md`
