# Presentation

## One-Sentence Version

This repo is becoming a fast-build workbench: a place where artifact builds, research systems, and explanation tools are being pushed together until a more reusable method falls out.

## Casual Update Framing

The strongest current tone is still not "behold, a finished empire."

It is more like:

"Of course I built it this way. I had a backlog, a temporary window for API-assisted experimentation, and a few projects that were useful enough to start revealing a broader pattern. Some of them are already demoable. Some are clearly mid-spinup. A few newer stubs make the larger system easier to see. The interesting part is that the build loop itself is getting faster and more legible."

That framing fits the repo better than pretending everything is equally mature.

## What The Audience Should Understand

- this is a real update, not just a plan
- there are already multiple concrete artifacts worth showing
- `topolski-explorer` is real and in process, not finished and not speculative
- `topolski-explorer` now has full current-corpus staging and a frozen demo-ready processing snapshot, not just a tiny proof-of-concept slice
- `topolski-explorer` now has `82` exported item assessments covering `265` pages, which makes the public story much stronger
- `topolski-explorer` is converging on a publishable derived finding-aid layer, not just a private experiment
- the larger concept is not one app, but a growing build ecosystem
- the supporting tooling is starting to matter because it speeds up the next wave
- the knowledge-work toolset has crossed from stubs into working local tools

## The Three Main Demonstration Anchors

### `julia-stl`

Show this as the proof that a project can go all the way from prompt energy to finished artifact.

It demonstrates:

- reframing
- iterative taste
- a tangible result

### `decksmith`

Show this as the meta-accelerator.

It demonstrates:

- explanation as build infrastructure
- reusable packaging of project communication
- a direct reduction in the cost of future updates and demos

### `topolski-explorer`

Show this as the most ambitious live research direction.

It demonstrates:

- the value of the temporary API-enabled constraint shift
- a real local `v1` pipeline and search surface over `1306` indexed chunks
- a real derived artifact library that can be shared without shipping the scans
- a clearer `v2` thesis than the project had when it started
- the practical need to split between broad-coverage models and high-trust reread models under real rate limits
- a path toward publishing the outputs of assessment rather than the source scans themselves

Keep the tone honest: the right phrase is "in process on a real path," not "finished system."

## The Knowledge-Work Toolset

Four of the eight projects now form a working local suite:

- `throughline`: multi-span semantic retrieval — indexes at three span sizes, surfaces files that stay relevant across all of them — working local v1
- `trails`: temporal archaeology — assembles a chronological arc of how a topic developed across years of notes — working local v1
- `askme`: gap detection — reads the corpus, finds what is thin, stale, or missing, returns ranked prompts — working local v1, seven strategies
- `signal`: post-capture structuring — extracts observations, decisions, questions, friction points, and follow-ups from a single note with line-level provenance — working local v1
- `ladder`: explanation layer — generates audience-specific explainers from structured YAML definitions

All four are integrated into a companion notes toolchain. The suite forms a loop: Signal structures the raw note. Throughline and Trails surface what is relevant and how it developed. Askme notices what is missing and asks for it.

These are not all equally mature, and they do not need to be. Their value is that together they make the larger knowledge-work loop visible and usable.

## The Build Method Is Part Of The Story

One thing worth naming explicitly: the method being used here is part of what is being demonstrated.

The pattern — design the project in conversation, write a locked AGENTS.md, hand to a task agent, integrate the output — is producing real scaffolding faster than solo builds. The repo is not just a set of projects. It is also a live test of how quickly a personal build system can move when explanation and tooling are built alongside the thing rather than after.

That is worth mentioning because it is honest, and because it makes the "why is this a hackathon submission" question easier to answer.

One more thing now belongs in that method story: monitoring.

The Topolski build became easier to reason about as soon as it had:

- a dashboard
- a processing matrix
- a transcription status script
- a public-safe export path for derived assessment artifacts

That is not busywork. It is part of what makes a long-running agentic build legible enough to steer.

## The Meta-Concept

The repo is circling a method for building faster:

1. find the real question behind the first project idea
2. reduce the build to the smallest legible artifact
3. preserve the learnings as durable handoff material
4. build an explanation layer early instead of late
5. let one project create tools that make the next one cheaper
6. use adjacent stubs to clarify the ecosystem before every part is fully built

That is the part worth naming in the update.

## Recommended Story Arc

1. Start with the honest premise: this is a workbench, not a polished suite.
2. Show `julia-stl` as proof of finish.
3. Show `decksmith` as the thing that emerged because explaining the work became part of the work.
4. Show `topolski-explorer` as the big swing that is now past the speculative phase but still actively in process.
   In the current push, emphasize that it is paused in a strong demo state rather than stalled.
5. Briefly introduce the knowledge-work toolset — four working tools — as the surrounding system becoming visible.
6. Connect everything to the broader idea: a personal build system for rapidly turning concepts into demos and then into better-scoped next builds.
7. Close on the next push: this round still has spinup energy, but it produced real scaffolding, monitoring surfaces, and a clearer flagship path, so the next update should be substantially sharper.

## Suggested Closing Tone

The closing note should feel casual, not ceremonial:

"This round did not produce one perfect flagship and call it done. It produced several real builds, a clearer thesis, and better infrastructure for the next run. The bigger system is easier to see now than it was a week ago. That is a good trade. The interesting part now is not whether to keep going. It is how much faster the next pass can move."
