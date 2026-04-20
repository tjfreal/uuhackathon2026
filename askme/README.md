# Askme

Askme is a gap detector for personal knowledge systems.

It reads index files from an sb-style corpus, looks for what is missing, stale, thin, or
still unresolved, and turns those gaps into prompts designed to get the user writing.

The inversion is the point: instead of the user deciding what to capture next, the corpus
surfaces its own unfinished edges and asks for them.

## What It Is

- a standalone CLI tool
- deterministic in the core version: no server, no cloud, no model required
- index-first: works from `.index/` files alone, with optional richer corpus reads
- output-focused: returns a ranked list of prompts that can be printed, serialized, or
  dropped into an inbox note

## Current Status

Askme is now a real local `v1`.

The current build includes:

- a working `askme.py` CLI
- tolerant parsers for `stats.md`, `people.md`, and `blockouts.md`
- five gap-detection strategies
- weighted ranking across strategies
- `text`, `json`, and `inbox` output modes
- committed output conventions under `outputs/`

What it does not include yet:

- model-assisted prompt rewriting
- prompt deduplication across runs
- a feedback loop based on answered versus skipped prompts

## The Gaps It Detects

**Sparse stubs** (`--type stubs`)
Files with `<= 10` lines that have gone stale in `domains/`, `references/people/`,
`references/books/`, or `references/articles/`. Legacy catch-all directories are excluded.

Example prompt:
`The project-name stub hasn't been updated in 89 days. What do you know about this project now?`

**Open questions** (`--type questions`)
Companion JSON files with non-empty `open_questions` arrays, pulled from `daily/*/` review
passes. Weighted by recency — fresh open questions rank higher than old ones.

Example prompt:
`You left this question open 38 days ago. "What changed here?" — what's the current state?`

**People with minimal context** (`--type people`)
People who appear in a few notes but still have almost-empty stubs. Parsed from the `people.md`
index (`## Name (path)` heading format).

Example prompt:
`A collaborator comes up in your notes but their stub is almost empty. What do you know about them? How did you meet?`

**Dormant threads** (`--type threads`)
Reads daily note synthesis sections directly, finds `Threads to watch` bullet lists, and
checks whether those threads have resurfaced in newer daily notes. Does not depend on the
blockouts index.

Example prompt:
`"self-forgiveness" was flagged as a thread to watch in your 2026-03-11 synthesis. Where is that now?`

**Domain gaps** (`--type domains`)
Subdirectory-level domains that are sparse relative to their expected richness. Skips
individual `.md` files that happen to live inside a domain folder.

Example prompt:
`Your health/nutrition notes are sparse. What does a good eating day look like for you?`

**Unprocessed inbox** (`--type inbox`)
Items in `inbox/` that are older than a minimum age and have not been moved to
`inbox/completed/`. Flags things that landed and went quiet.

Example prompt:
`Inbox item "meeting-notes" has been sitting unprocessed for 47 days. Route, stub, or archive it.`

**Mentioned but unstubbed** (`--type unstubbed`)
People appearing in recent daily notes (last 60 days) who lack a `references/people/` stub.
Pulled from the NER entity index.

Example prompt:
`A collaborator appears in 3 recent daily notes but has no people stub. Worth creating one?`

## CLI

```bash
# Generate the top 10 prompts across all strategies
python askme.py --index-dir ~/notes/.index --corpus ~/notes --n 10

# Focus on a single strategy
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type stubs
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type people
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type questions
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type threads
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type domains
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type inbox
python askme.py --index-dir ~/notes/.index --corpus ~/notes --type unstubbed

# Filter out very recent gaps
python askme.py --index-dir ~/notes/.index --corpus ~/notes --min-age 30

# Emit JSON for downstream tooling
python askme.py --index-dir ~/notes/.index --corpus ~/notes --format json

# Write inbox-style output to a file
python askme.py --index-dir ~/notes/.index --corpus ~/notes --format inbox --out ~/notes/inbox/askme-2026-04-19.md
```

## Output Format

Text output:

```text
1. [stubs] The project-name.md stub hasn't been updated in 89 days.
   → What do you know about Project Name now?
   Source: domains/focus/project-name.md (8 lines, last modified 2026-01-21, 89 days old)

2. [questions] You left this question open 38 days ago.
   → "What changed here?" — what's the current state?
   Source: daily/2026-03-12/2026-03-12-0915.json (from 2026-03-12, 38 days old)
```

JSON output:

```json
[
  {
    "rank": 1,
    "strategy": "questions",
    "score": 0.92,
    "setup": "You left this question open 38 days ago.",
    "prompt": "\"What changed here?\" — what's the current state?",
    "source": "daily/2026-03-12/2026-03-12-0915.json"
  }
]
```

## Directory Layout

```text
askme/
├── askme.py
├── README.md
├── AGENTS.md
├── presentation.md
├── learnings.md
├── roadmap.md
└── outputs/
```

## Notes On Public Conventions

This repo is public. Askme is built against a private notes system.

That means examples in this repo should stay generic:

- use `~/notes` as the corpus placeholder
- avoid real private person names in examples
- avoid private project names that are not part of this repo
- keep example prompts legible without depending on the private system behind them

## Usage

```bash
python askme.py                    # top 10 gaps across all strategies
python askme.py --type stubs       # sparse stubs only
python askme.py --type threads     # dormant threads from synthesis sections
python askme.py -n 20              # more results
```

Askme finds the gap, the user answers it, and the response flows back into the corpus.

## Dependencies

- Python 3.10+
- no required external packages
- reads from `.index/`: `stats.md`, `people.md`, `entities.md`
- reads `daily/*.md` synthesis sections directly for thread detection
- reads companion JSON files and stub files directly when `--corpus` is given
