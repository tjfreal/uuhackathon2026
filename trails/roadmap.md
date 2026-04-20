# Trails Roadmap

## Purpose

Build a local tool that reconstructs the history of a topic from a corpus of text files and
turns scattered mentions into one legible arc.

## What We Set Out To Build

- a standalone CLI over arbitrary text corpora
- opportunistic date extraction instead of strict metadata requirements
- one useful excerpt per file, sorted into chronology
- optional embedding search when an index already exists
- optional narrative output when a model SDK is available
- durable outputs that are worth keeping as artifacts

## Current State

Real local `v1` exists in `trails.py`.

It currently has:

- recursive text-file discovery
- keyword search with AND logic across query terms
- optional embedding-mode retrieval from `chunks.jsonl`
- date extraction from filename, frontmatter, and inline ISO dates
- excerpt extraction with markdown cleanup
- deduplication and chronological assembly
- list, json, and narrative output modes
- clean fallback behavior when optional dependencies are missing

## Phases

### Phase 1: Real-Corpus Demo Pass

- [ ] run Trails on a real local corpus using sanitized public examples
- [ ] generate committed demo outputs in `outputs/`
- [ ] check excerpt quality on genuinely messy notes
- [ ] confirm the date ordering feels trustworthy in realistic cases

Minimum success condition:
at least a few timeline outputs that are worth showing without apologizing for them.

### Phase 2: Output Refinement

- [ ] improve markdown cleanup for frontmatter-heavy files
- [ ] reduce weak excerpts when the match line is structurally noisy
- [ ] make duplicate handling more robust for near-identical companion files
- [ ] decide whether content-scan dates need clearer labeling in list output

Minimum success condition:
the output should read like a timeline, not like ripped fragments from a parser.

### Phase 3: Integration Polish

- [ ] decide whether CLI wrapper integration should stay a future target or become a near-term priority
- [ ] define the resting place for saved timeline artifacts
- [ ] check whether Trails outputs should be indexed back into the larger system by default
- [ ] make sure the CLI surface stays small while integration grows

Minimum success condition:
Trails fits the surrounding tool loop without becoming less portable on its own.

### Phase 4: Optional Upgrade Path

- [ ] evaluate whether embedding mode should support more than one adjacent index schema
- [ ] improve narrative mode prompts so the prose adds synthesis instead of paraphrase
- [ ] decide whether domain filtering needs richer path-selection behavior
- [ ] consider a future diff mode or comparison mode only if the core arc output is already strong

## Decisions That Now Look Mostly Locked

- keep the tool standalone and CLI-first
- keep stdlib-only keyword mode as the baseline
- keep one excerpt per file as the default unit
- keep optional features optional instead of turning them into runtime requirements

## What Not To Pretend Yet

- that narrative mode is the main value
- that every corpus will produce clean date ordering without edge cases
- that embedding mode is more important than strong default keyword behavior
- that Trails is already fully integrated into the larger system

## Success Criteria For The Next Push

- the repo has a few committed outputs that prove the concept on a real corpus
- the README reads as a working tool, not a future tool
- the examples stay within the repo's public sanitization conventions
- Trails is clearly legible as the synthesis/history layer beside Throughline
