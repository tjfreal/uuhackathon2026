# Presentation

Askme flips the direction of capture.

A personal notes system usually waits for the user to decide what to write next.
Askme reads what is already there, notices what is thin, stale, unresolved, or missing,
and asks for that instead.

That makes it a useful extension of the larger note system loop:

- capture
- structure
- retrieve
- synthesize
- explain
- notice what is missing
- feed that back into capture

The important part is that the prompts are grounded in real gaps.

Not:
"write something reflective."

Instead:

- a stub that has been sitting untouched for four months
- an open question left behind in a March session
- a collaborator who appears in the notes but barely exists in their own stub
- a thread that was important enough to flag, then never obviously revisited
- a domain that looks suspiciously under-described
- an inbox item that landed weeks ago and has not moved
- a person who keeps showing up in recent notes but has no file at all yet

That gives Askme a better tone than a journaling app or a generic prompt generator. It
should feel like a thoughtful collaborator who has actually read the notes.

The current build matters because it is already real in a small, legible way:

- local CLI
- no required external packages
- index-first core
- optional richer corpus reads
- ranked prompt output in text, JSON, or inbox-ready markdown

So Askme is not a giant platform claim.

It is a sharp little loop-closer.

The corpus reads itself, identifies one of its own open edges, and asks to be extended.
No model required in the core version. The intelligence is in the index.
