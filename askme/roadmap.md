# Askme Roadmap

This is the project-level roadmap for Askme.

It is not a promise to turn the tool into a giant product. It is a map of the next useful
pushes now that the local `v1` exists.

## Current State

Askme now has:

- a working local CLI
- five implemented gap strategies
- weighted ranking across strategies
- text, JSON, and inbox output formats
- index-only operation with optional corpus enrichment

That is enough for a real first pass. The next work is about signal quality and loop
closure, not basic existence.

## Immediate Priority

### 1. Run It Against A Real Corpus

The most important next step is not more abstraction. It is real use.

That means:

- run Askme against a live `~/notes/.index`
- generate the committed example outputs in `outputs/`
- inspect whether the top prompts actually feel worth answering

The ranking only becomes real once it has to survive contact with an actual corpus.

### 2. Tighten Prompt Quality

The current prompts are good enough for `v1`, but some strategies will need editorial
refinement once they hit real notes.

Most likely pressure points:

- open-question overload from a single session
- thread prompts that are technically correct but too vague
- domain prompts that surface sparse-but-unimportant areas

### 3. Improve Thread And Domain Precision

Those are the noisiest strategies in the current build.

The next useful pass is likely:

- better thread reappearance detection than token matching against paths
- stronger domain heuristics
- lightweight suppression controls for known low-value gaps

## Secondary Priority

### Prompt Deduplication

If the same gap keeps surfacing every run, the tool will get ignored.

Useful future work:

- do not repeat the same prompt every day
- suppress very similar prompts in the same run
- remember which prompts were recently shown

### Feedback Loop

Askme gets stronger if it can learn which prompts were answered and which were skipped.

That does not need to be fancy at first. Even a lightweight response-tracking convention
would improve future ranking decisions.

### CLI Integration

The obvious long-term fit is integration into a companion notes CLI.

That belongs on the notes-side toolchain, but the workflow is already clear:

1. generate prompts
2. choose one
3. answer it in an editor
4. route the response back into the corpus

## Not The Priority Yet

- model-assisted rewriting
- trying to make every strategy equally sophisticated
- turning Askme into a service or app
- premature UI work beyond the CLI and inbox path

The right next step is to make the prompts sharper on real notes, not to broaden the surface area.
