# Ladder
*Communication layer · in-progress*

It turns the proposal set into something inspectable enough to critique or extend.

This is in progress, not a finished tool. It matters here because it shows where the system is trying to go next.

**What it is**: Generates audience-aware explainers for the note-system ecosystem.

**The problem it solves**: A system that only makes sense to its builder stays trapped at the level of private tooling and cannot easily support teaching, collaboration, or institutional translation.

**A concrete example**: The same Surface component can be explained to library colleagues as a way of bringing back useful old notes, and to collaborators as a retrieval and explainability problem.

**How it fits**:
- Explains note-system and the proposal-layer tools.
- Feeds Decksmith with structured content that can become presentation material.
- Preserves the people-first lineage behind the system instead of leaving it implicit.

**Inputs**:
- structured component descriptions
- audience profiles
- ecosystem framing
- concrete examples from the actual system

**Outputs**:
- audience-specific explainers
- component cards
- overview documents for talks and workshops

**Dependencies**:
- YAML source-of-truth files
- markdown templates
- generator script

**Current limitations**:
- It is in progress and only covers a first slice of the ecosystem so far
- Good outputs still depend on honest, well-maintained source data
- Templates can enforce structure but not automatically guarantee good judgment

**Next rung for you**: Read the YAML and templates directly to see how the communication layer is encoded.
