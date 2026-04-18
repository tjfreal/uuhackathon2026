# Decksmith Roadmap

## Purpose

Build a local-first presentation generator that turns structured project material into editable slide decks.

## Current State

Decksmith is now in a shareable early-tool state.

What exists now:

- a reusable AppleScript renderer in [scripts/build_presentation_template.applescript](scripts/build_presentation_template.applescript)
- a deck-package pattern under [outputs](outputs)
- multiple working example decks
- documentation that explains the current format and workflow

The next work is not “prove this can work.” That part is done. The next work is hardening the authoring model without making the system heavy.

## Phase 1: Authoring Reference
Status: complete

Goal:

- document the slide row format and config fields more explicitly

Deliverable:

- a concise authoring reference with examples and supported layouts

## Phase 2: Package Creation Workflow
Status: next

Goal:

- make creating a new deck package more deliberate and less copy-paste fragile

Possible outputs:

- a documented package-creation checklist
- a small helper script or template copier if it proves necessary

## Phase 3: Theme And Layout Validation
Status: active

Goal:

- confirm how robust the current source model is across different themes and deck styles

Questions:

- do the current layouts hold up across multiple Keynote themes?
- does the image placement logic need constraints or just better documentation?

## Phase 4: More Specific Image Placement
Status: next

Goal:

- let slides place images more deliberately than the current centered or sidebar presets

Why:

- the current layout vocabulary is useful, but it still tends to stack images into generic middle-of-slide placements
- some decks need image placement that follows the narrative rhythm of the slide, not just a small preset list

Possible directions:

- add named anchor positions such as `top-right`, `bottom-right`, `bottom-left`, and `top-left`
- support bounded image frames rather than one global fit area
- allow image placement zones that vary by slide layout
- optionally support explicit margins or normalized x/y placement if the simpler presets stop being enough

Guardrails:

- keep the authoring model simple enough to write by hand
- prefer a small number of meaningful placement controls over a full manual layout system
- avoid turning Decksmith into a coordinate-heavy design tool unless real decks clearly require it

## Phase 5: Format Stability
Status: active

Goal:

- decide how long the delimiter-based source format should remain the default

Decision points:

- stay with the current `|||` format
- adopt markdown frontmatter later
- add a preprocessing step only if it solves a real pain point

## Phase 6: Versioning Strategy
Status: future

Goal:

- decide how generated deck artifacts should relate to the source packages

Questions:

- should `.key` and `.pptx` always be ignored?
- should example generated decks remain in the repo as demonstrations?
- where should the boundary live between source of truth and convenient artifact?

## Immediate Next Steps

1. Decide whether one starter package should become the canonical example.
2. Define the next image-placement vocabulary beyond `full`, `center`, and sidebars.
3. Test one more deck with a different theme and image mix.
4. Decide whether generated deck binaries should remain tracked for examples or be left out of version control.
5. Consider a helper for creating a new deck package from a template.

## Decisions To Lock

- long-term source format
- how much layout vocabulary to support before complexity outweighs value
- how specific image placement should become before it stops being pleasant to author
- whether deck generation should stay AppleScript-first or gain a preprocessing step
- how to treat generated `.key` and `.pptx` files in the long term
