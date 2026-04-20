# Signals
*Organization layer · proposal*

It treats extraction as a bridge between unstructured writing and more inspectable downstream workflows.

This is proposal, not a finished tool. It matters here because it shows where the system is trying to go next.

**What it is**: Extracts structured observations from freeform prose so notes become more usable over time.

**The problem it solves**: Freeform notes are flexible, but important observations, decisions, and recurring patterns are easy to leave buried inside paragraphs.

**A concrete example**: A long daily note about a project might contain one clear observation about what keeps slowing the work down; Signals would help pull that out so it does not stay hidden in the middle of the prose.

**How it fits**:
- Builds on the freeform corpus preserved by note-system.
- Can improve retrieval and explanation by making observations easier to reference.
- Gives Ladder a concrete organization story beyond simple tagging.

**Inputs**:
- local note corpus
- freeform prose
- repeated patterns in notes

**Outputs**:
- extracted observations or signals
- structured summaries for later reuse

**Dependencies**:
- note-system corpus
- parsing over note text

**Current limitations**:
- It is still a proposal rather than a finished tool
- Extraction can oversimplify nuanced prose
- Structured output is only useful if it stays tied back to the original note

**Next rung for you**: Decide whether Signals should emit structured data, lightweight summaries, or both.
