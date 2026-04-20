# Hackathon Roadmap

This is the repo-level roadmap.

It is not a promise that every project will advance at the same speed. It is a map of the
next useful pushes, given the current state of the repo.

## Immediate Priority

### 1. Finish The Broad Topolski Pass

`topolski-explorer` remains the main thesis project.

Current operations state:

- full current local corpus staged
- full page-image render complete
- broad vision transcription resumed on `gpt-4.1-mini`
- current completion snapshot: `82 / 138` items and `265 / 634` pages transcribed
- local monitoring script added for progress checks

Immediate next steps:

- let the resumed broad pass keep moving
- rebuild the local index after a meaningful new chunk of pages lands
- keep the dashboard and processing matrix current enough to show real progress
- keep refreshing the exported public artifact layer as enough new pages accumulate
- keep the exported artifact library in a form that can rebuild search without shipping the scans

### 2. Preserve The Hybrid Topolski Strategy

Do not collapse back into one-model thinking.

Working split:

- broad coverage: faster vision model
- exacting rereads, eval subset, and hard pages: stronger model

That hybrid is now part of the plan, not a temporary embarrassment.

### 3. Keep The Demo Surface Legible

The Topolski dashboard and search UI are now part of the project’s credibility.

Near-term expectation:

- show corpus progress honestly
- show what the system believes it has indexed
- show where layout confidence is still provisional

### 4. Solidify The Public Artifact Layer

The Topolski project now has a better public shape than "code that could be run someday."

Near-term expectation:

- export sanitized per-item assessment JSON from the live run
- keep raw scans and live local artifacts out of git
- let a clone rebuild the local vector index from published assessment outputs

## Secondary Priority

### `decksmith`

Use `decksmith` to package the hackathon story once the current Topolski pass has enough
material to justify a stronger deck.

The next useful move is not arbitrary polishing. It is a deck that explains:

- what exists
- what is in process
- what the larger ecosystem thesis is
- what the Topolski experiment actually taught

### `julia-stl`

Keep as the strongest finished artifact in the repo story.

This project does not need urgent new build work right now. It needs to remain legible as
the proof that finished form is possible in this repo.

## Knowledge-Work Toolset

`throughline`, `trails`, `askme`, and `signal` are now working local v1 tools, each with a standalone CLI verified against a real corpus.

Current state:

- all four have working CLIs verified against a real corpus
- `askme` has seven gap-detection strategies, including two added post-hackathon from real use
- `trails` uses the existing embedding index for semantic search when available
- `throughline` builds its own multi-span index independently of the main embedding stack
- `signal` outputs slot into the existing companion-directory convention

Next useful pushes:

- `askme`: prompt deduplication across runs; feedback loop for answered vs. skipped
- `signal`: review-state tracking; batch mode over date ranges
- `throughline`: lightweight web UI for parallel column display
- `trails`: `--save` flag to write timelines back into the corpus as synthesis artifacts

`ladder` remains the explanation layer. Keep framing coherent as the toolset matures.

## Presentation Goal

The repo should be ready for a stronger narrative pass, not a fake polished launch.

The target presentation should be able to say:

- several projects are already real
- one research build is clearly in motion
- the repo is converging on a reusable build method
- the next push will be stronger because the tooling, monitoring, and framing are catching up
