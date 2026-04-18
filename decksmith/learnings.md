# Learnings

## Core Learning

Decksmith became useful only once content and rendering were separated. A one-off slide script can prove feasibility, but it does not create a reusable presentation workflow.

## What Matters Most

- deck content should change without editing generator logic
- speaker notes should travel with the slide source
- local editability matters more than full automation
- a generated deck should still be easy to refine by hand
- copying a self-contained deck package is a feature, not a smell

## What The Cleanup Clarified

- the repo works best when it reads as a tool with example outputs, not a pile of generated decks
- the `outputs/` directory is clearer when framed as a set of portable deck packages
- generated `.key` and `.pptx` files are useful artifacts, but the source files remain the real source of truth

## Constraint

Decksmith has to support public explanation of work that may begin in private or messy project folders. That means the system should make it easy to author from sanitized material rather than assuming raw project notes are presentation-ready.

## Important Model Shift

The image model improved once images became explicit per-slide attachments rather than directory-wide assets to dump into a deck.

The better abstraction is:

- slides are the unit of intent
- images belong to specific slides
- each slide can declare one image and one small layout mode

That gives a meaningful jump in usefulness without dragging the system into full layout-engine complexity.

## Practical Lesson

Presentation generation is closer to document compilation than to automatic design. The goal is not to remove judgment. The goal is to make repeated structure cheap so human judgment can focus on framing and story.

Another practical lesson is that a small source format can still carry a lot of intent if the right fields exist. In this case, speaker notes plus a single image attachment per slide cover a large portion of the actual need.

## What Worked

- separating the shared template from per-deck packages
- keeping a package-local `build_presentation.applescript`
- preserving speaker notes in generated decks
- using a deliberately small image-layout vocabulary
- validating the pattern on multiple real decks instead of one demo

## Current Maturity

Decksmith is no longer just a concept. It now has:

- a reusable AppleScript template
- multiple successful deck packages
- functioning Keynote generation
- functioning PowerPoint export
- image-aware slides
- a repo structure that can be shared without much explanation

## Near-Term Direction

- keep the source format simple
- keep the example packages explicit
- add documentation before adding major capability
- resist expanding layout controls until a real deck clearly demands it
