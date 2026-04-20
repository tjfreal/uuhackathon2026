# Bridge
*Retrieval layer · proposal*

It turns semantic similarity into an explicit bridge-making workflow, which makes evaluation criteria and false positives important.

This is proposal, not a finished tool. It matters here because it shows where the system is trying to go next.

**What it is**: Detects meaningful cross-domain connections across the corpus.

**The problem it solves**: Some of the most useful ideas come from noticing that two things belong together, but those links are easy to miss when notes sit in separate domains.

**A concrete example**: A note about help-desk service philosophy and a note about note-system tooling might look unrelated until Bridge highlights the shared idea of a reachable next rung.

**How it fits**:
- Often starts from notes that Surface makes visible again.
- Uses the same underlying corpus as note-system.
- Gives Ladder a way to explain synthesis as a system behavior.

**Inputs**:
- local note corpus
- semantic similarity signals
- note metadata
- resurfaced candidates from tools like Surface

**Outputs**:
- suggested cross-domain note pairs
- candidate bridges worth reviewing or linking

**Dependencies**:
- note-system corpus
- retrieval signals

**Current limitations**:
- It is still a proposal rather than a finished tool
- Similarity alone does not guarantee a meaningful connection
- Too many weak bridges would erode trust quickly

**Next rung for you**: Pressure-test what counts as a meaningful bridge versus a merely similar phrase.
