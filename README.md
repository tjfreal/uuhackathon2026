# UU Hackathon 2026

This repository is a live hackathon workbench.

It is not one polished product and it is not pretending to be. It is a cluster of builds, proposal stubs, reframes, and support tools that together show a working method getting sharper in public.

The current state:

- several things are demonstrably real and running
- the knowledge-work toolset has moved from scaffolded stubs to a working local suite
- the most interesting result may be the build pattern emerging across all of them

There is still some spinup energy in the repo. That is fine. The repo reads best as: here are the current demos, here are the newer stubs that extend the system horizon, and here is why the next push could be materially stronger.

## Current Read

The strongest repo-level story right now is not "look at a finished suite."

It is:

- one finished artifact that proves taste and iteration can land
- one workflow tool that makes future project communication cheaper
- one ambitious research build that is clearly real but still in process
- several adjacent tools and concepts that are starting to look like parts of a larger knowledge-work ecosystem

That maps roughly to:

- [julia-stl](julia-stl): the strongest finished artifact
- [decksmith](decksmith): the clearest workflow/tooling win
- [topolski-explorer](topolski-explorer): the biggest research-system swing, currently mid-build
- [throughline](throughline): multi-span semantic retrieval with throughline detection — working local v1
- [trails](trails): temporal archaeology — reconstruct how a topic developed across a corpus — working local v1
- [askme](askme): gap detector that turns missing knowledge into prompts — working local v1, 7 strategies
- [signal](signal): post-capture signal extraction from freeform notes — working local v1
- [ladder](ladder): an explanation layer for making the whole ecosystem legible

## What Seems To Be Happening

Across the projects, the same pattern keeps showing up:

- the project gets better when the real question is found
- the strongest version is usually smaller and more legible than the first imagined version
- outputs become more useful when they are treated as durable artifacts instead of disposable demos
- explanation keeps turning out to be part of the build, not a separate cleanup phase
- one project keeps creating leverage for the next one

That may be the most important hackathon result so far.

The repo is starting to look less like a pile of disconnected experiments and more like an early personal build system for turning half-formed ideas into explainable tools quickly.

## What Exists Right Now

### `julia-stl`

A finished artifact build that turned "make a Julia set STL" into the stronger question: "use Julia structure as a deformation language for a vase."

This one already has the full shape of a real project:

- a working generator
- a browser playground
- rendered outputs
- a successful physical print

### `decksmith`

A workflow tool that came out of pressure from the work itself: if the projects are worth showing, presentation is part of the build.

Decksmith now has:

- a reusable source format
- a Keynote generation path
- PowerPoint export
- multiple working example decks

This matters because it lowers the cost of the next update, the next demo, and the next project explanation.

### `topolski-explorer`

The boldest current build, and still very much in process.

This project is using API-assisted vision and retrieval over the Topolski Chronicles corpus. The current read is no longer speculative: there is a real local pipeline, a real local index, and a real local search surface.

The current status is best described as:

- `v1` page-level semantic retrieval is working
- the broad corpus pass is actively moving: `82 / 138` items and `265 / 634` pages have now been transcribed
- the local artifact path is real
- a public-safe derived artifact layer now exists, so the project is no longer only a private runtime demo
- the project is worth continuing
- `v2` layout-aware extraction, feature certification, and observability are the next serious layer

So this is not finished, but it is also not hand-wavy. The path is real; the sharper version is what is now in process.

## The Knowledge-Work Toolset

Four of the eight projects form a working local suite around a personal notes corpus:

### `throughline`

Multi-span semantic retrieval. Indexes a corpus at three span sizes (≈25, 75, 200 tokens), queries all three in one pass, and surfaces files that show up across multiple span sizes as throughlines. Working local v1 — `index`, `query`, and `list-indices` commands.

### `trails`

Temporal archaeology. Given a topic, assembles a chronological arc across all matching files — dates from filenames, frontmatter, and content. Keyword and embedding search modes. Working local v1.

### `askme`

Gap detection. Reads corpus index files and surfaces what is missing, stale, or unresolved as ranked prompts. Seven strategies: sparse stubs, open questions, thin people stubs, dormant threads, sparse domains, unprocessed inbox items, and people mentioned without stubs. Working local v1.

### `signal`

Post-capture structuring. Reads a single markdown note and extracts typed signals — observations, decisions, questions, friction points, follow-ups — with line-level provenance. Writes `signals.json` and `signals_review.md` into the note's companion directory. Working local v1.

### `ladder`

Explanation layer. Generates audience-specific explainers for the ecosystem from YAML component and audience definitions. If the system cannot explain itself, it is incomplete.

Together these form a knowledge-work loop:

- capture → `signal` structures the raw note
- retrieve → `throughline` and `trails` surface what is relevant and how it developed
- notice what is missing → `askme` asks for it
- feed answers back into capture

## A Note On Privacy Conventions

This repo is public. The projects are built on top of a private personal notes system.

Any documentation, example, or test query in this repo should stand on its own without
pointing back to that system. The conventions enforced across all project files:

- corpus paths use `~/notes` as the generic placeholder, not actual system paths
- real person names from the private notes index do not appear as examples — use generic
  collaborator language instead
- personal project names not represented in this repo do not appear as named examples
- runtime state files with absolute paths are gitignored

See `AGENTS.md` for the full sanitization rules. Any new project file should follow these
conventions from the start.

## How To Read The Repo

If you want the current flagship direction:

1. [topolski-explorer/README.md](topolski-explorer/README.md)
2. [topolski-explorer/learnings.md](topolski-explorer/learnings.md)
3. [topolski-explorer/ROADMAP.md](topolski-explorer/ROADMAP.md)

If you want the strongest finished build:

1. [julia-stl/README.md](julia-stl/README.md)
2. [julia-stl/learnings.md](julia-stl/learnings.md)

If you want the clearest "this will make the next projects faster" tool:

1. [decksmith/README.md](decksmith/README.md)
2. [decksmith/learnings.md](decksmith/learnings.md)

If you want the emerging knowledge-work toolset direction:

1. [throughline/README.md](throughline/README.md)
2. [trails/README.md](trails/README.md)
3. [askme/README.md](askme/README.md)
4. [signal/presentation.md](signal/presentation.md)
5. [ladder/README.md](ladder/README.md)

If you want the repo-level process and update framing:

1. [learnings.md](learnings.md)
2. [presentation.md](presentation.md)
3. [AGENTS.md](AGENTS.md)

## Best Current Framing For The Next Push

The next hackathon update does not need to oversell polish.

It can say, pretty casually and pretty truthfully:

- several things are now demonstrably real
- the larger build direction is getting clearer
- a few more project stubs now make the larger ecosystem easier to see
- `topolski-explorer` is still in process, but on a real path
- the repo is converging on a repeatable way to build faster
- the next update should be much stronger because the tooling, framing, and adjacent concepts are catching up to the main ideas

That is enough.
