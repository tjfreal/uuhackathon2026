# Surface
*Retrieval layer · proposal*

It makes retrieval proactive rather than query-only, which raises questions about scoring, explainability, and trust.

This is proposal, not a finished tool. It matters here because it shows where the system is trying to go next.

**What it is**: Resurfaces older notes when they are likely to be relevant again.

**The problem it solves**: Notes get captured and forgotten. The archive becomes a graveyard unless something brings useful material back at the right time.

**A concrete example**: During a weekly review, Surface could show the user a note from two years ago about library service that suddenly matters again while he is designing Ladder.

**How it fits**:
- Builds on the note-system corpus and review habit.
- Can feed Bridge by making candidate notes visible again.
- Gives Ladder a concrete retrieval story to explain.

**Inputs**:
- local note corpus
- recent daily notes
- semantic similarity signals
- review context

**Outputs**:
- ranked list of notes worth revisiting
- candidate resurfacing digest for review

**Dependencies**:
- note-system corpus
- parsing and embedding passes over local notes

**Current limitations**:
- It is still a proposal rather than a finished tool
- Relevance scoring can be persuasive without being correct
- A resurfaced note still needs human judgment to matter

**Next rung for you**: Start with the ranking logic and the question of how Surface should explain why something was resurfaced.
