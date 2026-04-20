# Learnings

_Updated as the build progresses. Start with design decisions; add build lessons as they emerge._

## Core Insight

Freeform notes are most valuable when they can stay freeform at capture time and become
structured later.

That is the job of `signal`.

The source of the signal should remain the note itself. The system can derive artifacts,
but it should not pretend that sidecar files or attachment folders are the primary record
of thought. The markdown note stays authoritative.

## Design Decisions Made Before Building

**The note is the only source.**
`signal` reads one `.md` file at a time. It does not mine the companion directory for
metadata, OCR text, attachments, or auxiliary artifacts. That keeps the epistemic boundary
clean: notes are source, companion directories hold derived outputs.

**Outputs belong in the companion directory.**
If the input note is `2026-04-19.md`, derived outputs should live in the sibling
directory `2026-04-19/`. That matches existing note-system conventions without turning
that directory into a second source of truth.

**Deterministic first, model-assisted later.**
The strongest first version is not an all-knowing extractor. It is a simple, auditable
tool that can recover obvious observations, decisions, questions, friction points, and
follow-ups from real notes. The first value is inspectability.

**Signals must preserve provenance.**
An extracted signal is only useful if it points back to the original note clearly enough
to be checked. File path, heading context, line range, and original text span matter more
than fancy classification in v1.

**Review is part of the product, not a cleanup phase.**
Signals are interpretations of notes, not facts. The output should make review easy:
accept, reject, retag, rewrite, or ignore. If the review loop is weak, the extracted
structure will not be trusted.

**The first downstream payoff should be small and legible.**
Do not start by wiring Signals into every other proposal. The first useful proof is that
a messy daily note can produce a short reviewable artifact that is easier to reuse later.

## Working Definition Of A Signal

For v1, a signal is a short extracted unit that captures one thing from a note that the
future self would plausibly want back.

Candidate types:

- `observation`
- `decision`
- `question`
- `friction`
- `follow_up`

These are not eternal categories. They are just a strong enough starting grid to test
whether post-hoc structure improves reuse.

## What To Watch For During Build

- Over-extraction: too many weak signals will make the review artifact noisier than the note
- False certainty: extracted prose can sound more settled than the original note actually was
- Weak provenance: if source spans are vague, the tool becomes hard to trust
- Heading/line parsing edge cases in real markdown notes
- Output creep: derived artifacts should not start acting like a replacement note format

## 2026-04-19

The first useful version of `signal.py` now exists.

That matters less because the code is large or sophisticated and more because the project
has crossed the line from idea to inspectable tool. The contract is now concrete:

- `python signal.py extract <note-path>`
- one markdown note in
- one companion directory out
- `signals.json` plus `signals_review.md`

## What The First Implementation Confirmed

**Line-based extraction was the right first cut.**
The locked question in the roadmap was whether `v1` should be line-based, sentence-based,
or paragraph-based. Line-based with a little continuation logic was the correct answer.
It is easy to audit, easy to explain, and good enough to recover obvious cues without
pretending the tool understands more than it does.

**Absolute paths need to be handled carefully.**
Using a canonicalized path that resolves symlinks produced awkward `/private/tmp/...`
provenance during testing. Switching to a plain absolute path kept provenance clean
without changing the trust model. That is a small implementation detail, but it affects
how legible the outputs feel.

**The review artifact really is part of the product.**
The JSON is useful as a machine-readable output, but the markdown review file is the
thing that makes the extraction feel worth keeping. Without that file, `signal` would be
correct but less usable.

**There is no honest in-repo daily-note demo yet.**
The repo mostly contains project docs, briefs, and explainers. That means the first pass
was verified against synthetic representative notes rather than a genuine public daily
note fixture. That is the honest read, and it should stay explicit until a real shareable
example exists.

## What Still Looks Fragile

- tables and code blocks may still produce weak matches under simple heading parsing
- rhetorical questions and generic words like `problem` can create false positives
- multiline paragraphs are intentionally under-modeled in `v1`
- the real test is still a messy actual note, not a clean synthetic fixture

## Keeping This File Current

Add a dated entry when:

- A design assumption turns out to be wrong
- The extraction schema changes materially
- A review workflow turns out to be better or worse than expected
- A real note produces a surprisingly good or surprisingly bad result
- The tool starts to suggest a broader note-system pattern worth carrying into other projects
