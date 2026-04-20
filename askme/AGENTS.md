# Askme — Agent Build Brief

Read README.md before starting. This file locks all design decisions so you can build
without re-deciding mid-session.

---

## What You Are Building

A standalone CLI tool that reads index files from an sb-style note-system, detects
knowledge gaps, and generates prompts designed to get the user writing.

The system notices what it doesn't know and asks for it. This is the reverse of standard
capture: instead of the user deciding what to write, the corpus surfaces its own gaps.

The demo: run `python askme.py --index-dir ~/note-system/.index` and show a ranked list
of prompts, each tied to a real gap in the corpus — a stub not touched in 90 days, an
open question from a March synthesis session, a person stub with three lines of content.
The prompts should feel like a good question from a thoughtful collaborator, not like
a database query.

---

## Directory Layout To Build

```
askme/
├── askme.py            ← the tool (single script)
├── README.md           ← already written
├── AGENTS.md           ← this file
├── presentation.md     ← already written
├── learnings.md        ← already written
└── outputs/            ← example prompt outputs to commit
    └── README.md
```

---

## Locked Decisions

### Input: what the tool reads

The tool operates in two modes depending on what's available:

**Index-only mode** (requires only `--index-dir`):
Reads these files from the index directory:
- `stats.md` — file list with line counts and modification dates
- `people.md` — people index with file paths and mention counts
- `blockouts.md` — review companion file index

This mode works on any sb-compatible corpus without needing the actual files.

**Corpus mode** (requires `--corpus` in addition to `--index-dir`):
Also reads:
- Companion JSON files (`daily/YYYY-MM-DD/YYYY-MM-DD-HHMM.json`) for `open_questions` arrays
- People stubs directly for line count verification
- Domain subdirectories for sparsity calculation

Prefer index-only mode for the core demo. Corpus mode is the richer path.

### Gap detection: five strategies

Implement all five. Each produces a list of `GapEntry` objects with a score.

**Strategy 1: Sparse stubs**
Source: `stats.md` (line count per file)

A stub is any file with ≤ 10 lines. A gap stub is one that:
- Has ≤ 10 lines AND
- Was last modified more than 30 days ago AND
- Is in `domains/`, `references/people/`, or `pages/` (not `daily/`, `inbox/`, `archive/`)

Score = days since last modified (capped at 365). Older = higher priority.

Prompt template: `The {filename} stub hasn't been updated in {days} days. What do you know about {name} now?`

Extract the display name from the filename: `collaborator-name.md` → "Collaborator Name", `project-name.md` → "project name".

**Strategy 2: Open questions from companion JSON**
Source: companion JSON files in `daily/YYYY-MM-DD/` directories (corpus mode only)

These files have an `open_questions` array. Each non-empty entry is a gap.

Score based on age: questions from the last 30 days score highest (still live);
questions older than 90 days score lower (but still valid — may have been forgotten).

Prompt template: `You left this question open {days} ago: "{question}" — what's the current state?`

**Strategy 3: People with minimal context**
Source: `people.md` or direct file reads

A person gap is any person stub that:
- Appears in 1–3 files (not a peripheral mention) AND
- Has fewer than 8 lines in their stub file

Score = mention count (higher mention count + sparse stub = higher priority gap).

Prompt template: `{name} comes up in your notes but their stub is almost empty. What do you know about them? How did you meet?`

**Strategy 4: Dormant threads**
Source: `blockouts.md` — specifically the "Threads to watch" sections from synthesis entries

Parse synthesis companion files for `**Threads to watch**` sections. Any thread that:
- Appeared in a synthesis note AND
- Has not appeared in a daily note since that synthesis date (check `stats.md` modification dates as a proxy)

Score = days since the synthesis note that flagged it.

Prompt template: `"{thread}" was flagged as a thread to watch in your {date} synthesis. Where is that now?`

**Strategy 5: Domain gaps**
Source: `stats.md` — file count and line count per domain subdirectory

Identify the sparsest domains relative to their expected richness. A domain is sparse if:
- It has fewer than 5 files OR
- Its total line count is less than 200 lines

Score = (expected richness based on domain name) / (actual line count). Heuristic weights:
- `health/nutrition` — high expected richness (nutrition is rarely captured)
- `parenting/milestones` — high expected richness
- Any domain with a `learnings.md` or `metrics.md` stub but few entries — gap indicator

Prompt template: `Your {domain} notes are sparse. {Specific question based on domain.}`

Domain-specific questions (hardcoded for now, keep the list small):
- `health/nutrition` → "What does a good eating day look like for you?"
- `health/sleep` → "What's your current sleep pattern? What affects it?"
- `parenting` → "What's something one of your kids did recently that you want to remember?"
- `garden` → "What's the current state of the garden? What worked this season?"

### Ranking and selection

After running all five strategies, combine all `GapEntry` objects into a single ranked list.

Normalize scores to [0, 1] within each strategy. Apply a weight per strategy:
- Sparse stubs: 0.8
- Open questions: 1.0 (highest — these are already articulated)
- People: 0.7
- Dormant threads: 0.9
- Domain gaps: 0.5

Final score = normalized_score × strategy_weight.

Sort descending. Return top N (default: 5).

### Prompt quality rules

Every generated prompt must:
1. Name the specific thing (file, person, question, thread) — not generic
2. Include a timeframe when available ("89 days ago", "since March")
3. End with an open question — something that invites a full sentence, not yes/no
4. Sound like a curious colleague, not a database query

**Bad**: `Please provide additional context for references/people/collaborator-name.md`
**Good**: `This collaborator comes up in your notes a few times. What do you know about them? How did you meet?`

**Bad**: `Open question detected in 2026-03-11 companion file`
**Good**: `You left this question open in March: "self-forgiveness as ongoing work — what's the current state?" Where is that now?`

### Output formats

**`--format text`** (default):

```
{rank}. [{strategy}] {setup}
   → {prompt}
   Source: {relative-path} ({metadata})
```

Print a blank line between entries.

**`--format json`**:

```json
[
  {
    "rank": 1,
    "strategy": "questions",
    "score": 0.92,
    "setup": "You left this question open 38 days ago",
    "prompt": "Self-forgiveness as ongoing work — what's the current state?",
    "source": "daily/2026-03-11/2026-03-11-1430.json"
  }
]
```

**`--format inbox`**:

Write a markdown file suitable for dropping into an inbox:

```markdown
# Askme — {YYYY-MM-DD}

Generated from gaps in the note-system index.

---

{rank}. {setup}
**Prompt**: {prompt}
Source: {relative-path}

---
```

### CLI interface

```
python askme.py [options]

Options:
  --index-dir PATH      Path to .index/ directory (required)
  --corpus PATH         Path to corpus root (enables corpus mode)
  --type TYPE           Filter to one strategy: stubs | people | questions | threads | domains
  --n INT               Number of prompts to return (default: 5)
  --format FORMAT       Output format: text | json | inbox (default: text)
  --out PATH            Write output to file instead of stdout
  --min-age DAYS        Only surface gaps older than N days (default: 0)
```

### Error behavior

- `--index-dir` missing or not a directory: `Error: index directory not found: {path}`
- Index exists but `stats.md` missing: warn, skip strategies that need it, continue with others
- Companion JSON is malformed: skip silently, don't crash
- No gaps found: `No gaps detected in {strategy}. Try --type to broaden the search.`
- All strategies return zero results: `The index looks complete — or the index files may need regenerating.`

---

## Build Order

### Step 1: Data structures

```python
@dataclass
class GapEntry:
    strategy: str           # "stubs" | "people" | "questions" | "threads" | "domains"
    raw_score: float        # unnormalized score within strategy
    score: float            # normalized and weighted final score
    setup: str              # first line of output (the situation)
    prompt: str             # the question to ask
    source: str             # relative path to source file
    metadata: str           # one-line annotation (line count, days old, etc.)
```

### Step 2: Index parsers

Write a parser for each index file format:

`parse_stats(path: Path) -> List[Dict]` — parses `stats.md` into file records with path, lines, mtime.

`parse_people(path: Path) -> List[Dict]` — parses `people.md` into person records with name, path, mention_count.

`parse_blockouts(path: Path) -> List[Dict]` — parses `blockouts.md` into review records.

These parsers must be tolerant — if a section is missing or malformed, return what's available.

### Step 3: Gap detectors

One function per strategy. Each returns `List[GapEntry]` with raw scores.

```python
def detect_stub_gaps(stats: List[Dict], min_age_days: int) -> List[GapEntry]: ...
def detect_question_gaps(corpus_root: Path) -> List[GapEntry]: ...
def detect_people_gaps(people: List[Dict], corpus_root: Optional[Path]) -> List[GapEntry]: ...
def detect_thread_gaps(blockouts: List[Dict], stats: List[Dict]) -> List[GapEntry]: ...
def detect_domain_gaps(stats: List[Dict]) -> List[GapEntry]: ...
```

### Step 4: Ranking

```python
def rank_gaps(all_gaps: List[GapEntry], n: int) -> List[GapEntry]:
    # normalize within each strategy group, apply weights, sort, return top n
```

### Step 5: Output rendering

Write `render_text`, `render_json`, `render_inbox` — each takes `List[GapEntry]` and returns a string.

### Step 6: CLI

Use `argparse`. No subcommands — askme does one thing.

---

## Example Outputs to Commit

After the tool builds, run these and commit the outputs:

```bash
python askme.py --index-dir ~/note-system/.index --n 5 --out outputs/example-prompts.md
python askme.py --index-dir ~/note-system/.index --type people --n 5 --out outputs/people-gaps.md
python askme.py --index-dir ~/note-system/.index --format json --n 5 --out outputs/gaps.json
```

---

## What to Leave for Later

- Model-assisted prompt rewriting (current prompts are template-driven; a model pass is v2)
- CLI wrapper integration with a companion notes toolchain (lives outside this repo)
- `--write` mode: open an editor with the prompt, route the response on save
- Learning from which prompts were answered vs. skipped (feedback loop)
- Prompt deduplication across runs (don't surface the same gap every day)

---

## Keeping This File Current

Update this file when:
- A locked decision changes during the build
- An index file format turns out to differ from what's documented here
- A gap strategy is discovered to be too noisy or too quiet

Document build lessons in `learnings.md`, not here.

---

## Dependencies

- Python 3.10+
- No required external packages
- Reads from `.index/`: `stats.md`, `people.md`, `blockouts.md`
- Optional: direct corpus access for companion JSON and domain file reads
