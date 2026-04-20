# Presentation

## One-Sentence Version

Throughline is a local search tool that runs the same query across multiple chunk sizes and highlights the files that remain relevant across them.

## Short Story Arc

The strongest presentation sequence is:

1. explain the normal hidden problem in semantic search: chunk size changes results
2. show the three span idea: local, medium, broad
3. show one query returning three different result sets
4. show the repeated files as throughlines
5. explain why those repeated hits are the point

## What The Audience Should Understand

- embedding search does not have one neutral chunk size
- relevance that persists across chunk sizes is more trustworthy
- the project is useful because it makes retrieval behavior inspectable
- the interface can stay simple because the idea itself is strong

## Framing The Work

This is best presented as a retrieval-quality tool rather than a generic search interface.

The technical move is not just "build three indices." The technical move is to treat agreement across indices as a meaningful ranking signal.

## The Real Technical Story

The audience does not need every implementation detail. They need the throughline:

- choose a directory of text
- build three overlapping span indices
- embed the query once
- score each span independently
- collapse to the best hit per file per span
- highlight files that recur across spans

That is enough to make the claim concrete.

## Why The CLI Direction Works

The command-line version is not a compromise. It is closer to the real use case.

It shows that the project is a tool, not just a demo surface. It also keeps the focus on retrieval behavior instead of presentation chrome.

## Recommended Demo Structure

1. Run `throughline index` on a text directory
2. Run a narrow query to show sharp small-span behavior
3. Run a broader conceptual query to show large-span behavior
4. Point out the files that appear in `2/3` or `3/3` spans
5. Close on the claim that stable relevance across chunk sizes is the useful new signal

## Closing Message

The strongest conclusion is not "this searches text in three ways."

It is: "this makes chunking visible and turns cross-span agreement into evidence."
