# Presentation

Signal extracts reusable structure from freeform notes without asking the writer to give
up freeform writing.

That is the core pitch.

- you write the note the way you actually think
- later, Signal pulls out the parts that are likely to matter again
- the note remains the source
- the companion directory stores the derived artifacts

The important design choice is what Signal does **not** do.

It does not treat attachments, sidecars, or other metadata files as equal sources.
It reads the markdown note only. That keeps the authority of the note intact and makes
the derived outputs easier to trust.

The current state is no longer just conceptual.

There is now a working local `v1`:

- a standalone `signal.py` CLI
- deterministic extraction over one note at a time
- `signals.json`
- `signals_review.md`

So the right framing is not "finished system."

It is: a real first pass that is small, inspectable, and worth testing on actual notes.

The cleanest demo is simple:

1. start with one long daily note
2. run Signal on it
3. show the extracted observations, questions, friction points, and follow-ups
4. show that each one points back to the original lines in the note

The tool sits in an interesting place in the larger note-system:

- not capture
- not retrieval
- not quite sensemaking

It is a post-capture structuring layer.

The point is to make messy notes more reusable later without forcing the original note
into a rigid template up front. That is why it belongs here.

One thing to keep honest in the presentation:

the repo does not contain a public daily-note demo file, because the notes system is
private. The tool has been verified on real daily notes — outputs are clean and the
line-level provenance is genuinely useful — but the public demo path is still a
representative synthetic note or a brief inline example. The tool's honesty comes from
the output, not the input.
