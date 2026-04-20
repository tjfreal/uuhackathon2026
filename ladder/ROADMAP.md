# Ladder Roadmap

## Purpose

Build a documentation and explanation layer for the note-system ecosystem that can generate clear, audience-specific entry points into the system.

The build should stay grounded in the original "library as a ladder" idea: a people-first service model where the task is to help someone reach a next rung from where they actually are. In this project, that principle is being applied to note-system scaffolds, AI-mediated knowledge work, and explanation in the automation age.

## What We Set Out To Build

- a structured map of the system and its parts
- a small authoring format for audience-specific explainers
- reusable templates for different contexts
- a generator that turns system metadata into readable markdown outputs
- a tool that helps with workshops, classes, collaboration, and public framing
- a way to preserve the human lineage of the project so outputs do not become generic tool summaries

## Current Component Map

| Component | Current location | Status | Notes |
|-----------|------------------|--------|-------|
| Core concept | `ladder/README.md` | existing | strong framing, needs implementation shape |
| System map | external / not assembled | planned | needs a single source of truth for tools and relationships |
| Audience profiles | not built yet | planned | librarian, student, collaborator, self |
| Output templates | not built yet | planned | markdown-first is enough for the first version |
| Generator | not built yet | planned | can start as a simple script and stay local-first |
| Example explainers | not built yet | planned | should prove the concept fast |
| Lineage framing | partly captured in docs | in progress | should connect help-desk/service philosophy to current knowledge-work framing |

## Phases

### Phase 1: Define The Source Of Truth

- [ ] decide what object Ladder explains: one tool, the whole ecosystem, or both
- [ ] define a minimal schema for system components
- [ ] list required fields such as name, purpose, inputs, outputs, dependencies, and audience value
- [ ] choose where that schema should live
- [ ] decide which non-component framing fields are required to preserve the people-first lineage

### Phase 2: Audience Model

- [ ] define 3-4 target audiences
- [ ] list the main questions each audience needs answered first
- [ ] decide which concepts should be omitted or simplified per audience
- [ ] write one short exemplar paragraph for each audience
- [ ] define the "next rung" for each audience so outputs always invite a concrete next step

### Phase 3: Template Design

- [ ] design a markdown output template for a one-page explainer
- [ ] design a shorter "what is this?" template
- [ ] decide how examples and workflows are inserted
- [ ] decide whether tone adaptation is rule-based, prompt-based, or both
- [ ] decide where the meta layer appears: origin, values, and why explanation belongs inside the system

### Phase 4: Generator Build

- [ ] create a small local script that reads the system map and a target audience
- [ ] generate markdown output into a predictable directory
- [ ] support optional examples and workflow snippets
- [ ] keep the first version deterministic and inspectable

### Phase 5: Demo And Use

- [ ] generate one explainer for self
- [ ] generate one explainer for librarians
- [ ] generate one explainer for students or workshop use
- [ ] review whether the outputs actually help explain the ecosystem
- [ ] verify that the outputs still read like a people-first service philosophy carried into technical work

## Decisions To Lock

- what data structure represents the ecosystem
- which audiences to support first
- deterministic templates versus model-assisted rewriting
- whether Ladder belongs inside the core note-system repo or as a companion tool
- how the lineage and meta-framing are represented rather than left implicit

## First Hackathon Slice

If this gets a basic implementation during the hackathon, the smallest useful version is:

1. a hand-written JSON or YAML system map
2. two audience templates
3. a script that emits markdown explainers
4. one concrete example output that could be used in a talk or class

That is enough to prove the concept without overbuilding it.

For this repo specifically, keep the scope disciplined:

1. do not depend on `throughline`
2. do not treat `Route` as a built component
3. build around the components and framing that already belong to `Ladder`
