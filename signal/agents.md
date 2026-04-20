# Signal — Agent Build Brief

Read `learnings.md`, `roadmap.md`, and `presentation.md` before starting. This file locks
the current design decisions so you can build without re-deciding the concept mid-session.

---

## What You Are Building

A standalone CLI tool that extracts structured signals from a single markdown note.

The source of truth is the note itself.

Given a note like `2026-04-19.md`, the tool reads only that file, extracts a small set of
structured signals, and writes the derived artifacts into the sibling companion directory
`2026-04-19/`.

The claim: freeform notes do not need to become rigid at capture time in order to become
more structured later.

The demo: run Signal on one long daily note and show a readable review artifact containing
observations, decisions, questions, friction points, and follow-ups, each linked back to
its original span in the note.

---

## Directory Layout To Build

```
signal/
├── signal.py              ← the tool (single script)
├── learnings.md           ← already written
├── roadmap.md             ← already written
├── presentation.md        ← already written
├── agents.md              ← this file
└── outputs/               ← example outputs copied here for demo/commit if useful
```

Do not redesign the project around a larger package structure yet. A single readable
script is better for the first pass.

---

## Locked Decisions

### Source boundary

Read exactly one markdown note file per run.

Do not ingest:

- the companion directory as input
- attachments
- OCR text
- JSON sidecars
- metadata files

The note is the only source. The companion directory is for derived outputs only.

### Companion directory convention

For an input note:

- `2026-04-19.md`

the companion directory is:

- `2026-04-19/`

When the tool runs, it should write outputs there. If the companion directory does not
exist, create it automatically.

### Minimal output files

For v1, always write:

- `signals.json`
- `signals_review.md`

into the companion directory.

Example:

```text
2026-04-19.md
2026-04-19/
  signals.json
  signals_review.md
```

### Signal schema

Every extracted signal must include:

```json
{
  "id": "sig-0001",
  "type": "observation",
  "text": "The weekly review keeps failing when notes are too long.",
  "source_file": "/abs/path/2026-04-19.md",
  "heading": "Weekly review",
  "line_start": 42,
  "line_end": 44,
  "confidence": 0.84
}
```

Allowed `type` values in v1:

- `observation`
- `decision`
- `question`
- `friction`
- `follow_up`

Do not invent more categories in the first pass.

### Extraction strategy

Deterministic first. No model dependency in the first implementation.

Use plain heuristics over parsed markdown lines and heading context. Favor transparency
over cleverness.

Examples of good starting cues:

- `question`
  - lines ending in `?`
  - lines starting with `Q:`
  - bullets that clearly ask what/why/how/should

- `decision`
  - lines starting with `Decision:`
  - phrases like `I decided`, `I’m going to`, `I will`

- `friction`
  - phrases like `blocked by`, `stuck on`, `keeps failing`, `problem`, `friction`

- `follow_up`
  - lines starting with `TODO:`, `Next:`, `Follow up:`
  - phrases like `need to`, `should try`, `come back to`

- `observation`
  - phrases like `I noticed`, `it seems`, `the pattern is`, `what keeps happening`

Do not chase paragraph-perfect NLP in v1. Start with line-level or small span-level
extraction that you can audit.

### Provenance requirements

Every extracted signal must preserve:

- source file path
- heading context when available
- line start and line end
- original extracted text

If provenance is weak, the output will not be trustworthy.

### Review artifact

`signals_review.md` should be readable by a human without opening the JSON.

Recommended shape:

```md
# Signals Review

Source: 2026-04-19.md

## observation

- [sig-0001] lines 42-44
  Weekly review keeps breaking when the note is too long.

## friction

- [sig-0002] lines 51-52
  I keep losing the one useful takeaway inside a long daily note.
```

Include heading context where possible. Keep the markdown easy to skim.

### CLI interface

```
python signal.py extract <note-path>
```

Optional flags for v1:

```
  --stdout-json        Print JSON to stdout in addition to writing files
  --stdout-review      Print markdown review to stdout in addition to writing files
  --no-create-dir      Fail instead of creating the companion directory
```

Do not build batch mode first. Single-note extraction is the correct unit for the first
pass and matches the note/companion-dir convention.

### Error behavior

- Input note missing:
  `Error: note path does not exist: {path}`

- Input is not a markdown file:
  `Error: expected a markdown file, got: {path}`

- Companion directory missing and `--no-create-dir` passed:
  `Error: companion directory does not exist: {path}`

- No signals extracted:
  not an error; still write an empty `signals.json` and a review file that says no signals were found

---

## Build Order

### Step 1: Note + companion path handling

Write:

```python
def companion_dir_for(note_path: Path) -> Path:
    return note_path.with_suffix('')
```

Validate the input note, then create or check the companion directory depending on flags.

### Step 2: Markdown parsing

Parse the note into line records with:

- line number
- raw text
- current heading context

Headings can be captured with simple `#` markdown heading detection.

You do not need a full markdown parser in v1.

### Step 3: Rule-based extraction

Write one extractor per signal type, or one extractor with ordered rule checks.

Good first internal shape:

```python
@dataclass
class Signal:
    id: str
    type: str
    text: str
    source_file: str
    heading: str | None
    line_start: int
    line_end: int
    confidence: float
```

Start with line-based extraction. If two consecutive lines clearly belong together,
allow a small span, but do not overcomplicate this immediately.

### Step 4: Serialization

Write:

- `signals.json`
- `signals_review.md`

Use stdlib `json`. Keep the JSON easy to diff.

### Step 5: CLI

Use `argparse` with a single subcommand:

```text
python signal.py extract path/to/2026-04-19.md
```

Keep the tool standalone and local. No network calls.

### Step 6: Example outputs

After the tool works, run it on one or two real notes and copy representative outputs
into `signal/outputs/` for demo/commit if they are suitable to share.

---

## What Success Looks Like

1. `python signal.py extract path/to/2026-04-19.md` runs without error
2. It creates or uses `path/to/2026-04-19/`
3. It writes `signals.json` and `signals_review.md`
4. The extracted signals are legible and clearly traceable back to the note
5. A messy note becomes easier to reuse without rewriting the original note

The first version does not need to be exhaustive. It needs to be trustworthy enough that
the output feels worth keeping.

---

## What To Leave For Later

- batch extraction over many notes
- model-assisted classification or rewriting
- acceptance state and reviewer edits
- integration with `sb` CLI
- feeding accepted signals into `Surface`, `Ladder`, or other tools automatically
- reading anything from the companion directory as source input

The temptation will be to make Signal into a general metadata harvester. Do not do that
in v1. The clean source boundary is part of what makes the tool coherent.

---

## Keeping This File Current

Update this file when:

- a locked decision changes
- the source boundary changes
- the schema changes materially
- a build constraint appears that the next agent needs in order to continue safely

Do not use this file as a build diary. Put build lessons in `learnings.md`.
