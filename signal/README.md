# Signal

`signal` is a small local CLI that extracts structured signals from a single markdown note.

It is not a note-taking app and it is not a metadata warehouse.

The note stays the source.
The companion directory holds derived outputs.

## What It Does

Given a note like:

- `2026-04-19.md`

`signal` reads only that file, applies deterministic heuristics, and writes:

- `2026-04-19/signals.json`
- `2026-04-19/signals_review.md`

The first pass looks for five signal types:

- `observation`
- `decision`
- `question`
- `friction`
- `follow_up`

Each extracted signal preserves provenance:

- absolute source file path
- heading context when available
- line start and line end
- extracted text
- heuristic confidence

## Current Status

The first implementation is now real.

`signal.py` currently supports:

- `python signal.py extract <note-path>`
- automatic companion-directory creation
- `--stdout-json`
- `--stdout-review`
- `--no-create-dir`

The extractor is intentionally simple:

- heading-aware line parsing
- deterministic rule checks
- small-span continuation for indented follow-on lines
- readable review output grouped by signal type

This is not trying to be paragraph-perfect NLP. The value in `v1` is that you can audit why a signal appeared and jump back to the original note lines quickly.

## Why It Matters

The claim behind `signal` is small but useful:

freeform notes do not need to become rigid at capture time in order to become more structured later.

That makes `signal` a post-capture structuring layer in the larger note ecosystem:

- capture stays flexible
- structure can be derived later
- review stays possible because provenance is preserved

## What It Does Not Do

For `v1`, `signal` does **not** ingest:

- companion-directory contents as source input
- attachments
- OCR text
- JSON sidecars
- metadata files

The extractor has been verified against real daily notes. Outputs are legible and auditable — the review file groups results by signal type with line references back to the source.

## Usage

```bash
python signal.py daily/2026-04-19.md    # extract signals, print review to terminal
```

Writes `signals.json` and `signals_review.md` into the note's companion directory.
The companion directory is the existing convention for derived files alongside daily notes,
so signal outputs slot naturally into the existing structure.

## Next Useful Push

1. review-state tracking: mark signals as acted on, skipped, or promoted to stubs
2. tighter heuristics for friction and observation (currently lowest precision of the five types)
3. multi-note batch mode: `python signal.py --since 2026-04-01` over a date range
