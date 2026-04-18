# Roadmap

## Current State

The project is now in a shareable state.

What exists now:

- a canonical STL generator in [julia_vase.py](julia_vase.py)
- a fast tuning tool in [julia_vase_playground.html](julia_vase_playground.html)
- a packaged output set in [assets](assets)
- the exploratory history in [archive](archive)
- refreshed public-facing notes in [README.md](README.md), [learnings.md](learnings.md), and [presentation.md](presentation.md)

The cleanup and packaging step is done. The next work is refinement, not organization.

## Phase 1: Lock Named Candidates
Status: next

Goal:

- choose 2-3 explicit parameter profiles worth carrying forward

Deliverable:

- named candidates with saved parameter sets and matching preview STL files

## Phase 2: Refine Shape Language
Status: active

Goal:

- smooth the surface motion without losing the strong vertical character

Main questions:

- can the channels become more wave-like and less trench-like?
- should the outer envelope stay nearly fixed, or breathe more?
- where is the boundary between expressive asymmetry and broken flow?

Deliverable:

- one clearly leading concept candidate

## Phase 3: Increase Fidelity
Status: active but secondary

Goal:

- raise mesh quality once the concept is stable

Main levers:

- `num_layers`
- `num_angles`
- `scan_steps`
- `boundary_refine_steps`
- `max_iter`

Deliverable:

- high-resolution STL builds for the leading candidate

## Phase 4: Render And Print Comparison
Status: next

Goal:

- compare concept quality against fidelity quality in real outputs

Deliverable:

- side-by-side renders
- at least one more physical print
- short notes on what changed perceptually

## Phase 5: Canonical Release Candidate
Status: future

Goal:

- freeze one hero build as the reference object

Deliverable:

- locked parameter profile
- canonical STL
- canonical render
- canonical print photo

## Phase 6: Presentation Package
Status: future

Goal:

- turn the cleaned repository into a concise demo or submission package

Possible outputs:

- short slide deck
- process board using the preview series
- before/after view of early contour methods versus the ring-based generator

Deliverable:

- a presentation-ready bundle built from the current repo structure

## Immediate Next Steps

1. Save the exact parameters for the best current preview variants.
2. Generate one or two higher-fidelity meshes from those settings.
3. Render them side by side.
4. Print the strongest candidate.
5. Decide whether the next bottleneck is still concept or now mostly fidelity.

## Decision Gates

- If higher fidelity improves the form directly, keep pushing resolution.
- If higher fidelity only makes the surface problems more obvious, go back to concept tuning.
- If the print looks better than the render, tune evaluation and lighting before changing geometry.
- If one candidate is clearly ahead, freeze it and build the presentation package around that version.
