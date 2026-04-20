# Topolski Processing Matrix

This file tracks the active processing approaches in the Topolski project.

It exists to support one question:

- did we do anything interesting here or nah?

That question cannot be answered by a single pipeline run. It has to be answered by comparing multiple ways of reading the same material.

## Matrix

| Approach | Current Status | Inputs | Outputs | Strengths | Weaknesses | Main Question |
|----------|----------------|--------|---------|-----------|------------|---------------|
| Whole-page vision pass | working | page JPEG | `transcription.json` | fast path to usable semantic retrieval; strong broad scene understanding | weak on small inserts, footers, sidebars, and exact region boundaries | is one full-page read enough for discovery, even if it is not enough for trust? |
| Page-level retrieval lanes | working | page transcription outputs | local Chroma index | lets text, sketches, entities, summaries, and blended signals compete | still inherits page-level coarseness from upstream extraction | which lane is actually dependable for which query type? |
| Feature manifest | working | page transcriptions + indexed chunk metadata | `data/feature_manifest.json` | makes current extraction visible and inspectable | heuristic and coarse; not yet confidence-aware | can we certify what the system believes is present on a page? |
| Dashboard/status surface | working | manifests + staged corpus + Chroma stats | `/dashboard` in local app | makes observability part of the interface | only as good as the underlying manifests | does trust improve when the corpus state is explicit? |
| Layout manifest scaffold | working | current page-level outputs | `data/layout_manifest.json` | turns layout-aware v2 into a concrete target | bounds are provisional and not geometry-grounded | what page components should the next build even try to isolate? |
| Region crop generation | in progress | page images + layout manifest | crop images + crop manifest | lets us stop treating a page as one thing | depends on weak provisional regions for now | does crop-level rereading recover neglected local detail? |
| Region-level transcription | in progress | crop manifest + crop images | region transcription manifest | should improve small-text and mixed-region coverage | depends on crop quality and region typing | can targeted rereads beat the current single-pass page read? |
| Benchmark query evaluation | planned | indexed corpus + fixed query set | evaluation notes/results | forces evidence over vibes | takes effort to define good test cases | are improvements real or just plausible-sounding? |

## Current Read

The project has already crossed one threshold:

- it is no longer speculative whether this corpus can be made locally searchable

The next threshold is harder:

- can we make it trustworthy enough that the user knows what kind of evidence a result is based on?

That is why the current work is shifting from “build search” to “compare readings.”

## What Would Count As Interesting

The next iteration should surface something stronger than “the model kind of got some pages right.”

Interesting outcomes would include:

- mixed-layout broadsheets really do require component-aware extraction
- sketch descriptions become a major retrieval signal rather than a side effect
- index/list pages deserve special treatment and materially improve navigation
- trust improves when feature certification and corpus observability are made first-class
- region-level rereads recover classes of information the page-level pass consistently misses

If none of those things happen, that is useful too. It would mean the current page-level approach already captures most of the value.

## Working Rule

Keep the current `v1` pipeline runnable.

Build `v2` as a comparison framework rather than a blind replacement:

1. preserve the baseline
2. add a new approach
3. compare outputs
4. decide whether the new approach is actually telling us something new
