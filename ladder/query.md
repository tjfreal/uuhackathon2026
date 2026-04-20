# Ladder Build Query

Use this file to answer the questions that define the first great version of `Ladder`.

The goal is to remove ambiguity before building: what `Ladder` explains, who it is for, what inputs it needs, what outputs it should generate, and what a successful hackathon slice actually looks like.

## Critical Questions

Answer these first. They determine the architecture.

1. What is the primary thing `Ladder` explains in v1?
   - the whole note-system ecosystem
   - one tool at a time
   - both, with ecosystem overview plus per-tool explainers

2. What is the main job of `Ladder` in this repo right now?
   - onboarding new people into the system
   - producing audience-specific documentation
   - supporting talks, classes, or workshops
   - helping you clarify the system while designing it

3. What is the smallest version that would feel genuinely useful by the end of the hackathon?
   - a schema only
   - a schema plus templates
   - a generator that emits markdown explainers
   - a generator plus 1-3 polished example outputs

4. What must `Ladder` do well enough that you would call it successful?
   - make the system understandable to outsiders
   - make audience differences explicit
   - generate reusable docs quickly
   - surface the “next rung” for a given audience

## Audience

5. Which audiences matter most for the first release?
   - librarians
   - students
   - collaborators
   - workshop attendees
   - yourself
   - another audience not listed above

6. Which one audience should be treated as the design anchor for v1?

7. For each target audience, what are the first three questions they need answered?

8. What does each audience already know coming in?
   - note-system concepts
   - AI literacy concepts
   - library/information literacy language
   - nothing at all

9. What should be intentionally simplified, omitted, or deferred for each audience?

10. What is the desired outcome for each audience after reading a `Ladder` explainer?
   - basic understanding
   - confidence to try the system
   - ability to teach it
   - ability to critique or collaborate on it

## Scope And Content Model

11. What are the canonical components `Ladder` needs to explain first?
   - `Surface`
   - `Bridge`
   - `Trails`
   - `Signals`
   - `Throughline`
   - `Ladder`
   - something else

12. What fields does every component need in the source-of-truth data?
   - name
   - one-sentence purpose
   - problem it solves
   - inputs
   - outputs
   - dependencies
   - example workflow
   - audience-specific value
   - limitations

13. Should `Ladder` explain only stable parts of the system, or also proposal-level concepts and unfinished tools?

14. How important is it that `Ladder` makes relationships between tools explicit rather than describing them in isolation?

15. What kind of examples are required for the outputs to feel concrete?
   - example user journey
   - example workflow through multiple tools
   - before/after explanation
   - institutional use case
   - classroom/workshop use case

## Output Design

16. What outputs should v1 generate?
   - one-page explainer
   - short “what is this?” summary
   - workshop handout
   - speaker notes / talk framing
   - collaborator onboarding brief

17. What should a generated explainer always contain, regardless of audience?

18. What should change by audience?
   - tone
   - vocabulary
   - depth
   - examples
   - ordering of sections
   - calls to action

19. How deterministic should the first version be?
   - fully template-driven
   - template-driven with optional model rewrite pass
   - model-assisted drafting from the start

20. What would make an output feel wrong, even if it is technically accurate?
   - too abstract
   - too academic
   - too product-marketing-like
   - too insider-heavy
   - too generic

## Voice And Framing

21. What voice should `Ladder` outputs have?
   - scholarly
   - practical
   - invitational
   - institutional
   - workshop-friendly
   - personal but rigorous

22. Which phrases, frames, or metaphors are central and should recur?
   - “the library as a ladder”
   - “next reachable rung”
   - “explanation as part of the system”
   - “AI literacy / information literacy bridge”

23. Which tones or rhetorical habits should be avoided?

24. Should outputs explicitly connect the system to library and AI-literacy scholarship in v1, or should that stay optional?

## Build And Data Decisions

25. Where should the source-of-truth data live?
   - JSON
   - YAML
   - markdown frontmatter
   - a small Python module

26. Who is expected to maintain that source data, and how often will it change?

27. Do you want the first implementation to be readable and hand-editable before it is elegant?

28. Should generated files be committed to the repo, or treated as disposable build artifacts?

29. What is the expected command-line interface for v1?
   - generate one audience for one tool
   - generate one audience for the whole ecosystem
   - generate all supported outputs in a batch

30. What should happen when required data is missing?
   - fail loudly
   - generate with placeholders
   - skip incomplete sections

## Demo And Evaluation

31. What exact demo would best prove `Ladder` works?
   - one tool explained for two different audiences
   - one ecosystem overview plus one audience-specific variant
   - one workshop-ready explainer someone else could use

32. What should the final example outputs be for this repo?

33. How will you judge whether the generated explanations are actually good?
   - clarity to outsiders
   - fidelity to the system
   - usefulness in teaching
   - ease of reuse
   - speed of generation

34. Who would you most want to hand a generated `Ladder` output to first?

35. What would cause you to say the current implementation missed the point?

## Recommended V1 Defaults

If you want to move fast, these are reasonable defaults to either confirm or reject.

- Explain both the ecosystem and individual tools.
- Start with `self`, `librarian`, and `student` audiences.
- Use a hand-edited YAML or JSON source-of-truth file.
- Keep v1 deterministic and markdown-first.
- Generate:
  - a short overview
  - a one-page audience explainer
  - one concrete example output for repo/demo use
- Treat relationship-mapping between tools as a core requirement, not a nice-to-have.
- Include at least one workflow example and one institutional or teaching relevance section.

## Fast Answer Format

If you want a compact way to respond, fill this in:

```md
Primary object explained:
Main job in this repo:
Design-anchor audience:
Other audiences:
Canonical components:
Required component fields:
V1 outputs:
Generation style:
Voice:
Scholarship references in v1:
Source-of-truth format:
CLI shape:
Best demo:
Success criteria:
```
