# Learnings

## Core Learning

Throughline became clearer once it stopped being framed as "the correct chunk size for semantic search" and started being framed as "show what survives chunk-size changes."

That makes the project less about tuning one embedding pipeline and more about exposing retrieval stability as a signal in its own right.

## What The Simplification Clarified

- the strongest version is a local CLI tool, not a web app
- the core interaction is simple: point at a directory, build indices, query thereafter
- the project does not need note-system-specific language to be legible
- the demo value comes from the retrieval behavior, not from interface complexity

## Important Concept Learning

Chunk size is usually an invisible decision in embedding search, but it changes the shape of relevance in practice.

- small spans recover sharp local matches
- medium spans hold sentence-to-paragraph continuity
- larger spans preserve broader thematic context
- repeated hits across those spans are more interesting than hits from only one of them

That is the real insight behind the project.

## What Works About The Current Design

- three fixed spans are enough to create visible contrast without turning the tool into a research platform
- file-level grouping is a good v1 throughline rule because it keeps the concept legible
- word-count windows are sufficient for this prototype and avoid extra dependency complexity
- storing offsets now preserves a path toward better overlap logic later

## Product Learning

The useful product is not "another semantic search script."

It is a retrieval view that answers a different question:

"What stays relevant when I stop pretending one chunk size is the truth?"

That makes the tool explanatory as well as practical.

## Why CLI-First Helps

- it matches the real likely usage pattern better than a Flask demo
- it makes the tool easier to drop into existing local workflows
- it reduces build scope without weakening the core claim
- it forces the terminal output to make throughlines explicit instead of relying on layout gloss

## Constraint Learning

The project gets weaker if it tries to solve too many retrieval questions at once.

For this version, it is enough to:

- index plain text and markdown-like files from a chosen directory
- build three span indices
- reuse one query embedding across all spans
- show best-per-file results
- highlight files that recur across spans

That is already enough to demonstrate the idea.

## What Still Matters Later

- offset-overlap matching across span results
- document-level or heading-level baseline lanes
- richer corpus selection and ignore controls
- integration into a larger search workflow

Those are good extensions, but they are not required to prove the point now.

## Best Current Mental Model

Throughline is a multi-resolution semantic search tool.

It does not try to hide retrieval granularity. It turns that granularity into part of the evidence.
