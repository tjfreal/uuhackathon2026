# Trails — Agent Build Brief

Read README.md before starting. This file locks all design decisions so you can build
without re-deciding mid-session.

---

## What You Are Building

A standalone CLI tool that reconstructs the history of a topic from a corpus of text files.

Given a directory of markdown/text files and a query string, Trails finds every file that
mentions the topic, extracts a date for each file, pulls the relevant passage, and renders
a chronological timeline — either as a dated excerpt list or as a prose narrative.

The tool is corpus-agnostic. It does not depend on any specific file naming convention
beyond opportunistic date detection. It works on any flat or nested directory of text files.

The demo: run `python trails.py query "julia vase" --corpus ~/notes` and show a
decade of scattered mentions assembled into a single arc — from first sketch to 2026
breakthrough. The arc exists in the corpus; Trails makes it visible.

---

## Directory Layout To Build

```
trails/
├── trails.py           ← the tool (single script)
├── README.md           ← already written
├── AGENTS.md           ← this file
├── presentation.md     ← already written
├── learnings.md        ← already written
└── outputs/            ← example outputs to commit after a demo run
    └── README.md       ← explains what's in here
```

---

## Locked Decisions

### Language and dependencies

Python 3.10+. No required external dependencies — stdlib only for the core tool.

Optional numpy for embedding-based search. Do not require it. Detect it at runtime and
enable the `--index` flag only if available.

Do not use PyYAML, pandas, or any NLP library. Keep it auditable and portable.

### Date extraction strategy

Dates come from three places, in priority order:

1. **Filename**: `YYYY-MM-DD.md` or `YYYY-MM-DD-slug.md` — extract from the stem.
   Also handles `YYYY_MM_DD` format. Exact day known.

2. **Frontmatter**: Look for `date:` in the first 10 lines of a file.
   Accept `YYYY-MM-DD`, `YYYY-MM`, `YYYY`.

3. **Content scan**: Look for the first ISO date pattern in the file body
   (`\b\d{4}-\d{2}-\d{2}\b`). Take the earliest found. Mark as "content-date."

4. **No date found**: Assign `undated`. Sort undated entries to the end.

Do not try to be clever about relative dates ("last week", "March"). Ignore them.
Dates are either parseable or they are not.

### Relevance search

Two modes, selected by whether `--index` is passed:

**Keyword mode** (default):
- Case-insensitive substring search across file content
- Also search the filename
- A file matches if the query string appears anywhere in it
- Multi-word queries: all words must appear (AND logic, not phrase match)
- Do not use regex unless the user quotes a regex with `--regex`

**Embedding mode** (when `--index <embeddings-dir>` is passed):
- Load `chunks.jsonl` from the index directory (same format as throughline)
- Embed the query with `nomic-ai/nomic-embed-text-v1.5` (prefix: `search_query: `)
- Score all chunks, take best chunk per file, rank files by score
- Use top-N files by score as the match set (N = `--n`, default 20)
- Requires `sentence-transformers` and `numpy`

### Passage extraction

For each matching file:
- Find the matching region (the line containing the match, or the highest-scoring chunk)
- Expand context: take the 3 lines before and 3 lines after the match line
- Strip markdown formatting (headers, bullets, bold/italic markers) from the excerpt
- Truncate to 200 characters with `...` if longer
- If multiple matches in one file: take the highest-scoring or first match only

One excerpt per file. No multi-excerpt output from a single file.

### Deduplication

A file should appear at most once in the output, even if it matches multiple times.

If the same content appears in both a daily note and a companion JSON, prefer the daily note.
Detect near-duplicates by comparing excerpts: if excerpt similarity > 80% (simple character
overlap), keep the one with the more specific date and skip the other.

### Output formats

**`--format list`** (default):

```markdown
## {topic} arc

{date}  {relative-path}
  {excerpt}

{date}  {relative-path}
  {excerpt}
```

Dates render as: `YYYY-MM-DD` for exact, `YYYY-MM` for month-only, `YYYY` for year-only,
`YYYY (circa)` when date comes from content scan, `undated` otherwise.

**`--format narrative`**:

Use an LLM call (via `anthropic` SDK if available, otherwise `openai`) to write a 3-5
paragraph prose narrative of the arc. Pass the assembled timeline as context.

If neither SDK is available, fall back to list format with a warning.

**`--format json`**:

Emit a JSON array of `{date, date_confidence, file, excerpt}` objects. For programmatic use.

### CLI interface

```
python trails.py query <topic> [options]

Arguments:
  topic               Query string (required)

Options:
  --corpus PATH       Root directory to search (default: current directory)
  --format            Output format: list | narrative | json (default: list)
  --out PATH          Write output to file instead of stdout
  --n INT             Max files to include in timeline (default: 30)
  --index PATH        Path to embeddings directory (enables semantic search)
  --domain SUBDIR     Restrict search to a subdirectory of corpus (e.g. "domains/garden")
  --since YYYY-MM-DD  Only include files with dates on or after this date
  --until YYYY-MM-DD  Only include files with dates on or before this date
  --show-dates        Print date extraction method alongside each entry (debug)
```

### Output file naming

When `--out` is not specified: print to stdout.

When writing to a file:
- If `--out` is a directory: write `{directory}/{YYYY-MM-DD}-{slug}.md`
- If `--out` is a full path: use it directly
- Slug is the query string lowercased, spaces replaced with hyphens, max 40 chars

### Error behavior

- Corpus directory does not exist: `Error: corpus path does not exist: {path}`
- No files found: `No text files found in {path}`
- No matches: `No matches found for "{topic}" in {file-count} files.` (exit 0, not error)
- Index path given but numpy missing: warn and fall back to keyword mode
- Index path given but `chunks.jsonl` missing: `Error: no embeddings index found at {path}`

---

## Build Order

### Step 1: File discovery

```python
TEXT_EXTENSIONS = {'.md', '.markdown', '.txt', '.rst', '.text', '.org'}

def discover_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob('*')
                  if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS)
```

### Step 2: Date extraction

Write `extract_date(path: Path, text: str) -> Tuple[Optional[date], str]` where the
second return value is the confidence: `"filename"`, `"frontmatter"`, `"content"`, or `"none"`.

Test cases to handle:
- `2026-01-15.md` → `date(2026, 1, 15)`, `"filename"`
- `2026-01-15-my-notes.md` → `date(2026, 1, 15)`, `"filename"`
- `2026_01_15.md` → `date(2026, 1, 15)`, `"filename"`
- File with `date: 2025-03` in first 10 lines → `date(2025, 3, 1)`, `"frontmatter"`
- File with `2024-07-22` anywhere in body → `date(2024, 7, 22)`, `"content"`
- No date found → `None`, `"none"`

### Step 3: Search

Write `search_keyword(files, query) -> List[Tuple[Path, str]]` returning `(path, matched_line)`.

Write `search_embedding(files, query, index_dir) -> List[Tuple[Path, str, float]]` returning
`(path, best_chunk_text, score)`.

### Step 4: Passage extraction

Write `extract_passage(path: Path, text: str, match_hint: str, context_lines: int = 3) -> str`.

### Step 5: Assembly

```python
@dataclass
class TimelineEntry:
    date: Optional[date]
    date_confidence: str
    path: Path
    rel_path: str
    excerpt: str
```

Sort entries: exact dates first (ascending), then month/year estimates, then undated.

### Step 6: Output rendering

Write `render_list(entries, query, corpus_root) -> str`.
Write `render_narrative(entries, query) -> str` (LLM call or fallback).
Write `render_json(entries) -> str`.

### Step 7: CLI

Use `argparse`. Single subcommand: `query`. Match the interface documented above.

---

## What Success Looks Like

1. `python trails.py query "julia vase" --corpus ~/notes` runs without error
2. Output shows at least 3 dated entries in chronological order
3. Each entry shows a legible excerpt — not markdown noise, actual content
4. `--format narrative` produces a readable prose arc (or a clean fallback message)
5. `--domain domains/garden` restricts results to that subdirectory
6. Running on a corpus with no matches exits cleanly with a message, not an error

---

## Example Outputs to Commit

After the tool builds, run these and commit the outputs to `outputs/`:

```bash
python trails.py query "3d scanning" --corpus ~/notes --out outputs/3d-scanning-arc.md
python trails.py query "julia vase" --corpus ~/notes --out outputs/julia-vase-arc.md
python trails.py query "knowledge building" --corpus ~/notes --out outputs/knowledge-building-arc.md
```

These prove the concept and serve as demo material.

---

## What to Leave for Later

- Fuzzy/semantic date parsing ("last spring", "a few years ago")
- Narrative mode that pulls from a structured review format specifically
- Automatic cross-referencing to people stubs during assembly
- Interactive mode (`--interactive` to walk the arc one entry at a time)
- CLI wrapper integration with a companion notes toolchain (lives outside this repo)
- Diff mode: compare two timelines to surface divergence

---

## Keeping This File Current

Update this file when:
- A locked decision changes during the build
- A new design constraint surfaces
- A step is discovered to be harder or easier than expected

Do not update this file to document what was built — that belongs in `learnings.md`.

---

## Dependencies

- Python 3.10+
- No required packages
- Optional: `sentence-transformers`, `numpy` (for `--index` mode)
- Optional: `anthropic` or `openai` (for `--format narrative`)
