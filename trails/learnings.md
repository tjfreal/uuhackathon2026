# Learnings

This file tracks what changed while Trails moved from concept to a working local `v1`.

It is not a polished retrospective. It is the running record of what the build taught once
the tool existed as code instead of only as a spec.

## Core Insight

The most useful output of a knowledge system is not a search result — it is an arc.
Search tells you where something is. A timeline tells you how it got there.
These are different questions that deserve different tools.

## Core Learning

Trails clarified that search and synthesis are not the same thing.

Search answers "where is this?"
Trails answers "how did this develop?"

Those are different enough that they deserve separate tools and separate output shapes.

## What Held Up From The Initial Design

**Date extraction should stay opportunistic, not required.**
That held up. Filename, frontmatter, and content scans are enough to make a useful first pass
without pretending every file has clean metadata.

**One excerpt per file is the right default.**
The timeline gets noisy fast if one file can contribute several moments. Treating the file as
the unit of memory keeps the arc legible.

**Keyword-first was the right build order.**
The stdlib path made the tool testable immediately. Embedding mode works better as an upgrade
path than as a requirement.

**The output really is the artifact.**
The markdown timeline is not disposable terminal chatter. It is the useful thing Trails makes.

## Build Notes

## 2026-04-19

**Embedding indices need file-relative identity, not absolute-path assumptions.**
The useful shared contract with adjacent retrieval tools is the corpus-relative file path in
`chunks.jsonl`. Trails should treat that as the stable key and only fall back to basename
matching when necessary.

**Near-duplicate detection can get noisy fast if it is too cheap.**
A simplistic character-overlap heuristic collapsed distinct excerpts during early testing.
Even a lightweight similarity pass needs to preserve clearly different timeline moments.

**Content-scan dates are best treated as approximate chronology, not exact timestamps.**
Even when the body contains a full ISO date, the story value is usually "this file points to
that period" rather than "this note definitively belongs on that exact day." Rendering and
sorting should preserve that softer confidence.

**Markdown cleanup is a real part of excerpt quality.**
The first pass at passage extraction was technically correct but too noisy. Date lines,
heading markers, and formatting debris can make an excerpt look worse than the underlying
corpus actually is.

**A clean fallback path matters more than clever optional features.**
Narrative mode and embedding mode are both useful, but only if they degrade without drama.
For this kind of tool, a good warning plus a readable list output is better than a hard stop.

## What Still Looks Worth Watching

- excerpt quality on messy real corpora
- duplicate handling between near-identical source files
- how often content-scan dates are useful versus misleading
- whether narrative mode adds genuine synthesis or just polish
