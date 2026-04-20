# Ladder — Agent Build Brief

Read README.md, ROADMAP.md, query.md, and response.md before starting. This file locks
all open decisions from the ROADMAP so you can build without re-deciding mid-session.

---

## What You Are Building

A CLI tool that generates audience-specific explainers for the note-system ecosystem.
Source of truth lives in YAML. Templates are markdown. Generator is a Python script.
Output is committed markdown files.

The claim: the same system explained for a library colleague and for a technical
collaborator should feel like two genuinely different entry points — not the same text
with different fonts. The contrast is what proves the concept.

The demo: generate a component card for Surface written for all-staff, then generate the
same component card written for a collaborator. Show both side by side.

---

## Directory Layout To Build

```
ladder/
├── data/
│   ├── ecosystem.yaml              ← one-page overview content
│   ├── components/                 ← one YAML file per component
│   │   ├── note-system.yaml
│   │   ├── surface.yaml
│   │   ├── bridge.yaml
│   │   ├── throughline.yaml
│   │   ├── trails.yaml
│   │   ├── signals.yaml
│   │   ├── ladder.yaml
│   │   └── decksmith.yaml
│   └── audiences/                  ← one YAML file per audience
│       ├── all_staff.yaml
│       ├── student.yaml
│       ├── collaborator.yaml
│       └── self.yaml
├── templates/
│   ├── component_card.md.j2        ← one component, one audience
│   ├── audience_explainer.md.j2    ← whole ecosystem, one audience
│   └── ecosystem_overview.md.j2    ← one-page intro, all audiences
├── outputs/
│   └── (generated .md files go here, committed)
├── ladder.py                       ← the generator
└── AGENTS.md                       ← this file
```

---

## Locked Decisions

### Source of truth format

YAML. One file per component in `data/components/`. One file per audience in
`data/audiences/`. These files are hand-editable in a text editor. No special tooling
required to update them.

### Component YAML schema

Every component file must have all required fields. If a field is missing, the generator
must fail with a clear message naming the missing field. Do not generate with placeholders.

```yaml
name: Surface
layer: retrieval
status: proposal                    # proposal | in-progress | built
one_line: Resurfaces older notes when they are likely to be relevant again.
problem: Notes get captured and forgotten. The archive becomes a graveyard.
inputs:
  - embedding index
  - link graph
  - recent daily notes
outputs:
  - ranked list of notes worth revisiting
  - optional weekly resurfacing digest
dependencies:
  - notes parse-embeddings
  - notes parse-links
example: During a weekly review, Surface shows three notes from two years ago that
         are semantically close to what you wrote this week.
audience_value:
  all_staff: You stop losing things you used to know.
  student: Your notes from September become useful again in March.
  collaborator: The ranking function is inspectable and tunable.
  self: The decay model needs a visit — current scoring ignores recency.
next_rung:
  all_staff: Ask the user to show you a real resurfacing result from his own notes.
  student: Try keeping a daily note for two weeks and run a search at the end.
  collaborator: The scoring function in query_embeddings.py is the place to start.
  self: Decide whether Surface should expose why it ranked something — explainability.
limitations:
  - Quality depends on embedding index coverage
  - Does not distinguish revisiting from having already acted on a note
```

### Audience YAML schema

```yaml
id: all_staff
name: Library Colleagues (All-Staff)
description: Mixed technical literacy. No assumed AI or PKM background.
             Some consumer AI experience. Skeptical and curious in equal measure.
vocabulary_level: plain                 # plain | accessible | technical
omit:
  - implementation details
  - model names
  - vector indices
  - ChromaDB
lead_with: what the system does for a person, not how it works
frame: personal and practical — "here is what I built and why it matters to you"
prior_knowledge:
  - information literacy
  - library workflows
  - general consumer AI experience
first_questions:
  - What is this, and what does it actually do for you?
  - How is this different from just using Google Docs or Obsidian or ChatGPT?
  - Why are you showing us this — is this something we could use?
desired_outcome: basic understanding + enough curiosity to ask one good question
```

### Ecosystem YAML schema

`data/ecosystem.yaml` holds content for the one-page overview:

```yaml
system_name: Note System
tagline: A local-first knowledge system for building and surfacing what you know.
what_it_is: >
  A personal knowledge system that lives on your own machine. You capture notes in
  plain text, and a set of tools helps you find connections, resurface forgotten ideas,
  and communicate what you know to different audiences.
why_it_matters: >
  Notes get captured and forgotten. Search helps you find things you know to look for.
  This system helps you find things you forgot you knew.
local_first_note: >
  Everything runs on your machine. No subscription. No cloud account required.
  Your notes stay yours.
layers:
  - id: capture
    name: Capture
    description: Daily notes, inbox, audio ingestion
  - id: organization
    name: Organization
    description: Routing, tagging, stub creation
  - id: retrieval
    name: Retrieval
    description: Surface, Bridge, Throughline — finding what matters
  - id: sensemaking
    name: Sensemaking
    description: Trails, Signals — understanding patterns
  - id: communication
    name: Communication
    description: Ladder — explaining the system to others
  - id: presentation
    name: Presentation
    description: Decksmith — turning content into decks
components_in_order:
  - note-system
  - surface
  - bridge
  - throughline
  - trails
  - signals
  - ladder
  - decksmith
```

### Template design

Use Jinja2 for templating. `pip install jinja2` — single dependency. Do not use
f-strings for templates; Jinja2 lets templates be edited without touching Python.

**component_card.md.j2** — one component, one audience:

```jinja2
# {{ component.name }}
*{{ component.layer | title }} layer · {{ component.status }}*

{{ component.audience_value[audience.id] }}

**The problem it solves**: {{ component.problem }}

**An example**: {{ component.example }}

**Next rung for you**: {{ component.next_rung[audience.id] }}
```

**audience_explainer.md.j2** — whole ecosystem for one audience:

Covers: what is this, the six-layer map, three component spotlights selected for
relevance to this audience, limitations honestly stated, what this audience could do next.

**ecosystem_overview.md.j2** — one-page intro for any audience:

Covers: what_it_is, why_it_matters, local_first_note, the six layers briefly,
status of what is built vs. proposed. No jargon. Usable as a talk-opener slide in prose.

---

## CLI Interface

```
# Single component, single audience — the minimal unit
python ladder.py generate --audience all_staff --component surface

# Ecosystem overview — whole system, single audience
python ladder.py generate --audience all_staff --overview

# All components for one audience — batch within audience
python ladder.py generate --audience all_staff --all-components
```

Output goes to `outputs/`. File naming:
- `outputs/component_card__surface__all_staff.md`
- `outputs/audience_explainer__all_staff.md`
- `outputs/ecosystem_overview.md`

Overwrite existing outputs without prompting — outputs are generated artifacts.

### Error behavior

- Missing required YAML field: fail with `ValueError: component 'surface' is missing required field 'example'`
- Unknown audience ID: fail with `ValueError: unknown audience 'workshop' — valid: all_staff, student, collaborator, self`
- Unknown component name: fail with `ValueError: unknown component 'route' — see data/components/`
- Missing `next_rung` for an audience: fail with the field name and the missing audience key

---

## Build Order

### Step 1: Data files

Write all YAML files before writing any Python. The data is the hard part.

**Components to populate** (all 8):

| Component | Layer | Status | Notes |
|---|---|---|---|
| note-system | foundation | built | The base system — daily notes, inbox, notes CLI, embedding index |
| surface | retrieval | proposal | Resurfaces notes by semantic proximity to recent writing |
| bridge | retrieval | proposal | Detects cross-domain connections across the corpus |
| throughline | retrieval | in-progress | Multi-span semantic search — being built at hackathon |
| trails | sensemaking | proposal | Reconstructs how an idea developed across time |
| signals | organization | proposal | Extracts structured observations from prose |
| ladder | communication | in-progress | This tool — generates audience-specific explainers |
| decksmith | presentation | proposal | Generates editable decks from structured content |

**Audiences to populate** (all 4): `all_staff`, `student`, `collaborator`, `self`

Focus `all_staff.yaml` first — it is the design-anchor and the demo audience.

**Voice rule** embedded in every template and every example:
> Every explainer must contain at least one sentence that only makes sense if you know
> this specific system — a real example, a real number, a real workflow step. A generic
> description is wrong even if technically accurate.

### Step 2: ladder.py

Single script. No external dependencies beyond Jinja2.

```python
import argparse
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

DATA_DIR = Path(__file__).parent / 'data'
TEMPLATES_DIR = Path(__file__).parent / 'templates'
OUTPUT_DIR = Path(__file__).parent / 'outputs'

def load_component(name: str) -> dict: ...
def load_audience(id: str) -> dict: ...
def load_ecosystem() -> dict: ...
def validate_component(data: dict, name: str) -> None: ...  # raises on missing fields
def validate_audience(data: dict, id: str) -> None: ...

def generate_component_card(component_name: str, audience_id: str) -> str: ...
def generate_audience_explainer(audience_id: str) -> str: ...
def generate_ecosystem_overview() -> str: ...

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    gen = subparsers.add_parser('generate')
    gen.add_argument('--audience', required=True)
    gen.add_argument('--component', default=None)
    gen.add_argument('--overview', action='store_true')
    gen.add_argument('--all-components', action='store_true')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.command == 'generate':
        if args.overview:
            content = generate_ecosystem_overview()
            out = OUTPUT_DIR / 'ecosystem_overview.md'
            out.write_text(content)
            print(f'wrote {out}')
        elif args.component:
            content = generate_component_card(args.component, args.audience)
            out = OUTPUT_DIR / f'component_card__{args.component}__{args.audience}.md'
            out.write_text(content)
            print(f'wrote {out}')
        elif args.all_components:
            audience = load_audience(args.audience)
            for yaml_file in (DATA_DIR / 'components').glob('*.yaml'):
                name = yaml_file.stem
                content = generate_component_card(name, args.audience)
                out = OUTPUT_DIR / f'component_card__{name}__{args.audience}.md'
                out.write_text(content)
                print(f'wrote {out}')

if __name__ == '__main__':
    main()
```

### Step 3: Templates

Write three templates in `templates/`. Each template should:
- Use the component's `audience_value[audience.id]` as the opening — that is the hook
- Include the `status` field visibly when status is `proposal` (e.g., "This is proposed, not yet built")
- End with `next_rung[audience.id]` — the call to action
- Never use technical vocabulary not in `data/audiences/<id>.yaml` vocabulary_level

Templates are Jinja2 markdown. Keep them readable as raw text, not just as rendered output.

### Step 4: Example outputs

After the generator works, produce the three demo outputs and commit them:

1. `outputs/ecosystem_overview.md` — talk-opener prose, all audiences
2. `outputs/component_card__surface__all_staff.md` — no jargon, one example, the hook
3. `outputs/component_card__surface__collaborator.md` — architecture visible, tensions named

These are the proof-of-concept artifacts. They should be usable directly in a talk or
handed to a colleague without further editing.

---

## Voice Constraints

Bake these into the templates — not enforced by code, but enforced by structure:

**Avoid in all outputs:**
- AI hype language: "revolutionary," "transformative," "supercharge"
- Passive institutional voice: "it is believed that," "one might consider"
- Technical jargon for `all_staff` and `student` audiences: no "embeddings," "ChromaDB,"
  "vector index," "cosine similarity" without a plain-language translation immediately after
- Completeness theater: do not list every feature; pick the ones that matter for this audience

**Required in every output:**
- One concrete example grounded in the user's actual system (not hypothetical)
- The `next_rung` — what this audience could do or engage with next
- Status transparency — if something is a proposal, say so

**Central metaphors** (use them, don't explain them):
- "The library as a ladder" — equity frame; there is always a rung they can reach
- "Local-first" — runs on your machine, no subscription, your files stay yours
- "Explanation as part of the system" — Ladder is not documentation added after; it is a tool

---

## What Success Looks Like

1. `python ladder.py generate --audience all_staff --component surface` runs without error
2. The output could be handed to a library colleague who has never heard of a personal note system
   and they would understand what it is trying to do
3. `python ladder.py generate --audience collaborator --component surface` produces
   visibly different content — architecture visible, design tensions named
4. The YAML files are editable in a text editor without running anything first
5. A new component can be explained in under ten minutes of YAML editing

---

## What to Leave for Later

- Model-assisted tone rewriting (template-driven is the v1; model pass is v2)
- Batch generation across all audiences and all components (`--all` flag)
- Integration with the `sb` CLI
- Workshop handout format (deferred — Decksmith handles presentation)
- Full collaborator brief (deferred)
- Scholarship citations in body text (optional appendix only)
- Route, Voice Loop, Stub Triage, and other codex-sb-tooling proposals not listed here

---

## Dependencies

- Python 3.10+
- `jinja2` — templating (`pip install jinja2`)
- `pyyaml` — YAML loading (`pip install pyyaml`)
- No other dependencies. No model calls. No network.
