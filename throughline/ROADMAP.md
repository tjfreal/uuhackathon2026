# Throughline Roadmap

## Purpose

Build a multi-span semantic search layer for the note-system that makes retrieval granularity explicit and highlights throughlines across chunk sizes.

## What We Set Out To Build

- parameterized embedding generation for several chunk spans
- a multi-index query engine
- throughline detection across result sets
- a local UI for side-by-side comparison
- a reusable tool, not just a hackathon demo

## Current Component Map

| Component | Current location | Status | Notes |
|-----------|------------------|--------|-------|
| Project spec | `hackathon-project.md` | existing | strongest planning doc |
| Candidate summary | `candidates/throughline/README.md` | existing | companion brief |
| Embedding pipeline | `scripts/parse_embeddings.py` | external existing | needs span support |
| Query runner | `scripts/query_embeddings.py` | external existing | needs multi-index support |
| Current embedding store | `.index/embeddings/` | external existing | document-level baseline |
| Concept docs | `domains/focus/knowledge/*.md` | external existing | framing and rationale |
| UI | not built yet | planned | Flask or static app |

## Phases

### Phase 1: Foundations

- [ ] confirm chunking strategy and target span sizes
- [ ] inspect existing embedding metadata format
- [ ] define output layout for per-span indices
- [ ] decide throughline grouping key

Deliverable:
write down the index format, the target span set, and the grouping rule in enough detail that the embedding and query work can be done without re-deciding the concept every hour.

### Phase 2: Index Build

- [ ] add fixed-span chunking to `scripts/parse_embeddings.py`
- [ ] build at least three span indices
- [ ] document index metadata so query code can load any span directory
- [ ] measure index size and build time

Suggested first span set:

- 25 tokens for sharp local detail
- 75 tokens for sentence-to-paragraph continuity
- 200 tokens for broader thematic capture
- keep the existing heading/document lane as a baseline if it is already available

Minimum success condition:
one corpus, three span indices, and enough metadata to map every hit back to source path and offsets.

### Phase 3: Query Layer

- [ ] add a multi-span query runner
- [ ] rank results independently per span
- [ ] group repeated hits into throughlines
- [ ] expose structured JSON output for UI consumption

Minimum result schema:

- query text
- span size
- source path
- offset range
- preview text
- score
- throughline group id

The throughline rule can start simple:
group results when they come from the same source file and overlapping or adjacent source offsets across spans.

### Phase 4: UI

- [ ] build a local query page
- [ ] render one column per span size
- [ ] highlight throughlines
- [ ] show source path, preview text, and score

The first UI does not need to be fancy. It only needs to make one idea legible fast:
which concepts keep reappearing as chunk size changes.

### Phase 5: Demo and Hardening

- [ ] find reliable demonstration queries
- [ ] verify useful contrast between spans
- [ ] write usage notes
- [ ] decide whether to fold this into `sb` or keep standalone

Good demo queries should include:

- a narrow factual query
- a conceptual query
- a query that is likely to benefit from larger spans
- a query that is likely to benefit from smaller spans

## Decisions To Lock

- chunk sizes
- overlap amount between fixed windows
- throughline matching rule
- CLI versus standalone web app

## First Hackathon Slice

If this gets built as a minimal but convincing prototype during the hackathon, the smallest useful version is:

1. build three indices over the same note corpus
2. run one query across all three
3. merge and group repeated hits
4. render the result in a simple local web page

That would already be enough to demonstrate the claim.

## Notes

Use this file as the running map between concept, implementation, and final resting place of each subsystem.
