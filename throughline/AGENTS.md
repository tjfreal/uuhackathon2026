# Throughline — Agent Build Brief

Read README.md and ROADMAP.md before starting. This file locks the open decisions
from the ROADMAP so you can build without re-deciding the concept mid-session.

---

## What You Are Building

A multi-span semantic search tool for the note-system. One query runs against three
embedding indices built at different chunk sizes. Results are merged and passages that
appear across multiple span sizes — throughlines — are highlighted.

The claim: if a passage is relevant at 25 tokens AND 75 tokens AND 200 tokens, that
relevance signal is robust. It is not an artifact of one chunking choice.

The demo: one text input, three result columns (one per span), throughline passages
visually distinguished.

---

## Source Infrastructure

**Existing embedding pipeline** (read-only, do not modify):
```
~/notes/scripts/parse_embeddings.py
~/notes/scripts/query_embeddings.py
~/notes/.index/embeddings/   ← existing heading-based index
```

**Existing chunk schema** in `.index/embeddings/chunks.jsonl`:
```json
{"file": "domains/health/metrics.md", "heading": "Sleep", "text": "...", "vector": [...]}
```
No offset fields exist. The new chunker must add them.

**Python environment**: `~/venv2/` — has `sentence-transformers`, `numpy`, `torch`.
Always run with `source ~/venv2/bin/activate`.

**Model**: `nomic-ai/nomic-embed-text-v1.5`
- Prefix documents with `search_document: `
- Prefix queries with `search_query: `
- Use `normalize_embeddings=True`
- Embed dim: 768

**Corpus**: The notes corpus at `~/notes/`
Exclude directories: `.git`, `.index`, `archive`, `templates`, `.claude`, `sessions`, `venv`

---

## Locked Decisions

### Span sizes and token approximation

Use three fixed-span indices. Token counts are approximated as `words × 1.3`:

| Span name | Approx tokens | Word window | Step (50% overlap) | What it captures |
|---|---|---|---|---|
| `span_25` | ~25 tok | 19 words | 10 words | Sharp local detail, phrases |
| `span_75` | ~75 tok | 58 words | 29 words | Sentence-to-paragraph continuity |
| `span_200` | ~200 tok | 154 words | 77 words | Broader thematic passages |

Do not use an actual tokenizer — word-count approximation is sufficient and keeps
the build dependency-free. Use Python's `text.split()` for word counting.

The existing heading-based index is the baseline document-level lane. Do not modify it.
The three new span indices are additive.

### Chunk schema for span indices

Every chunk in the new indices must include offset fields:

```json
{
  "file": "domains/health/metrics.md",
  "span": "span_75",
  "word_start": 120,
  "word_end": 178,
  "text": "...",
  "vector": [...]
}
```

No `heading` field in span chunks — spans cut across headings by design.
`word_start` and `word_end` are word-level indices into the source file's word list.

### Index output layout

```
throughline/
├── indices/
│   ├── span_25/
│   │   ├── chunks.jsonl
│   │   └── meta.json
│   ├── span_75/
│   │   ├── chunks.jsonl
│   │   └── meta.json
│   └── span_200/
│       ├── chunks.jsonl
│       └── meta.json
├── throughline_index.py    ← builds all three span indices
├── throughline_query.py    ← multi-span query runner + throughline detection
└── app.py                  ← Flask UI
```

`meta.json` per span index:
```json
{
  "model": "nomic-ai/nomic-embed-text-v1.5",
  "span": "span_75",
  "word_window": 58,
  "word_step": 29,
  "embed_dim": 768,
  "last_built": 1234567890.0,
  "chunk_count": 12450
}
```

### Throughline detection rule

A result is a **throughline** when the same file appears in the top-N results from
at least two different span indices for the same query.

Grouping key: `file` path only. Do not require offset overlap for v1 — file-level
agreement across spans is sufficient to make the concept legible in the demo.

Throughline strength: count how many span indices returned the file. Maximum is 3
(all three spans agree). Display as a badge: `2/3 spans` or `3/3 spans`.

### UI

Flask. Local only. Single page, no login, no database.

Layout: header with a search input, then three columns side by side (one per span).
Within each column, result cards show: file path (shortened), score, text preview (120 chars).
Cards from files that are throughlines get a colored left border and a badge.

A fourth "Throughlines" summary panel above the columns lists files that appeared in
2+ spans, sorted by throughline strength then score.

---

## Build Order

### Step 1: throughline_index.py

Build all three span indices over the note-system corpus.

```python
# Pseudocode for the span chunker
words = text.split()
for start in range(0, len(words), word_step):
    end = min(start + word_window, len(words))
    chunk_text = ' '.join(words[start:end])
    if len(chunk_text.strip()) < 30:  # skip tiny trailing chunks
        continue
    yield {
        'file': rel_path,
        'span': span_name,
        'word_start': start,
        'word_end': end,
        'text': chunk_text,
    }
```

Make it resumable: check `meta.json` last_built against file mtime before re-embedding.
Batch size 32, show progress. This will take a while on 4000+ files — let it run.

Accept `SB_ROOT` as a CLI argument (default: `~/notes`).
Write indices to `throughline/indices/` relative to the script's directory.

### Step 2: throughline_query.py

Multi-span query runner. Accepts a query string, returns structured results.

```python
def query_all_spans(query_text, indices_dir, n_per_span=10):
    """
    Returns dict: {
        'query': str,
        'spans': {
            'span_25': [{'file', 'score', 'text', 'word_start', 'word_end'}, ...],
            'span_75': [...],
            'span_200': [...],
        },
        'throughlines': [{'file', 'span_count', 'best_score', 'spans': [...]}, ...]
    }
    """
```

Load each index independently. Embed the query once and reuse the vector across all
three cosine similarity searches. Return best chunk per file per span (not per chunk).

Throughline detection: collect all files across all span results, count span appearances,
filter to those appearing in 2+, sort by span_count desc then best_score desc.

Also expose a CLI mode:
```
python throughline_query.py "attention and focus" --n 8
```

### Step 3: app.py

Flask app. Single route. Calls `query_all_spans` and renders results.

```python
@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    query = ''
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            results = query_all_spans(query, INDICES_DIR)
    return render_template('index.html', query=query, results=results)
```

Run on port 5051 (avoids collision with Topolski on 5050).

---

## Demo Queries to Prepare

Test these against the real corpus to verify useful contrast across spans:

1. **Narrow / factual**: `"heat mat seed starting"` — should show high span_25 precision
2. **Conceptual**: `"knowledge building over time"` — should show span_200 breadth
3. **Cross-domain**: `"energy and attention"` — should produce throughlines across health and focus domains
4. **Proper noun**: `"knowledge-work"` — throughlines expected across focus and learning notes

---

## What Success Looks Like

A colleague can type a query, see three columns of results, and immediately understand
why the same file appearing in all three columns means something different than a file
appearing in only one. The throughline panel makes that legible without explanation.

The index build can run unattended. The query response is fast (sub-second once indices
are loaded). The app runs locally with no internet connection after initial model download.

---

## What to Leave for Later

- Offset-level overlap matching (file-level grouping is sufficient for v1)
- Integration into `sb` CLI (keep standalone for now)
- The heading-based index as a fourth lane (document-level baseline can be added later)
- Authentication, deployment, or any non-local serving
