# UU Hackathon 2026 — Agent Brief

Read [README.md](README.md), [learnings.md](learnings.md), and [presentation.md](presentation.md) before doing repo-level work.

This file is written for the actual audience here: future me, delegated task agents, and the small committee behind the curtain. Yes, it is still just me. No, the committee has not become easier to impress.

## What This Repo Is

This is a hackathon workbench for a cluster of related builds.

Do not treat it like a single-product repo that merely happens to contain some extras.
Do not force every subproject into the same maturity level.
Do treat it as a fast-moving ecosystem where artifact builds, research systems, and explanation tools are informing each other.

## Current Repo Thesis

The important thing being built here is not only the individual projects.

The more interesting thing is a method:

- reframe quickly
- find the smallest legible artifact
- preserve learnings as durable handoff material
- build explanation infrastructure alongside the thing
- let one project reduce the cost of the next one
- let newer stubs clarify the ecosystem before every piece is fully built

If a task helps that method become clearer or faster, it is probably aligned.

## Current Priority Read

- `topolski-explorer` is the main thesis project right now, but it should be described as in process
- `julia-stl` is the strongest proof that the work can land in finished form
- `decksmith` is the clearest tool that makes future updates and demos cheaper
- `throughline`, `trails`, `askme`, `signal`, and `ladder` matter because they make the larger system easier to see
- `trails` and `askme` now have full project scaffolding: README, AGENTS, presentation, and learnings files — treat them as first-class projects, not stubs
- `topolski-explorer` now has a fully staged current corpus and an active broad transcription run; treat the operations layer as real project state, not just background plumbing
- `topolski-explorer` now also has an emerging public artifact layer; treat exported assessment JSON as part of the project output, not merely packaging residue
- current broad-pass snapshot: `82 / 138` items and `265 / 634` pages transcribed, with a matching public artifact export layer

## How To Behave In This Repo

- preserve the difference between finished artifacts, working tools, in-process builds, and proposal-level concepts
- prefer legibility over inflated scope
- keep outputs and learnings worth reusing later
- do not write as if every project must sound equally complete
- do not erase the "spinup" feeling if it is the honest read
- do not confuse early momentum with failure just because the full shape is not here yet
- when summarizing `topolski-explorer`, keep it on the "real local `v1`, sharper `v2` in process" framing
- when summarizing the current Topolski run, note the model split honestly: `gpt-4.1-mini` for broad corpus throughput, stronger models reserved for exacting rereads and evaluation
- if a long-running process exists, expose a monitoring surface instead of assuming the user will infer progress from silence
- when discussing GitHub/public-sharing shape, distinguish sharply between raw corpus assets, live local runtime data, and publishable derived assessment artifacts
- when summarizing smaller sibling repos, assume they are mostly sanitized already unless a concrete leak is found; avoid inventing drama where there is only wording cleanup left

## What A Good Repo-Level Update Should Sound Like

The voice should be casual, grounded, and slightly amused by the fact that this is obviously becoming a bigger system than originally advertised.

Good update tone:

- some things are already real
- some things are promising for concrete reasons
- one major project is clearly in process on a real path
- the larger pattern is getting easier to name
- the next push should be materially stronger because the tooling and framing are catching up

Bad update tone:

- pretending the repo is a finished platform
- flattening all projects into marketing copy
- hiding uncertainty that is actually informative
- overselling newer stubs as if they are already fully built

## Preferred Framing For The Next Push

Use a structure like this:

1. Here is what is real now.
2. Here is what changed in the current round.
3. Here is the meta-concept the projects and stubs are starting to demonstrate.
4. Here is why the next update should be much stronger.

Repo-level roadmap now lives in [roadmap.md](roadmap.md). Consult it before writing update copy that implies all projects are moving at the same rate.

## Notes For Task Agents

- start from the existing learnings files instead of re-deriving the strategy
- preserve project-specific language when it is doing real conceptual work
- when in doubt, sharpen the build loop rather than broadening the scope
- if a task improves handoff, demo quality, or future build speed, it is probably high leverage
- reflect the expanded repo accurately: `askme`, `trails`, and `signal` now matter at the root-story level
- treat monitoring scripts, dashboards, and progress surfaces as legitimate build artifacts when a project has multi-hour background work
- do not describe a blocked model lane as "quiet progress" if the logs show rate-limit failure; surface the bottleneck and the fallback clearly

## Privacy and Sanitization Conventions

This repo is public or approaching public. The projects are built on top of a private personal
knowledge system. The two must not bleed into each other.

**Follow these rules in any file you write or edit:**

**Paths**: Use `~/notes` as the generic corpus path in examples and documentation.
Never use actual system paths like `~/Documents/Claude_Code/note-system` or anything
containing a username. If a project produces a runtime state file with an absolute path
baked in (e.g., `.throughline_state.json`), that file belongs in `.gitignore`.

**People names**: Do not use real names from a private people index as examples in code
or documentation. Use `"a collaborator"`, `"a colleague"`, or placeholder filenames like
`collaborator-name.md`. The same applies to stub prompts — "What do you know about
this person?" not "What do you know about [real name]?"

**Personal project names**: Only reference project names that are represented in this
hackathon repo. Generic concepts from a private notes system (dormant side projects,
personal experiments not in this repo) should not appear as named examples. If an
example topic is needed, use a project from this repo (`julia vase`, `3d scanning`,
`throughline`) or a neutral placeholder (`project-name`, `knowledge-building`).

**Institution names**: Avoid naming specific institutions, spaces, or employers in
examples and test queries. Use generic terms (`research-lab`, `knowledge-work`) instead.

**The membrane**: The private notes system is the source of real corpus examples and
demo data. But documentation, AGENTS.md files, and example outputs should stand on their
own without pointing back to it. If a reader could use the example to locate or identify
the private system, the example is too specific.

## Current Working Joke

If this starts to look like a small research lab with suspiciously good slide tooling and an increasingly opinionated note ecosystem, that is because absolutely nothing unusual is happening and everyone should remain calm.
