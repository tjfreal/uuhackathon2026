# Trails

Trails is a local-first temporal archaeology tool. Given a corpus of text files and a topic, it finds every mention across the corpus, extracts dates from filenames and content, and assembles a chronological arc — a timeline of how an idea developed.

The problem it solves: a topic like "3d scanning" or "design review" has context scattered across years of daily notes, project stubs, companion files, and legacy archives. No single file captures the arc. Trails assembles it.

## What It Is

- A standalone CLI tool — no server, no cloud, no required external dependencies
- Input: a corpus directory + a topic or query string
- Output: a readable markdown timeline, one dated excerpt per match, assembled in order
- Optional: `--index` for embedding-based retrieval when an existing `chunks.jsonl` index is available
- Optional: `--format narrative` for a prose summary of the arc when a supported SDK is installed

## How It Works

1. **Discover** — find all text files in the corpus
2. **Search** — find files mentioning the topic (keyword by default; embedding-based if an index is supplied)
3. **Date-extract** — parse dates from filenames (`YYYY-MM-DD.md`), frontmatter, and inline ISO content markers
4. **Excerpt** — pull the relevant passage from each matching file
5. **Assemble** — sort by date, deduplicate overlapping content, render timeline
6. **Output** — write to stdout or a file

## CLI

```bash
# Basic timeline for a topic
python trails.py query "3d scanning" --corpus ~/notes

# Restrict to one part of the corpus
python trails.py query "design review" --corpus ~/notes --domain projects

# Prose narrative instead of dated list
python trails.py query "meeting notes" --corpus ~/notes --format narrative

# Write output to file
python trails.py query "3d scanning" --corpus ~/notes --out outputs/3d-scanning-arc.md

# Use embedding index for semantic search instead of keyword
python trails.py query "capture friction" --corpus ~/notes --index ~/notes/.index/embeddings
```

## Output Format

Default (dated list):

```
## 3d scanning arc

2018 (circa)  archive/legacy-notes/scanning.md
  First note about using phone-based capture. Too noisy for useful reconstruction.

2024-11-02  daily/2024-11-02.md
  Returning to 3d scanning as a documentation tool, not just a novelty test.

2026-02  projects/capture/3d-scanning.md
  Shift from one-off scans to a repeatable local workflow. The question becomes
  how to keep the artifacts searchable later.

2026-03-10  daily/2026-03-10.md
  First clean run that feels worth keeping. Good enough to become part of the process.
```

Other output modes:

- `--format json` returns structured entries for downstream tools
- `--format narrative` asks an LLM for a 3-5 paragraph arc if a supported SDK is available; otherwise it falls back to list output with a warning

## Directory Layout

```
trails/
├── trails.py           ← the tool
├── README.md           ← this file
├── AGENTS.md           ← build brief for hackathon agent
├── presentation.md     ← public framing
├── learnings.md        ← design lessons as they accumulate
├── roadmap.md          ← next useful pushes
└── outputs/            ← example timeline outputs (committed)
```

## Status

Real local `v1` exists.

Current state:

- the standalone CLI is implemented in `trails.py`
- keyword mode works with stdlib only
- embedding mode works against an existing `chunks.jsonl` index when `numpy` and `sentence-transformers` are available
- narrative mode is optional and falls back cleanly when no supported SDK is installed
- the remaining high-value work is real-corpus demo output, refinement, and integration polish

## Usage

```bash
python trails.py "topic"                          # keyword search, prints timeline to terminal
python trails.py "topic" --format narrative       # prose arc via LLM if API key is present
python trails.py "topic" --domain garden          # restrict to one domain subdirectory
python trails.py "topic" --since 2025-01-01       # date-bounded arc
```

When the corpus has an existing embedding index at `.index/embeddings/chunks.jsonl`,
`trails.py` automatically uses it for semantic search. Falls back to keyword mode otherwise.

## Relationship to Throughline

Throughline answers: what notes are relevant to this topic *right now*?
Trails answers: how did this topic *develop* across time?

They are complementary. Run both on "3d scanning" and you get coverage + history.

## Dependencies

- Python 3.10+
- No required external packages
- Optional: `numpy` and `sentence-transformers` for embedding-based search
- Optional: `anthropic` or `openai` for narrative mode
