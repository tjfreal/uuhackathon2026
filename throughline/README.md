# Throughline

Throughline is a local semantic retrieval tool that exposes what stays relevant across chunk sizes.

Standard embedding search picks one granularity and hides it. A 75-token chunk may surface a hit that a 25-token chunk misses, or vice versa. Throughline builds three parallel indices at different span sizes, queries all three in one pass, and reports which files keep showing up — the **throughlines** — alongside the per-span rankings.

The result: one query, three lenses, and a clear signal for which sources are genuinely load-bearing versus incidentally relevant.

## What It Does

- indexes a text corpus at three fixed span sizes (≈25, 75, and 200 tokens)
- scores all three indices against a query in a single pass
- detects throughlines: files that appear in results across 2 or 3 span sizes
- reports ranked hits per span plus a throughline summary at the top
- uses `nomic-ai/nomic-embed-text-v1.5` — same model as the broader embedding stack
- state file tracks the active index so repeated queries do not require re-specifying paths

## CLI

```bash
# Index a corpus (builds all three span indices)
python throughline.py index ~/notes

# Query the active index
python throughline.py query "3d scanning workflow"

# Query with more results per span
python throughline.py query "capture friction" --n 12

# Point at a specific index directory explicitly
python throughline.py query "retrieval" --index-dir .index/throughline/notes-abc123/

# List known local indices
python throughline.py list-indices
```

## Output

```
Query: "3d scanning workflow"
Index: .index/throughline/notes-abc123/

Throughlines
------------
3/3  daily/2024-11-02.md              score=0.8821  spans=[span_25, span_75, span_200]
2/3  domains/work/3d-digital/dam-vision.md  score=0.8614  spans=[span_75, span_200]

span_25 (top 8)
---------------
 1. [3/3      ] daily/2024-11-02.md
    score=0.8821 words=0-19
    First clean run using polycam for a real scan. The workflow is finally worth repeating.

 2. [2/3      ] domains/work/3d-digital/dam-vision.md
    score=0.8744 words=42-61
    Scanning workflow for institutional artifact documentation — repeatable local pipeline.
...
```

## How Span Sizes Work

| Span name | Word window | Step | Best for |
|-----------|-------------|------|----------|
| `span_25` | 19 words | 10 | fine-grained phrase matching |
| `span_75` | 58 words | 29 | paragraph-level context |
| `span_200` | 154 words | 77 | document-level relevance |

A file appearing in all three spans is making a strong claim: it is relevant at the phrase level, the paragraph level, and the document level simultaneously. That is the throughline signal.

## Directory Layout

```
throughline/
├── throughline.py      ← the tool
├── README.md           ← this file
├── AGENTS.md           ← build brief
├── presentation.md     ← public framing
├── learnings.md        ← design notes
└── ROADMAP.md          ← next pushes
```

Index state is stored in `.index/throughline/` relative to the corpus root (or next to the script in standalone use). Not committed.

## Status

Working local `v1`.

- `index` command builds all three span indices; incremental rebuild skips unchanged corpora
- `query` command loads and scores all spans in one pass, detects throughlines, prints results
- `list-indices` command shows known local indices and active selection
- state file tracks the active index between invocations
- runs as a standalone CLI via `python throughline.py`

## Dependencies

- Python 3.10+
- `sentence-transformers`
- `numpy`
- `torch`
- `nomic-ai/nomic-embed-text-v1.5` (downloaded on first use)
