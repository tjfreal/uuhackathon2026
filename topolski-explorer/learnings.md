# Topolski Explorer Learnings

This file is a running account of what the current Topolski build has actually demonstrated, where it is weak, and what the next rebuild should be trying to prove.

It is not a victory lap. It is a course correction document.

## What The Current Build Proved

The project is on a real path.

It is now possible to:

- process the local corpus into a durable staged layout
- generate page images locally
- send those pages through a vision model
- save local transcription outputs
- embed several retrieval lanes
- search the resulting corpus through a local UI

That matters because it means the project is not speculative anymore. There is a functioning local artifact with API-assisted processing behind it.

Some queries already feel meaningfully useful. Obvious named or well-signaled topics like `Churchill` can surface coherent results quickly. The system can already support browsing and discovery in a way that would have been hard to achieve with ordinary OCR-first methods.

The newer dashboard and processing-matrix work also proved something important: corpus observability is not a side quest. Once the project began surfacing what features were present, what was indexed, and which extraction lanes were merely provisional, the work became easier to reason about and easier to criticize honestly.

That is the good news.

One more thing is now true: the project has crossed from "public-sharing theory" into
"public-sharing implementation."

A first sanitized artifact library can now be exported from the live run without
redistributing the raw collection or touching the active working directories.

The current frozen snapshot now stands at:

- `82 / 138` items transcribed
- `265 / 634` pages transcribed
- `1306` indexed chunks in the local Chroma store
- `82` sanitized item assessment files in the exported artifact library

## What The Current Build Did Not Prove

The current build does **not** yet prove that the system understands the pages at a trustworthy structural level.

The weak point is not just model quality. It is the shape of the pipeline.

Right now, the project relies heavily on single-pass page interpretation. That is enough to get broad semantic retrieval working, but it is not enough to trust that the system is correctly isolating:

- main typeset text blocks
- handwritten notes and marginalia
- captions
- footers
- sidebars
- index/list structures
- inset boxes
- sketch clusters

Confidence by category right now is roughly:

- broad sketch and scene understanding: fairly high
- main page theme and summary: moderate to fairly high
- large typeset blocks: moderate
- handwritten text: moderate to low
- small inserts, footers, sidebars, marginal notes, and mixed-layout boundaries: low

That means the current version is a real retrieval prototype, but not yet a reliable document-understanding system.

## The Central Lesson

The next improvement is not “use a slightly better prompt.”

The next improvement is to stop pretending the page is one thing.

These broadsheets are mixed-layout documents. A single full-page call can produce a useful synthesis, but it cannot be trusted to fully recover all component regions when the page contains small text, overlapping visual structures, or multiple reading modes.

So the real transition is:

- from page-level semantic approximation
- to layout-aware extraction

And from:

- ad hoc anecdotal query tests
- to explicit cross-approach evaluation

That is the next target.

## Rebuild Thesis

The current system should be treated as `v1`.

`v1` says:

- the corpus can be made locally searchable
- vision models can unlock handwriting + sketch retrieval
- the project is worth continuing

`v2` needs to say more:

- we can identify page regions and page component types
- we can run targeted extraction on those regions
- we can certify what features are actually present and indexed
- we can tell when a result is grounded in solid evidence versus broad page-level inference

There is also now a parallel publication thesis:

- the meaningful public artifact is the assessment layer, not the source scans
- the project should be able to rebuild its local finding-aid index from exported assessment JSON

## Exact Questions The Rebuild Must Answer

### Layout And Boundaries

- Can we reliably identify the major regions on a page?
- Can we distinguish text blocks, handwritten annotations, sketch zones, captions, inserts, footers, and list/index sections?
- Can we preserve enough geometry to know where a feature came from?

### Extraction Quality

- Does region-level extraction materially improve typeset transcription completeness?
- Does it improve handwriting capture?
- Does it improve recovery of small text like footers, sidebars, and inset labels?
- Does it reduce semantic drift in page summaries?

### Retrieval Trust

- Which result signals are genuinely dependable: text, summary, entities, sketch description, or blended?
- When a search result surfaces, can we say what features were actually present and used?
- Can we identify which pages are index-like, image-heavy, or handwriting-heavy so the user knows what kind of result they are seeing?

### Coverage And Observability

- What fraction of pages have strong typeset coverage?
- What fraction appear to contain handwriting?
- What fraction are sketch-dominant?
- Which items are only weakly represented because the extraction path is still too coarse?

### Interestingness Test

The most important rebuild question is not “did we improve a metric?” It is:

- did we discover something non-obvious about how this corpus should be read computationally?

More specifically:

- do mixed-layout illustrated broadsheets require a component-aware reading model to become genuinely searchable?
- can sketch descriptions and page structure outperform naive text-centric retrieval?
- can observability and feature certification become part of the research interface rather than an afterthought?

If the answer to those is yes, then the project has done something interesting.

## Rebuild Plan

### Phase 1: Preserve V1, Do Not Throw It Away

- keep the current page-level pipeline runnable
- keep the current local search UI available
- keep scaling the corpus incrementally

`v1` remains the baseline against which the rebuild should be judged.

### Phase 2: Add A Layout Manifest Stage

For each page, generate a layout manifest that identifies candidate regions and their guessed types.

Minimum region types:

- `typeset_block`
- `handwritten_block`
- `caption`
- `footer`
- `sidebar`
- `index_or_list`
- `sketch_region`
- `mixed_region`

The first version can be approximate. The important thing is to make the page decomposable.

### Phase 3: Add Region-Level Extraction

Once regions exist, run targeted extraction per region rather than relying on one full-page read.

Target outputs:

- transcribed text by region
- handwritten transcription by region
- sketch descriptions by region
- typed region metadata
- page-level rollup synthesized from region outputs

### Phase 4: Add Feature Certification

Produce a derived feature manifest that says:

- what the system believes exists on the page
- what was successfully extracted
- what chunk types are indexed
- what the evidence basis is for retrieval

This is the bridge from “search result” to “trustworthy result.”

### Phase 5: Add A Dashboard

Build a local status surface that makes the corpus legible:

- processing progress
- feature coverage
- page-type distribution
- handwriting/sketch/index incidence
- pages or items worth inspecting manually

This is not decoration. It is part of the research method.

## Questions To Surface In The Next Iteration

- Are there recurrent page archetypes that deserve their own extraction strategy?
- Are index pages valuable enough to parse specially?
- Should some pages be re-run at crop level because the full-page pass is demonstrably inadequate?
- Is there a useful relationship between region geometry and retrieval quality?
- Which failures are model failures, and which are pipeline-design failures?
- At what point does adding more corpus stop helping because the representation itself is still too coarse?
- Which experimental lane actually changed what a human can find, verify, or trust?
- Which parts of the assessment layer are strong enough to publish as a durable public artifact?

## Current Read

The project is not done, but it is not flailing.

The current build proved the path is real. The rebuild now needs to prove the path is sharp.

For the current hackathon push, that is enough. The run has been paused intentionally in a
demo-ready state rather than stretched into a compute bottleneck story.

It also now has a clearer end-state:

- inspect once
- assess at multiple granularities
- save those assessments
- rebuild the index from them
- return the user to the original source material

That is a real project shape, not just a pile of pipeline stages.
