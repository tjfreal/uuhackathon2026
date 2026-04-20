# Ladder Build Response

Answers to the critical questions in `query.md`.
Written to remove ambiguity before building.

---

## Fast Answer

```
Primary object explained:    Both — the ecosystem as a whole and individual tools within it.
                             The ecosystem overview is the hook; the per-tool explainers
                             are the substance. They should fit together coherently,
                             but "one coherent document" is not itself a design rule.

Main job in this repo:       Supporting talks, classes, and workshops. Specifically,
                             an all-staff presentation where the user shows colleagues what
                             the system does and why it matters. This is the demo context.

Design-anchor audience:      Library colleagues at a staff meeting. Mixed technical literacy.
                             No assumption of AI familiarity. Some will be skeptical. Some
                             will be curious. None should feel left out.

Other audiences:             Students (especially in workshops), collaborators building
                             adjacent tools, the user himself for design clarity while building.

Canonical components:        Surface, Bridge, Trails, Signals, Ladder, Decksmith —
                             plus the underlying note-system system they sit on top of.
                             See component definitions below.

Required component fields:   name, one-sentence purpose, problem it solves, inputs,
                             outputs, audience-specific value, example, limitations.

V1 outputs:                  One ecosystem overview (short). One one-page audience explainer
                             (librarian/all-staff version as the anchor). One concrete example
                             output that could be handed to someone or shown on screen.

Generation style:            Template-driven markdown first. Optional model rewrite pass
                             for tone. Keep it deterministic and inspectable in v1.

Voice:                       Practical and invitational. Personal but rigorous.
                             Grounded in real examples from the actual system.

Scholarship references:      Optional in v1. Do not lead with citations.
                             They belong in an appendix or as inline footnotes, not the body.

Source-of-truth format:      YAML. Hand-editable, readable, easy to extend.

CLI shape:                   `ladder generate --audience librarian --component surface`
                             as the minimal unit. Batch mode (all audiences, all components)
                             as a second-tier target.

Best demo:                   One tool explained for two audiences side by side.
                             The contrast is the demo. Same system, different entry point.

Success criteria:            A colleague at all-staff who has never heard of a personal note system
                             says "I understand what this is trying to do" — not "that sounds
                             complicated."
```

---

## Critical Questions — Full Answers

### 1. What does Ladder explain in v1?

Both the ecosystem and individual tools. The ecosystem overview answers the first question
any audience has: "what is this, actually?" The per-tool explainers give them somewhere
to go next based on what they care about. They should share a clear framing and feel like
parts of the same project, but they do not need to collapse into one master document.

### 2. What is the main job of Ladder in this repo right now?

Supporting talks and workshops, with all-staff as the primary use case. the user is building
toward a presentation where he shows library colleagues — people of widely varying
technical backgrounds — what he has been building and why it matters. Ladder is the
tool that generates the explainer materials for that context. It also helps clarify
the system while designing it, because writing a clear audience-specific explanation
of a component forces design thinking.

It also has a meta role. Ladder does not only explain the system. It helps the system
show its own values, human entry points, and reasons for existing. In that sense,
explanation is part of the architecture rather than a layer added afterward.

### 3. Smallest version that feels genuinely useful by end of hackathon?

A generator that emits markdown explainers, plus one to three polished example outputs.
The schema alone is not enough. Templates alone are not enough. There must be one output
that could be handed to a colleague or shown on a projector and feel real.

### 4. What must Ladder do well enough to call it successful?

- Make the system understandable to outsiders who are not technical
- Make audience differences explicit — not just one explainer that waves at different people
- Surface the "next rung" — tell each audience what they could engage with next if they want more

---

## Audience

### 5–6. Design-anchor audience

**Library colleagues at all-staff.** Mixed AI literacy. Some have heard of ChatGPT; some
use it daily; some are skeptical of it. None should be assumed to know what a personal note system is,
what embeddings are, or why local-first matters. The anchor is someone who is curious and
open but has not had a reason yet to investigate this kind of tool. If the explainer works
for them, it works for everyone else with minor adaptation.

### 7. First three questions each audience needs answered

**Library colleagues (all-staff):**
1. What is this, and what does it actually do for you?
2. How is this different from just using Google Docs or Obsidian or ChatGPT?
3. Why are you showing us this — is this something we could use?

**Students (workshop context):**
1. What does it mean to have a personal note system?
2. How does AI fit into this without it doing everything for you?
3. Can I build something like this, or is this only for technical people?

**Collaborators (building adjacent tools):**
1. What does the system currently do well and where does it break?
2. How do the tools relate to each other — what depends on what?
3. What is the design philosophy — what would a good contribution look like?

**Self (design clarity):**
1. Does the thing I just built actually solve the problem it was supposed to solve?
2. Can I explain this to someone who was not in the room when I designed it?
3. What would I cut if I had to?

### 8. What each audience already knows coming in

- **All-staff**: information literacy, library workflows, probably some consumer AI experience
- **Students**: varies widely; some AI literacy, very little PKM exposure
- **Collaborators**: technical fluency, probably PKM adjacent, may not know the specifics
- **Self**: everything — the challenge is not knowledge, it is forcing rigor and simplicity

### 9. What to simplify, omit, or defer per audience

**All-staff**: Omit implementation details entirely. No mention of ChromaDB, embeddings,
vector indices, or local models. Defer the "how it works" to a follow-up. Lead with
what it does for a person, not how it does it.

**Students**: Simplify the tool-chain into three moves: capture, connect, communicate.
Omit the system architecture. Defer multi-tool workflows — start with the idea of a
single daily note and what happens to it.

**Collaborators**: Omit the personal backstory; lead with the architecture and design
principles. Defer the equity framing — they can get there on their own once they see
the code.

**Self**: Nothing should be omitted. This is the one audience that needs the full map
including what is broken, unfinished, or wrong.

### 10. Desired outcome per audience after reading

- **All-staff**: basic understanding + enough curiosity to ask one good question
- **Students**: confidence to try one part of the system, even just a daily note habit
- **Collaborators**: ability to critique or contribute — they should know where the
  seams are
- **Self**: ability to teach it — the strongest test of whether the design is clear

---

## Scope and Content Model

### 11. Canonical components Ladder needs to explain

These are the tools in the ecosystem. All are proposals-stage except the underlying
note-system system, which exists and runs.

| Component | Layer | What it does |
|---|---|---|
| **Note System** (the base) | Foundation | Local markdown corpus + daily notes + review passes + `sb` CLI |
| **Surface** | Retrieval | Resurfaces old notes based on current relevance |
| **Bridge** | Retrieval | Detects meaningful cross-domain connections across the corpus |
| **Trails** | Sensemaking | Reconstructs how an idea developed across time and notes |
| **Signals** | Organization | Extracts structured observations from freeform prose |
| **Ladder** | Communication | Generates audience-aware explainers of the system |
| **Decksmith** | Presentation | Generates editable presentation decks from structured content |

`Throughline` is intentionally out of scope for this project for now. It is being built
concurrently elsewhere and should not be treated as a dependency or a current input to
the Ladder implementation.

### 12. Required fields per component in source data

```yaml
name: Surface
layer: retrieval
one_line: Resurfaces older notes when they are likely to be relevant again.
problem: Notes get captured and forgotten. The archive becomes a graveyard.
inputs:
  - embedding index
  - link graph
  - tag index
  - recent daily notes
outputs:
  - ranked list of notes worth revisiting
  - optional weekly resurfacing digest
dependencies:
  - notes parse-embeddings
  - notes parse-links
  - notes parse-hashtags
example: During a weekly review, Surface shows three notes from two years ago that
         are semantically close to what you wrote this week.
audience_value:
  all_staff: You stop losing things you used to know.
  student: Your notes from September become useful again in March.
  collaborator: The ranking function is inspectable and tunable.
limitations:
  - Quality depends on embedding index coverage
  - Does not yet distinguish between revisiting and having already acted on a note
status: proposal
```

### 13. Should Ladder explain only stable parts or also proposals?

Both, clearly labeled. The base note-system system is stable and real. The tools
are proposals. The explainer should make this distinction visible — not to
undermine the work, but because honesty about what is built versus what is imagined
is itself a demonstration of the system's values. "Here is what exists. Here is what
it could become" is a stronger talk than pretending everything is finished.

### 14. How important is relationship-mapping between tools?

Critical, not optional. The tools only make sense in relationship to each other.
Surface feeds Bridge. Trails needs the link graph that parse-links builds. Decksmith
packages what Ladder generates. An explainer that describes each tool in isolation
misses the point of the whole proposal set. The index.md in codex-sb-tooling has
the right instinct here — the six layers (capture, organization, retrieval,
sensemaking, communication, presentation) are the scaffold for explaining how they fit.

### 15. What kinds of examples are required

**For the demo:** one example user journey through multiple tools — capture a daily
note, Surface finds a related old note a week later, Bridge connects it to something
from a different domain, Trails shows the idea's history, and Ladder explains all of
this at all-staff. That arc is the demo.

**For the outputs:** at least one before/after — "here is what a raw daily note looks
like, here is what the system does with it over time."

---

## Output Design

### 16. What outputs should v1 generate?

- **Ecosystem overview**: one page, all audiences, explains what the system is and
  why it exists. This is the talk-opener slide in prose form.
- **Audience explainer**: one page per audience, explains the same system from their
  entry point. The all-staff version is the v1 anchor.
- **Component card**: a short structured description of one tool for one audience.
  The unit that can be mixed and matched into talks or handouts.

Not in v1: workshop handout (deferred), speaker notes format (deferred — Decksmith
handles this), full collaborator brief (deferred).

### 17. What every explainer must contain regardless of audience

- What the system does in one sentence
- The problem it solves
- One concrete example of it working
- What the reader could do next (the next rung)

### 18. What changes by audience

- Vocabulary (embeddings vs. "the system finds related things")
- Examples (health notes vs. research notes vs. course materials)
- Depth (architecture visible for collaborators, invisible for all-staff)
- Call to action (try it vs. question the design vs. teach it)

### 19. How deterministic should v1 be?

Template-driven with optional model rewrite pass. The template produces a correct
explainer. The rewrite pass adjusts tone for the audience. The template output should
always be inspectable and editable — never a black box.

### 20. What makes an output feel wrong even if technically accurate?

Too abstract. An output that could describe any knowledge management system without
naming one specific thing the user has actually built is wrong. Every explainer should contain
at least one sentence that only makes sense if you know this specific system — a real
example, a real number, a real workflow step.

---

## Voice and Framing

### 21. Voice

**Invitational and practical.** The register is "here is something I built and what
I learned from building it, and here is why I think it might matter to you." It is
personal but grounded. It is not a product pitch, not a research paper, not a
TED talk. It is a colleague showing their work.

It should also preserve the older lineage of the idea. "The library as a ladder"
started as a people-first approach to service work and only later became a way of
thinking about note-system scaffolds and knowledge work in the automation age.
The human purpose should come first in the framing.

### 22. Central phrases and metaphors

- **"The library as a ladder"** — the equity frame. No matter who walks in, there
  is a rung they can reach. The system is designed around this. Explanation is part
  of the system, not an afterthought, because if the system cannot be explained at
  different levels, it has not kept the promise.
- **"The next rung"** — every audience gets told where they could go next if they
  want more. No one is left at the bottom of a ladder with no guidance.
- **"Local-first"** — the system runs on your machine, uses your files, does not
  require a subscription or a cloud account. This is a value, not just a technical
  choice.
- **"Explanation as part of the system"** — Ladder is not documentation added after
  the fact. It is a tool within the system, because a system that cannot explain
  itself has not finished the job.
- **People-first lineage** — the current build grows out of help-desk and library
  service values, then extends those values into note-system scaffolds and knowledge
  work in the automation age.

### 23. Tones and habits to avoid

- Avoid AI hype language ("revolutionary," "transformative," "supercharge")
- Avoid passive institutional voice ("it is believed that," "one might consider")
- Avoid insider density without a bridge — do not use "embeddings," "ChromaDB,"
  or "vector index" for a general audience without offering a plain-language
  translation first
- Avoid completeness theater — do not list every feature; pick the ones that matter
  for this audience and this moment

### 24. Should outputs connect to library and AI literacy scholarship?

Optional in v1, not required. When present, citations should be light — a name and
a claim, not a literature review. The Leo Lo AI literacy work and the knowledge-building
theory in the proposals are appropriate touchstones. They belong at the end or as
optional depth, not in the opening.

---

## Build and Data Decisions

### 25. Where should the source-of-truth data live?

YAML. One file per component, in a `data/` directory. YAML is readable by humans
and parseable by scripts. It can be edited by hand without a special tool. Markdown
frontmatter is an option but makes schema validation harder.

### 26. Who maintains the source data and how often will it change?

the user maintains it. It will change frequently early on as the system evolves and infrequently
once the components stabilize. The format should be easy to update in a text editor
without running the generator first.

### 27. Should v1 be readable and hand-editable before it is elegant?

Yes. Absolutely. A YAML file and a Python template script that any librarian who has
seen Python once could read is better than an elegant framework that only the user can touch.

### 28. Should generated files be committed?

Yes. Commit the generated outputs. They are artifacts, not just build products. A
colleague should be able to read a generated explainer directly from the repo without
running anything. The generator is for updating them, not for gating access to them.

### 29. CLI shape for v1

```
# Minimal unit — one audience, one component
ladder generate --audience librarian --component surface

# Ecosystem overview — one audience, whole system
ladder generate --audience librarian --overview

# Batch — all audiences, all components (deferred to v2)
ladder generate --all
```

### 30. What should happen when required data is missing?

Fail loudly with a clear message naming the missing field. Do not generate with
placeholders — a hallucinated example is worse than no example. Do not silently skip
sections — a partial explainer looks like a finished one and misleads.

---

## Demo and Evaluation

### 31. What demo best proves Ladder works?

One tool explained for two audiences side by side. Show a component card for Surface
written for all-staff and the same card written for a collaborator. The contrast makes
the point: same system, different entry point. This is also the thing a builder can
produce in a hackathon window without overbuilding.

### 32. What should the final example outputs be?

1. Ecosystem overview — suitable for the opening of an all-staff talk
2. Surface explainer for all-staff — concrete, no jargon, one example
3. Surface explainer for collaborators — architecture visible, design tensions named

These three files prove the concept and are directly usable.

### 33. How to judge whether generated explanations are actually good?

**Primary test:** give the all-staff explainer to one colleague who was not in the room
and ask "what does this system do?" If their answer matches what the user intended, the
explainer works.

**Secondary tests:**
- Fidelity — does it describe the actual system, not a generic one?
- Next rung — does it tell the reader what to do next?
- Speed — can a new component be explained in under ten minutes of YAML editing?

### 34. Who to hand the first output to?

A skeptical librarian colleague. Not a technical collaborator. Not a student. The
all-staff context means the hardest audience is the right test. If it lands there,
it lands everywhere.

### 35. What would make the implementation miss the point?

An explainer that explains the system but does not invite the reader anywhere. A tool
that generates technically accurate content that no one would want to read. A generator
so complex that updating a component description requires running a build pipeline.
A document that sounds like a product brochure rather than a person showing their work.

The point is: explanation is part of the system. If the explainer itself feels like
an afterthought, Ladder has failed at its own premise.

The build also misses the point if it forgets the original ladder idea: meeting people
where they are and helping them reach a next rung without assuming they already speak
the language of the system.

---

## Notes on Unresolved Items

**Connectedness of the suite**: The proposals were not designed with Ladder as the
endpoint from the start. Some tools (Surface, Bridge) could be explained now because
they are well-specified. Others (Trails, Signals) are earlier-stage and will produce
weaker explainers until the proposals mature. The generator should handle this gracefully
— a status field in the YAML (proposal / in-progress / built) lets the template
acknowledge where something is in its development without pretending it is finished.
