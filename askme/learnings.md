# Learnings

This file tracks what turned out to matter while building Askme.

It is not a polished retrospective. It is the durable handoff layer for what the current
build clarified.

## Core Insight

The value of a knowledge system is not only what it contains.

It is also what it noticeably does not contain.

Making absence legible is its own retrieval move.

## Design Decisions That Held Up

**Specific prompts beat generic reflection.**
The useful prompts are the ones that name the actual missing thing: a stub, a person, an
open question, a domain, a dormant thread. The moment the wording drifts into lifestyle
app language, the tool gets weaker.

**The deterministic version was the right first build.**
Gap detection really is index math plus editorial templates. A model pass may improve the
surface later, but it was not needed to make the first useful version real.

**Five strategies, one ranking was the right shape.**
The product is not a menu of categories. It is one editorial surface where several kinds
of absence compete for attention.

**Inbox-style output still matters.**
A good prompt should be able to land somewhere durable, not just scroll by in a terminal.
Keeping `inbox` output in the core CLI was worth it.

## What The Build Clarified

### There Were No Real `.index` Fixtures In-Repo

The repo did not contain checked-in `stats.md`, `people.md`, or `blockouts.md` examples.

That forced the right implementation choice:

- make the parsers tolerant
- parse path-first, not format-first
- accept that metadata order may drift
- treat markdown tables and loose markdown lines as equally plausible

That is better than overfitting to a sample that may not match the real notes-side index.

### Corpus Mode Should Stay Additive

The index-only path is the right core demo.

Corpus mode adds real value for:

- `open_questions` extraction from companion JSON
- stub line-count verification for people
- richer domain and thread reads later

But the tool should still be useful when only `.index/` is available.

### Open Questions Are High Signal And Slightly Dangerous

They are often the best prompts because the user already articulated the gap themselves.

They also risk dominating the list if one session produced a lot of them. The weighting is
right for now, but future versions may need a per-file cap or dedupe pass.

### Domain Gaps Are The Noisiest Strategy

The domain heuristic is useful because it broadens the tool beyond named files and open
questions.

It is also the easiest place to get false positives. Some sparse domains are genuinely
fine. That means the domain lane should stay lower-weight and remain a place for future
suppression logic.

## 2026-04-19 Build Notes

- Askme now has a working local `v1` CLI in `askme.py`
- the parser layer was implemented to handle markdown tables and looser line formats
- malformed JSON is skipped silently, as intended
- the build was verified against a synthetic corpus fixture because no real public test
  corpus exists in this repo
- the missing example-output files are now an operational task, not a design task: they
  should be generated once a real `~/notes/.index` corpus is available locally

## What To Watch Next

- prompt duplication from multiple open questions in one companion file
- false positives in thread detection when token matching is too weak
- domain heuristics surfacing intentionally sparse areas
- whether the `people` strategy should broaden beyond `1-3` mentions in real usage
- whether output ranking feels editorially right once the tool runs against a large real corpus
