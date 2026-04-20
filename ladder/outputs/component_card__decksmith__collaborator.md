# Decksmith
*Presentation layer · proposal*

It connects the communication layer to a concrete presentation pipeline rather than leaving the final mile manual.

This is proposal, not a finished tool. It matters here because it shows where the system is trying to go next.

**What it is**: Generates editable presentation decks from structured content.

**The problem it solves**: Once the work is worth sharing, presentation becomes part of the build rather than a separate afterthought.

**A concrete example**: A Ladder overview could become the opening frame of an all-staff talk, while Decksmith would handle turning that structure into an editable deck instead of a one-off slide scramble.

**How it fits**:
- Uses Ladder output as structured source material.
- Sits downstream from the rest of the note-system ecosystem.
- Reinforces the idea that communication and presentation are distinct layers.

**Inputs**:
- structured content
- outlines
- explainer material from Ladder

**Outputs**:
- editable presentation decks
- speaker-ready slide structures

**Dependencies**:
- source content
- presentation templates

**Current limitations**:
- It is still a proposal rather than a finished tool
- Presentation structure is helpful, but it does not replace editorial judgment
- The boundary between authoring and deck generation still needs refinement

**Next rung for you**: Inspect where Ladder output should stop and Decksmith input should begin.
