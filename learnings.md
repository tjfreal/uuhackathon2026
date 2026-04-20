# Hackathon Learnings

This file tracks what changed at the repo level during the hackathon.

It is not a polished retrospective. It is a running account of what seems true right now, while the projects are still moving.

It is also an active coordination document. I refer other task agents to this file so they can build from the current strategic read instead of starting cold or inventing their own framing.

These learnings files are not isolated notes. They roll up into a larger private aggregation system behind the curtain, so they should be treated as durable handoff material rather than disposable scratch text.

## Current Repo-Level Learning

The neat thing happening here is not just that several projects exist.

The neat thing is that they are starting to reveal a repeatable build pattern and a larger system shape at the same time.

Across the subprojects, the same lessons keep reappearing:

- the project gets better when the real question is found
- the strongest version is usually smaller and more legible than the first imagined version
- outputs become more useful when they are treated as durable artifacts
- explanation keeps showing up as part of the build, not as cleanup
- one project can create tooling, framing, or structure that makes the next one cheaper

That suggests the repo is slowly becoming a personal build system, not just a stack of separate hackathon entries.

## The Main Shift

The most important change was not one technical implementation detail. It was a temporary rule change.

Normally the work leans toward local-only systems over personal corpora, with an emphasis on durability and workflows that do not collapse when an API key disappears. For the duration of this hackathon, that preference has been relaxed on purpose.

That changed the project set:

- some work stayed relatively close to the usual instincts (`julia-stl`)
- some work emerged from the need to explain the work (`decksmith`)
- some work only became realistic because API access was explicitly on the table (`topolski-explorer`)
- some newer stubs clarified what the broader note system loop might actually include (`askme`, `signal`)

That constraint shift did not just produce more output. It surfaced a broader working method and made adjacent tool ideas easier to name.

## What The Current Projects Are Demonstrating

### Julia STL

`julia-stl` is still the clearest completed artifact in the repo.

Its most important lesson is not just that it worked. It is that the project improved once the question changed from literal reproduction to controlled modulation. That reframe turned a weaker build into a stronger one.

It remains proof that this repo can produce a finished, tasteful, demoable object.

### Decksmith

`decksmith` matters because it came from workflow pressure, not from a pre-written product thesis.

That is useful. The repo needed a better way to turn build thinking into presentations, and the tool now makes future updates, demos, and handoffs cheaper. It is a support project, but it is also part of the acceleration story.

### Topolski Explorer

`topolski-explorer` is where the temporary rule change becomes most visible.

The current build has now proved a little more than "this might work someday."

It has:

- a local raw corpus
- a preprocessing path
- a vision transcription path
- multiple retrieval lanes
- a local search UI over saved artifacts

That means `v1` is real.

What is still unresolved is trust. The current page-level pass is useful, but it is too coarse to confidently recover the internal structure of these mixed-layout pages. Small inserts, sidebars, footers, handwritten regions, and visual/text boundaries still need a more explicit representation.

So the live Topolski question is no longer "can this work at all?"

It is:

- how should the page be decomposed?
- what features can be certified?
- what observability is needed to trust the search results?

That is the right kind of unresolved.

### Throughline

`throughline` keeps clarifying a retrieval idea that feels bigger than the project itself: chunk size should not be hidden, and repeated relevance across span sizes is a useful signal.

### Trails

`trails` clarifies that search and synthesis are not the same thing. A useful system may need both a "where is it?" tool and a "how did this develop?" tool.

### Askme

`askme` names another useful inversion: a knowledge system is not only defined by what it contains, but also by what it noticeably lacks.

That is a meaningful expansion of the loop. Retrieval does not just answer questions; it can also generate the next good question.

### Signal

`signal` clarifies another boundary that matters: notes can stay freeform at capture time and still become structured later.

That helps protect the writing process while still making later reuse possible.

### Ladder

`ladder` still names a recurring truth: explanation is architecture.

If the larger system cannot explain itself to different audiences, then it is still structurally incomplete.

## Current Strategic Read

The current best framing is still not "one polished product."

It is:

- one finished artifact
- one workflow tool
- one ambitious research-system build in progress
- several adjacent tools and concepts that make the larger ecosystem easier to see

At the moment:

- flagship thesis project: `topolski-explorer`
- strongest finished artifact: `julia-stl`
- strongest acceleration tool: `decksmith`
- clearest new note system loop extensions: `askme` and `signal`

## What Seems Most Promising

The repo is starting to show how future projects could move faster.

The likely acceleration loop now looks something like this:

1. reframe the project early
2. identify the smallest legible artifact
3. preserve learnings during the build
4. make the explanation surface part of the implementation
5. let one project create structure for the next
6. use the growing toolset to tighten the next build loop

That loop is not fully formalized yet, but it is getting easier to see.

## Current Topolski Read

The Topolski path now has more shape than it did at the start of the hackathon.

A first local searchable slice is working, and the full current local corpus is now staged.
That matters.

The current build proved:

- the corpus can be made locally searchable
- vision models can pull enough signal for browsing and discovery
- multiple retrieval lanes are viable
- the project is worth continuing
- the dashboard and processing-matrix layer make the system easier to criticize honestly
- a representative evaluation subset is more useful than ad hoc spot checks

The current build did **not** prove:

- that small inserts, footers, and sidebars are being recovered reliably
- that handwritten versus typeset versus sketch boundaries are being isolated with confidence
- that one full-page pass is the right unit of understanding
- that the current search surface exposes enough evidence to fully trust results
- that the strongest vision model is automatically the right broad-corpus model under hackathon time pressure

So the rebuild thesis is now clearer:

- keep `v1` as a useful page-level retrieval baseline
- build `v2` around layout-aware extraction, feature manifests, and observability/dashboard surfaces
- treat model choice as part of pipeline design, not just a quality slider

## Current Topolski Operations Read

The Topolski project is now in a different phase than it was a few hours ago.

The local-prep phase is no longer the question:

- the full current local corpus has been staged
- the corpus currently stands at `138` items and `634` rendered pages
- the long-running uncertainty is now almost entirely at the API-processing layer

That changed one practical lesson very quickly:

- `gpt-4.1` gave a stronger page-reading baseline
- `gpt-4.1` also ran into hard request limits fast enough that it stopped being a realistic full-corpus model for the current window
- switching to `gpt-4.1-mini` was the right throughput decision for broad coverage, even if it is not the final certification model

That is a useful hackathon learning in its own right.

The build now has a more explicit split:

- broad-corpus pass: use the faster model to keep coverage moving
- exacting subset and difficult pages: keep the stronger model available for evaluation and region-aware rereads

That is a better use of credits than letting the strongest lane idle against caps.

The current concrete snapshot:

- `82 / 138` items transcribed
- `265 / 634` pages transcribed
- a matching public artifact export now exists for `82` items and `265` assessed pages

Another important shift happened alongside that operational split: the public shape of the
project got clearer.

The strongest read is no longer "pipeline skeleton for processing Topolski someday."

It is closer to:

- process the collection once
- save many layers of assessment
- publish a derived finding-aid layer
- rebuild the local search index from that layer
- use the resulting tool to point back to the original digital collection

That is a much stronger project.

This is still in process, but it is now usefully in process.

## Current Publishing Read

The Topolski project is now much closer to a public GitHub shape that says something real.

What the repo can now plausibly publish:

- code
- docs
- sanitized derived assessment JSON
- rebuild instructions for a local vector index

What it still keeps local:

- raw PDFs
- rendered page images
- crop images
- live Chroma state
- API keys and runtime data

That distinction is the right one. The public artifact is not the scan library. It is the
assessment library built on top of it.

## What Still Feels Open

- how explicitly the next hackathon update should foreground the meta-concept versus the individual builds
- how much of the Topolski `v2` direction can be made demoable in the next push
- whether `decksmith` should stay a supporting side-path in the story or be named as core acceleration infrastructure
- which of the newer stubs should be framed as "promising adjacent builds" versus "parts of the main ecosystem thesis"
- how to present the Topolski model split honestly: broad fast pass versus high-trust reread lane
- how much of the corpus can be pushed through tonight on `gpt-4.1-mini` before the next bottleneck appears

## The Agent-Build Loop Is Working

The pattern being tested here — write a detailed AGENTS.md, hand it to a task agent,
integrate the output — is producing usable results faster than building from scratch.

`trails` and `askme` went from concept to full project scaffolding (README, AGENTS,
presentation, learnings) in a single session. The AGENTS.md files were specific enough
that an agent could build without re-deciding design questions mid-run.

The lesson: the build brief is the product at this stage. A well-written AGENTS.md is
worth more than a half-built implementation. The implementation catches up; a vague brief
creates drift that is expensive to fix.

The acceleration loop is getting clearer:
1. design the thing in conversation
2. write a locked AGENTS.md that captures all decisions
3. hand to a task agent — get back working code
4. integrate on the private notes side

Short recursion, high throughput. The method scales.

## Sanitization Is Part Of The Build Convention

This repo is public. The projects draw on a private notes system. Keeping a clean
membrane between the two is not a one-time cleanup — it is an ongoing convention.

What was fixed in the current round:
- hardcoded private system paths (`~/Documents/Claude_Code/...`) replaced with `~/notes`
- real person names from the private notes index removed from examples and replaced with
  generic collaborator language
- personal project names from private notes (not represented in this repo) removed from
  examples — replaced with either hackathon project names or neutral placeholders
- runtime state files with absolute paths added to `.gitignore`
- institution-specific test queries in AGENTS files replaced with generic terms

The sanitization rules are now documented in `AGENTS.md` so future task agents will
follow the same conventions without needing to be told explicitly.

A quick re-check on the smaller repos this round did not turn up new raw-path leakage.
The remaining cleanup there is mostly wording quality, not obvious data exposure.

**The test**: any example in any documentation file should be legible on its own without
connecting back to the private system. If following the example would lead someone to the
private corpus, it is too specific.

## Monitoring Is Part Of The Build

Another lesson from the current Topolski run: a long agent or pipeline task needs a
deliberate monitoring surface, or else it just becomes background anxiety.

The repo now has a simple local check for the transcription run:

- `topolski-explorer/scripts/transcription_status.py`

That script reports:

- staged items and pages
- transcribed items and pages
- completion percentages
- the last successfully written item/page/time

This is not glamorous, but it is good build hygiene. If a process can run for hours, it
should expose whether it is making forward progress or just failing politely in the dark.

## Working Rule For The Next Stretch

Build toward the highest-leverage next update, not the most complete long-term architecture.

The near-term goal is not to make every project final.

The near-term goal is to make the next push obviously stronger:

- better demos
- clearer framing
- stronger handoff material
- sharper evidence that the build loop itself is improving
- a more visible ecosystem story around the newer stubs

If that works, the next update should feel much larger without needing to pretend this round was already the final form.
