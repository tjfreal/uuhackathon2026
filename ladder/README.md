# Ladder

## Potential

Ladder is a communication and onboarding layer for the note system itself.

Its purpose is not to organize notes directly. Its purpose is to explain the system clearly to different audiences, using examples, concepts, and levels of complexity that match where those audiences are starting from.

Possible output modes:

- for self-reflection
- for colleagues
- for librarians
- for students
- for workshops or talks

`Ladder` treats explanation as part of the system, not as an afterthought.

It is also more meta than a documentation generator alone. `Ladder` explains the system, but it also explains why the system is shaped the way it is, what kind of human problem it is trying to solve, and how a person might find a next step into it.

## Lineage

The idea predates the current note-system proposals.

The original concept of "the library as a ladder" came out of help desk management and a people-first view of library service: no matter where someone starts, there should be a rung they can reach next. The point was not only to provide answers, but to notice where a person was starting and help them move one step further without making them feel excluded, behind, or out of place.

`Ladder` carries that service philosophy forward into note-system scaffolds and knowledge work in the automation age. The question is no longer only how to help someone at a desk or service point. It is also how to help people enter increasingly technical systems of note-making, retrieval, AI assistance, and personal knowledge work without requiring insider language or prior commitment to the whole stack.

That lineage matters because it keeps `Ladder` grounded. This is not just a system for describing tools. It is a people-first layer for helping someone find a usable next rung into a changing knowledge environment.

## Inputs

Ladder depends on a maintained map of the system and its tools:

- feature descriptions
- relationships between tools
- example workflows
- outputs from other tools like `Surface`, `Bridge`, `Trails`, and `Signals`
- optional templates for different audiences

It can be implemented as a template-driven markdown generator, with optional local-model rewriting for tone or audience adaptation.

The core idea is to generate explainers that answer questions such as:

- what does this system actually do
- what problem does each part solve
- what does a beginner need first
- how do these pieces connect
- why does this matter in library, learning, and AI-literacy contexts

## Current Implementation

This repo now contains a first local implementation of `Ladder`.

- `data/` holds the hand-edited source of truth for the ecosystem, audiences, and components
- `templates/` holds the markdown template shapes the generator is based on
- `ladder.py` generates markdown outputs into `outputs/`

The first slice is intentionally small and deterministic:

- one ecosystem overview
- one audience explainer
- component cards for one audience at a time

### CLI

```bash
python3 ladder.py generate --audience all_staff --overview
python3 ladder.py generate --audience all_staff --explainer
python3 ladder.py generate --audience all_staff --component surface
python3 ladder.py generate --audience collaborator --all-components
```

Generated files are written to `outputs/` and are meant to be committed as readable artifacts.

## What It Enables

`Ladder` supports:

- public explanation of the system
- workshop and talk preparation
- clearer design thinking while building
- audience-specific documentation
- better translation between personal tooling and institutional relevance

This is important if the system is meant to become an example that other people can understand, critique, and learn from.

## Real-World Connections

This tool connects directly to information literacy and AI literacy work in libraries. A strong system is not enough on its own; it must also be explainable, adaptable, and teachable.

- Leo S. Lo's survey work on AI literacy in academic libraries argues for stratified and tailored approaches to AI education because readiness and competence vary widely.
  Source: https://crl.acrl.org/index.php/crl/article/view/26409
- Work on library instructors' views of ChatGPT suggests that libraries can play an important role in navigating AI through instruction, but only if tools and concepts can be integrated thoughtfully.
  Source: https://crl.acrl.org/index.php/crl/article/view/26938
- Recent work on student generative AI use also highlights the connection between AI literacy and information literacy.
  Source: https://crl.acrl.org/index.php/crl/article/view/27271

`Ladder` is also consistent with knowledge-building theory, especially where the goal is not just personal learning but contribution to broader understanding.

## Why It Matters

You described the library as a ladder: no matter what someone knows, there should be a rung they can reach next.

`Ladder` matters because it turns that principle into a design requirement. The system should not only help build knowledge; it should help people enter the work of building knowledge.

In that sense, `Ladder` is both a communication layer and a values check on the rest of the system. If a note-system scaffold only works for the person who built it, or only makes sense to technically fluent insiders, it has failed the ladder test.
