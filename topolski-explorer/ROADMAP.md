# Topolski Explorer Roadmap

## Purpose

Build a local-first research interface over the Topolski Chronicles that uses API-assisted processing to create durable local search artifacts, interpretable corpus metadata, and a trustworthy view into what the collection actually contains.

## Current State

The project already has:

- a local raw corpus of PDFs and metadata JSON in `staged_data_raw/`
- a preprocessing step that renders normalized page images into `data/staged/`
- a vision transcription step that extracts typeset text, handwriting, sketch descriptions, entities, and page summaries
- a local Chroma index with multiple retrieval lanes
- a local search UI that works over saved outputs
- a frozen demo snapshot at `82 / 138` items, `265 / 634` pages, and `1306` indexed chunks

That is enough for a real demo. It is not yet enough for strong trust in the corpus representation.

The current build should be treated as `v1: page-level semantic retrieval`.

The next build should be treated as `v2: layout-aware extraction and feature certification`.

## Main Build Tracks

### Track 1: Corpus Processing

- [x] normalize the raw corpus into a working staged layout
- [x] render page images locally
- [x] make vision transcription resume-safe
- [x] persist local transcription outputs
- [x] complete staging of the full current local corpus
- [ ] continue scaling the processed corpus beyond the current frozen hackathon slice
- [ ] preserve the current `v1` path as the baseline for comparison

### Track 2: Retrieval

- [x] build multiple retrieval lanes per page
- [x] run local search against saved Chroma state
- [x] support local demo behavior without requiring reranking
- [x] establish a processing-approaches matrix so experiments can be compared instead of hand-waved
- [x] add a rebuild path from exported public artifacts back into a local Chroma index
- [ ] evaluate retrieval quality on a stable benchmark query set
- [ ] tune ranking only if the benchmark reveals recurring failure modes

### Track 2B: Public Artifact Layer

This is now a real build track, not just a future packaging concern.

Goal:

- publish derived assessments without redistributing the raw scans
- preserve enough structured output to rebuild the finding aid layer
- let the public project read as "new index over a public collection" rather than "code skeleton"

Current build status:

- [x] publishing policy documented
- [x] safe export script for selected derived artifacts
- [x] sanitized per-item assessment library export
- [x] rebuild script that can index from exported assessment JSON
- [ ] decide whether to publish page-level transcription snapshots beyond the sanitized artifact library
- [ ] decide how often to refresh the exported library during the hackathon

### Track 3: Feature Manifest

This is now a first-class requirement.

Build a derived metadata layer that says what the system believes exists on each page and in each item, so search results can be interpreted against known corpus features rather than treated as opaque semantic guesses.

Target outputs:

- per-page feature flags
- per-item rollups
- corpus-level summaries

Initial feature categories:

- `has_typeset_text`
- `has_handwritten_text`
- `has_sketches`
- `has_entities`
- `has_summary`
- `is_index_like`
- `is_list_like`
- `is_image_heavy`
- `is_text_heavy`
- `has_portrait`
- `has_crowd_scene`
- `has_architecture`
- `indexed_chunk_types`

The first version does not need perfect confidence scoring. It only needs to make the feature surface visible and inspectable.

The second version should begin to expose uncertainty, not just presence flags.

### Track 4: Layout-Aware Extraction

This is now the central rebuild track.

The current page-level pass is useful, but it is too coarse to trust with small text, sidebars, footers, captions, and mixed visual/text boundaries.

Rebuild goal:

- identify candidate page regions
- type those regions
- run targeted extraction on them
- synthesize page-level outputs from region-level evidence

Initial region categories:

- `typeset_block`
- `handwritten_block`
- `caption`
- `footer`
- `sidebar`
- `index_or_list`
- `sketch_region`
- `mixed_region`

Current build status:

- [x] provisional layout manifest scaffold
- [x] region crop generation from the scaffold
- [x] sample region-level transcription pass
- [ ] representative evaluation subset selection
- [ ] measured or model-assisted layout segmentation
- [ ] full-corpus region-level transcription

### Track 5: Dashboard / Status Surface

This is also now a first-class requirement.

Build a bento-style local dashboard that shows:

- what items exist locally
- what items are processed
- what features have been detected
- what chunk types are indexed
- where coverage is thin or incomplete
- which items/pages are likely index pages, sketch-heavy pages, handwriting-heavy pages, or otherwise useful anchors

The dashboard should serve two roles:

1. build observability
2. feature certification for search trust

Current build status:

- [x] local dashboard route and bento-style status surface
- [x] feature-manifest visibility
- [x] layout-manifest visibility
- [x] processing-matrix visibility in project artifacts
- [ ] processing-matrix visibility inside the dashboard
- [ ] region-sample trust reporting inside the dashboard

## Agent-Army Split

The next build should be parallelized around disjoint ownership, not vague “help everywhere” prompts.

1. Corpus scaling agent
   Owns larger-batch preprocessing, page transcription, and incremental reindexing.

2. Evaluation agent
   Owns benchmark queries, judgment schema, and retrieval comparisons across approaches.

3. Region-sample agent
   Owns deterministic selection of representative pages and regions for exacting comparison.

4. Layout agent
   Owns the transition from provisional layout guesses to measured or model-assisted segmentation.

5. Dashboard trust agent
   Owns status surfacing, processing-matrix visibility, and explicit cautions about provisional evidence.

6. Region transcription agent
   Owns crop-level prompt design, resume-safe execution, and normalized region outputs.

## Near-Term Sequence

1. resume scaling transcription and indexing after the current hackathon snapshot
2. preserve the current `v1` search path as the baseline
3. keep exporting the public-safe artifact library as the corpus grows
4. surface that artifact-library direction in project docs and presentation
5. keep the processing matrix current as each new lane lands
6. choose a representative evaluation subset instead of relying on ad hoc spot checks
7. prototype region-aware extraction on that subset
8. use the dashboard and the subset results to decide whether `v2` is actually improving trust

## First Useful Deliverables

### Feature Manifest v1

- [ ] one generated JSON file per item, or one corpus manifest file
- [ ] page-level feature flags derived from transcription outputs
- [ ] item-level counts and summaries
- [ ] indexed chunk-type visibility
- [ ] explicit signal for pages that are only weakly characterized by the current pipeline

### Layout Manifest v1

- [ ] one generated file per page or per item describing candidate regions
- [ ] region type guesses
- [ ] rough geometric bounds
- [ ] support for crop-level follow-up extraction
- [ ] comparison against the current page-level pass on a small evaluation subset

### Dashboard v1

- [ ] corpus totals: items, pages, transcribed pages, indexed pages
- [ ] cards for feature coverage
- [ ] table of processed items with counts
- [ ] quick lists: most index-like, most sketch-heavy, most handwriting-heavy
- [ ] links back into the search and page-image views

## What Can Wait

- perfect scoring theory
- complex classifier logic
- polished design system work
- full collection completion before the observability layer exists

The point of the next phase is not elegance. It is legibility and trust.

## Interestingness Test

The next iteration should not only improve the system. It should help answer whether anything genuinely interesting is happening here.

Questions to keep in frame:

- Are mixed-layout illustrated broadsheets inherently badly served by single-pass page interpretation?
- Does layout-aware decomposition create a materially better research interface?
- Can feature certification and observability become part of the archive UX instead of a hidden implementation detail?
- Are we learning something general about this class of documents, or just getting incremental search improvements?
