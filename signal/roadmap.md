# Signal Roadmap

## Purpose

Build a local tool that extracts structured signals from a single markdown note and writes
the derived output into that note's companion directory.

The aim is not to replace freeform writing with a rigid capture format. The aim is to let
freeform writing stay flexible while still becoming more reusable later.

## What We Set Out To Build

- a standalone CLI that reads one markdown note
- a minimal signal schema with clear provenance
- deterministic extraction rules that work without a model
- review artifacts written beside the source note
- one or two demo outputs that prove the concept on real daily notes

## Locked Constraints

- Source input is the markdown note only
- The companion directory is for outputs, not source ingestion
- Outputs should be inspectable and durable
- The first version should work with stdlib Python if reasonably possible
- Model assistance is optional later, not part of the core claim

## Proposed Output Files

Given:

- `2026-04-19.md`

Write derived artifacts to:

- `2026-04-19/signals.json`
- `2026-04-19/signals_review.md`

Possible later additions:

- `2026-04-19/signals_accepted.json`
- `2026-04-19/signals_digest.md`

## Minimal Signal Schema

Each extracted signal should include:

- `id`
- `type`
- `text`
- `source_file`
- `heading`
- `line_start`
- `line_end`
- `confidence`

Optional fields for later:

- `tags`
- `status`
- `review_note`
- `canonical_text`

## Phases

### Phase 1: Note Parsing

- [x] accept a path to a markdown file
- [x] detect or create the companion directory
- [x] parse headings and line ranges
- [x] preserve raw line text for provenance

### Phase 2: Deterministic Extraction

- [x] define rule-based extraction patterns for `observation`
- [x] define rule-based extraction patterns for `decision`
- [x] define rule-based extraction patterns for `question`
- [x] define rule-based extraction patterns for `friction`
- [x] define rule-based extraction patterns for `follow_up`
- [x] emit structured signals with source spans

### Phase 3: Review Artifacts

- [x] write `signals.json`
- [x] write `signals_review.md`
- [x] make the review markdown easy to skim by heading and signal type
- [x] include original excerpts so the reviewer can judge context quickly

### Phase 4: Demo And Validation

- [ ] run on one real daily note outside the public repo
- [ ] run on one longer messier note outside the public repo
- [x] evaluate signal precision versus noise on synthetic representative notes
- [ ] revise the schema if the outputs feel over-structured or under-specific

### Phase 5: Optional Upgrade Path

- [ ] add optional model-assisted classification or rewriting
- [ ] add accept/reject workflow
- [ ] add digest generation across several reviewed daily notes
- [ ] explore whether reviewed signals should help `Surface`, `Ladder`, or another tool

## First Hackathon Slice

The smallest useful version is:

1. `signal.py extract path/to/note.md`
2. parse the markdown note only
3. emit a short JSON list of signals with source spans
4. emit a readable markdown review file in the companion directory

That is enough to prove the concept without overbuilding it.

## Decisions Locked During Build

- first extractor shape: line-based with small continuation spans
- confidence: rule-derived and hand-tuned by cue strength
- review grouping: grouped by type, with heading context retained inside each item
- companion directories: created automatically unless `--no-create-dir` is passed

## Current Read

`signal` now has a real `v1` implementation in `signal.py`.

The current state is best described as:

- the core CLI contract is implemented
- the deterministic extractor is working
- the outputs are inspectable and legible
- the project still needs validation on messy real notes

That is a good first shape. It proves the concept without pretending the heuristics are finished.

## Success Criteria

- one messy note becomes a smaller, reviewable artifact
- the extracted signals are clearly traceable back to the note
- the output is useful enough that keeping it feels reasonable
- the process does not pressure the user into changing how they write notes
